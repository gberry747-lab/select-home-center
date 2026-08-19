#!/usr/bin/env python3
"""Milestone completion emails for the SHC Home Tracker.

Each run: pulls the Monday Customer Projects board (+ Kristin's Permitting
board), computes every customer's milestone list exactly like the tracker
pages do, diffs against the last run's snapshot, and emails the customer
when a milestone newly reads Complete. All newly-completed milestones for a
customer batch into ONE email.

Safety rails (same doctrine as warranty_reminder_agent):
- DRY_RUN unless env DRY_RUN=0 - dry runs only log what WOULD send.
- Kill switch: ~/.config/shc/PAUSE-MILESTONE-EMAILS (existence pauses sends).
- First time a customer is seen, their state is baselined silently (no email
  blast for history).
- No Email on the Monday row = no email, logged.
- HEARTBEAT file written every run - silence means the agent is dead, not idle.

Config: ~/.config/shc/smtp.json {"host","port","user","password","from"}
State:  ~/.config/shc/milestone_notify_state.json
Log:    ~/.config/shc/milestone_notify.log

HARD RULE (Gregory): nothing goes to customers until his explicit go-live.
Ship with DRY_RUN on; flip only when he says go.
"""
import json, os, pathlib, smtplib, sys, datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import build_tracker as bt

CFG_DIR = pathlib.Path.home() / ".config/shc"
STATE_F = CFG_DIR / "milestone_notify_state.json"
LOG_F = CFG_DIR / "milestone_notify.log"
HEART_F = CFG_DIR / "milestone_notify.HEARTBEAT"
PAUSE_F = CFG_DIR / "PAUSE-MILESTONE-EMAILS"
SMTP_F = CFG_DIR / "smtp.json"
DRY_RUN = os.environ.get("DRY_RUN", "1") != "0"

def log(msg):
    line = f"{datetime.datetime.now().isoformat(timespec='seconds')} {msg}"
    print(line)
    with open(LOG_F, "a") as f:
        f.write(line + "\n")

def fetch_customers():
    q = ('query{boards(ids:[%s]){items_page(limit:100){items{id name group{title} '
         'column_values{id text column{title type}}}}}}' % bt.BOARD_ID)
    board = bt.monday_query(q)["boards"][0]
    rollup = bt.permit_rollup()
    out = []
    for item in board["items_page"]["items"]:
        if item["group"]["title"] not in bt.ACTIVE_GROUPS:
            continue
        if "NADP" in (item["name"] or "").upper():
            continue
        cols = {cv["column"]["title"]: cv for cv in item["column_values"]}
        email = (cols.get("Email") or {}).get("text", "").strip()
        deal = (cols.get("Deal Number") or {}).get("text", "")
        vin = (cols.get("VIN Number") or {}).get("text", "")
        site_steps = []
        for cv in item["column_values"]:
            if cv["column"]["type"] != "status":
                continue
            t = cv["column"]["title"]
            site_steps.append((t, bt.ES_STEP.get(t, t),
                               bt.status_class(cv.get("text")), "", ""))
        site_steps.sort(key=lambda s_: 0 if s_[0] == "Permitting" else 1)
        pr = bt.permit_match(rollup, item["name"], vin)
        if pr:
            rest = [s_ for s_ in site_steps if s_[0] != "Permitting"]
            site_steps = bt.permit_steps(pr, team_view=False) + rest
        slug = bt.slug_for(item["id"], deal)
        # milestone name -> status class (pre-steps excluded: always done)
        steps = {en: cls for en, _es, cls, _n1, _n2 in site_steps if cls != "na"}
        out.append({"id": str(item["id"]), "name": item["name"], "email": email,
                    "url": f"{bt.SITE}/track/{slug}/", "steps": steps})
    return out

def build_email(name, completed, url):
    first = name.split(",")[0].split(" & ")[0].strip()
    items = "".join(
        f'<tr><td style="padding:6px 0;font-size:16px;color:#1c2340">'
        f'<span style="color:#2e8b57;font-weight:bold">&#10003;</span>&nbsp; {m}</td></tr>'
        for m in completed)
    plural = "milestones" if len(completed) > 1 else "milestone"
    subject = f"Great news, {first} - your home just hit a new {plural}!"
    html = f"""<html><body style="margin:0;background:#f4f5fa;font-family:Arial,Helvetica,sans-serif">
<table width="100%" cellpadding="0" cellspacing="0"><tr><td align="center" style="padding:24px 12px">
<table width="560" cellpadding="0" cellspacing="0" style="max-width:560px;background:#ffffff;border-radius:14px;overflow:hidden">
<tr><td style="background:#101a7a;padding:22px 28px">
<div style="color:#ffffff;font-size:13px;font-weight:bold;letter-spacing:1px">SELECT <span style="color:#f5a623">HOME CENTER</span></div>
<div style="color:#ffffff;font-size:22px;font-weight:bold;margin-top:10px">Your home just moved forward!</div>
</td></tr>
<tr><td style="padding:26px 28px 8px">
<p style="font-size:16px;color:#1c2340;margin:0 0 14px">Hi {first},</p>
<p style="font-size:16px;color:#1c2340;margin:0 0 14px">Just completed on your new home:</p>
<table cellpadding="0" cellspacing="0">{items}</table>
</td></tr>
<tr><td align="center" style="padding:18px 28px 8px">
<a href="{url}" style="background:#f5a623;color:#3a2a00;text-decoration:none;font-weight:bold;font-size:16px;padding:14px 30px;border-radius:10px;display:inline-block">See Your Home Tracker</a>
</td></tr>
<tr><td style="padding:14px 28px 26px">
<p style="font-size:13px;color:#6a7090;margin:0">Questions any time: 912-208-6065 &middot; Se Habla Espa&ntilde;ol<br>
Select Home Center &middot; 6047 Second St. N., Folkston, GA 31537 &middot; SelectHomeCenter.com</p>
</td></tr>
</table></td></tr></table></body></html>"""
    text = (f"Hi {first},\n\nJust completed on your new home:\n" +
            "".join(f"  - {m}\n" for m in completed) +
            f"\nSee your Home Tracker: {url}\n\nQuestions any time: 912-208-6065\n"
            "Select Home Center - Folkston, GA")
    return subject, html, text

def send(to, subject, html, text):
    cfg = json.load(open(SMTP_F))
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = cfg["from"]
    msg["To"] = to
    msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html, "html"))
    with smtplib.SMTP(cfg["host"], cfg["port"]) as s:
        s.starttls()
        s.login(cfg["user"], cfg["password"])
        s.send_message(msg)

def main():
    CFG_DIR.mkdir(parents=True, exist_ok=True)
    paused = PAUSE_F.exists()
    state = json.load(open(STATE_F)) if STATE_F.exists() else {}
    customers = fetch_customers()
    sent = would = 0
    for c in customers:
        prev = state.get(c["id"])
        if prev is None:
            state[c["id"]] = c["steps"]
            log(f"baseline {c['name']} ({len(c['steps'])} milestones, no email)")
            continue
        completed = [m for m, cls in c["steps"].items()
                     if cls == "done" and prev.get(m) != "done"]
        state[c["id"]] = c["steps"]
        if not completed:
            continue
        if not c["email"]:
            log(f"SKIP {c['name']}: completed {completed} but no Email on Monday row")
            continue
        subject, html, text = build_email(c["name"], completed, c["url"])
        if DRY_RUN or paused:
            would += 1
            log(f"DRY-RUN would email {c['email']} ({c['name']}): {completed}")
        else:
            try:
                send(c["email"], subject, html, text)
                sent += 1
                log(f"SENT {c['email']} ({c['name']}): {completed}")
            except Exception as e:
                log(f"ERROR sending to {c['email']} ({c['name']}): {e}")
    json.dump(state, open(STATE_F, "w"), indent=1)
    mode = "PAUSED" if paused else ("DRY_RUN" if DRY_RUN else "LIVE")
    log(f"run complete [{mode}]: {len(customers)} customers, {sent} sent, {would} would-send")
    HEART_F.write_text(datetime.datetime.now().isoformat())

if __name__ == "__main__":
    main()

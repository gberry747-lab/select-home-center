#!/usr/bin/env python3
"""Build private customer 'My Home Tracker' pages on selecthomecenter.com from the
Monday.com Customer Projects board.

SCOPE RULE (do not change): this script may query ONLY the Select Home Center
workspace's Customer Projects board (BOARD_ID below). Never account-wide queries.

Usage:
  python3 scripts/build_tracker.py --demo         # build track/demo/ only, no API
  python3 scripts/build_tracker.py                # build all Active Projects pages

Token: env MONDAY_API_TOKEN, or first line of ~/.config/shc/monday_token
Output: track/<slug>/index.html  (slug = salted hash of the Monday item id, unguessable)
After running, commit + push the repo to deploy (GitHub Pages).
"""
import argparse, hashlib, html, json, os, pathlib, sys, urllib.request

BOARD_ID = "9770686595"          # Customer Projects board, Select workspace ONLY
SITE = "https://selecthomecenter.com"
PHONE = "9122086065"
REVIEW_URL = "REVIEW_URL_PLACEHOLDER"   # set to the Google review link (g.page/r/...)
SALT = "shc-tracker-2026"
ACTIVE_GROUPS = ("Active Projects", "SHS/NADP Projects")
REPO = pathlib.Path(__file__).resolve().parent.parent

# Milestones that come before the site-work statuses on the board.
# v1: these render as complete for every active customer (a deal on the board
# means financing/order/arrival already happened). Refine later if the board
# grows columns for them.
PRE_STEPS_EN = ["Financing approved", "Home ordered", "Home arrived at our lot"]
PRE_STEPS_ES = ["Financiamiento aprobado", "Casa ordenada", "Casa llegó a nuestro lote"]

ES_STEP = {
    "Land Clearing": "Limpieza del terreno", "Dirt Pad": "Plataforma de tierra",
    "Well": "Pozo de agua", "Power Pole": "Poste de electricidad",
    "HVAC": "Aire acondicionado y calefacción", "Electric": "Conexión eléctrica",
    "Steps": "Escalones", "Septic": "Sistema séptico", "Skirting": "Faldón",
    "Trim Out": "Acabados", "Delivery": "Entrega", "Set": "Instalación",
}

def token():
    t = os.environ.get("MONDAY_API_TOKEN")
    if not t:
        p = pathlib.Path.home() / ".config/shc/monday_token"
        if p.exists():
            t = p.read_text().strip().splitlines()[0]
    if not t:
        sys.exit("No Monday token. Set MONDAY_API_TOKEN or write ~/.config/shc/monday_token")
    return t

def monday_query(q):
    req = urllib.request.Request(
        "https://api.monday.com/v2",
        data=json.dumps({"query": q}).encode(),
        headers={"Authorization": token(), "Content-Type": "application/json",
                 "API-Version": "2024-10"})
    with urllib.request.urlopen(req, timeout=30) as r:
        out = json.loads(r.read())
    if "errors" in out:
        sys.exit(f"Monday API error: {out['errors']}")
    return out["data"]

def fetch_board():
    q = f'''query {{ boards(ids: [{BOARD_ID}]) {{
        name
        columns {{ id title type }}
        groups {{ id title }}
        items_page(limit: 100) {{ items {{
            id name group {{ title }}
            column_values {{ id text column {{ title type }} }}
        }} }}
    }} }}'''
    return monday_query(q)["boards"][0]

def slug_for(item_id, deal=""):
    """Readable, typeable, unguessable: deal341-XK7M2R (charset avoids 0/O/1/I/L)."""
    digest = hashlib.sha256(f"{SALT}:{item_id}".encode()).hexdigest()
    charset = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"
    code = "".join(charset[int(digest[i*2:i*2+2], 16) % len(charset)] for i in range(6))
    prefix = f"deal{deal}-" if deal else "home-"
    return prefix + code

CARD_TEMPLATE = """<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow">
<title>Home Tracker Card - {NAME}</title>
<style>
 body{font-family:Montserrat,"Avenir Next","Segoe UI",Arial,sans-serif;background:#f4f5fa;margin:0;padding:24px;display:flex;justify-content:center}
 .card{width:5.5in;background:#fff;border:2px solid #101a7a;border-radius:14px;overflow:hidden}
 .top{background:linear-gradient(160deg,#101a7a,#313a8d);color:#fff;padding:16px 20px}
 .top .brand{font-weight:800;font-size:.85rem;letter-spacing:.02em}
 .top .brand span{color:#f5a623}
 .top h1{font-size:1.15rem;margin:8px 0 0}
 .mid{display:flex;gap:16px;padding:16px 20px;align-items:center}
 .qr{flex:0 0 150px} .qr svg{width:150px;height:150px}
 .steps{font-size:.8rem;color:#1c2340;line-height:1.5}
 .steps b{color:#101a7a}
 .url{margin:0 20px 4px;background:#eef1ff;border:1.5px dashed #101a7a;border-radius:9px;padding:10px 12px;text-align:center;font-family:Menlo,monospace;font-size:.85rem;font-weight:700;color:#101a7a;letter-spacing:.01em;word-break:break-all}
 .keep{text-align:center;font-size:.72rem;color:#6a7090;padding:6px 20px 2px}
 .bot{background:#101a7a;color:#c9cdf0;text-align:center;font-size:.7rem;padding:9px;margin-top:10px}
 .bot b{color:#f5a623}
 @media print{body{background:#fff;padding:0} .card{border-radius:0}}
</style></head><body>
<div class="card">
 <div class="top"><div class="brand">SELECT <span>HOME CENTER</span></div>
  <h1>The {NAME} Home Tracker</h1></div>
 <div class="mid">
  <div class="qr">{QR_SVG}</div>
  <div class="steps"><b>Watch your new home come to life:</b><br>
   1. Point your phone camera at this code<br>
   2. Tap the link that pops up<br>
   3. On the page, follow the 3 steps under<br>&nbsp;&nbsp;&nbsp;"Save this page" so it's always one tap away<br>
   <span style="color:#6a7090">Para español: toque "Español" en la página</span></div>
 </div>
 <div class="url">{URL}</div>
 <div class="keep">Keep this card - you can type the address above into any phone or computer, any time.</div>
 <div class="bot">Questions any time: <b>912-208-6065</b> · Se Habla Español · SelectHomeCenter.com</div>
</div>
</body></html>"""

def build_card(name, slug, outdir):
    try:
        import segno
    except ImportError:
        print("  (segno not installed - skipping QR card. Fix: python3 -m pip install segno)")
        return
    url = f"{SITE}/track/{slug}/"
    qr = segno.make(url, error="q")
    svg = qr.svg_inline(scale=4, dark="#101a7a")
    page = (CARD_TEMPLATE.replace("{NAME}", html.escape(name))
            .replace("{QR_SVG}", svg)
            .replace("{URL}", url.replace("https://", "")))
    (outdir / "card.html").write_text(page, encoding="utf-8")

def status_class(text):
    t = (text or "").strip().lower()
    if t in ("complete", "completed", "done"): return "done"
    if t in ("in progress", "working on it"): return "active"
    if t in ("scheduled",): return "scheduled"
    if t in ("n/a",): return "na"
    return "wait"

TEMPLATE = open(REPO / "scripts" / "tracker_template.html", encoding="utf-8").read()

def build_page(name, deal, vin, make, model, steps, outdir):
    """steps: list of (title_en, title_es, cls, note_en, note_es)"""
    total = len([s for s in steps if s[2] != "na"])
    done = len([s for s in steps if s[2] == "done"])
    all_done = done == total and total > 0
    current = next((s for s in steps if s[2] == "active"), None) or \
              next((s for s in steps if s[2] == "scheduled"), None) or \
              next((s for s in steps if s[2] == "wait"), None)
    rows = []
    for i, (en, es, cls, note_en, note_es) in enumerate(steps, 1):
        if cls == "na":
            continue
        icon = "&#10003;" if cls == "done" else ("&#9679;" if cls == "active" else str(i))
        badge = {"done": ("Complete", "Completado"), "active": ("In progress", "En proceso"),
                 "scheduled": ("Scheduled", "Programado"), "wait": ("Upcoming", "Pendiente")}[cls]
        rows.append(f'''<div class="step {cls}"><div class="dot">{icon}</div><div class="scard">
<div class="srow"><span class="sname" data-en="{html.escape(en)}" data-es="{html.escape(es)}">{html.escape(en)}</span></div>
<span class="badge" data-en="{badge[0]}" data-es="{badge[1]}">{badge[0]}</span></div></div>''')
    if all_done:
        head_en, head_es = f"Welcome home, {name}!", f"¡Bienvenidos a casa, {name}!"
        next_tag = ("All done", "Todo listo")
        next_h = ("Your home is complete!", "¡Su casa está terminada!")
        next_p = ("Every milestone is finished. It was an honor to build this journey with you. "
                  "If we took good care of you, a quick Google review helps other families find us.",
                  "Todos los pasos están terminados. Fue un honor acompañarlos. "
                  "Si le cuidamos bien, una reseña en Google ayuda a otras familias a encontrarnos.")
        review_html = f'<a class="review" href="{REVIEW_URL}" data-en="&#11088; Leave us a Google review" data-es="&#11088; Déjanos una reseña en Google">&#11088; Leave us a Google review</a>'
    else:
        head_en, head_es = f"Your home is on its way, {name}!", f"¡Su casa está en camino, {name}!"
        cur_en = current[0] if current else "Next steps"
        cur_es = current[1] if current else "Próximos pasos"
        next_tag = ("Happening now", "En proceso")
        next_h = (cur_en, cur_es)
        next_p = ("Our team is on it. We'll update this page and message you the moment it's done.",
                  "Nuestro equipo está en ello. Actualizaremos esta página y le avisaremos en cuanto esté listo.")
        review_html = ""
    page = (TEMPLATE
        .replace("{{HEAD_EN}}", html.escape(head_en)).replace("{{HEAD_ES}}", html.escape(head_es))
        .replace("{{SUB_EN}}", html.escape(f"{make} {model}".strip() or "Your new home"))
        .replace("{{SUB_ES}}", html.escape(f"{make} {model}".strip() or "Su nueva casa"))
        .replace("{{DEALCHIP}}", html.escape(f"Deal #{deal} · Folkston, GA" if deal else "Folkston, GA"))
        .replace("{{DONE}}", str(done)).replace("{{TOTAL}}", str(total))
        .replace("{{PCT}}", str(int(100 * done / total) if total else 0))
        .replace("{{NEXT_TAG_EN}}", next_tag[0]).replace("{{NEXT_TAG_ES}}", next_tag[1])
        .replace("{{NEXT_H_EN}}", html.escape(next_h[0])).replace("{{NEXT_H_ES}}", html.escape(next_h[1]))
        .replace("{{NEXT_P_EN}}", html.escape(next_p[0])).replace("{{NEXT_P_ES}}", html.escape(next_p[1]))
        .replace("{{REVIEW}}", review_html)
        .replace("{{STEPS}}", "\n".join(rows))
        .replace("{{SITE}}", SITE).replace("{{PHONE}}", PHONE))
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "index.html").write_text(page, encoding="utf-8")

def build_demo():
    steps = [(en, es, "done", "", "") for en, es in zip(PRE_STEPS_EN, PRE_STEPS_ES)]
    steps += [("Land Clearing", ES_STEP["Land Clearing"], "done", "", ""),
              ("Dirt Pad", ES_STEP["Dirt Pad"], "done", "", ""),
              ("Well", ES_STEP["Well"], "done", "", ""),
              ("Septic", ES_STEP["Septic"], "active", "", ""),
              ("Power Pole", ES_STEP["Power Pole"], "scheduled", "", ""),
              ("Electric", ES_STEP["Electric"], "wait", "", ""),
              ("HVAC", ES_STEP["HVAC"], "wait", "", ""),
              ("Steps", ES_STEP["Steps"], "wait", "", "")]
    outdir = REPO / "track" / "demo"
    build_page("Johnson Family", "341", "DEMO", "Clayton", "Epic Journey “Desoto”",
               steps, outdir)
    build_card("Johnson Family", "demo", outdir)
    print("built track/demo/ (+card)")

def build_all():
    board = fetch_board()
    n = 0
    for item in board["items_page"]["items"]:
        if item["group"]["title"] not in ACTIVE_GROUPS:
            continue
        cols = {cv["column"]["title"]: cv for cv in item["column_values"]}
        deal = (cols.get("Deal Number") or {}).get("text", "")
        vin = (cols.get("VIN Number") or {}).get("text", "")
        make = (cols.get("Make") or {}).get("text", "")
        model = (cols.get("Model") or {}).get("text", "")
        steps = [(en, es, "done", "", "") for en, es in zip(PRE_STEPS_EN, PRE_STEPS_ES)]
        for cv in item["column_values"]:
            if cv["column"]["type"] != "status":
                continue
            t = cv["column"]["title"]
            steps.append((t, ES_STEP.get(t, t), status_class(cv.get("text")), "", ""))
        slug = slug_for(item["id"], deal)
        outdir = REPO / "track" / slug
        build_page(item["name"], deal, vin, make, model, steps, outdir)
        build_card(item["name"], slug, outdir)
        print(f"built track/{slug}/ (+card)  ({item['name']}, deal {deal})")
        n += 1
    print(f"{n} customer pages built. Commit + push to deploy.")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()
    build_demo() if a.demo else build_all()

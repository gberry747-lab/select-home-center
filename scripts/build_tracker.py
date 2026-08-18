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
REVIEW_URL = "https://g.page/r/CaaWPBbx_KDPEBE/review"   # SHC Google review link (from master plan binder)
SALT = "shc-tracker-2026"
# RULE (Gregory, 2026-08-17): NADP homes are NOT Select Home Center homes.
# Never include the SHS/NADP group or any item mentioning NADP in SHC systems.
ACTIVE_GROUPS = ("Active Projects", "Finished Projects")
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
    "Permitting": "Permisos", "Plumbing": "Plomería", "Inspections": "Inspecciones",
    "Trim out": "Acabados",
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


STAFF_TEMPLATE = """<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow">
<title>Home Tracker - Team Page</title>
<style>
 body{font-family:Montserrat,"Avenir Next","Segoe UI",Arial,sans-serif;background:#f4f5fa;color:#1c2340;margin:0;padding:0 16px 40px}
 .wrap{max-width:640px;margin:0 auto}
 header{background:linear-gradient(160deg,#101a7a,#313a8d);color:#fff;margin:0 -16px;padding:22px 20px}
 header .brand{font-weight:800;font-size:.9rem} header .brand span{color:#f5a623}
 header h1{font-size:1.3rem;margin:8px 0 0}
 .howto{background:#fff;border:1px solid #e2e4f0;border-radius:12px;padding:14px 18px;margin:16px 0;font-size:.88rem;line-height:1.6}
 .howto b{color:#101a7a}
 .cust{background:#fff;border:1px solid #e2e4f0;border-radius:12px;padding:14px 18px;margin:10px 0;display:flex;flex-wrap:wrap;gap:10px;align-items:center;justify-content:space-between}
 .cust .who{font-weight:800;font-size:1rem} .cust .deal{color:#6a7090;font-size:.8rem}
 .btns{display:flex;gap:8px;flex-wrap:wrap}
 .btns a,.btns button{border:0;cursor:pointer;text-decoration:none;font-weight:700;font-size:.8rem;border-radius:9px;padding:9px 13px;font-family:inherit}
 .b-view{background:#eef1ff;color:#101a7a} .b-card{background:#101a7a;color:#fff} .b-copy{background:#f5a623;color:#3a2a00} .b-mail{background:#2e8b57;color:#fff}
 .note{font-size:.75rem;color:#6a7090;margin-top:18px;text-align:center}
</style></head><body><div class="wrap">
<header><div class="brand">SELECT <span>HOME CENTER</span> - TEAM ONLY</div>
<h1>Customer Home Trackers</h1></header>
<div class="howto"><b>New customer checklist:</b><br>
1. <b>Print card:</b> tap their gold-framed "Print card" button, then File &gt; Print. Card goes in their paperwork folder.<br>
2. <b>Send link</b>, either way:<br>
&nbsp;&nbsp;&bull; <b>Email customer</b> (green button): opens an email that's already written - type their address, hit Send. On the office computer signed into hello@selecthomecenter.com it sends from the store address.<br>
&nbsp;&nbsp;&bull; Or <b>Copy link</b> and paste into a text from your phone: <i>"Congratulations! Here's your personal Home Tracker - watch every step of your new home: [paste link]. Save this text!"</i><br>
3. That's it. The page updates by itself as Monday statuses change. Keep this team page bookmarked; do not share this page's address with customers.</div>
{ROWS}
<div class="note">Updated automatically from the Monday board each time the tracker refreshes. Questions: ask Gregory.</div>
</div>
<script>
function cp(u,btn){navigator.clipboard.writeText(u).then(()=>{btn.textContent="Copied!";setTimeout(()=>btn.textContent="Copy link",1500);});}
</script></body></html>"""

def build_staff_page(entries):
    """entries: list of (name, deal, slug)"""
    rows = []
    import urllib.parse
    for name, deal, slug in entries:
        url = f"{SITE}/track/{slug}/"
        subj = urllib.parse.quote("Your Home Tracker - Select Home Center")
        body = urllib.parse.quote(
            "Congratulations from all of us at Select Home Center!\n\n"
            "Here is your personal Home Tracker - watch every step of your new home, "
            f"from financing to keys day:\n\n{url}\n\n"
            "Tip: open it on your phone and follow the 'Save this page' steps so it's always one tap away. "
            "Para espanol, toque 'Espanol' arriba en la pagina.\n\n"
            "Questions any time: 912-208-6065\n\n- Your Select Home Center Team\nSelectHomeCenter.com")
        mailto = f"mailto:?subject={subj}&body={body}"
        rows.append(f'''<div class="cust"><div><div class="who">{html.escape(name)}</div>
<div class="deal">Deal #{html.escape(deal) if deal else "-"} · {url.replace("https://","")}</div></div>
<div class="btns"><a class="b-view" href="{url}" target="_blank">View page</a>
<a class="b-card" href="{url}card.html" target="_blank">Print card</a>
<button class="b-copy" onclick="cp(\'{url}\',this)">Copy link</button>
<a class="b-mail" href="{mailto}">Email customer</a></div></div>''')
    code = slug_for("staff-page", "")
    outdir = REPO / "track" / f"team-{code[5:]}"
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "index.html").write_text(STAFF_TEMPLATE.replace("{ROWS}", "\n".join(rows)), encoding="utf-8")
    print(f"staff page: {SITE}/track/team-{code[5:]}/")



# ---------- Site chrome (real header/footer from the live site) ----------
import re as _re

def _absolutize(chunk):
    chunk = _re.sub(r'href="((?!https?:|/|#|tel:|mailto:)[^"]+\.html)"', r'href="/\1"', chunk)
    chunk = chunk.replace('src="assets/', 'src="/assets/').replace('href="assets/', 'href="/assets/')
    chunk = chunk.replace('src="js/', 'src="/js/').replace('href="css/', 'href="/css/')
    return chunk

_CHROME = None
def site_chrome():
    global _CHROME
    if _CHROME is None:
        src = (REPO / "contact.html").read_text(encoding="utf-8")
        css = _re.search(r'<link rel="stylesheet" href="(css/styles\.css[^"]*)">', src).group(1)
        header = src[src.index("<body>") + 6 : src.index("</header>") + 9]
        footer = src[src.index('<footer class="footer">') : src.index("</body>")]
        _CHROME = (f'<link rel="stylesheet" href="/{css}">', _absolutize(header), _absolutize(footer))
    return _CHROME

SITE_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
{ROBOTS}
<title>{TITLE} | Select Home Center</title>
<meta name="description" content="{DESC}">
{CSSLINK}
<style>{CSS}</style>
</head>
<body>
{HEADER}
<section id="main" tabindex="-1" class="page-hero">
  <div class="container">
    <h1>{H1}</h1>
    <p>{TAGLINE}</p>
  </div>
</section>
<section>
  <div class="container" style="max-width:{MAXW};padding-top:34px;padding-bottom:56px">
{CONTENT}
  </div>
</section>
{FOOTER}
{SCRIPT}
</body>
</html>"""

def build_site_page(outpath, *, title, desc, h1, tagline, content, css, script, maxw="560px", noindex=False):
    csslink, header, footer = site_chrome()
    page = (SITE_PAGE.replace("{ROBOTS}", '<meta name="robots" content="noindex,nofollow">' if noindex else '')
            .replace("{TITLE}", title).replace("{DESC}", desc).replace("{CSSLINK}", csslink)
            .replace("{CSS}", css).replace("{HEADER}", header).replace("{H1}", h1)
            .replace("{TAGLINE}", tagline).replace("{MAXW}", maxw).replace("{CONTENT}", content)
            .replace("{FOOTER}", footer).replace("{SCRIPT}", script))
    outdir = REPO / outpath
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "index.html").write_text(page, encoding="utf-8")

GATE_CSS = """
.gcard{background:#fff;border:1px solid #e2e4f0;border-radius:16px;box-shadow:0 8px 30px rgba(16,26,122,.10);padding:26px 26px 24px}
.gcard label{display:block;font-weight:700;font-size:.85rem;margin:12px 0 5px;color:#1c2340}
.gcard input{width:100%;box-sizing:border-box;padding:12px;border:2px solid #d9dcec;border-radius:10px;font-size:1rem;font-family:inherit}
.gcard input:focus{outline:none;border-color:#101a7a}
.gcard .gbtn{width:100%;margin-top:18px;background:#f5a623;color:#3a2a00;border:0;border-radius:11px;padding:14px;font-size:1rem;font-weight:800;cursor:pointer;font-family:inherit}
.gcard .gbtn:hover{background:#e08c00}
.gerr{display:none;margin-top:12px;background:#fdecea;color:#8c2f26;border-radius:9px;padding:10px 12px;font-size:.85rem}
.ghelp{margin-top:14px;font-size:.82rem;color:#6a7090;line-height:1.5}
.ghelp a{color:#101a7a;font-weight:700}
.gsample{display:block;text-align:center;margin-top:12px;font-size:.9rem;color:#101a7a;font-weight:700}
"""

GATE_SCRIPT = """<script>
const ENTRIES={ENTRIES};
const ITER={ITER};
function b64(s){return Uint8Array.from(atob(s),c=>c.charCodeAt(0));}
async function tryEntry(cred,e){
 const km=await crypto.subtle.importKey('raw',new TextEncoder().encode(cred),'PBKDF2',false,['deriveBits']);
 const bits=new Uint8Array(await crypto.subtle.deriveBits({name:'PBKDF2',salt:b64(e.s),iterations:ITER,hash:'SHA-256'},km,512));
 const ct=b64(e.c);const out=new Uint8Array(ct.length);
 for(let i=0;i<ct.length;i++)out[i]=ct[i]^bits[i];
 const txt=new TextDecoder().decode(out);
 return txt.startsWith('OK:')?txt.slice(3):null;
}
async function go(){
 const btn=document.getElementById('gbtn');btn.textContent='{CHECKING}';
 const cred={CRED};
 for(const e of ENTRIES){
  try{const slug=await tryEntry(cred,e);if(slug){location.href='/track/'+slug+'/';return;}}catch(x){}
 }
 btn.textContent='{BUTTON}';
 document.getElementById('gerr').style.display='block';
}
document.addEventListener('keydown',e=>{if(e.key==='Enter')go();});
</script>"""

# ---------- Access gates (Team + Track My Home) ----------
import base64, secrets

GATE_ITER = 200000

def _gate_encrypt(credential, slug):
    salt = secrets.token_bytes(16)
    pad = hashlib.pbkdf2_hmac("sha256", credential.encode(), salt, GATE_ITER, dklen=64)
    plain = ("OK:" + slug).encode()
    ct = bytes(a ^ b for a, b in zip(plain, pad))
    return {"s": base64.b64encode(salt).decode(), "c": base64.b64encode(ct).decode()}

def _gate_page(path, title, h1, tagline, fields, button, checking, errmsg, extra, entries, cred_js, noindex=False):
    content = f"""<div class="gcard">
{fields}
  <button class="gbtn" id="gbtn" onclick="go()">{button}</button>
  <div class="gerr" id="gerr">{errmsg}</div>
  {extra}
</div>"""
    script = (GATE_SCRIPT.replace("{ENTRIES}", json.dumps(entries)).replace("{ITER}", str(GATE_ITER))
              .replace("{CHECKING}", checking).replace("{BUTTON}", button).replace("{CRED}", cred_js))
    build_site_page(path, title=title, desc=tagline, h1=h1, tagline=tagline,
                    content=content, css=GATE_CSS, script=script, noindex=noindex)

def build_team_gate(team_slug):
    pw_file = pathlib.Path.home() / ".config/shc/team_gate_password"
    if not pw_file.exists():
        print("  (no team gate password file - skipping team gate)")
        return
    pw = pw_file.read_text().strip()
    _gate_page("team", "Team Sign-In", "Team Sign-In",
        "Select Home Center staff only.",
        '<label for="pw">Team password</label><input id="pw" type="password" autocomplete="current-password">',
        "Open Team Page", "Checking...",
        "That password didn&#39;t match. Check with Gregory if you need it.",
        "", [_gate_encrypt(pw, team_slug)],
        "document.getElementById(\'pw\').value.trim()", noindex=True)
    print("team gate: /team/")

def _norm_last(name):
    parts = [w for w in name.replace("&", " ").split() if w.isalpha()]
    return (parts[-1] if parts else name).lower()

def _norm_phone(raw):
    d = "".join(ch for ch in raw if ch.isdigit())
    return d[-10:]

def build_myhome_gate(cust_entries):
    """cust_entries: list of (item_name, phone, slug) - only those with phone are matchable."""
    entries = []
    for name, phone, slug in cust_entries:
        ph = _norm_phone(phone or "")
        if len(ph) == 10:
            entries.append(_gate_encrypt(_norm_last(name) + ph, slug))
    fields = ('<label for="ln">Last name / Apellido</label><input id="ln" autocomplete="family-name" placeholder="Smith">'
              '<label for="ph">Mobile phone / Tel&eacute;fono</label><input id="ph" type="tel" autocomplete="tel" placeholder="912-555-1234">')
    extra = ('<div class="ghelp">Use the last name and cell phone number from your purchase paperwork. '
             'No luck? Call or text us at <a href="tel:9122086065">912-208-6065</a> and we&#39;ll send your link. '
             '&iquest;Necesita ayuda en espa&ntilde;ol? Ll&aacute;menos.</div>'
             '<a class="gsample" href="/track/demo/">See a sample Home Tracker &rarr;</a>'
             '<a class="gsample" href="/warranty-checklist/">See a sample Warranty Checklist &rarr;</a>')
    cred_js = ("document.getElementById(\'ln\').value.toLowerCase().replace(/[^a-z]/g,\'\')"
               "+document.getElementById(\'ph\').value.replace(/[^0-9]/g,\'\').slice(-10)")
    _gate_page("my-home", "Track My Home", "Track My Home",
        "Watch your new home come to life - every Select Home Center family gets a private tracking page.",
        fields, "Find My Home", "Looking...",
        "We couldn&#39;t find a match. Double-check the spelling and number, or call us at 912-208-6065 - we&#39;ll get you your link right away.",
        extra, entries, cred_js, noindex=False)
    print(f"my-home gate: /my-home/ ({len(entries)} matchable customers)")


# ---------- Interactive Warranty Checklist page (site chrome) ----------
WC_CSS = """
.wc-progress{background:#fff;border:1px solid #e2e4f0;border-radius:14px;box-shadow:0 6px 24px rgba(16,26,122,.08);padding:16px 20px;margin-bottom:18px}
.wc-pct{font-size:1.3rem;font-weight:800;color:#101a7a}
.wc-bar{height:9px;background:#e2e4f0;border-radius:999px;margin-top:8px;overflow:hidden}
.wc-bar>div{height:100%;width:0%;background:linear-gradient(90deg,#f5a623,#e08c00);border-radius:999px;transition:width .3s}
.wc-h{font-size:.78rem;letter-spacing:.11em;text-transform:uppercase;color:#6a7090;font-weight:800;margin:18px 0 10px}
.wc-h.red{color:#a93226}
.wc-item{display:flex;gap:12px;background:#fff;border:1px solid #e2e4f0;border-radius:12px;padding:13px 14px;margin-bottom:8px;cursor:pointer;user-select:none}
.wc-item input{width:22px;height:22px;flex:0 0 22px;accent-color:#2e8b57;cursor:pointer}
.wc-item.done .wc-t{text-decoration:line-through;color:#6a7090}
.wc-t{font-size:.92rem;font-weight:600;color:#1c2340}
.wc-n{font-size:.8rem;color:#6a7090;font-weight:400;margin-top:2px}
.wc-r{display:inline-block;font-size:.65rem;font-weight:800;letter-spacing:.05em;background:#eef1ff;color:#313a8d;border-radius:999px;padding:2px 8px;margin-top:6px;text-transform:uppercase}
.wc-actions{display:flex;gap:10px;margin-top:18px}
.wc-actions a,.wc-actions button{flex:1;text-align:center;text-decoration:none;font-weight:800;font-size:.85rem;border-radius:11px;padding:12px 8px;border:0;cursor:pointer;font-family:inherit}
.wc-print{background:#101a7a;color:#fff}
.wc-reset{background:#fff;border:2px solid #e2e4f0;color:#6a7090}
.wc-note{margin-top:12px;font-size:.78rem;color:#6a7090}
.wc-lang{float:right;background:#eef1ff;border:1px solid #ccd3f5;color:#101a7a;border-radius:999px;padding:4px 12px;font-size:.75rem;font-weight:700;cursor:pointer;font-family:inherit}
"""

def _wc_item(k, t_en, t_es, n_en=None, n_es=None, repeat=False):
    note = (f'<div class="wc-n" data-en="{n_en}" data-es="{n_es}">{n_en}</div>' if n_en else "")
    rep = ('<span class="wc-r" data-en="Repeats yearly" data-es="Se repite cada a&ntilde;o">Repeats yearly</span>' if repeat else "")
    return (f'<div class="wc-item" data-k="{k}"><input type="checkbox"><div>'
            f'<div class="wc-t" data-en="{t_en}" data-es="{t_es}">{t_en}</div>{note}{rep}</div></div>')

WC_SCRIPT = """<script>
const KEY='shc-warranty-checklist';
const saved=JSON.parse(localStorage.getItem(KEY)||'{}');
const items=[...document.querySelectorAll('.wc-item')];
function refresh(){
 const done=items.filter(i=>i.querySelector('input').checked).length;
 document.getElementById('done').textContent=done;
 document.getElementById('total').textContent=items.length;
 document.getElementById('bar').style.width=(100*done/items.length)+'%';
}
items.forEach(it=>{
 const k=it.dataset.k, cb=it.querySelector('input');
 cb.checked=!!saved[k];
 it.classList.toggle('done',cb.checked);
 it.addEventListener('click',e=>{
  if(e.target!==cb) cb.checked=!cb.checked;
  saved[k]=cb.checked;
  it.classList.toggle('done',cb.checked);
  localStorage.setItem(KEY,JSON.stringify(saved));
  refresh();
 });
});
refresh();
function resetAll(){
 ['filter','insp-sched','insp-done'].forEach(k=>{delete saved[k];});
 localStorage.setItem(KEY,JSON.stringify(saved));
 location.reload();
}
let es=false;
function toggleLang(){
 es=!es;
 document.getElementById('langbtn').textContent=es?'English':'Espa\u00f1ol';
 document.querySelectorAll('[data-en]').forEach(el=>{el.innerHTML=es?el.getAttribute('data-es'):el.getAttribute('data-en');});
 const pp=document.getElementById('printpdf');
 if(pp) pp.href='/assets/docs/SHC-Warranty-Owners-Checklist'+(es?'-ES':'')+'.pdf';
}
</script>"""

def build_warranty_page():
    parts = []
    def H(en, es, red=False):
        cls = " red" if red else ""
        parts.append(f'<div class="wc-h{cls}" data-en="{en}" data-es="{es}">{en}</div>')
    def I(*a, **kw):
        parts.append(_wc_item(*a, **kw))
    H("At closing (day one)", "Al cierre (d&iacute;a uno)")
    I("reg", "Signed the warranty Registration Page (including the annual-inspection acknowledgment)",
      "Firm&eacute; la p&aacute;gina de registro de la garant&iacute;a (incluida la inspecci&oacute;n anual)")
    I("date", "Wrote down my Agreement Date (closing day) and my anniversary date",
      "Anot&eacute; mi fecha de contrato (d&iacute;a de cierre) y mi aniversario")
    I("docs", "Put the warranty booklet AND sales receipt together somewhere safe",
      "Guard&eacute; juntos el folleto de garant&iacute;a Y el recibo de compra",
      "You may need both to get service.", "Puede necesitar ambos para obtener servicio.")
    I("remind", "Set 3 phone reminders: 60 days before, 30 days before, and ON my anniversary date",
      "Puse 3 recordatorios: 60 d&iacute;as antes, 30 d&iacute;as antes y EN mi aniversario")
    H("Your first year", "Su primer a&ntilde;o")
    I("wait", "I know the first 30 days are a waiting period (year-one problems go to the manufacturer&#39;s warranty)",
      "S&eacute; que los primeros 30 d&iacute;as son de espera (el primer a&ntilde;o los problemas van a la garant&iacute;a del fabricante)")
    I("factory", "Reported ANY issues to the manufacturer in writing before the 1-year factory warranty ended",
      "Report&eacute; TODO problema al fabricante por escrito antes de terminar la garant&iacute;a de f&aacute;brica de 1 a&ntilde;o",
      "Call us at 912-208-6065 if you need help writing it up.", "Ll&aacute;menos al 912-208-6065 si necesita ayuda.")
    H("All year, every year", "Todo el a&ntilde;o, cada a&ntilde;o")
    I("filter", "Doing the owner&#39;s-manual maintenance (filters, coils, drain lines) and KEEPING RECEIPTS",
      "Hago el mantenimiento del manual (filtros, serpentines, drenajes) y GUARDO RECIBOS",
      "No proof of maintenance can void coverage.", "Sin comprobantes, pueden anular la cobertura.", repeat=True)
    H("The big one: annual inspection", "Lo m&aacute;s importante: inspecci&oacute;n anual", red=True)
    I("insp-sched", "Scheduled this year&#39;s inspection (Dynamic: 833-205-8200, $299 - or my own licensed inspector)",
      "Program&eacute; la inspecci&oacute;n de este a&ntilde;o (Dynamic: 833-205-8200, $299 - o mi propio inspector)", repeat=True)
    I("insp-done", "Inspection DONE and paperwork RECEIVED by Dynamic within 30 days of my anniversary",
      "Inspecci&oacute;n HECHA y papeles RECIBIDOS por Dynamic dentro de 30 d&iacute;as de mi aniversario",
      "Missing this once voids the warranty. Questions? 912-208-6065.",
      "Faltar una vez anula la garant&iacute;a. &iquest;Preguntas? 912-208-6065.", repeat=True)
    H("If something breaks", "Si algo se da&ntilde;a")
    I("call", "I know the rule: call 833-205-8200 BEFORE any repair, turn the item off, protect it",
      "Conozco la regla: llamar al 833-205-8200 ANTES de reparar, apagar y proteger el equipo",
      "$75 service fee per visit. Unauthorized repairs are not reimbursed.",
      "Cuota de $75 por visita. Reparaciones sin autorizaci&oacute;n no se reembolsan.")
    content = ('<button class="wc-lang" id="langbtn" onclick="toggleLang()">Espa&ntilde;ol</button>'
               '<div style="clear:both"></div>'
               '<div class="wc-progress"><span class="wc-pct"><span id="done">0</span> '
               '<span data-en="of" data-es="de">of</span> <span id="total">0</span> '
               '<span data-en="done" data-es="listos">done</span></span>'
               '<div class="wc-bar"><div id="bar"></div></div></div>'
               + "".join(parts) +
               '<div class="wc-actions">'
               '<a class="wc-print" id="printpdf" href="/assets/docs/SHC-Warranty-Owners-Checklist.pdf" target="_blank" rel="noopener" '
               'data-en="&#128424; Print the paper version" data-es="&#128424; Imprimir la versi&oacute;n en papel">&#128424; Print the paper version</a>'
               '<button class="wc-reset" onclick="resetAll()" data-en="Start a new year" data-es="Comenzar nuevo a&ntilde;o">Start a new year</button></div>'
               '<p class="wc-note" data-en="Checkmarks are saved on this phone only. At the start of each warranty year, tap &#39;Start a new year&#39; to un-check the yearly items." '
               'data-es="Las marcas se guardan solo en este tel&eacute;fono. Al comenzar cada a&ntilde;o, toque &#39;Comenzar nuevo a&ntilde;o&#39;.">'
               'Checkmarks are saved on this phone only. At the start of each warranty year, tap &#39;Start a new year&#39; to un-check the yearly items.</p>')
    build_site_page("warranty-checklist",
        title="Warranty Owner&#39;s Checklist",
        desc="Keep your free lifetime home warranty active: the Select Home Center owner&#39;s checklist for new manufactured home owners.",
        h1="Your Warranty Owner&#39;s Checklist",
        tagline="Check things off as you do them - this page remembers, right on your phone. Hablamos Espa&ntilde;ol.",
        content=content, css=WC_CSS, script=WC_SCRIPT, maxw="640px", noindex=False)
    print("warranty checklist page: /warranty-checklist/")

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
    rank = {"done": 0, "active": 1, "scheduled": 2, "wait": 3}
    steps = sorted([s_ for s_ in steps if s_[2] != "na"], key=lambda s_: rank[s_[2]])
    rows = []
    for i, (en, es, cls, note_en, note_es) in enumerate(steps, 1):
        icon = "&#10003;" if cls == "done" else ("&#9679;" if cls == "active" else "&#9675;")
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
        review_html = f'<a class="review" href="{REVIEW_URL}" target="_blank" rel="noopener" data-en="&#11088; Leave us a Google review" data-es="&#11088; Déjanos una reseña en Google">&#11088; Leave us a Google review</a>'
        review_html += f'<a class="review" style="background:#101a7a;color:#fff;margin-top:8px" target="_blank" rel="noopener" href="{SITE}/warranty-checklist/" data-en="&#128220; Your Warranty Owner&#39;s Checklist (PDF)" data-es="&#128220; Su lista de garantía (PDF)">&#128220; Your Warranty Owner&#39;s Checklist (PDF)</a>'
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

def build_demo_page():
    """Just the Johnson demo page + card (safe to run after build_all)."""
    steps = [(en, es, "done", "", "") for en, es in zip(PRE_STEPS_EN, PRE_STEPS_ES)]
    steps += [("Permitting", ES_STEP["Permitting"], "done", "", ""),
              ("Land Clearing", ES_STEP["Land Clearing"], "done", "", ""),
              ("Dirt Pad", ES_STEP["Dirt Pad"], "done", "", ""),
              ("Well", ES_STEP["Well"], "wait", "", ""),
              ("Septic", ES_STEP["Septic"], "done", "", ""),
              ("Power Pole", ES_STEP["Power Pole"], "scheduled", "", ""),
              ("Electric", ES_STEP["Electric"], "wait", "", ""),
              ("HVAC", ES_STEP["HVAC"], "active", "", ""),
              ("Steps", ES_STEP["Steps"], "wait", "", "")]
    outdir = REPO / "track" / "demo"
    build_page("Johnson Family", "341", "DEMO", "Clayton", "Epic Journey “Desoto”", steps, outdir)
    build_card("Johnson Family", "demo", outdir)
    print("built track/demo/ (+card)")

def build_demo():
    steps = [(en, es, "done", "", "") for en, es in zip(PRE_STEPS_EN, PRE_STEPS_ES)]
    steps += [("Permitting", ES_STEP["Permitting"], "done", "", ""),
              ("Land Clearing", ES_STEP["Land Clearing"], "done", "", ""),
              ("Dirt Pad", ES_STEP["Dirt Pad"], "done", "", ""),
              ("Well", ES_STEP["Well"], "wait", "", ""),
              ("Septic", ES_STEP["Septic"], "done", "", ""),
              ("Power Pole", ES_STEP["Power Pole"], "scheduled", "", ""),
              ("Electric", ES_STEP["Electric"], "wait", "", ""),
              ("HVAC", ES_STEP["HVAC"], "active", "", ""),
              ("Steps", ES_STEP["Steps"], "wait", "", "")]
    outdir = REPO / "track" / "demo"
    build_page("Johnson Family", "341", "DEMO", "Clayton", "Epic Journey “Desoto”",
               steps, outdir)
    build_card("Johnson Family", "demo", outdir)
    build_staff_page([("Johnson Family (demo)", "341", "demo")])
    team_code = slug_for("staff-page", "")
    build_team_gate(f"team-{team_code[5:]}")
    build_myhome_gate([("Johnson Family (demo)", "", "demo")])
    build_warranty_page()
    print("built track/demo/ (+card +staff page)")

def build_all():
    board = fetch_board()
    n = 0
    entries = []
    gate_entries = []
    for item in board["items_page"]["items"]:
        if item["group"]["title"] not in ACTIVE_GROUPS:
            continue
        if "NADP" in (item["name"] or "").upper():
            continue
        cols = {cv["column"]["title"]: cv for cv in item["column_values"]}
        phone = (cols.get("Phone") or {}).get("text", "")
        deal = (cols.get("Deal Number") or {}).get("text", "")
        vin = (cols.get("VIN Number") or {}).get("text", "")
        make = (cols.get("Make") or {}).get("text", "")
        model = (cols.get("Model") or {}).get("text", "")
        steps = [(en, es, "done", "", "") for en, es in zip(PRE_STEPS_EN, PRE_STEPS_ES)]
        site_steps = []
        for cv in item["column_values"]:
            if cv["column"]["type"] != "status":
                continue
            t = cv["column"]["title"]
            site_steps.append((t, ES_STEP.get(t, t), status_class(cv.get("text")), "", ""))
        # RULE (Gregory, 2026-08-18): Permitting comes before well/septic/transport,
        # so it always renders as the first site-work milestone.
        site_steps.sort(key=lambda s_: 0 if s_[0] == "Permitting" else 1)
        steps += site_steps
        slug = slug_for(item["id"], deal)
        outdir = REPO / "track" / slug
        build_page(item["name"], deal, vin, make, model, steps, outdir)
        build_card(item["name"], slug, outdir)
        print(f"built track/{slug}/ (+card)  ({item['name']}, deal {deal})")
        entries.append((item["name"], deal, slug))
        gate_entries.append((item["name"], phone, slug))
        n += 1
    build_staff_page(entries)
    team_code = slug_for("staff-page", "")
    build_team_gate(f"team-{team_code[5:]}"[6:] if False else f"team-{team_code[5:]}")
    build_myhome_gate(gate_entries)
    build_warranty_page()
    build_demo_page()
    print(f"{n} customer pages built. Commit + push to deploy.")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()
    build_demo() if a.demo else build_all()

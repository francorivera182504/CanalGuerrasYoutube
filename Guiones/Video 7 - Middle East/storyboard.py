"""Storyboard del Video 7: una entrada de datos por escena (ver engine.py)."""
import math, random
from PIL import Image, ImageDraw, ImageChops
import engine as E
from engine import View, W, H, COL, ease, ramp, lerp

L, R_, CEN = [520, 540], [1400, 540], [960, 540]
def P(sid, at): return E.T(sid, at)

# ---------------- elementos especiales ----------------
NJ = [(-75.56, 39.63), (-75.13, 39.95), (-74.72, 40.15), (-74.94, 40.34), (-75.19, 40.58), (-75.07, 40.85), (-74.98, 41.08), (-74.69, 41.36),
      (-73.89, 40.99), (-73.92, 40.80), (-74.01, 40.66), (-74.26, 40.47), (-73.98, 40.41), (-74.05, 40.0), (-74.1, 39.75), (-74.4, 39.36),
      (-74.96, 38.93), (-74.97, 39.19), (-75.4, 39.38)]
def nj(can, n, v, t, sid):
    t0 = P(sid, "Jersey")
    if t < t0: return
    cx, cy = sum(p[0] for p in NJ) / len(NJ), sum(p[1] for p in NJ) / len(NJ); f = math.cos(math.radians(40.1)) / math.cos(math.radians(31.5))
    pts = [v.P(35.0 + (x - cx) * f + 1.6, 31.6 + (y - cy)) for x, y in NJ]
    E.arrowline(n, pts + [pts[0]], ramp(t, t0, t0 + 1.0), COL["WHITE"], 5, head=False)
def nj_label(can, v, t, sid):
    E.put_text(can, "NEW JERSEY (SAME SCALE)", 30, "WHITE", *v.P(36.9, 33.1), t, P(sid, "Jersey") + 0.6, stroke=6)

def flagpole(swap_at, start_b=False, raise_only=False):
    """mástil sobre el edificio: bandera genérica azul baja, sube una verde (sin emblemas)."""
    def f(can, v, t, sid):
        t0 = P(sid, swap_at) if swap_at else E.SC[sid][0] - 99
        d = ImageDraw.Draw(can); x, ytop, ybot = 1010, 230, 340
        d.line([(x, ytop - 10), (x, ybot + 30)], fill=(30, 30, 30), width=9); d.line([(x, ytop - 10), (x, ybot + 30)], fill=(200, 200, 200), width=5)
        k = ramp(t, t0, t0 + 1.4)
        if start_b: k = 1.0
        if k < 0.5:   # baja la azul
            y = lerp(ytop, ybot, k * 2); col = (70, 140, 230)
        else:          # sube la verde
            y = lerp(ybot, ytop, (k - 0.5) * 2); col = (60, 170, 90)
        wv = [(x + 6 + i * 12, y + 6 * math.sin(t * 5 + i * 0.7)) for i in range(11)]
        poly = wv + [(px, py + 70) for px, py in wv[::-1]]
        d.polygon(poly, fill=col, outline=(0, 0, 0))
    return f

def timeline005(can, v, t, sid):
    t0 = E.SC[sid][0]; d = ImageDraw.Draw(can); k = ramp(t, t0, t0 + 2.0); x0, x1, y = 260, 1660, 300
    d.line([(x0, y), (lerp(x0, x1, k), y)], fill=COL["YEL"], width=8)
    for i, yr in enumerate(("1948", "1967", "1979", "2000", "2023", "2026")):
        u = i / 5
        if k >= u: d.ellipse((x0 + (x1 - x0) * u - 11, y - 11, x0 + (x1 - x0) * u + 11, y + 11), fill=COL["WHITE"]); E.put_text(can, yr, 34, "WHITE", x0 + (x1 - x0) * u, y - 45, t, t0 + u * 2, stroke=6)

def settlements(can, n, v, t, sid):
    t0 = P(sid, "built")
    if t < t0: return
    if "sett" not in E.D:
        m = E.rmask(v, "WB"); a = (E.np.asarray(m) > 128); ys, xs = E.np.nonzero(a); rnd = random.Random(3)
        E.D["sett"] = [(xs[i], ys[i]) for i in (rnd.randrange(len(xs)) for _ in range(70))]
    pts = E.D["sett"]; nshow = int(len(pts) * ramp(t, t0, t0 + 7.0, "cubic"))
    for p in pts[:nshow]: n.dot(p, COL["BLUE"], 6)

def gaza_settle(can, n, v, t, sid):
    t0 = P(sid, "pulled"); rnd = random.Random(5); m = E.np.asarray(E.rmask(v, "GAZA")) > 128; ys, xs = E.np.nonzero(m)
    pts = [(xs[i], ys[i]) for i in (rnd.randrange(len(xs)) for _ in range(21))]
    gone = int(21 * ramp(t, t0, t0 + 3.0, "cubic"))
    for p in pts[gone:]: n.dot(p, COL["BLUE"], 14)

def gaza_ring(col, at):
    def f(can, n, v, t, sid):
        t0 = P(sid, at)
        if t < t0: return
        r = max(E.region("GAZA"), key=len); E.arrowline(n, [v.P(*p) for p in r] + [v.P(*r[0])], ramp(t, t0, t0 + 1.5), COL[col], 8, head=False)
    return f

def fence_break(can, n, v, t, sid):
    r = max(E.region("GAZA"), key=len); east = [p for p in r if p[0] > 34.38]; east.sort(key=lambda p: p[1])
    pts = [v.P(*p) for p in east]; t0 = P(sid, "broke")
    if t < t0: n.line(pts, COL["GREY"], 6); return
    gaps = [int(len(pts) * u) for u in (0.2, 0.45, 0.7, 0.85)]; seg = []
    for i, p in enumerate(pts):
        if any(abs(i - g) <= 1 for g in gaps):
            if len(seg) > 1: n.line(seg, COL["GREY"], 6)
            seg = []
        else: seg.append(p)
    if len(seg) > 1: n.line(seg, COL["GREY"], 6)

def stick(d, x, y, s, col):
    d.ellipse((x - 11 * s, y - 52 * s, x + 11 * s, y - 30 * s), fill=(255, 255, 255), outline=(0, 0, 0), width=3)
    for a, b in (((x, y - 30 * s), (x, y)), ((x, y), (x - 10 * s, y + 26 * s)), ((x, y), (x + 10 * s, y + 26 * s)), ((x - 16 * s, y - 18 * s), (x + 16 * s, y - 18 * s))):
        d.line([a, b], fill=col, width=int(6 * s))
def people(can, v, t, sid):
    t0 = P(sid, "driven"); d = ImageDraw.Draw(can)
    for i in range(10):
        x = 360 + i * 135; y = 600; col = (255, 255, 255)
        if i < 9 and t > t0 + i * 0.08:
            k = (t - t0 - i * 0.08); x += 40 * math.sin(k * 2.2 + i); col = COL["GOLD"]
        stick(d, x, y, 2.0, col)
    E.put_text(can, "9 IN 10", 90, "GOLD", 960, 300, t, t0, stroke=10)

def ipc(can, v, t, sid):
    t0 = P(sid, "famine"); d = ImageDraw.Draw(can); x, y0 = 560, 760; k = ramp(t, E.SC[sid][0] + 0.5, t0 + 0.4)
    cols = [(200, 230, 200), (250, 230, 100), (240, 150, 60), (220, 60, 50), (120, 20, 30)]
    for i in range(5):
        yy = y0 - i * 90; d.rectangle((x - 70, yy - 80, x + 70, yy), outline=(255, 255, 255), width=3)
        if k * 5 > i: d.rectangle((x - 66, yy - 76, x + 66, yy - 4), fill=cols[i])
        E.put_text(can, f"PHASE {i + 1}", 30, "WHITE", x + 170, yy - 40, t, E.SC[sid][0], stroke=5, pop=False)

def enrich(can, v, t, sid):
    a = E.SC[sid][0]; d = ImageDraw.Draw(can); x0, x1, y = 260, 1660, 560
    d.rounded_rectangle((x0, y - 40, x1, y + 40), 20, outline=(255, 255, 255), width=4)
    k = ramp(t, P(sid, "sixty") - 0.6, P(sid, "sixty") + 0.6); fill = lerp(0.0367, 0.60, k) if t > a + 0.5 else 0.0367
    d.rounded_rectangle((x0 + 4, y - 36, x0 + 4 + (x1 - x0 - 8) * fill, y + 36), 18, fill=COL["GOLD"])
    for val, lab, col in ((0.0367, "3.67% DEAL", "GREEN"), (0.60, "60%", "GOLD"), (0.90, "~90% WEAPONS-GRADE", "RED")):
        xx = x0 + (x1 - x0) * val; d.line([(xx, y - 60), (xx, y + 60)], fill=COL[col], width=4)
        E.put_text(can, lab, 32, col, xx, y + 100 if val != 0.60 else y - 100, t, a + 0.3, stroke=6)

def pager_flash(can, n, v, t, sid):
    rnd = random.Random(11)
    for at in ("exploded", "walkie"):
        t0 = P(sid, at)
        for i in range(160):
            lon = rnd.uniform(35.2, 36.4); lat = rnd.uniform(33.1, 34.3); ti = t0 + rnd.random() * 0.5
            if ti <= t < ti + 0.7: n.dot(v.P(lon, lat), COL["ORANGE"], 10, k=1 - (t - ti) / 0.7)

def chapters_list(can, v, t, sid):
    chs = []
    for s in E.ORDER:
        c = E.G[s]["chapter"]
        if c != "HOOK" and c not in chs: chs.append(c)
    t0 = P(sid, "Which")
    for i, c in enumerate(chs):
        x = 330 + (i % 3) * 630; y = 300 + (i // 3) * 120
        E.put_card(can, c, (x, y), "LBLUE" if i % 2 else "GOLD", t, t0 + i * 0.12, 600, 30)

# ---------------- escenas ----------------
LEB = View(35.9, 33.6, 3.4); NORTH = View(35.5, 33.1, 2.6); GAZAW = View(34.45, 31.40, 1.5); TEH = View(51.4, 35.7, 6); LEBW = View(36.6, 32.6, 10.5)
MAND = View(35.2, 31.35, 8.4)
E.VIEWS["mandate"] = MAND; E.VIEWS["wb"] = View(35.25, 31.92, 2.6)
STORY = {
 "001": dict(shot="hook_iran", fx=[("killed", "shake", 14), ("killed", "flash", 0.35), ("killed", "boom", 0.45), ("strikes", "creak", 0.06)]),
 "002": dict(shot="hormuz", card=[("~20% OF WORLD OIL", [1540, 260], "GOLD", "fifth", 520)], fx=[("missiles", "boom", 0.25), ("closing", "click", 0.2)]),
 "003": dict(view="levant_w", view2="region", move="Iran", fill=[("Israel", "BLUE", 0.35), ("Palestine", "GREEN", 0.45)], custom=[nj], custom2=[nj_label],
             pulse=[("TEHRAN", "GOLD", "Iran")], arrow=[([30, 330], "HORMUZ", "LBLUE", "America", 0.1), ("HORMUZ", [1900, 900], "GOLD", "oil", -0.2)],
             label=[("?", [1500, 330], "YEL", "ceasefire", 150)]),
 "004": dict(view="iran", bg="dim", icon=[("el_embassy", [960, 560], 560, None)], custom2=[flagpole("changed")], label=[("TEHRAN, 1979", [960, 860], "LBLUE", "February", 44)]),
 "005": dict(view="region", bg="dim", custom2=[timeline005], icon=[("el_isr_leader", [560, 640], 360, "two"), ("el_pal_leader", [960, 640], 360, "two"), ("el_iran_leader", [1360, 640], 360, "every")]),
 "101": dict(bg="card", view="mandate"),
 "101a": dict(view="mandate", fill=[("MANDATE", "WHITE", 0.18)], icon=[("el_jewish_arrival", [480, 560], 380, "Jews"), ("el_pal_farmer", [1440, 560], 380, "Palestinian")],
              label=[("SAME LAND", [960, 250], "YEL", "same", 64)]),
 "102": dict(view="mandate", fill=[("MANDATE", "GOLD", 0.3)], icon=[("el_british_1947", [1480, 560], 360, "Britain")], label=[("MANDATORY PALESTINE", [960, 860], "GOLD", "Mandatory", 40)],
             card=[("JEWS", [480, 420], "BLUE", "Jews", 260), ("ARABS", [480, 600], "GREEN", "Arabs", 260)]),
 "103": dict(view="mandate", fill=[("PART_J", "BLUE", 0.5, "split"), ("PART_A", "GREEN", 0.5, "split")], pulse=[("JERUSALEM", "WHITE", "Jerusalem")], label=[("JERUSALEM: INTERNATIONAL", (33.2, 31.75), "WHITE", "Jerusalem", 32), ("UN PLAN 1947 (SIMPLIFIED)", [330, 860], "LBLUE", "split", 28)],
             card=[("33 YES", [1650, 300], "GREEN", "Thirty", 300), ("13 NO", [1650, 450], "RED", "thirteen", 300), ("10 ABSTAIN", [1650, 600], "GREY", "ten", 300)]),
 "104": dict(view="mandate", bg="dim", icon=[("el_isr_leader", [520, 600], 400, "Jewish"), ("el_pal_leader", [1400, 600], 400, "Arab")],
             card=[("JEWISH LEADERS: ACCEPT", [520, 280], "BLUE", "accepted", 560), ("ARAB LEADERS: REJECT", [1400, 280], "GREEN", "rejected", 560)]),
 "105": dict(view="mandate", view2="levant_w", move="armies", fill=[("Israel", "BLUE", 0.35, "independence")],
             arrow=[("CAIRO", (34.6, 31.2), "RED", "armies", 0.15), ("AMMAN", (35.35, 31.85), "RED", "armies", 0.1), ("DAMASCUS", (35.65, 32.85), "RED", "armies", 0.1),
                    ("BEIRUT", (35.25, 33.0), "RED", "armies", -0.1), ([1910, 380], (35.8, 32.4), "RED", "armies", 0.05)],
             label=[("ISRAEL DECLARES INDEPENDENCE", [960, 250], "BLUE", "declared", 44)], fx=[("Fighting", "boom", 0.2), ("armies", "shake", 6)]),
 "106": dict(view="mandate", bg="dim", card=[("ISRAEL: WAR OF INDEPENDENCE", [500, 280], "BLUE", "Israelis", 640), ("PALESTINIANS: NAKBA (\"CATASTROPHE\")", [1420, 280], "GREEN", "Nakba", 640)],
             icon=[("el_pal_refugees", [960, 590], 400, "Around")], count=[(0, 700000, "{:,.0f}–750,000", [960, 820], "Around", 2.0, 56, "WHITE")]),
 "107": dict(view="mandate", fill=[("ISRAEL49", "BLUE", 0.4), ("GAZA", "GOLD", 0.6, "Egypt"), ("WB", "PURPLE", 0.5, "Jordan")],
             label=[("ISRAEL ~77%", (34.85, 30.7), "BLUE", 0.3, 40), ("GAZA (EGYPT)", (33.3, 31.45), "GOLD", "Egypt", 34), ("WEST BANK (JORDAN)", (36.9, 32.2), "PURPLE", "Jordan", 34)],
             card=[("ARAB STATE FROM UN PLAN: NEVER FORMED", [960, 260], "RED", "never", 760)]),
 "201": dict(bg="card", view="mandate"),
 "201a": dict(view="sinai", fill=[("Israel", "BLUE", 0.35), ("Egypt", "RED", 0.12)], arrow=[("CAIRO", (33.6, 30.4), "RED", "troops", 0.1)],
              dot=[("TIRAN", "RED", "Straits", 18)], pulse=[("TIRAN", "RED", "Straits")], label=[("STRAITS OF TIRAN CLOSED", (36.3, 27.75), "RED", "Straits", 34)],
              card=[("ISRAELI LEADERS FEAR A WIDER WAR", [960, 820], "BLUE", "feared", 760)]),
 "202": dict(shot="levant67", count=[(1, 6, "DAY {:.0f}", [1700, 250], "six", 2.5, 64, "YEL")],
             card=[("GAZA + SINAI (EGYPT)", [330, 300], "GOLD", "Gaza", 520), ("WEST BANK + E. JERUSALEM (JORDAN)", [330, 470], "GOLD", "West", 520), ("GOLAN HEIGHTS (SYRIA)", [330, 640], "GOLD", "Golan", 520)],
             fx=[("struck", "boom", 0.25), ("struck", "shake", 6)]),
 "203": dict(view="sinai", fill=[("Israel", "BLUE", 0.3), ("SINAI", "GREEN", 0.35, "Sinai"), ("GAZA", "RED", 0.5, "Gaza", "hatch"), ("WB", "RED", 0.5, "Gaza", "hatch")],
             label=[("SINAI BACK TO EGYPT (1982)", (33.5, 29.0), "GREEN", "Sinai", 34), ("ISRAELI MILITARY CONTROL", (37.4, 31.9), "RED", "control", 34)], icon=[("el_two_officials", [1550, 720], 300, "peace")]),
 "204": dict(view="wb", fill=[("WB", "GREEN", 0.25)], custom=[settlements], count=[(0, 740000, "{:,.0f}–780,000 SETTLERS", [960, 250], "Today", 2.0, 56, "BLUE")],
             card=[("ICJ: AGAINST INTERNATIONAL LAW", [520, 800], "GOLD", "court", 560), ("ISRAEL: MUST BE NEGOTIATED", [1400, 800], "BLUE", "rejects", 560)]),
 "205": dict(view="wb", bg="dim", icon=[("el_crowd_tehran", [820, 580], 520, None), ("el_isr_soldier", [1560, 580], 360, "rule")], card=[("INTIFADA = \"SHAKING OFF\"", [960, 260], "GOLD", "meaning", 640)]),
 "205a": dict(view="levant", bg="dim", icon=[("el_checkpoint", [520, 580], 400, "Palestinians"), ("el_bus", [1400, 580], 420, "Israelis")],
              card=[("FEAR · LOSS · INSECURITY — BOTH SIDES", [960, 830], "WHITE", "Civilians", 820)]),
 "206": dict(view="mandate", bg="dim", icon=[("el_contract", [960, 560], 260, "letters")],
             card=[("PLO RECOGNISES ISRAEL", [480, 360], "GREEN", "recognised", 560), ("ISRAEL RECOGNISES THE PLO", [1440, 360], "BLUE", "recognised:1", 560)],
             arrow=[([700, 470], [1250, 470], "GREEN", "recognised", -0.1), ([1250, 650], [700, 650], "BLUE", "recognised:1", -0.1)]),
 "207": dict(view="mandate", bg="dim", icon=[("el_two_officials", [960, 470], 420, None)],
             card=[("PALESTINIAN AUTHORITY", [500, 260], "GREEN", "created", 520), ("5 YEARS", [1450, 260], "GOLD", "five", 300),
                   ("BORDERS", [330, 800], "GREY", "borders", 360), ("JERUSALEM", [750, 800], "GREY", "Jerusalem", 360), ("REFUGEES", [1170, 800], "GREY", "refugees", 360), ("SETTLEMENTS", [1590, 800], "GREY", "settlements", 360)]),
 "208": dict(view="mandate", bg="dim", card=[("BORDERS", [330, 800], "GREY", None, 360), ("JERUSALEM", [750, 800], "GREY", None, 360), ("REFUGEES", [1170, 800], "GREY", None, 360),
                                             ("SETTLEMENTS", [1590, 800], "GREY", None, 360), ("STILL OPEN", [960, 450], "RED", "never", 420)]),
 "208a": dict(view="mandate", bg="dim", icon=[("el_isr_leader", [960, 560], 400, None)], card=[("YITZHAK RABIN, 1995", [960, 260], "BLUE", "Rabin", 560), ("PEACE PROCESS SHAKEN", [960, 820], "RED", "deepened", 560)]),
 "208b": dict(view="mandate", bg="dim", icon=[("el_isr_leader", [480, 600], 340, "Israeli"), ("el_us_president", [960, 600], 340, "Clinton"), ("el_pal_leader", [1440, 600], 340, "Palestinian")],
              card=[("CAMP DAVID, 2000", [960, 250], "WHITE", "Camp", 460), ("NO FINAL AGREEMENT", [960, 840], "RED", "without", 520)]),
 "301": dict(bg="card", view="iran"),
 "302": dict(view="ivl", bg="dim", icon=[("el_shah", [560, 580], 400, "Shah"), ("el_isr_leader", [1360, 580], 380, "partners")],
             card=[("QUIET PARTNERS", [960, 260], "GOLD", "quiet", 460)], arrow=[([760, 520], [1160, 520], "GOLD", "sharing", -0.15), ([1160, 640], [760, 640], "BLUE", "sharing", -0.15)]),
 "303": dict(view="iran", bg="dim", icon=[("el_crowd_tehran", [800, 590], 560, None), ("el_iran_leader", [1500, 590], 360, "leaders")],
             card=[("1979: ISLAMIC REPUBLIC", [800, 260], "GOLD", "Islamic", 560)], fx=[("revolution", "boom", 0.2)]),
 "303a": dict(view="iran", bg="dim", card=[("US EMBASSY SEIZED", [960, 280], "RED", "stormed", 520)],
              count=[(0, 52, "{:.0f} AMERICANS", [560, 560], "52", 1.0, 80, "WHITE"), (0, 444, "{:.0f} DAYS", [1360, 560], "444", 1.5, 80, "YEL")]),
 "304": dict(view="iran", bg="dim", icon=[("el_embassy", [960, 560], 560, None)], custom2=[flagpole("handed")], card=[("ISRAELI EMBASSY → PLO", [480, 300], "GREEN", "handed", 520)]),
 "305": dict(view=LEBW, fill=[("Israel", "BLUE", 0.3), ("Lebanon", "GOLD", 0.15)], arrow=[("HAIFA", (35.5, 33.5), "BLUE", "invaded", 0.15), ([1910, 250], (36.0, 33.9), "GOLD", "Revolutionary", 0.1)],
             pulse=[((35.6, 33.4), "GOLD", "Hezbollah")], label=[("IRAN", [1780, 200], "GOLD", "Revolutionary", 40), ("HEZBOLLAH 1982", (37.1, 34.3), "GOLD", "Hezbollah", 38)]),
 "306": dict(view="ivl", bg="dim", icon=[("el_isr_leader", [520, 580], 360, None), ("el_iran_leader", [1400, 580], 360, None), ("el_crate", [960, 700], 200, "sold")],
             card=[("ENEMIES IN PUBLIC", [960, 260], "RED", "Enemies", 460), ("PARTNERS IN SECRET", [960, 400], "GOLD", "partners", 460)]),
 "401": dict(bg="card", view="mandate"),
 "402": dict(view="mandate", bg="dim", card=[("TALKS COLLAPSE (2000)", [960, 260], "WHITE", "collapsed", 520),
                                             ("ISRAELIS KILLED, INCL. CIVILIANS", [520, 560], "BLUE", "israelis", 580), ("PALESTINIANS KILLED, INCL. CIVILIANS", [1400, 560], "GREEN", "palestinians", 580)]),
 "402a": dict(view="wb", fill=[("WB", "GREEN", 0.2)], line=[([(35.02, 32.55), (35.06, 32.40), (34.99, 32.25), (34.97, 32.10), (35.05, 32.02), (35.17, 32.08), (35.20, 32.04), (35.05, 31.97),
                                                                 (35.0, 31.86), (35.10, 31.79), (35.16, 31.72), (35.10, 31.66), (34.96, 31.55), (35.0, 31.40)], "RED", "barrier", 8)],
              card=[("ISRAEL: STOPS BOMBERS", [460, 300], "BLUE", "stopped", 480), ("PALESTINIANS: CUTS OFF LAND", [1460, 300], "GREEN", "cut", 520), ("ICJ 2004: SECTIONS INSIDE WB ILLEGAL", [960, 800], "GOLD", "2004", 700)]),
 "403": dict(view="gaza", fill=[("GAZA", "GREEN", 0.25)], custom=[gaza_settle], count=[(21, 0, "{:.0f} SETTLEMENTS", [1500, 280], "pulled", 3.0, 56, "BLUE")],
             label=[("~8,500 SETTLERS LEFT", [1500, 380], "WHITE", "settlers", 40)]),
 "404": dict(view="levant", fill=[("GAZA", "GREEN", 0.6, "Gaza"), ("WB", "GOLD", 0.45, "Authority")], card=[("HAMAS: 74 / 132 SEATS", [1500, 260], "GREEN", "elections", 480)],
             label=[("HAMAS", (33.45, 31.45), "GREEN", "Gaza", 40), ("PALESTINIAN AUTHORITY", (36.9, 32.4), "GOLD", "Authority", 36)]),
 "405": dict(view=GAZAW, fill=[("GAZA", "GREEN", 0.3)], custom=[gaza_ring("BLUE", "blockade")], dot=[("RAFAH", "GOLD", "Egypt", 18)], label=[("RAFAH (EGYPT)", (34.05, 31.2), "GOLD", "Egypt", 34)],
             card=[("ISRAEL: STOP WEAPONS", [440, 280], "BLUE", "stopping", 460), ("PALESTINIANS: COLLECTIVE PUNISHMENT", [1460, 280], "GREEN", "collective", 560)]),
 "406": dict(view="levant", fill=[("GAZA", "GREEN", 0.4), ("Israel", "BLUE", 0.2)], salvo=[("GAZA", (34.85, 31.9), 14, "RED", "Rockets", 0.6), ((34.75, 31.65), "GAZA", 10, "BLUE", "strikes", 0.0)],
             label=[("2008", [1560, 300], "WHITE", "2008", 56), ("2014", [1560, 400], "WHITE", "2014", 56), ("2021", [1560, 500], "WHITE", "2021", 56)],
             card=[("CEASEFIRE…", [960, 800], "WHITE", "ceasefire", 380, "underneath")]),
 "406a": dict(view="levant", bg="dim", icon=[("el_shelter_family", [520, 590], 380, "Israeli"), ("el_dark_gaza_house", [1400, 590], 380, "Gaza")],
              count=[(15, 0, "{:.0f}s", [520, 280], "fifteen", 3.0, 90, "RED")], card=[("POWER CUTS", [1400, 280], "GOLD", "power", 360)]),
 "407": dict(shot="natanz", card=[("NATANZ", [1600, 250], "GOLD", "Natanz", 320), ("STUXNET (2010)", [1600, 380], "GREEN", "Stuxnet", 380)], fx=[("sabotage", "click", 0.2)]),
 "408": dict(view="iran", bg="dim", icon=[("el_contract", [700, 560], 300, "signed"), ("el_us_president", [1450, 580], 340, "Trump")],
             card=[("2015 DEAL: CAP 3.67%", [700, 260], "GOLD", "limited", 460), ("2018: US EXITS", [1450, 260], "RED", "pulled", 400)]),
 "409": dict(view="iran", pulse=[("TEHRAN", "RED", "killed")], fill=[("Iran", "GOLD", 0.15)], card=[("IRAN: ISRAEL DID IT", [500, 760], "GOLD", "blamed", 480), ("ISRAEL: NO CLAIM", [1420, 760], "BLUE", "claim", 420)],
             label=[("2020", [960, 250], "WHITE", "2020", 56)]),
 "501": dict(bg="card", view="levant"),
 "502": dict(view=View(34.5, 31.42, 1.6), fill=[("GAZA", "GREEN", 0.3)], custom=[fence_break],
             arrow=[((34.42, 31.33), (34.58, 31.28), "RED", "broke", 0.1), ((34.47, 31.45), (34.65, 31.47), "RED", "broke", 0.1), ((34.52, 31.55), (34.68, 31.6), "RED", "broke", -0.1)],
             label=[("SOUTHERN ISRAEL", (34.85, 31.35), "BLUE", "southern", 36)], fx=[("broke", "boom", 0.3), ("broke", "shake", 8)]),
 "503": dict(view="levant", bg="dim", count=[(0, 1200, "~{:,.0f} KILLED", [560, 480], "1,200", 1.5, 76, "WHITE"), (0, 251, "{:.0f} HOSTAGES", [1360, 480], "251", 1.5, 76, "WHITE")],
             label=[("SOURCE: ISRAELI TALLY", [960, 640], "LBLUE", "According", 32)], card=[("DEADLIEST DAY IN ISRAEL'S HISTORY", [960, 800], "BLUE", "deadliest", 700)]),
 "504": dict(view="gaza", fill=[("GAZA", "GREEN", 0.3)], card=[("GOAL 1: DESTROY HAMAS", [1480, 280], "BLUE", "destroy", 520), ("GOAL 2: BRING HOSTAGES HOME", [1480, 420], "BLUE", "hostages", 520)],
             arrow=[((34.56, 31.64), (34.47, 31.52), "BLUE", "ground", 0.1)], salvo=[((34.6, 31.6), "GAZA", 12, "BLUE", "air", 0.0)], fx=[("massive", "boom", 0.2)]),
 "504a": dict(view="gaza", bg="dim", icon=[("el_hostage_bus", [600, 580], 420, "truce")], card=[("7-DAY TRUCE (NOV 2023)", [960, 260], "GOLD", "one", 520), ("105 HOSTAGES ↔ 240 PRISONERS", [1360, 560], "WHITE", "hundred", 520)],
              arrow=[([1000, 820], [1700, 820], "BLUE", "resumed", 0.0)], label=[("SOUTH", [1820, 820], "BLUE", "south", 40)]),
 "505": dict(view="gaza", fill=[("GAZA", "GREEN", 0.25)], bg="dim", count=[(0, 74746, "{:,.0f}", [960, 380], "74,746", 2.5, 120, "WHITE")],
             label=[("REPORTED BY GAZA'S HEALTH MINISTRY (PART OF HAMAS-RUN GOVERNMENT)", [960, 500], "LBLUE", "Ministry", 36), ("DOES NOT SEPARATE CIVILIANS / FIGHTERS", [960, 570], "LBLUE", "separate", 36)],
             card=[("ISRAEL: THOUSANDS WERE FIGHTERS", [960, 760], "BLUE", "thousands", 620)]),
 "506": dict(view="gaza", bg="dim", custom2=[people], label=[("~1.9 MILLION DISPLACED", [960, 800], "WHITE", "1.9", 54)]),
 "507": dict(view="gaza", bg="dim", custom2=[ipc], card=[("IPC: FAMINE CONFIRMED IN GAZA CITY (AUG 2025)", [1300, 330], "GOLD", "confirmed", 600), ("ISRAEL REJECTS THE FINDING", [1300, 620], "BLUE", "rejected", 520)]),
 "508": dict(view="levant", bg="dim", icon=[("el_court", [960, 560], 420, None)], card=[("SOUTH AFRICA: GENOCIDE", [430, 300], "GOLD", "accusing", 480), ("ISRAEL: DENIES / SELF-DEFENCE", [1490, 300], "BLUE", "denies", 520),
                                                                                       ("COURT: PREVENT GENOCIDAL ACTS", [960, 800], "WHITE", "ordered", 560, "ruled"), ("NO RULING ON THE ACCUSATION YET", [960, 800], "RED", "ruled", 640)],
             count=[(2026, 2029, "{:.0f}", [960, 250], "decision", 2.0, 64, "YEL")]),
 "508a": dict(view=GAZAW, fill=[("GAZA", "GREEN", 0.3)], pulse=[("RAFAH", "WHITE", "killed")], card=[("YAHYA SINWAR — OCT 2024", [1450, 280], "WHITE", "Sinwar", 520), ("THE WAR CONTINUES", [1450, 760], "RED", "war", 440)]),
 "601": dict(bg="card", view="wide"),
 "602": dict(view="wide", fill=[("Israel", "BLUE", 0.4), ("Iran", "GOLD", 0.15)],
             pulse=[((35.8, 33.9), "GOLD", "Hezbollah"), ((38.5, 35.0), "GOLD", "Syria"), ((43.5, 33.3), "GOLD", "Iraq"), ("SANAA", "GOLD", "Houthis"), ("GAZA", "GOLD", "Hamas")],
             line=[(["TEHRAN", (35.8, 33.9)], "GOLD", "arm", 3), (["TEHRAN", (38.5, 35.0)], "GOLD", "arm", 3), (["TEHRAN", (43.5, 33.3)], "GOLD", "arm", 3), (["TEHRAN", "SANAA"], "GOLD", "arm", 3), (["TEHRAN", "GAZA"], "GOLD", "arm", 3)],
             label=[("HEZBOLLAH", (33.2, 35.0), "GOLD", "Hezbollah", 30), ("MILITIAS", (40.5, 36.2), "GOLD", "militias", 30), ("HOUTHIS", (44.2, 13.8), "GOLD", "Houthis", 30), ("HAMAS", (31.7, 30.6), "GOLD", "Hamas", 30),
                    ("\"AXIS OF RESISTANCE\" (IRAN'S TERM)", [960, 860], "WHITE", "axis", 36)]),
 "603": dict(view=NORTH, fill=[("Israel", "BLUE", 0.3), ("Lebanon", "GOLD", 0.2)], salvo=[((35.5, 33.35), (35.45, 32.95), 10, "GOLD", "firing", 0.4), ((35.4, 32.95), (35.5, 33.35), 10, "BLUE", "fired", 0.0)],
             card=[("TENS OF THOUSANDS EVACUATED — BOTH SIDES", [960, 820], "WHITE", "thousands", 820)]),
 "604": dict(view=LEB, fill=[("Lebanon", "GOLD", 0.18)], custom=[pager_flash], card=[("PAGERS — SEPT 17, 2024", [1500, 280], "ORANGE", "pagers", 520), ("WALKIE-TALKIES — SEPT 18", [1500, 420], "ORANGE", "walkie", 520),
                                                                                       ("NETANYAHU LATER CONFIRMED APPROVING IT", [960, 820], "BLUE", "confirmed", 760)], fx=[("exploded", "boom", 0.15), ("walkie", "boom", 0.12)]),
 "605": dict(view=LEB, fill=[("Lebanon", "GOLD", 0.15)], pulse=[("BEIRUT", "RED", "killed")], dot=[("BEIRUT", "RED", "killed", 18)], card=[("HASSAN NASRALLAH (LEADER 32 YEARS)", [1400, 280], "WHITE", "Nasrallah", 600)], fx=[("killed", "boom", 0.25)]),
 "605a": dict(view=NORTH, fill=[("Israel", "BLUE", 0.3), ("Lebanon", "GOLD", 0.2)], arrow=[((35.25, 33.0), (35.3, 33.3), "BLUE", "crossed", 0.1), ((35.6, 33.05), (35.6, 33.33), "BLUE", "crossed", -0.1)],
              card=[("CEASEFIRE — NOV 27, 2024", [1450, 280], "WHITE", "ceasefire", 520)], salvo=[((35.3, 32.9), (35.5, 33.4), 5, "BLUE", "though", 0.0)]),
 "606": dict(shot="redsea_ship", card=[("RED SEA", [1600, 250], "LBLUE", "Red", 300), ("BAB EL-MANDEB: −55% TRANSITS", [1500, 390], "GOLD", "fell", 560)]),
 "607": dict(view="ivl", line=[(["TEHRAN", "BAGHDAD", "DAMASCUS", "BEIRUT"], "GOLD", 0.0, 7)], pulse=[("DAMASCUS", "RED", "toppled")],
             label=[("X", (37.0, 34.2), "RED", "land", 110), ("ASSAD FALLS — DEC 2024", [1400, 250], "RED", "toppled", 44)]),
 "701": dict(bg="card", view="region"),
 "702": dict(view="region", fill=[("Israel", "BLUE", 0.4), ("Iran", "GOLD", 0.2)], dot=[("DAMASCUS", "RED", "strike", 18)], salvo=[("TEHRAN", "TELAVIV", 30, "GOLD", "300", 0.0)],
             count=[(0, 300, "{:.0f}+", [1500, 300], "300", 2.0, 90, "GOLD")], fx=[("launched", "creak", 0.08)]),
 "703": dict(view="region", fill=[("Israel", "BLUE", 0.4), ("Iran", "GOLD", 0.2)], salvo=[("TEHRAN", "TELAVIV", 26, "GOLD", None, 0.9)], arrow=[("TELAVIV", "ISFAHAN", "BLUE", "limited", 0.15)],
             label=[("MOST SHOT DOWN", [960, 820], "WHITE", "shot", 44)]),
 "703a": dict(view=TEH, fill=[("Iran", "GOLD", 0.15)], pulse=[("TEHRAN", "RED", "killed")], card=[("ISMAIL HANIYEH (HAMAS) — JULY 2024", [1350, 260], "WHITE", "Haniyeh", 620),
                                                                                           ("IRAN: RETALIATION", [520, 780], "GOLD", "retaliation", 420), ("ISRAEL LATER ACKNOWLEDGED IT", [1380, 780], "BLUE", "acknowledged", 560)]),
 "703b": dict(view="region", fill=[("Israel", "BLUE", 0.4), ("Iran", "GOLD", 0.2)], salvo=[("TEHRAN", "TELAVIV", 24, "GOLD", "180", 0.8)], arrow=[("TELAVIV", "TEHRAN", "BLUE", "struck", 0.15)],
              count=[(0, 180, "~{:.0f} MISSILES", [1500, 300], "180", 1.5, 64, "GOLD")]),
 "704": dict(shot="iran_jets", card=[("JUNE 13, 2025", [400, 250], "WHITE", 0.2, 380), ("ISRAEL: NEAR A NUCLEAR WEAPON", [1440, 250], "BLUE", "dangerously", 560)], fx=[("bigger", "creak", 0.08)]),
 "705": dict(view="iran", bg="dim", custom2=[enrich], card=[("IRAN: PROGRAM IS PEACEFUL", [960, 260], "GOLD", "peaceful", 560), ("MATERIAL IS NOT A BOMB", [960, 820], "WHITE", "same", 520)]),
 "706": dict(shot="fordow", card=[("FORDOW", [1650, 250], "GOLD", "Fordow", 300), ("US STRIKES — JUNE 22", [450, 250], "WHITE", "22nd", 460)], fx=[("bombing", "boom", 0.35), ("bombing", "shake", 10)]),
 "707": dict(view="region", fill=[("Israel", "BLUE", 0.4), ("Iran", "GOLD", 0.2)], count=[(1, 12, "DAY {:.0f}", [960, 250], 0.0, 3.0, 70, "YEL")],
             card=[("IRAN REPORTS ~1,062 KILLED", [1420, 640], "GOLD", "1,062", 520), ("ISRAEL REPORTS 29 KILLED", [480, 640], "BLUE", "29", 480), ("?", [1300, 400], "WHITE", "survived", 160)],
             label=[("CEASEFIRE", [960, 330], "WHITE", "ceasefire", 50)]),
 "801": dict(bg="card", view="levant"),
 "802": dict(view="gaza", bg="dim", card=[("33 HOSTAGES ↔ ~1,800 PRISONERS", [960, 270], "WHITE", "33", 640), ("MARCH 2025: STRIKES RESUME", [960, 430], "RED", "March", 560),
                                         ("ISRAEL: HAMAS REFUSED MORE RELEASES", [500, 700], "BLUE", "blamed", 600), ("HAMAS: ISRAEL ABANDONED PHASE 2", [1420, 700], "GREEN", "abandoned", 600)]),
 "803": dict(view="gaza", bg="dim", icon=[("el_aid_truck", [1400, 590], 420, "aid")], card=[("OCT 2025: 20-POINT PLAN", [560, 300], "GOLD", "twenty", 520), ("LAST LIVING HOSTAGES HOME", [560, 560], "WHITE", "living", 520),
                                                                                          ("PARTIAL ISRAELI PULLBACK", [560, 780], "BLUE", "pulled", 520)]),
 "804": dict(view="gaza", fill=[("GAZA", "GREEN", 0.3)], card=[("DISARM HAMAS", [460, 300], "GREY", "disarming", 420), ("FULL WITHDRAWAL", [1460, 300], "GREY", "withdrawal", 420),
                                                             ("INTERNATIONAL FORCE", [460, 720], "GREY", "international", 420), ("REBUILD", [1460, 720], "GREY", "rebuilding", 420)],
             salvo=[((34.6, 31.6), "GAZA", 5, "BLUE", "Strikes", 0.0)]),
 "805": dict(view="gulf", fill=[("Iran", "GOLD", 0.2)], pulse=[("BANDAR", "RED", "blockaded")],
             card=[("FEB: STRIKES", [330, 280], "RED", "February", 360), ("APR: CEASEFIRE", [750, 280], "WHITE", "April", 360), ("APR: US BLOCKADE", [1170, 280], "BLUE", "blockaded", 360), ("JUN: 60-DAY DEAL", [1590, 280], "GREEN", "June", 360)]),
 "806": dict(shot="hormuz", shot_off=0.0, card=[("JULY: BLOCKADE BACK", [1500, 250], "RED", "July", 480), ("TALKS IN QATAR — NOV 2026", [1500, 390], "WHITE", "Qatar", 520)]),
 "901": dict(bg="card", view="wide", fill=[("Israel", "BLUE", 0.4), ("Palestine", "GREEN", 0.5), ("Iran", "GOLD", 0.2), ("Lebanon", "GOLD", 0.2), ("Yemen", "GOLD", 0.15)]),
 "902": dict(view="mandate", bg="dim", icon=[("el_isr_leader", [440, 580], 420, None)],
             card=[("NO ARMED HAMAS ON ITS BORDER", [1260, 300], "BLUE", "Hamas", 760), ("NO IRANIAN MISSILES / BOMB", [1260, 470], "BLUE", "missiles", 760), ("NO PALESTINIAN STATE NOW", [1260, 640], "BLUE", "opposes", 760)]),
 "903": dict(view="mandate", bg="dim", icon=[("el_pal_leader", [440, 580], 420, None)],
             card=[("STATE ON 1967 LINES", [1260, 260], "GREEN", "state", 760), ("CAPITAL: EAST JERUSALEM", [1260, 410], "GREEN", "capital", 760), ("HAMAS MUST GIVE UP WEAPONS", [1260, 560], "GREEN", "weapons", 760),
                   ("HAMAS: END WAR + FULL WITHDRAWAL", [1260, 760], "GOLD", "demands", 760)]),
 "904": dict(view="iran", bg="dim", icon=[("el_iran_leader", [440, 560], 420, None), ("el_iran_family", [1260, 760], 280, "ordinary")],
             card=[("NO NUCLEAR WEAPON", [1260, 260], "GOLD", "never", 640), ("KEEP ENRICHING", [1260, 400], "GOLD", "enriching", 640), ("END BLOCKADE, SANCTIONS, ATTACKS", [1260, 540], "GOLD", "blockade", 640)]),
 "905": dict(view="wide", bg="dim", icon=[("el_isr_leader", [480, 580], 330, None), ("el_pal_leader", [960, 580], 330, None), ("el_iran_leader", [1440, 580], 330, None)],
             card=[("SINCE 1979: LINKED", [960, 260], "GOLD", "linked", 480), ("SECURITY · LAND · SOVEREIGNTY · POWER", [960, 830], "WHITE", "unresolved", 1000)]),
 "906": dict(view="iran", bg="dim", icon=[("el_embassy", [960, 560], 560, None)], custom2=[flagpole("came")], label=[("TEHRAN, 1979", [960, 860], "LBLUE", 0.0, 44)]),
 "907": dict(view="wide", bg="dim", custom2=[chapters_list], card=[("SUBSCRIBE", [960, 800], "RED", "subscribe", 400)]),
}
E.STORY.update(STORY)

"""Prezentáció: docs/prezentacio.pptx az ÓE NIK prezentációs sablonjára építve.

A sablon mestereit és elrendezéseit használja (címdia, tartalmi dia),
a tartalmat a sablon betűtípusával (Open Sans) és színével (1D294D) rajzolja rá.
Futtatás: python3 scripts/build-slides.py   (python-pptx szükséges)
"""
import copy
import sys
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "docs" / "templates" / "NIK_prezentacio_sablon_2025.pptx"
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "docs" / "prezentacio.pptx"

FONT = "Open Sans"
NAVY = RGBColor(0x1D, 0x29, 0x4D)
TINT = RGBColor(0xEC, 0xEF, 0xF5)      # kártyák háttere
MUTED = RGBColor(0x5B, 0x65, 0x80)     # másodlagos szöveg
GREY = RGBColor(0x9A, 0xA3, 0xB8)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
GOOD = RGBColor(0x2E, 0x7D, 0x32)
BAD = RGBColor(0xC0, 0x00, 0x00)
RISK = {
    "Kritikus": (RGBColor(0xC0, 0x00, 0x00), WHITE),
    "Magas": (RGBColor(0xE4, 0x6C, 0x0A), WHITE),
    "Közepes": (RGBColor(0xFF, 0xC0, 0x00), NAVY),
    "Alacsony": (RGBColor(0x53, 0x81, 0x35), WHITE),
}
X0, W0 = 0.3, 9.4          # tartalmi terület: a cím bal szélétől
Y0, Y1 = 1.75, 6.75        # a cím alatt, az alsó sáv felett

prs = Presentation(str(TEMPLATE))

# a sablon mintadiáinak eltávolítása
sld_ids = prs.slides._sldIdLst
for sld in list(sld_ids):
    prs.part.drop_rel(sld.rId)
    sld_ids.remove(sld)

M_BANDS, M_NAVY = prs.slide_masters[0], prs.slide_masters[1]
L_TITLE = M_NAVY.slide_layouts[0]       # 2_1 Címdia
L_CONTENT = M_BANDS.slide_layouts[8]    # 1_8_tartalomrész

SLIDE_COUNT = 10  # a tárgy követelménye: max. 10 dia


def fix_total_in_layouts():
    """A sablon diaszámai fix '/39' összesítőt tartalmaznak: a valós diaszámra cseréljük."""
    for master in prs.slide_masters:
        for layout in master.slide_layouts:
            for fld in layout._element.iter(qn("a:fld")):
                if fld.get("type") != "slidenum":
                    continue
                nxt = fld.getnext()
                if nxt is not None and nxt.tag == qn("a:r"):
                    t = nxt.find(qn("a:t"))
                    if t is not None and t.text and t.text.startswith("/"):
                        t.text = f"/{SLIDE_COUNT}"


def add_slide_number(slide):
    """A python-pptx nem másolja át a diaszám helyőrzőt, ezért a layoutból klónozzuk."""
    for sp in slide.slide_layout.placeholders:
        if sp.placeholder_format.type is not None and "SLIDE_NUMBER" in str(sp.placeholder_format.type):
            el = copy.deepcopy(sp._element)
            sppr = el.find(qn("p:spPr"))
            for child in list(sppr):
                sppr.remove(child)
            slide.shapes._spTree.append(el)
            return


def remove_empty_placeholders(slide, keep=("title",)):
    for ph in list(slide.placeholders):
        t = str(ph.placeholder_format.type)
        if any(k.upper() in t for k in keep):
            continue
        ph._element.getparent().remove(ph._element)


def style_run(run, size, color=NAVY, bold=False, italic=False):
    f = run.font
    f.name = FONT
    f.size = Pt(size)
    f.bold = bold
    f.italic = italic
    f.color.rgb = color
    rpr = run._r.get_or_add_rPr()
    for tag in ("a:ea", "a:cs"):
        e = rpr.find(qn(tag))
        if e is None:
            e = etree.SubElement(rpr, qn(tag))
        e.set("typeface", FONT)


def text(slide, x, y, w, h, paras, size=14, color=NAVY, bold=False, align=PP_ALIGN.LEFT,
         anchor=MSO_ANCHOR.TOP, bullet=False, space_after=0, name=None):
    """paras: str | list of paragraphs; a paragraph is str or list of (text, {opts})."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    if name:
        tb.name = name
    tf = tb.text_frame
    tf.word_wrap = True
    tf.auto_size = None
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    if isinstance(paras, str):
        paras = [paras]
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        if space_after:
            p.space_after = Pt(space_after)
        if bullet:
            ppr = p._p.get_or_add_pPr()
            ppr.set("marL", str(Inches(0.22)))
            ppr.set("indent", str(-Inches(0.22)))
            bu = etree.SubElement(ppr, qn("a:buChar"))
            bu.set("char", "•")
        runs = [(para, {})] if isinstance(para, str) else para
        for t, o in runs:
            r = p.add_run()
            r.text = t
            style_run(r, o.get("size", size), o.get("color", color), o.get("bold", bold), o.get("italic", False))
    return tb


def shape(slide, kind, x, y, w, h, fill, line=None, radius=None, name=None, dash=False):
    s = slide.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h))
    if name:
        s.name = name
    s.shadow.inherit = False
    if fill is None:
        s.fill.background()
    else:
        s.fill.solid()
        s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line
        s.line.width = Pt(1)
        if dash:
            s.line.dash_style = 4  # MSO_LINE.DASH
    if radius is not None and kind == MSO_SHAPE.ROUNDED_RECTANGLE:
        s.adjustments[0] = radius
    return s


def card(slide, x, y, w, h, fill=TINT, name=None):
    return shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h, fill, radius=0.08, name=name)


def badge(slide, label, x, y, w, h, fill, color=WHITE, size=12):
    shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h, fill, radius=0.5)
    text(slide, x, y, w, h, label, size=size, color=color, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)


def circle_num(slide, n, x, y, d=0.55, fill=NAVY, color=WHITE):
    shape(slide, MSO_SHAPE.OVAL, x, y, d, d, fill)
    text(slide, x, y, d, d, str(n), size=16, color=color, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)


def content_slide(title, notes, layout=None):
    s = prs.slides.add_slide(layout or L_CONTENT)
    remove_empty_placeholders(s)
    tp = s.shapes.title
    tp.text_frame.text = title
    for r in tp.text_frame.paragraphs[0].runs:
        r.font.size = Pt(28)
    add_slide_number(s)
    s.notes_slide.notes_text_frame.text = notes
    return s


def column_chart(slide, x, y, w, h, title, cats, series, colors):
    data = CategoryChartData()
    data.categories = cats
    for name, vals in series:
        data.add_series(name, vals)
    gf = slide.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(x), Inches(y), Inches(w), Inches(h), data)
    ch = gf.chart
    ch.font.name = FONT
    ch.font.size = Pt(12)
    ch.font.color.rgb = NAVY
    ch.has_title = True
    ch.chart_title.text_frame.text = title
    tr = ch.chart_title.text_frame.paragraphs[0].runs[0]
    style_run(tr, 14, NAVY, bold=True)
    ch.has_legend = True
    ch.legend.position = XL_LEGEND_POSITION.TOP
    ch.legend.include_in_layout = False
    ch.legend.font.size = Pt(12)
    va = ch.value_axis
    va.visible = False
    va.has_major_gridlines = False
    ca = ch.category_axis
    ca.has_major_gridlines = False
    ca.tick_labels.font.size = Pt(12)
    ca.format.line.color.rgb = GREY
    plot = ch.plots[0]
    plot.gap_width = 60
    plot.overlap = -10
    plot.has_data_labels = True
    dl = plot.data_labels
    dl.position = XL_LABEL_POSITION.OUTSIDE_END
    dl.font.size = Pt(12)
    dl.font.color.rgb = NAVY
    dl.number_format = "0"
    dl.number_format_is_linked = False
    for ser, col in zip(plot.series, colors):
        ser.format.fill.solid()
        ser.format.fill.fore_color.rgb = col
    return gf


fix_total_in_layouts()

# ---- 1. Címdia --------------------------------------------------------------------
s = prs.slides.add_slide(L_TITLE)
for ph in s.placeholders:
    idx = ph.placeholder_format.idx
    if idx == 0:
        ph.text_frame.text = "Konténerizált webalkalmazás auditja a CIS Docker Benchmark alapján"
    elif idx == 13:
        ph.text_frame.text = "IT Audit – páros audit projekt\vAnderko Máté, Nagy József"
    elif idx == 14:
        ph.text_frame.text = "Auditált fél\vFiktív cég KFT."
    elif idx == 15:
        ph.text_frame.text = "Követelményrendszer\vCIS Docker Benchmark v1.6.0"
s.notes_slide.notes_text_frame.text = (
    "Bemutatkozás és a szerepek. A téma: egy időpontfoglaló webalkalmazás Docker futtatókörnyezetének "
    "megfelelőségi auditja a CIS Docker Benchmark v1.6.0 alapján, technikai eszközökkel, javítással és újraméréssel.")

# ---- 2. Cél, tárgy, mérce -------------------------------------------------------------
s = content_slide("Cél, tárgy és mérce",
    "Az audit célja: független, eszközökkel alátámasztott értékelés a CIS Docker Benchmarknak való megfelelésről, "
    "kockázatértékeléssel és akciótervvel. A teljeskörűség miatt a host, a daemon, az image-ek és a runtime is a tárgy "
    "része, nem csak az alkalmazás. A kizárásokat a tervben indokoltuk.")
cards2 = [
    ("Tárgy", "Időpontfoglaló webapp 3 konténerben: Nginx proxy, Flask app, PostgreSQL. Manjaro Linux host, Docker 29.8"),
    ("Mérce", "CIS Docker Benchmark v1.6.0, Level 1. Kiegészítő: Trivy (CIS 4.4) és NIST CSF besorolás"),
    ("Módszer", "Dokumentumvizsgálat, megfigyelés, docker-bench-security, Trivy, újrateljesítés (v1 → v2)"),
]
cw, gap = 2.95, 0.275
for i, (h, b) in enumerate(cards2):
    x = X0 + i * (cw + gap)
    card(s, x, Y0, cw, 3.55)
    circle_num(s, i + 1, x + 0.3, Y0 + 0.3)
    text(s, x + 0.3, Y0 + 1.05, cw - 0.6, 0.45, h, size=20, bold=True)
    text(s, x + 0.3, Y0 + 1.6, cw - 0.6, 1.85, b, size=15, color=MUTED)
card(s, X0, 5.6, W0, 1.0)
text(s, X0 + 0.3, 5.6, W0 - 0.6, 1.0,
     [[("Kizárva: ", {"bold": True}), ("CIS 7. fejezet (Swarm, N/A), alkalmazáskód (ASVS/DAST), hypervisor, BCP/DRP, behatolásteszt", {})]],
     size=14, anchor=MSO_ANCHOR.MIDDLE)

# ---- 3. Architektúra ---------------------------------------------------------------------
s = content_slide("A vizsgált rendszer: v1 és v2",
    "Bal oldalon a kiinduló állapot: Docker alapbeállítások és a hivatalos postgres image példája szerinti compose "
    "(a források a jelentés 3.1 fejezetében). Az adatbázis portját kényelmi okból publikáltuk. Mindhárom konténer root, "
    "mindhárom port nyitva minden interfészen, köztük az adatbázisé, gyenge jelszóval a compose fájlban. Jobb oldalon a v2: "
    "egyetlen publikált port a proxyn, az adatbázis csak belső hálózaton érhető el, minden konténer nem root userrel fut. "
    "Az alkalmazás kódja nem változott.")


def stack(x0, labels, ports, v2):
    colw = 4.5
    text(s, x0, Y0, colw, 0.4, "v2 – akcióterv után" if v2 else "v1 – alapbeállításos telepítés",
         size=18, bold=True, color=GOOD if v2 else BAD)
    top, bottom = Y0 + 0.6, Y1 - 0.1
    if v2:
        shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, x0, top, colw, 2.75, TINT, line=GREY, radius=0.05, dash=True)
        shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, x0, top + 1.55, colw, bottom - top - 1.55, None, line=GOOD, radius=0.05, dash=True)
        text(s, x0 + 2.4, top + 0.1, colw - 2.55, 0.3, "frontend", size=12, color=MUTED, align=PP_ALIGN.RIGHT)
        text(s, x0 + 2.0, bottom - 0.4, colw - 2.15, 0.3, "backend (internal)", size=12, color=GOOD, align=PP_ALIGN.RIGHT)
    else:
        shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, x0, top, colw, bottom - top, TINT, line=GREY, radius=0.05, dash=True)
        text(s, x0 + 2.0, bottom - 0.4, colw - 2.15, 0.3, "egy közös hálózat", size=12, color=MUTED, align=PP_ALIGN.RIGHT)
    for i, lbl in enumerate(labels):
        y = top + 0.5 + i * 1.3
        shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, x0 + 0.25, y, 2.1, 0.7, NAVY, radius=0.1)
        text(s, x0 + 0.25, y, 2.1, 0.7, lbl, size=14, bold=True, color=WHITE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        if ports[i]:
            badge(s, ports[i], x0 + 2.5, y + 0.16, 1.8, 0.38, GOOD if v2 else BAD, size=12)


stack(X0, ["proxy · root", "app · root", "db · root"], ["0.0.0.0:80", "0.0.0.0:8000", "0.0.0.0:5432"], False)
stack(X0 + 4.9, ["proxy · uid 101", "app · uid 10001", "db · postgres"], ["127.0.0.1:8080", None, None], True)

# ---- 4. Folyamat ------------------------------------------------------------------------
s = content_slide("Az audit menete",
    "A folyamat az előadások audit munkafolyamatát követi: tervezés, bizonyítékgyűjtés, értékelés, jelentés, utókövetés. "
    "A bizonyítékgyűjtést egyetlen szkript végzi, ezért a mérés megismételhető. Minden fájlnak SHA-256 hash-e van, "
    "a nyers kimeneteket nem módosítjuk.")
steps = [
    ("Terv", "cél, tárgy, kizárások, kockázati módszer"),
    ("v1 telepítés", "alapbeállítások, hivatalos image-példák"),
    ("Mérés", "docker-bench, Trivy, SHA-256 hash"),
    ("Értékelés", "13 megállapítás, kockázat, CSF"),
    ("Javítás", "v2 az akcióterv alapján"),
    ("Újramérés", "utókövetés, összehasonlítás"),
]
step_w = W0 / 6
ln = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(X0 + step_w / 2), Inches(Y0 + 0.9),
                            Inches(X0 + W0 - step_w / 2), Inches(Y0 + 0.9))
ln.line.color.rgb = GREY
ln.line.width = Pt(1.5)
for i, (h, b) in enumerate(steps):
    cx = X0 + i * step_w + step_w / 2
    circle_num(s, i + 1, cx - 0.33, Y0 + 0.57, d=0.66, fill=GOOD if i == 5 else NAVY)
    text(s, cx - step_w / 2 + 0.03, Y0 + 1.45, step_w - 0.06, 0.4, h, size=15, bold=True, align=PP_ALIGN.CENTER)
    text(s, cx - step_w / 2 + 0.08, Y0 + 1.9, step_w - 0.16, 1.4, b, size=13, color=MUTED, align=PP_ALIGN.CENTER)
card(s, X0, 4.85, W0, 1.45)
text(s, X0 + 0.3, 4.85, W0 - 0.6, 1.45,
     [[("Bizonyítékkezelés: ", {"bold": True}),
       ("mérésenként időbélyeges könyvtár, nyers kimenetek, SHA-256 hash, mérési napló, maszkolt jelszavak, verziókezelés", {})]],
     size=15, anchor=MSO_ANCHOR.MIDDLE)

# ---- 5. v1 eredmények ---------------------------------------------------------------------
s = content_slide("Kiinduló állapot (v1): messze a CIS ajánlásoktól",
    "Az alapbeállításos telepítés pontszáma 5. A WARN eredmények a host-auditálásban, a daemon-beállításokban és a "
    "konténer runtime-ban koncentrálódnak. A Trivy 454 magas vagy kritikus sérülékenységet talált, főleg a teljes Debian "
    "alapú latest image-ek felesleges csomagjaiban. Érdekesség: a python:latest a projekt előkészítése közben Python "
    "3.15-re váltott, és emiatt kódváltozás nélkül eltört a build. Ez a latest tag kockázatának gyakorlati példája.")
stats5 = [("5", "docker-bench score", "117 ellenőrzésből"), ("29", "WARN eredmény", "CIS 1–6. fejezet"),
          ("454", "magas + kritikus CVE", "3 image, Trivy")]
for i, (n, l, sub) in enumerate(stats5):
    y = Y0 + i * 1.7
    card(s, X0, y, 3.1, 1.5)
    text(s, X0 + 0.2, y, 3.1 - 0.4, 0.85, n, size=36, bold=True, color=BAD, anchor=MSO_ANCHOR.BOTTOM)
    text(s, X0 + 0.2, y + 0.88, 3.1 - 0.4, 0.6, [[(l, {"bold": True})], [(sub, {"size": 12, "color": MUTED})]], size=14)
cats = ["1 Host", "2 Daemon", "3 Daemon fájlok", "4 Image", "5 Runtime"]
column_chart(s, X0 + 3.35, Y0 - 0.05, W0 - 3.35, 4.95, "docker-bench eredmények CIS fejezetenként (v1)", cats,
             [("PASS", (1, 6, 8, 1, 18)), ("WARN", (9, 7, 0, 3, 10))], [NAVY, BAD])

# ---- 6. Top megállapítások ----------------------------------------------------------------
s = content_slide("A legsúlyosabb megállapítások",
    "Összesen 13 megállapítás: 1 kritikus, 4 magas, 4 közepes, 4 alacsony. A legsúlyosabb az M-05: a hálózatról "
    "közvetlenül elérhető adatbázis gyenge jelszóval, ami a személyes adatok (név, e-mail) kiszivárgásához vezethet. "
    "Minden megállapítást legalább egy független bizonyíték is alátámaszt, nem csak az eszköz kimenete.")
top = [
    ("Kritikus", "M-05", "Adatbázis-port minden interfészen, gyenge jelszóval", "docker ps: 0.0.0.0:5432 · CIS 5.9, 5.14"),
    ("Magas", "M-02", "Mindhárom konténer root felhasználóval fut", "inspect: Config.User = \"\" · CIS 4.1"),
    ("Magas", "M-03", "Jelszavak nyílt szövegként: compose fájl és env", "docker inspect kiolvasható · CIS 4.10"),
    ("Magas", "M-04", "latest image-ek, 454 magas/kritikus CVE", "Trivy · CIS 4.2–4.4"),
    ("Magas", "M-10", "Daemon alapbeállítással fut (userns, icc, live-restore)", "nincs daemon.json · CIS 2.x"),
]
for i, (lvl, fid, t, ev) in enumerate(top):
    y = Y0 + i * 1.0
    card(s, X0, y, W0, 0.85)
    fill, fg = RISK[lvl]
    badge(s, lvl, X0 + 0.15, y + 0.24, 1.15, 0.38, fill, fg, size=12)
    text(s, X0 + 1.45, y, 0.75, 0.85, fid, size=15, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    text(s, X0 + 2.2, y, 4.35, 0.85, t, size=14, anchor=MSO_ANCHOR.MIDDLE)
    text(s, X0 + 6.7, y, W0 - 6.85, 0.85, ev, size=12, color=MUTED, anchor=MSO_ANCHOR.MIDDLE)

# ---- 7. Kockázati mátrix ----------------------------------------------------------------
s = content_slide("Kockázati mátrix: hatás × valószínűség",
    "A kockázat a hatás és a bekövetkezési valószínűség függvénye, az előadás háromszintű skálája szerint. A jobb felső "
    "sarokban az M-05. A userns-remap hiánya (M-10) azért magas, mert enélkül a konténerbeli root azonos a host rootjával, "
    "így egy konténerkitörés host szintű kompromittálódás.")
lvl_grid = [["Közepes", "Magas", "Kritikus"], ["Alacsony", "Közepes", "Magas"], ["Alacsony", "Alacsony", "Közepes"]]
ids = [[[], ["M-02", "M-03", "M-10"], ["M-05"]],
       [["M-12"], ["M-01", "M-06", "M-07", "M-08"], ["M-04"]],
       [["M-13"], ["M-09", "M-11"], []]]
gx, gy, cell_w, cell_h = X0 + 1.1, Y0 + 0.35, 1.6, 1.25
text(s, X0, Y0 - 0.05, 1.0, 0.3, "Hatás ↑", size=12, bold=True, align=PP_ALIGN.RIGHT)
for r, h in enumerate(["Magas", "Közepes", "Alacsony"]):
    text(s, X0, gy + r * cell_h, 1.0, cell_h, h, size=12, color=MUTED, align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)
for c, v in enumerate(["Alacsony", "Közepes", "Magas"]):
    text(s, gx + c * cell_w, gy + 3 * cell_h + 0.05, cell_w, 0.3, v, size=12, color=MUTED, align=PP_ALIGN.CENTER)
text(s, gx, gy + 3 * cell_h + 0.4, 3 * cell_w, 0.3, "Valószínűség →", size=12, bold=True, align=PP_ALIGN.CENTER)
for r in range(3):
    for c in range(3):
        fill, fg = RISK[lvl_grid[r][c]]
        shape(s, MSO_SHAPE.RECTANGLE, gx + c * cell_w, gy + r * cell_h, cell_w - 0.06, cell_h - 0.06, fill)
        if ids[r][c]:
            lines = ["  ".join(ids[r][c][k:k + 2]) for k in range(0, len(ids[r][c]), 2)]
            text(s, gx + c * cell_w + 0.05, gy + r * cell_h, cell_w - 0.16, cell_h - 0.06, lines, size=13, bold=True,
                 color=fg, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
lx = gx + 3 * cell_w + 0.4
lw = X0 + W0 - lx
for i, (lvl, n) in enumerate([("Kritikus", 1), ("Magas", 4), ("Közepes", 4), ("Alacsony", 4)]):
    y = gy + i * 0.85
    card(s, lx, y, lw, 0.7)
    fill, fg = RISK[lvl]
    badge(s, str(n), lx + 0.15, y + 0.15, 0.6, 0.4, fill, fg, size=14)
    text(s, lx + 0.95, y, lw - 1.05, 0.7, lvl, size=15, bold=True, anchor=MSO_ANCHOR.MIDDLE)
text(s, lx, gy + 3.5, lw, 0.6, "Kezelés: javítás, felvállalás vagy áthárítás", size=12, color=MUTED)

# ---- 8. Javítások --------------------------------------------------------------------------
s = content_slide("Akcióterv: mit változtattunk a v2-ben",
    "A javítások nagy része néhány sor a compose fájlban és a Dockerfile-okban. A titkok a v2-ben telepítéskor "
    "generálódnak, és nem kerülnek verziókezelésbe. A host-auditáláshoz auditd szabályokat telepítettünk (M-01). "
    "A userns-remap miatt a konténerbeli felhasználók a hoston nem privilegizált UID-okra képződnek le: az app 10001-es "
    "UID-ja a hoston 110001.")
fixes = [
    ("M-05", "Egyetlen port: 127.0.0.1:8080, DB belső hálózaton"),
    ("M-02", "USER minden image-ben (10001 / postgres / 101)"),
    ("M-03", "Docker secrets, *_FILE, telepítéskor generálva"),
    ("M-04", "Rögzített alpine image-ek, gosu/pip törölve"),
    ("M-06/07", "erőforrás-korlátok, read-only root FS"),
    ("M-01", "auditd szabályok a Docker fájljaira"),
    ("M-08", "cap_drop: ALL, no-new-privileges"),
    ("M-10", "daemon.json: userns, icc, live-restore"),
]
fw = (W0 - 0.3) / 2
for i, (fid, t) in enumerate(fixes):
    x = X0 + (i % 2) * (fw + 0.3)
    y = Y0 + (i // 2) * 1.0
    card(s, x, y, fw, 0.85)
    badge(s, fid, x + 0.15, y + 0.23, 1.05, 0.4, GOOD, size=12)
    text(s, x + 1.35, y, fw - 1.45, 0.85, t, size=14, anchor=MSO_ANCHOR.MIDDLE)
text(s, X0, Y0 + 4.15, W0, 0.8,
     [[("Az alkalmazás kódja nem változott: ", {"bold": True}),
       ("minden javítás a compose fájlban, a Dockerfile-okban és a daemon.json-ban történt.", {})]],
     size=14, color=MUTED, anchor=MSO_ANCHOR.MIDDLE)

# ---- 9. Előtte–utána ----------------------------------------------------------------------
s = content_slide("Utókövetés: előtte és utána",
    "11 megállapítás javult, 2 kockázatot tudatosan felvállaltunk. A host fejezetben az auditd szabályok 8 WARN-t "
    "szüntettek meg. A magas és kritikus sérülékenységek száma 454-ről 0-ra csökkent: az alpine image-ek mellett a gosu "
    "és a pip eltávolítása és a csomagfrissítés is kellett.")
stats9 = [("5 → 61", "docker-bench score"), ("29 → 4", "WARN (CIS 1–6.)"), ("454 → 0", "magas + kritikus CVE"), ("3 → 0", "root konténer")]
sw = (W0 - 3 * 0.2) / 4
for i, (n, l) in enumerate(stats9):
    x = X0 + i * (sw + 0.2)
    card(s, x, Y0, sw, 1.3)
    text(s, x + 0.05, Y0 + 0.1, sw - 0.1, 0.7, n, size=24, bold=True, color=GOOD, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    text(s, x + 0.05, Y0 + 0.82, sw - 0.1, 0.4, l, size=12, color=MUTED, align=PP_ALIGN.CENTER)
column_chart(s, X0, Y0 + 1.45, W0, 3.1, "WARN eredmények CIS fejezetenként", cats,
             [("v1", (9, 7, 0, 3, 10)), ("v2", (1, 1, 0, 1, 1))], [GREY, NAVY])
text(s, X0, Y0 + 4.6, W0, 0.4,
     "Maradék 4 WARN: partíció, authorization, content trust (felvállalva), 1 szükséges proxy port", size=12, color=MUTED)

# ---- 10. Tanulságok ------------------------------------------------------------------------
s = content_slide("Tanulságok és következő lépések",
    "A legfontosabb módszertani tanulság: az automatizált eszköz négy ellenőrzésnél tévedett. Ezeket a forráskód "
    "elemzésével igazoltuk, és minden megállapítást független bizonyítékkal is alátámasztottunk. A fennmaradó kockázatok "
    "kezelésére új akciótervet javasoltunk. Kérdések?")
colw = (W0 - 0.3) / 2
for j, (head, items) in enumerate([
    ("Az eszköz kimenete nem bizonyíték", [
        "dash alatt hamis WARN (2.2, 2.9): bash-szintaxis sh-ban",
        "restart: always mégis PASS (5.15)",
        "SELinux: v1-ben hamis WARN, v2-ben csak formális PASS (5.3)"]),
    ("Következő lépések", [
        "Heti Trivy szkennelés és újraépítés CI-ban (CIS 4.4)",
        "Távoli naplógyűjtés (CIS 2.13)",
        "Proxy: javított upstream alap image, ha megjelenik"]),
]):
    x = X0 + j * (colw + 0.3)
    card(s, x, Y0, colw, 3.0)
    text(s, x + 0.25, Y0 + 0.2, colw - 0.5, 0.5, head, size=17, bold=True, color=BAD if j == 0 else GOOD)
    text(s, x + 0.25, Y0 + 0.9, colw - 0.5, 2.0, items, size=14, bullet=True, space_after=8)
shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, X0, Y0 + 3.3, W0, 1.4, NAVY, radius=0.08)
text(s, X0 + 0.3, Y0 + 3.3, W0 - 0.6, 1.4,
     "Az alapbeállításokkal telepített Docker környezet kritikus kockázatot hordoz, de néhány sor konfigurációval "
     "az alkalmazás módosítása nélkül javítható.", size=16, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)

assert len(prs.slides) == SLIDE_COUNT, len(prs.slides)
prs.core_properties.author = "Anderko Máté"
prs.core_properties.title = "CIS Docker Benchmark audit"
prs.save(str(OUT))
print("Kész:", OUT)

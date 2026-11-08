// Prezentáció: docs/prezentacio.pptx (10 dia, pptxgenjs, téma + layoutok)
// Futtatás: NODE_PATH=<node_modules: pptxgenjs> node scripts/build-slides.js [apply_theme.js útvonal]
const path = require("path");
const pptxgen = require("pptxgenjs");

const OUT = path.join(__dirname, "..", "docs", "prezentacio.pptx");
const THEME = {
  name: "Container Audit",
  headFontFace: "Calibri",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "0B2545", lt1: "FFFFFF", dk2: "13315C", lt2: "EEF2F6",
    accent1: "2EC4B6", accent2: "E63946", accent3: "F4A261", accent4: "E9C46A",
    accent5: "6A994E", accent6: "8D99AE", hlink: "2EC4B6", folHlink: "8D99AE",
  },
};
const HEX = THEME.colors;

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9"; // 10 x 5.625 in
pres.author = "Anderko Máté";
pres.title = "CIS Docker Benchmark audit";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
const C = pres.SchemeColor;
const RISK = { Kritikus: C.accent2, Magas: C.accent3, Közepes: C.accent4, Alacsony: C.accent5 };

// ---- Layoutok ----------------------------------------------------------------
pres.defineSlideMaster({
  title: "TITLE_DARK",
  background: { color: C.text1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 1.5, w: 8.8, h: 1.6, fontSize: 36, bold: true, color: C.background1, valign: "bottom", align: "left" }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.6, y: 3.25, w: 8.8, h: 1.2, fontSize: 16, color: C.accent1, valign: "top" }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: C.background1 },
  margin: [0.5, 0.5, 0.5, 0.5],
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.3, w: 9.0, h: 0.75, fontSize: 28, bold: true, color: C.text1, valign: "middle", align: "left", margin: 0 }, text: "" } },
  ],
  slideNumber: { x: 9.1, y: 5.2, w: 0.5, h: 0.3, fontSize: 10, color: C.accent6, align: "right" },
});
pres.defineSlideMaster({
  title: "CONTENT_DARK",
  background: { color: C.text1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.3, w: 9.0, h: 0.75, fontSize: 28, bold: true, color: C.background1, valign: "middle", align: "left", margin: 0 }, text: "" } },
  ],
  slideNumber: { x: 9.1, y: 5.2, w: 0.5, h: 0.3, fontSize: 10, color: C.accent6, align: "right" },
});

// ---- Segédfüggvények -------------------------------------------------------------
const shadow = () => ({ type: "outer", color: "000000", opacity: 0.12, blur: 4, offset: 1.5, angle: 90 });
function card(s, name, x, y, w, h, fill = C.background2) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { objectName: name, x, y, w, h, rectRadius: 0.08, fill: { color: fill }, line: { type: "none" }, shadow: shadow() });
}
function text(s, name, t, o) { s.addText(t, { objectName: name, isTextBox: true, margin: 0, ...o }); }
function badge(s, name, t, x, y, w, fill, color = C.background1, fontSize = 12) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { objectName: name + "-bg", x, y, w, h: 0.32, rectRadius: 0.16, fill: { color: fill }, line: { type: "none" } });
  text(s, name, t, { x, y, w, h: 0.32, fontSize, bold: true, color, align: "center", valign: "middle" });
}
function circleNum(s, name, n, x, y, d = 0.5, fill = C.accent1) {
  s.addShape(pres.shapes.OVAL, { objectName: name + "-c", x, y, w: d, h: d, fill: { color: fill }, line: { type: "none" } });
  text(s, name, String(n), { x, y, w: d, h: d, fontSize: 16, bold: true, color: C.text1, align: "center", valign: "middle" });
}
const darkText = (lvl) => (lvl === "Közepes" || lvl === "Magas" ? C.text1 : C.background1);

// ---- 1. Címdia ---------------------------------------------------------------------
pres.addSection({ title: "Bevezetés" });
let s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Bevezetés" });
s.addText("Konténerizált webalkalmazás auditja a CIS Docker Benchmark alapján", { placeholder: "title" });
s.addText([
  { text: "IT Audit – páros audit projekt", options: { breakLine: true } },
  { text: "Vezető auditor: Anderko Máté  ·  Rendszergazda: TBD", options: { color: C.background2, fontSize: 14 } },
], { placeholder: "body" });
s.addNotes("Bemutatkozás és a szerepek. A téma: egy időpontfoglaló webalkalmazás Docker futtatókörnyezetének megfelelőségi auditja a CIS Docker Benchmark v1.6.0 alapján, technikai eszközökkel, javítással és újraméréssel.");

// ---- 2. Cél, tárgy, mérce --------------------------------------------------------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Bevezetés" });
s.addText("Cél, tárgy és mérce", { placeholder: "title" });
const cards2 = [
  ["Tárgy", "Időpontfoglaló webapp 3 konténerben: Nginx proxy, Flask app, PostgreSQL. Manjaro Linux host, Docker 29.8"],
  ["Mérce", "CIS Docker Benchmark v1.6.0, Level 1. Kiegészítő: Trivy (CIS 4.4) és NIST CSF besorolás"],
  ["Módszer", "Dokumentumvizsgálat, megfigyelés, docker-bench-security, Trivy, újrateljesítés (v1 → v2)"],
];
cards2.forEach(([h, b], i) => {
  const x = 0.5 + i * 3.1;
  card(s, `card2-${i}`, x, 1.3, 2.8, 2.75);
  circleNum(s, `num2-${i}`, i + 1, x + 0.25, 1.5);
  text(s, `h2-${i}`, h, { x: x + 0.25, y: 2.15, w: 2.3, h: 0.4, fontSize: 18, bold: true, color: C.text1 });
  text(s, `b2-${i}`, b, { x: x + 0.25, y: 2.6, w: 2.3, h: 1.35, fontSize: 14, color: C.text2, valign: "top" });
});
text(s, "excl", [
  { text: "Kizárva: ", options: { bold: true } },
  { text: "CIS 7. fejezet (Swarm, N/A), alkalmazáskód (ASVS/DAST), hypervisor, BCP/DRP, behatolásteszt" },
], { x: 0.5, y: 4.35, w: 8.6, h: 0.5, fontSize: 12, color: C.accent6 });
s.addNotes("Az audit célja: független, eszközökkel alátámasztott értékelés a CIS Docker Benchmarknak való megfelelésről, kockázatértékeléssel és akciótervvel. A teljeskörűség miatt a host, a daemon, az image-ek és a runtime is a tárgy része, nem csak az alkalmazás. A kizárásokat a tervben indokoltuk.");

// ---- 3. Architektúra ---------------------------------------------------------------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Bevezetés" });
s.addText("A vizsgált rendszer: v1 és v2", { placeholder: "title" });
function stack(prefix, x0, labels, ports, v2) {
  text(s, `${prefix}-hdr`, v2 ? "v2 – akcióterv után" : "v1 – alapbeállításos telepítés", { x: x0, y: 1.2, w: 4.3, h: 0.35, fontSize: 16, bold: true, color: v2 ? C.accent1 : C.accent2 });
  if (v2) {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { objectName: `${prefix}-fe`, x: x0, y: 1.65, w: 4.3, h: 2.1, rectRadius: 0.06, fill: { color: C.background2 }, line: { color: C.accent6, width: 0.75, dashType: "dash" } });
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { objectName: `${prefix}-be`, x: x0, y: 2.95, w: 4.3, h: 1.95, rectRadius: 0.06, fill: { color: C.background1, transparency: 100 }, line: { color: C.accent1, width: 1, dashType: "dash" } });
    text(s, `${prefix}-fe-l`, "frontend", { x: x0 + 3.0, y: 1.7, w: 1.2, h: 0.25, fontSize: 10, color: C.accent6, align: "right" });
    text(s, `${prefix}-be-l`, "backend (internal)", { x: x0 + 2.6, y: 4.6, w: 1.6, h: 0.25, fontSize: 10, color: C.accent1, align: "right" });
  } else {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { objectName: `${prefix}-net`, x: x0, y: 1.65, w: 4.3, h: 3.25, rectRadius: 0.06, fill: { color: C.background2 }, line: { color: C.accent6, width: 0.75, dashType: "dash" } });
    text(s, `${prefix}-net-l`, "egy közös hálózat", { x: x0 + 2.6, y: 4.6, w: 1.6, h: 0.25, fontSize: 10, color: C.accent6, align: "right" });
  }
  labels.forEach((l, i) => {
    const y = 1.95 + i * 0.95;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { objectName: `${prefix}-box-${i}`, x: x0 + 0.25, y, w: 2.0, h: 0.6, rectRadius: 0.06, fill: { color: C.text1 }, line: { type: "none" } });
    text(s, `${prefix}-lbl-${i}`, l, { x: x0 + 0.25, y, w: 2.0, h: 0.6, fontSize: 13, bold: true, color: C.background1, align: "center", valign: "middle" });
    if (ports[i]) badge(s, `${prefix}-port-${i}`, ports[i], x0 + 2.4, y + 0.14, 1.7, v2 ? C.accent1 : C.accent2, v2 ? C.text1 : C.background1, 11);
  });
}
stack("v1", 0.5, ["proxy · root", "app · root", "db · root"], ["0.0.0.0:80", "0.0.0.0:8000", "0.0.0.0:5432"], false);
stack("v2", 5.2, ["proxy · uid 101", "app · uid 10001", "db · postgres"], ["127.0.0.1:8080", null, null], true);
s.addNotes("Bal oldalon a kiinduló állapot: Docker alapbeállítások és a hivatalos postgres image példája szerinti compose (a források a jelentés 3.1 fejezetében). Az adatbázis portját kényelmi okból publikáltuk. Mindhárom konténer root, mindhárom port nyitva minden interfészen, köztük az adatbázisé, gyenge jelszóval a compose fájlban. Jobb oldalon a v2: egyetlen publikált port a proxyn, az adatbázis csak belső hálózaton érhető el, minden konténer nem root userrel fut. Az alkalmazás kódja nem változott.");

// ---- 4. Folyamat ------------------------------------------------------------------
pres.addSection({ title: "Audit" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Audit" });
s.addText("Az audit menete", { placeholder: "title" });
const steps = [
  ["Terv", "cél, tárgy, kizárások, kockázati módszer"],
  ["v1 telepítés", "alapbeállítások, hivatalos image-példák"],
  ["Mérés", "docker-bench, Trivy, SHA-256 hash"],
  ["Értékelés", "13 megállapítás, kockázat, CSF"],
  ["Javítás", "v2 az akcióterv alapján"],
  ["Újramérés", "utókövetés, összehasonlítás"],
];
s.addShape(pres.shapes.LINE, { objectName: "timeline", x: 0.95, y: 2.0, w: 8.1, h: 0, line: { color: C.accent6, width: 1.5 } });
steps.forEach(([h, b], i) => {
  const x = 0.5 + i * 1.55;
  circleNum(s, `step-${i}`, i + 1, x + 0.2, 1.7, 0.6, i === 5 ? C.accent1 : C.background2);
  text(s, `step-h-${i}`, h, { x: x - 0.1, y: 2.45, w: 1.4, h: 0.35, fontSize: 15, bold: true, color: C.text1, align: "center" });
  text(s, `step-b-${i}`, b, { x: x - 0.1, y: 2.85, w: 1.4, h: 1.0, fontSize: 12, color: C.text2, align: "center", valign: "top" });
});
card(s, "evid", 0.5, 4.1, 9.0, 0.8, C.background2);
text(s, "evid-t", [
  { text: "Bizonyítékkezelés: ", options: { bold: true } },
  { text: "mérésenként időbélyeges könyvtár, nyers kimenetek, SHA-256 hash, mérési napló, maszkolt jelszavak, verziókezelés" },
], { x: 0.75, y: 4.1, w: 8.5, h: 0.8, fontSize: 14, color: C.text1, valign: "middle" });
s.addNotes("A folyamat az előadások audit munkafolyamatát követi: tervezés, bizonyítékgyűjtés, értékelés, jelentés, utókövetés. A bizonyítékgyűjtést egyetlen szkript végzi, ezért a mérés megismételhető. Minden fájlnak SHA-256 hash-e van, a nyers kimeneteket nem módosítjuk.");

// ---- 5. v1 eredmények ---------------------------------------------------------------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Audit" });
s.addText("Kiinduló állapot (v1): messze a CIS ajánlásoktól", { placeholder: "title" });
[["5", "docker-bench score", "117 ellenőrzésből"], ["29", "WARN eredmény", "CIS 1–6. fejezet"], ["454", "magas + kritikus CVE", "3 image, Trivy"]].forEach(([n, l, sub], i) => {
  const y = 1.25 + i * 1.25;
  card(s, `stat5-${i}`, 0.5, y, 3.2, 1.05);
  text(s, `stat5-n-${i}`, n, { x: 0.7, y, w: 1.3, h: 1.05, fontSize: 36, bold: true, color: C.accent2, valign: "middle" });
  text(s, `stat5-l-${i}`, [{ text: l, options: { bold: true, breakLine: true } }, { text: sub, options: { color: C.accent6, fontSize: 12 } }],
    { x: 1.95, y, w: 1.65, h: 1.05, fontSize: 14, color: C.text1, valign: "middle" });
});
s.addChart(pres.charts.BAR, [
  { name: "PASS", labels: ["1 Host", "2 Daemon", "3 Daemon fájlok", "4 Image", "5 Runtime"], values: [1, 6, 8, 1, 18] },
  { name: "WARN", labels: ["1 Host", "2 Daemon", "3 Daemon fájlok", "4 Image", "5 Runtime"], values: [9, 7, 0, 3, 10] },
], {
  objectName: "chart-v1", x: 4.0, y: 1.2, w: 5.5, h: 3.75, barDir: "col", barGrouping: "clustered",
  chartColors: [HEX.accent1, HEX.accent2], showLegend: true, legendPos: "t", legendFontSize: 12, legendFontFace: "+mn-lt",
  showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 11, dataLabelFontFace: "+mn-lt", dataLabelColor: HEX.dk2,
  catAxisLabelColor: HEX.dk2, catAxisLabelFontSize: 11, catAxisLabelFontFace: "+mn-lt",
  valAxisHidden: true, valGridLine: { style: "none" }, catGridLine: { style: "none" },
  showTitle: true, title: "docker-bench eredmények CIS fejezetenként (v1)", titleFontSize: 13, titleColor: HEX.dk1, titleFontFace: "+mn-lt",
});
s.addNotes("Az alapbeállításos telepítés pontszáma 5. A WARN eredmények a host-auditálásban, a daemon-beállításokban és a konténer runtime-ban koncentrálódnak. A Trivy 454 magas vagy kritikus sérülékenységet talált, főleg a teljes Debian alapú latest image-ek felesleges csomagjaiban. Érdekesség: a python:latest a projekt előkészítése közben Python 3.15-re váltott, és emiatt kódváltozás nélkül eltört a build. Ez a latest tag kockázatának gyakorlati példája.");

// ---- 6. Top megállapítások ------------------------------------------------------------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Audit" });
s.addText("A legsúlyosabb megállapítások", { placeholder: "title" });
const top = [
  ["Kritikus", "M-05", "Adatbázis-port minden interfészen, gyenge jelszóval", "docker ps: 0.0.0.0:5432 · CIS 5.9, 5.14"],
  ["Magas", "M-02", "Mindhárom konténer root felhasználóval fut", "inspect: Config.User = \"\" · CIS 4.1"],
  ["Magas", "M-03", "Jelszavak nyílt szövegként: compose fájl és env", "docker inspect kiolvasható · CIS 4.10"],
  ["Magas", "M-04", "latest image-ek, 454 magas/kritikus CVE", "Trivy · CIS 4.2–4.4"],
  ["Magas", "M-10", "Daemon alapbeállítással fut (userns, icc, live-restore)", "nincs daemon.json · CIS 2.x"],
];
top.forEach(([lvl, id, t, ev], i) => {
  const y = 1.2 + i * 0.75;
  card(s, `row6-${i}`, 0.5, y, 9.0, 0.62);
  badge(s, `lvl6-${i}`, lvl, 0.65, y + 0.15, 1.15, RISK[lvl], darkText(lvl));
  text(s, `id6-${i}`, id, { x: 1.95, y, w: 0.7, h: 0.62, fontSize: 14, bold: true, color: C.text1, valign: "middle" });
  text(s, `t6-${i}`, t, { x: 2.65, y, w: 4.3, h: 0.62, fontSize: 14, color: C.text1, valign: "middle" });
  text(s, `ev6-${i}`, ev, { x: 7.05, y, w: 2.35, h: 0.62, fontSize: 11, color: C.accent6, valign: "middle" });
});
s.addNotes("Összesen 13 megállapítás: 1 kritikus, 4 magas, 4 közepes, 4 alacsony. A legsúlyosabb az M-05: a hálózatról közvetlenül elérhető adatbázis gyenge jelszóval, ami a személyes adatok (név, e-mail) kiszivárgásához vezethet. Minden megállapítást legalább egy független bizonyíték is alátámaszt, nem csak az eszköz kimenete.");

// ---- 7. Kockázati mátrix ---------------------------------------------------------------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Audit" });
s.addText("Kockázati mátrix: hatás × valószínűség", { placeholder: "title" });
const lvlGrid = [["Közepes", "Magas", "Kritikus"], ["Alacsony", "Közepes", "Magas"], ["Alacsony", "Alacsony", "Közepes"]]; // sor: hatás M/K/A, oszlop: valósz. A/K/M
const ids = [[[], ["M-02", "M-03", "M-10"], ["M-05"]], [["M-12"], ["M-01", "M-06", "M-07", "M-08"], ["M-04"]], [["M-13"], ["M-09", "M-11"], []]];
const gx = 1.45, gy = 1.25, cw = 1.55, ch = 1.1;
["Magas", "Közepes", "Alacsony"].forEach((h, r) => text(s, `rowlbl-${r}`, h, { x: 0.5, y: gy + r * ch, w: 0.85, h: ch, fontSize: 12, color: C.text2, align: "right", valign: "middle" }));
["Alacsony", "Közepes", "Magas"].forEach((v, c) => text(s, `collbl-${c}`, v, { x: gx + c * cw, y: gy + 3 * ch + 0.05, w: cw, h: 0.3, fontSize: 12, color: C.text2, align: "center" }));
text(s, "axis-y", "Hatás ↑", { x: 0.5, y: gy - 0.05, w: 0.85, h: 0.25, fontSize: 11, bold: true, color: C.text1, align: "right" });
text(s, "axis-x", "Valószínűség →", { x: gx, y: gy + 3 * ch + 0.35, w: 3 * cw, h: 0.3, fontSize: 11, bold: true, color: C.text1, align: "center" });
for (let r = 0; r < 3; r++) for (let c = 0; c < 3; c++) {
  const lvl = lvlGrid[r][c];
  s.addShape(pres.shapes.RECTANGLE, { objectName: `cell-${r}-${c}`, x: gx + c * cw, y: gy + r * ch, w: cw - 0.05, h: ch - 0.05, fill: { color: RISK[lvl], transparency: 25 }, line: { type: "none" } });
  const list = ids[r][c];
  if (list.length) text(s, `ids-${r}-${c}`, list.join("  "), { x: gx + c * cw + 0.08, y: gy + r * ch, w: cw - 0.2, h: ch - 0.05, fontSize: 13, bold: true, color: darkText(lvl), align: "center", valign: "middle" });
}
[["Kritikus", 1], ["Magas", 4], ["Közepes", 4], ["Alacsony", 4]].forEach(([l, n], i) => {
  const y = 1.4 + i * 0.75;
  card(s, `leg-${i}`, 6.5, y, 3.0, 0.6);
  badge(s, `legb-${i}`, String(n), 6.65, y + 0.14, 0.6, RISK[l], darkText(l), 13);
  text(s, `legt-${i}`, l, { x: 7.4, y, w: 2.0, h: 0.6, fontSize: 15, bold: true, color: C.text1, valign: "middle" });
});
text(s, "mx-note", "Kezelés: javítás, felvállalás vagy áthárítás", { x: 6.5, y: 4.45, w: 3.0, h: 0.4, fontSize: 12, color: C.accent6 });
s.addNotes("A kockázat a hatás és a bekövetkezési valószínűség függvénye, az előadás háromszintű skálája szerint. A jobb felső sarokban az M-05. A userns-remap hiánya (M-10) azért magas, mert enélkül a konténerbeli root azonos a host rootjával, így egy konténerkitörés host szintű kompromittálódás.");

// ---- 8. Javítások ----------------------------------------------------------------------
pres.addSection({ title: "Eredmények" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Eredmények" });
s.addText("Akcióterv: mit változtattunk a v2-ben", { placeholder: "title" });
const fixes = [
  ["M-05", "Egyetlen port: 127.0.0.1:8080, DB belső hálózaton"],
  ["M-02", "USER minden image-ben (10001 / postgres / 101)"],
  ["M-03", "Docker secrets, *_FILE, telepítéskor generálva"],
  ["M-04", "Rögzített alpine image-ek, gosu/pip törölve"],
  ["M-06/07", "erőforrás-korlátok, read-only root FS"],
  ["M-01", "auditd szabályok a Docker fájljaira"],
  ["M-08", "cap_drop: ALL, no-new-privileges"],
  ["M-10", "daemon.json: userns, icc, live-restore"],
];
fixes.forEach(([id, t], i) => {
  const col = i % 2, row = Math.floor(i / 2);
  const x = 0.5 + col * 4.6, y = 1.2 + row * 0.8;
  card(s, `fix-${i}`, x, y, 4.4, 0.66);
  badge(s, `fixid-${i}`, id, x + 0.15, y + 0.17, 0.85, C.accent1, C.text1);
  text(s, `fixt-${i}`, t, { x: x + 1.15, y, w: 3.15, h: 0.66, fontSize: 14, color: C.text1, valign: "middle" });
});
text(s, "fix-note", [
  { text: "Az alkalmazás kódja nem változott ", options: { bold: true } },
  { text: "– minden javítás a compose fájlban, a Dockerfile-okban és a daemon.json-ban történt." },
], { x: 0.5, y: 4.5, w: 9.0, h: 0.45, fontSize: 13, color: C.text2 });
s.addNotes("A javítások nagy része néhány sor a compose fájlban és a Dockerfile-okban. A titkok a v2-ben telepítéskor generálódnak, és nem kerülnek verziókezelésbe. A host-auditáláshoz auditd szabályokat telepítettünk (M-01). A userns-remap miatt a konténerbeli felhasználók a hoston nem privilegizált UID-okra képződnek le: az app 10001-es UID-ja a hoston 110001.");

// ---- 9. Előtte–utána ----------------------------------------------------------------------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Eredmények" });
s.addText("Utókövetés: előtte és utána", { placeholder: "title" });
[["5 → 61", "docker-bench score"], ["29 → 4", "WARN (CIS 1–6.)"], ["454 → 0", "magas + kritikus CVE"], ["3 → 0", "root konténer"]].forEach(([n, l], i) => {
  const x = 0.5 + i * 2.3;
  card(s, `st9-${i}`, x, 1.2, 2.1, 1.1);
  text(s, `st9-n-${i}`, n, { x: x + 0.1, y: 1.25, w: 1.9, h: 0.6, fontSize: 26, bold: true, color: C.accent1, align: "center", valign: "middle" });
  text(s, `st9-l-${i}`, l, { x: x + 0.1, y: 1.85, w: 1.9, h: 0.35, fontSize: 12, color: C.text2, align: "center" });
});
s.addChart(pres.charts.BAR, [
  { name: "v1", labels: ["1 Host", "2 Daemon", "3 Daemon fájlok", "4 Image", "5 Runtime"], values: [9, 7, 0, 3, 10] },
  { name: "v2", labels: ["1 Host", "2 Daemon", "3 Daemon fájlok", "4 Image", "5 Runtime"], values: [1, 1, 0, 1, 1] },
], {
  objectName: "chart-cmp", x: 0.5, y: 2.45, w: 9.0, h: 2.35, barDir: "col", barGrouping: "clustered",
  chartColors: [HEX.accent6, HEX.accent1], showLegend: true, legendPos: "r", legendFontSize: 12, legendFontFace: "+mn-lt",
  showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 11, dataLabelFontFace: "+mn-lt", dataLabelColor: HEX.dk2,
  catAxisLabelColor: HEX.dk2, catAxisLabelFontSize: 11, catAxisLabelFontFace: "+mn-lt",
  valAxisHidden: true, valGridLine: { style: "none" }, catGridLine: { style: "none" },
  showTitle: true, title: "WARN eredmények CIS fejezetenként", titleFontSize: 13, titleColor: HEX.dk1, titleFontFace: "+mn-lt",
});
text(s, "cmp-note", "Maradék 4 WARN: partíció, authorization, content trust (felvállalva), 1 szükséges proxy port", { x: 0.5, y: 4.8, w: 8.4, h: 0.3, fontSize: 11, color: C.accent6 });
s.addNotes("11 megállapítás javult, 2 kockázatot tudatosan felvállaltunk. A host fejezetben az auditd szabályok 8 WARN-t szüntettek meg. A magas és kritikus sérülékenységek száma 454-ről 0-ra csökkent: az alpine image-ek mellett a gosu és a pip eltávolítása és a csomagfrissítés is kellett.");

// ---- 10. Tanulságok ------------------------------------------------------------------------
s = pres.addSlide({ masterName: "CONTENT_DARK", sectionTitle: "Eredmények" });
s.addText("Tanulságok és következő lépések", { placeholder: "title" });
text(s, "l-h", "Az eszköz kimenete nem bizonyíték", { x: 0.5, y: 1.25, w: 4.3, h: 0.4, fontSize: 18, bold: true, color: C.accent1 });
text(s, "l-b", [
  { text: "dash alatt hamis WARN (2.2, 2.9): bash-szintaxis sh-ban", options: { bullet: true, breakLine: true } },
  { text: "restart: always mégis PASS (5.15)", options: { bullet: true, breakLine: true } },
  { text: "SELinux: v1-ben hamis WARN, v2-ben csak formális PASS (5.3)", options: { bullet: true } },
], { x: 0.5, y: 1.75, w: 4.3, h: 2.4, fontSize: 14, color: C.background1, paraSpaceAfter: 8, valign: "top" });
text(s, "r-h", "Következő lépések", { x: 5.2, y: 1.25, w: 4.3, h: 0.4, fontSize: 18, bold: true, color: C.accent1 });
text(s, "r-b", [
  { text: "Heti Trivy szkennelés és újraépítés CI-ban (CIS 4.4)", options: { bullet: true, breakLine: true } },
  { text: "Távoli naplógyűjtés (CIS 2.13)", options: { bullet: true, breakLine: true } },
  { text: "Proxy: javított upstream alap image, ha megjelenik", options: { bullet: true } },
], { x: 5.2, y: 1.75, w: 4.3, h: 2.4, fontSize: 14, color: C.background1, paraSpaceAfter: 8, valign: "top" });
text(s, "concl", "Az alapbeállításokkal telepített Docker környezet kritikus kockázatot hordoz, de néhány sor konfigurációval az alkalmazás módosítása nélkül javítható.", { x: 0.5, y: 4.3, w: 9.0, h: 0.6, fontSize: 14, italic: true, color: C.background2 });
s.addNotes("A legfontosabb módszertani tanulság: az automatizált eszköz négy ellenőrzésnél tévedett. Ezeket a forráskód elemzésével igazoltuk, és minden megállapítást független bizonyítékkal is alátámasztottunk. A fennmaradó kockázatok kezelésére új akciótervet javasoltunk. Kérdések?");

(async () => {
  await pres.writeFile({ fileName: OUT });
  const themePath = process.argv[2];
  if (themePath) {
    const { applyTheme } = require(themePath);
    await applyTheme(OUT, THEME);
  }
  console.log("Kész:", OUT);
})();

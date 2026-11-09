// docs/jelentes.md -> docs/jelentes.docx (egyszerű Markdown-részhalmaz: címsorok, bekezdések,
// felsorolás, táblázatok, **félkövér**, `kód`, _dőlt_).
// Futtatás: NODE_PATH=<node_modules a docx csomaggal> node scripts/build-report.js
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, ShadingType,
  AlignmentType, HeadingLevel, LevelFormat, BorderStyle, Footer, PageNumber, PageBreak,
} = require("docx");

const SRC = path.join(__dirname, "..", "docs", "jelentes.md");
const OUT = path.join(__dirname, "..", "docs", "jelentes.docx");
const FONT = "Calibri";
const PAGE_W = 11906, MARGIN = 1134, CONTENT_W = PAGE_W - 2 * MARGIN; // A4, 2 cm margó
const ACCENT = "1F4E79", HEAD_FILL = "DCE6F1", RISK = { Kritikus: "C00000", Magas: "E46C0A", Közepes: "BF9000", Alacsony: "538135" };

function inline(text, base = {}) {
  const runs = [];
  const re = /(\*\*[^*]+\*\*|`[^`]+`|_[^_]+_|(?<![\*])\*[^*\s][^*]*\*(?!\*))/g;
  let last = 0, m;
  const push = (t, o = {}) => { if (t) runs.push(new TextRun({ text: t.replace(/\\\*/g, "*"), font: FONT, ...base, ...o })); };
  while ((m = re.exec(text))) {
    push(text.slice(last, m.index));
    const tok = m[0];
    if (tok.startsWith("**")) {
      const inner = tok.slice(2, -2);
      const color = RISK[inner] ? { color: RISK[inner] } : {};
      push(inner, { bold: true, ...color });
    } else if (tok.startsWith("`")) push(tok.slice(1, -1), { font: "Consolas", size: (base.size || 21) - 2, color: "333333" });
    else push(tok.slice(1, -1), { italics: true });
    last = m.index + tok.length;
  }
  push(text.slice(last));
  return runs;
}

function splitRow(line) {
  return line.trim().replace(/^\|/, "").replace(/\|$/, "").split(/(?<!\\)\|/).map((c) => c.trim());
}

function table(rows) {
  const header = rows[0];
  const body = rows.slice(2);
  const n = header.length;
  // oszlopszélesség: minimum a leghosszabb szó, a maradék a szöveg hosszával arányosan
  const CHAR = 95; // ~ 9 pt Calibri átlagos karakterszélesség (DXA)
  const clean = (s) => (s || "").replace(/[*`_]/g, "");
  const all = [header, ...body];
  const minW = Array.from({ length: n }, (_, i) =>
    (Math.max(3, ...all.map((r) => Math.max(0, ...clean(r[i]).split(/\s+/).map(
      (w) => [...w].reduce((a, ch) => a + (/[A-ZÁÉÍÓÖŐÚÜŰ0-9]/.test(ch) ? 1.3 : 1), 0))))) + 2) * CHAR);
  const tot = Array.from({ length: n }, (_, i) => Math.min(400, Math.max(...all.map((r) => clean(r[i]).length))) * CHAR);
  let widths;
  const minSum = minW.reduce((a, b) => a + b, 0);
  if (minSum >= CONTENT_W) widths = minW.map((w) => Math.floor((w / minSum) * CONTENT_W));
  else {
    const extra = tot.map((t, i) => Math.max(0, t - minW[i]));
    const exSum = extra.reduce((a, b) => a + b, 0) || 1;
    const free = CONTENT_W - minSum;
    widths = minW.map((w, i) => Math.floor(w + Math.min(extra[i], (extra[i] / exSum) * free)));
    // ha minden kifér, a maradékot arányosan szétosztjuk
    const left = CONTENT_W - widths.reduce((a, b) => a + b, 0);
    const wsum = widths.reduce((a, b) => a + b, 0);
    widths = widths.map((w) => Math.floor(w + (w / wsum) * left));
  }
  widths[n - 1] += CONTENT_W - widths.reduce((a, b) => a + b, 0);
  const emptyHeader = header.every((h) => !h);
  const border = { style: BorderStyle.SINGLE, size: 4, color: "A6A6A6" };
  const borders = { top: border, bottom: border, left: border, right: border };
  const cell = (txt, i, isHead) => new TableCell({
    width: { size: widths[i], type: WidthType.DXA },
    borders,
    shading: isHead ? { type: ShadingType.CLEAR, color: "auto", fill: HEAD_FILL } : undefined,
    margins: { top: 40, bottom: 40, left: 80, right: 80 },
    children: [new Paragraph({ spacing: { before: 0, after: 0 }, children: inline(txt, { size: 18, bold: isHead || undefined }) })],
  });
  const trs = [];
  if (!emptyHeader) trs.push(new TableRow({ tableHeader: true, children: header.map((h, i) => cell(h, i, true)) }));
  body.forEach((r) => trs.push(new TableRow({ cantSplit: true, children: Array.from({ length: n }, (_, i) => cell(r[i] || "", i, false)) })));
  return new Table({ width: { size: CONTENT_W, type: WidthType.DXA }, columnWidths: widths, rows: trs });
}

const lines = fs.readFileSync(SRC, "utf8").split(/\r?\n/);
const children = [];
let i = 0, firstH1 = true, para = [];
const flush = () => {
  if (para.length) children.push(new Paragraph({ spacing: { after: 120 }, alignment: AlignmentType.JUSTIFIED, children: inline(para.join(" "), { size: 21 }) }));
  para = [];
};

while (i < lines.length) {
  const line = lines[i];
  if (/^\s*$/.test(line)) { flush(); i++; continue; }
  if (line.startsWith("|")) {
    flush();
    const rows = [];
    while (i < lines.length && lines[i].startsWith("|")) rows.push(splitRow(lines[i++]));
    children.push(table(rows));
    children.push(new Paragraph({ spacing: { after: 80 }, children: [] }));
    continue;
  }
  let m;
  if ((m = line.match(/^(#{1,3}) (.*)$/))) {
    flush();
    const level = m[1].length, text = m[2];
    if (level === 1 && firstH1) {
      firstH1 = false;
      children.push(new Paragraph({ spacing: { before: 2400, after: 240 }, children: [new TextRun({ text, font: FONT, size: 44, bold: true, color: ACCENT })] }));
    } else if (level === 1) {
      const isMain = /^\d+\./.test(text) || text.startsWith("Melléklet");
      if (isMain && text.startsWith("1.")) children.push(new Paragraph({ children: [new PageBreak()] }));
      children.push(new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun({ text, font: FONT })] }));
    } else {
      children.push(new Paragraph({ heading: level === 2 ? HeadingLevel.HEADING_2 : HeadingLevel.HEADING_3, children: [new TextRun({ text, font: FONT })] }));
    }
    i++; continue;
  }
  if ((m = line.match(/^- (.*)$/))) {
    flush();
    children.push(new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 60 }, alignment: AlignmentType.JUSTIFIED, children: inline(m[1], { size: 21 }) }));
    i++; continue;
  }
  // a cím utáni első bekezdés (alcím)
  if (children.length === 1 && para.length === 0) {
    children.push(new Paragraph({ spacing: { after: 600 }, children: [new TextRun({ text: line, font: FONT, size: 28, color: "595959" })] }));
    i++; continue;
  }
  para.push(line.trim());
  i++;
}
flush();

const doc = new Document({
  creator: "Anderko Máté",
  title: "CIS Docker Benchmark audit – jelentés",
  styles: {
    default: { document: { run: { font: FONT, size: 21 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 30, bold: true, color: ACCENT },
        paragraph: { spacing: { before: 300, after: 120 }, keepNext: true, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 25, bold: true, color: ACCENT },
        paragraph: { spacing: { before: 220, after: 100 }, keepNext: true, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 22, bold: true, color: "404040" },
        paragraph: { spacing: { before: 180, after: 80 }, keepNext: true, outlineLevel: 2 } },
    ],
  },
  numbering: { config: [{ reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
    style: { paragraph: { indent: { left: 400, hanging: 260 } } } }] }] },
  sections: [{
    properties: { page: { size: { width: PAGE_W, height: 16838 }, margin: { top: MARGIN, bottom: MARGIN, left: MARGIN, right: MARGIN } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
      children: [new TextRun({ children: [PageNumber.CURRENT, " / ", PageNumber.TOTAL_PAGES], font: FONT, size: 18, color: "808080" })] })] }) },
    children,
  }],
});

Packer.toBuffer(doc).then((buf) => { fs.writeFileSync(OUT, buf); console.log("Kész:", OUT); });

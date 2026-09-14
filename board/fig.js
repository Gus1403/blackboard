/* Blackboard figures: small explanatory SVGs drawn with Rough.js (chalk strokes) and real <text>.
   Runs in the page (window.Fig, needs window.rough) and in Node (require, needs roughjs).
   Fig.render(template, spec) -> {svg, warnings}. Coordinates are a 720-wide canvas; height grows with content. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory(require('roughjs/bundled/rough.cjs.js'));
  else root.Fig = factory(root.rough);
})(typeof self !== 'undefined' ? self : this, function (rough) {
  'use strict';
  const W = 720;
  const THEME = { chalk: '#e9e6df', acc: '#9b3a4a', dim: '#8a8a84', bg: '#0c0c0c', font: "'Patrick Hand','Crimson Pro',Georgia,serif" };
  const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  const est = (s, size) => String(s).length * size * 0.5;            // hand font, average glyph ≈ 0.5em
  const sum = a => (a || []).reduce((s, r) => s + (+r[1] || 0), 0);
  const fmt = (v, spec) => typeof v === 'number' ? ((spec && spec.unit === '') ? v.toLocaleString() : ((spec && spec.unit) || '$') + v.toLocaleString()) : String(v);

  class Canvas {
    constructor(opts) {
      this.t = Object.assign({}, THEME, (opts && opts.theme) || {});
      this.g = rough.generator();
      this.seed = (opts && opts.seed) || 7;
      this.parts = []; this.texts = []; this.warnings = [];
      this.w = W; this.h = 0;
    }
    opt(o) { return Object.assign({ stroke: this.t.chalk, strokeWidth: 1.8, roughness: 1.25, bowing: 1.0, seed: this.seed }, o || {}); }
    draw(d) { for (const p of this.g.toPaths(d)) this.parts.push(`<path d="${p.d}" stroke="${p.stroke}" stroke-width="${p.strokeWidth}" fill="${p.fill || 'none'}" stroke-linecap="round" stroke-linejoin="round"/>`); }
    bump() { for (const y of arguments) if (y > this.h) this.h = y; }
    line(x1, y1, x2, y2, o) { this.draw(this.g.line(x1, y1, x2, y2, this.opt(o))); this.bump(y1, y2); }
    rect(x, y, w, h, o) { this.draw(this.g.rectangle(x, y, w, h, this.opt(o))); this.bump(y + h); }
    circle(x, y, r, o) { this.draw(this.g.circle(x, y, r * 2, this.opt(o))); this.bump(y + r); }
    poly(pts, o) { this.draw(this.g.polygon(pts, this.opt(o))); this.bump(...pts.map(p => p[1])); }
    curve(pts, o) { this.draw(this.g.curve(pts, this.opt(Object.assign({ roughness: 0.7 }, o)))); this.bump(...pts.map(p => p[1])); }
    path(d, o) { this.draw(this.g.path(d, this.opt(o))); }
    arrow(x1, y1, x2, y2, o) {
      o = o || {}; const c = o.color || this.t.chalk;
      this.line(x1, y1, x2, y2, { stroke: c, strokeWidth: o.width || 2 });
      const a = Math.atan2(y2 - y1, x2 - x1), L = o.head || 12;
      this.draw(this.g.polygon([[x2, y2], [x2 - L * Math.cos(a - 0.45), y2 - L * Math.sin(a - 0.45)], [x2 - L * Math.cos(a + 0.45), y2 - L * Math.sin(a + 0.45)]],
        this.opt({ stroke: c, fill: c, fillStyle: 'solid', roughness: 0.8 })));
    }
    text(x, y, s, o) {
      o = o || {}; if (s == null || s === '') return;
      const size = o.size || 20, anchor = o.anchor || 'start', color = o.color || this.t.chalk, font = o.font || this.t.font;
      const w = est(s, size), x0 = anchor === 'start' ? x : anchor === 'end' ? x - w : x - w / 2;
      this.texts.push({ x: x0, y: y - size * 0.75, w, h: size * 0.9, s: String(s) });
      this.parts.push(`<text x="${x}" y="${y}" font-family="${esc(font)}" font-size="${size}" fill="${color}" text-anchor="${anchor}"${o.weight ? ` font-weight="${o.weight}"` : ''}${o.italic ? ' font-style="italic"' : ''}>${esc(s)}</text>`);
      this.bump(y + 4);
    }
    lint() {
      const w = [], T = this.texts;
      for (let i = 0; i < T.length; i++) {
        const a = T[i];
        if (a.x < 0 || a.x + a.w > this.w) w.push(`"${a.s}" runs outside the figure`);
        for (let j = i + 1; j < T.length; j++) {
          const b = T[j];
          if (a.x < b.x + b.w && b.x < a.x + a.w && a.y < b.y + b.h && b.y < a.y + a.h) w.push(`"${a.s}" overlaps "${b.s}"`);
        }
      }
      return w.concat(this.warnings);
    }
    svg(pad) { const h = Math.ceil(this.h + (pad == null ? 14 : pad)); return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${this.w} ${h}" class="fig" role="img">${this.parts.join('')}</svg>`; }
  }

  // ---------- templates ----------
  const T = {};

  // T-accounts. spec: {panels:[{title,left:[[name,val]],right:[[name,val]],hi:[names],totals}], arrow, heads, unit}
  T.taccounts = (spec, C) => {
    const panels = spec.panels || [spec], n = panels.length, gap = n > 1 ? 70 : 0;
    const pw = Math.min(320, (W - 40 - gap * (n - 1)) / n), x0 = (W - (pw * n + gap * (n - 1))) / 2, top = 30;
    panels.forEach((p, i) => {
      const x = x0 + i * (pw + gap), m = x + pw / 2, row = 32, ty = top + 26;
      const rows = Math.max((p.left || []).length, (p.right || []).length), h = Math.max(120, 58 + row * rows + 10);
      if (p.title) C.text(m, top, p.title, { anchor: 'middle', size: 24 });
      C.line(x, ty, x + pw, ty); C.line(m, ty, m, ty + h);
      const heads = p.heads || spec.heads || ['owns / is owed', 'owes'];
      C.text(x + pw / 4, ty + 22, heads[0], { anchor: 'middle', size: 15, color: C.t.dim });
      C.text(x + 3 * pw / 4, ty + 22, heads[1], { anchor: 'middle', size: 15, color: C.t.dim });
      const hi = p.hi || [];
      const col = (items, xa, xb) => (items || []).forEach(([l, v], k) => { const f = hi.includes(l) ? C.t.acc : C.t.chalk; C.text(xa, ty + 58 + row * k, l, { color: f }); C.text(xb, ty + 58 + row * k, fmt(v, spec), { anchor: 'end', color: f }); });
      col(p.left, x + 10, m - 12); col(p.right, m + 12, x + pw - 10);
      if (p.totals !== false) {
        C.line(x + 10, ty + h - 14, m - 12, ty + h - 14); C.line(m + 12, ty + h - 14, x + pw - 10, ty + h - 14);
        C.text(m - 12, ty + h + 10, fmt(sum(p.left), spec), { anchor: 'end', size: 18, color: C.t.dim });
        C.text(x + pw - 10, ty + h + 10, fmt(sum(p.right), spec), { anchor: 'end', size: 18, color: C.t.dim });
      }
      if (i < n - 1) {
        const ax = x + pw + 12, ay = ty + 42;
        C.arrow(ax, ay, ax + gap - 24, ay, { color: C.t.acc });
        if (spec.arrow) C.text(ax + (gap - 24) / 2, ty + 8, spec.arrow, { anchor: 'middle', size: 15, color: C.t.acc });
      }
    });
  };

  // Stacked balance-sheet bars (Bank of England style). spec: {panels:[{title,left:[[name,val,hi]],right:[[name,val,hi]]}], heads, unit}
  T.bars = (spec, C) => {
    const panels = spec.panels || [spec], n = panels.length, gap = 50;
    const pw = Math.min(320, (W - 40 - gap * (n - 1)) / n), x0 = (W - (pw * n + gap * (n - 1))) / 2, H = 200, top = 46;
    const maxT = Math.max(...panels.map(p => Math.max(sum(p.left), sum(p.right)))) || 1, k = H / maxT, bw = pw * 0.38;
    const heads = spec.heads || ['assets', 'liabilities + equity'];
    panels.forEach((p, i) => {
      const x = x0 + i * (pw + gap);
      if (p.title) C.text(x + pw / 2, top - 16, p.title, { anchor: 'middle', size: 24 });
      [[p.left, x + pw * 0.08, p.heads ? p.heads[0] : heads[0]], [p.right, x + pw * 0.54, p.heads ? p.heads[1] : heads[1]]].forEach(([items, cx, head]) => {
        let y = top + H;
        C.text(cx + bw / 2, top + H + 24, head, { anchor: 'middle', size: 15, color: C.t.dim });
        for (const [name, val, hi] of items || []) {
          const h = val * k; y -= h;
          C.rect(cx, y, bw, h, hi ? { stroke: C.t.acc, strokeWidth: 2.6, roughness: 1.5 } : {});
          const c = hi ? C.t.acc : C.t.chalk;
          if (h >= 44) { C.text(cx + bw / 2, y + h / 2 - 2, name, { anchor: 'middle', size: 16, color: c }); C.text(cx + bw / 2, y + h / 2 + 18, fmt(val, spec), { anchor: 'middle', size: 16, color: c }); }
          else if (h >= 22) C.text(cx + bw / 2, y + h / 2 + 6, `${name} ${fmt(val, spec)}`, { anchor: 'middle', size: 14, color: c });
          else C.warnings.push(`bar segment "${name}" too thin for a label; say it in the caption`);
        }
      });
      if (i < n - 1) { const ax = x + pw + 8, ay = top + H / 2; C.arrow(ax, ay, ax + gap - 16, ay, { color: C.t.acc }); }
    });
    if (spec.arrow && n > 1) C.text(W / 2, top - 16, spec.arrow, { anchor: 'middle', size: 15, color: C.t.acc });
  };

  // Entities and labelled arrows. spec: {nodes:[{id,label,col,row,hi}], edges:[{from,to,label,hi,dashed}]}
  T.flow = (spec, C) => {
    const nodes = spec.nodes || [], cols = Math.max(...nodes.map(n => (n.col || 0) + 1), 1), rows = Math.max(...nodes.map(n => (n.row || 0) + 1), 1);
    const colW = (W - 40) / cols, rowH = spec.rowH || 120, top = 30, pos = {};
    nodes.forEach((n, i) => {
      const col = n.col == null ? i % cols : n.col, row = n.row == null ? Math.floor(i / cols) : n.row;
      const w = Math.max(96, est(n.label, 19) + 30), h = 46, cx = 20 + (col + 0.5) * colW, cy = top + row * rowH + h / 2;
      pos[n.id] = { x: cx - w / 2, y: cy - h / 2, w, h, cx, cy };
      if (n.shape === 'circle') C.circle(cx, cy, Math.max(w, h) / 2, n.hi ? { stroke: C.t.acc } : {});
      else C.rect(cx - w / 2, cy - h / 2, w, h, n.hi ? { stroke: C.t.acc, strokeWidth: 2.2 } : {});
      C.text(cx, cy + 7, n.label, { anchor: 'middle', size: 19, color: n.hi ? C.t.acc : C.t.chalk });
    });
    const edge = (a, b) => { // point on a's border toward b
      const dx = b.cx - a.cx, dy = b.cy - a.cy, sx = a.w / 2 / Math.abs(dx || 1e-9), sy = a.h / 2 / Math.abs(dy || 1e-9), s = Math.min(sx, sy);
      return [a.cx + dx * s, a.cy + dy * s];
    };
    for (const e of spec.edges || []) {
      const a = pos[e.from], b = pos[e.to]; if (!a || !b) { C.warnings.push(`edge ${e.from}→${e.to} names an unknown node`); continue; }
      const [x1, y1] = edge(a, b), [x2, y2] = edge(b, a), c = e.hi ? C.t.acc : C.t.chalk;
      C.arrow(x1, y1, x2, y2, { color: c });
      if (e.label) {
        const mx = (x1 + x2) / 2, my = (y1 + y2) / 2, dx = x2 - x1, dy = y2 - y1, L = Math.hypot(dx, dy) || 1;
        let nx = -dy / L, ny = dx / L; if (ny > 0 || (ny === 0 && nx < 0)) { nx = -nx; ny = -ny; }   // normal points up
        const off = e.side === 'below' ? -20 : 14;
        C.text(mx + nx * off, my + ny * off + (off < 0 ? 10 : 2), e.label, { anchor: 'middle', size: 15, color: e.hi ? C.t.acc : C.t.dim });
      }
    }
  };

  // Timeline. spec: {events:[{at,label,hi}], start, end, unit}
  T.timeline = (spec, C) => {
    const ev = spec.events || [], y = 80, x0 = 50, x1 = W - 50, num = ev.every(e => typeof e.at === 'number');
    const s = num ? (spec.start != null ? spec.start : Math.min(...ev.map(e => e.at))) : 0, e1 = num ? (spec.end != null ? spec.end : Math.max(...ev.map(e => e.at))) : ev.length - 1;
    const X = i => num ? x0 + (ev[i].at - s) / ((e1 - s) || 1) * (x1 - x0) : x0 + i / Math.max(ev.length - 1, 1) * (x1 - x0);
    C.line(x0 - 10, y, x1 + 10, y);
    C.draw(C.g.polygon([[x1 + 14, y], [x1 + 2, y - 6], [x1 + 2, y + 6]], C.opt({ fill: C.t.chalk, fillStyle: 'solid', roughness: 0.8 })));
    ev.forEach((e, i) => {
      const x = X(i), up = i % 2 === 0, c = e.hi ? C.t.acc : C.t.chalk;
      C.line(x, y - 8, x, y + 8, e.hi ? { stroke: C.t.acc, strokeWidth: 2.4 } : {});
      C.text(x, up ? y - 22 : y + 36, e.label, { anchor: 'middle', size: 18, color: c });
      if (e.at != null) C.text(x, up ? y + 30 : y - 16, String(e.at) + (spec.unit ? ' ' + spec.unit : ''), { anchor: 'middle', size: 14, color: C.t.dim });
    });
    C.bump(y + 50);
  };

  // Small table. spec: {cols:[...], rows:[[...]], hi:[[r,c]], align:['l','r',...]}
  T.table = (spec, C) => {
    const cols = spec.cols || [], rows = spec.rows || [], nc = cols.length || (rows[0] || []).length, row = 34, top = 34;
    const widths = []; for (let c = 0; c < nc; c++) widths.push(Math.max(70, est(cols[c] || '', 16) + 24, ...rows.map(r => est(r[c] == null ? '' : r[c], 19) + 24)));
    const tot = widths.reduce((a, b) => a + b, 0), k = Math.min(1, (W - 40) / tot), x0 = (W - tot * k) / 2;
    const xs = []; let x = x0; for (let c = 0; c < nc; c++) { xs.push(x); x += widths[c] * k; }
    const al = spec.align || [], hi = spec.hi || [];
    const put = (r, c, s, y, o) => { const a = al[c] === 'r' ? 'end' : al[c] === 'c' ? 'middle' : 'start'; const px = a === 'end' ? xs[c] + widths[c] * k - 12 : a === 'middle' ? xs[c] + widths[c] * k / 2 : xs[c] + 12; C.text(px, y, s, Object.assign({ anchor: a }, o)); };
    cols.forEach((h, c) => put(-1, c, h, top, { size: 16, color: C.t.dim }));
    if (cols.length) C.line(x0, top + 10, x0 + tot * k, top + 10);
    rows.forEach((r, ri) => r.forEach((v, c) => { const h = hi.some(([a, b]) => a === ri && (b == null || b === c)); put(ri, c, v == null ? '' : v, top + 10 + row * (ri + 1) - 6, { size: 19, color: h ? C.t.acc : C.t.chalk }); }));
    C.bump(top + 10 + row * rows.length + 4);
  };

  // Karnaugh map. spec: {vars:['A','B','C','D'], values:[by minterm index], loops:[{cells:[minterms], hi}]}
  T.kmap = (spec, C) => {
    const vars = spec.vars || ['A', 'B'], nv = vars.length, gray = n => n === 1 ? ['0', '1'] : ['00', '01', '11', '10'];
    const rb = nv === 2 ? 1 : nv === 3 ? 1 : 2, cb = nv - rb, R = gray(rb), Cc = gray(cb), cell = 56, x0 = (W - cell * Cc.length) / 2 + 20, y0 = 60;
    const rl = vars.slice(0, rb).join(''), cl = vars.slice(rb).join('');
    C.text(x0 - 16, y0 - 22, rl + ' \\ ' + cl, { anchor: 'end', size: 16, color: C.t.dim });
    Cc.forEach((g, c) => C.text(x0 + c * cell + cell / 2, y0 - 12, g, { anchor: 'middle', size: 16, color: C.t.dim }));
    R.forEach((g, r) => C.text(x0 - 12, y0 + r * cell + cell / 2 + 6, g, { anchor: 'end', size: 16, color: C.t.dim }));
    for (let r = 0; r <= R.length; r++) C.line(x0, y0 + r * cell, x0 + Cc.length * cell, y0 + r * cell, { roughness: 0.9 });
    for (let c = 0; c <= Cc.length; c++) C.line(x0 + c * cell, y0, x0 + c * cell, y0 + R.length * cell, { roughness: 0.9 });
    const where = {};
    R.forEach((rg, r) => Cc.forEach((cg, c) => { const m = parseInt(rg + cg, 2); where[m] = [r, c]; const v = (spec.values || [])[m]; if (v != null) C.text(x0 + c * cell + cell / 2, y0 + r * cell + cell / 2 + 7, String(v), { anchor: 'middle', size: 21, color: String(v) === '1' ? C.t.chalk : C.t.dim }); }));
    (spec.loops || []).forEach((lp, i) => {
      const cs = (lp.cells || []).map(m => where[m]).filter(Boolean); if (!cs.length) return;
      const r0 = Math.min(...cs.map(p => p[0])), r1 = Math.max(...cs.map(p => p[0])), c0 = Math.min(...cs.map(p => p[1])), c1 = Math.max(...cs.map(p => p[1]));
      C.rect(x0 + c0 * cell + 6 + i * 3, y0 + r0 * cell + 6 + i * 3, (c1 - c0 + 1) * cell - 12 - i * 6, (r1 - r0 + 1) * cell - 12 - i * 6, { stroke: lp.hi === false ? C.t.dim : C.t.acc, strokeWidth: 2.4, roughness: 1.6 });
      if (lp.label) { const lx = x0 + Cc.length * cell + 16, ly = y0 + 20 + i * 26; C.line(lx - 8, ly - 5, lx - 2, ly - 5, { stroke: C.t.acc, strokeWidth: 2.4, roughness: 1.2 }); C.text(lx + 4, ly, lp.label, { size: 16, color: C.t.acc }); }
    });
    C.bump(y0 + R.length * cell + 10);
  };

  // Vectors on a small grid. spec: {range:[min,max], vectors:[{x,y,from:[x,y],label,hi}], grid}
  T.vectors = (spec, C) => {
    const [lo, hi] = spec.range || [-1, 5], S = 300, x0 = (W - S) / 2, y0 = 30, k = S / (hi - lo);
    const X = v => x0 + (v - lo) * k, Y = v => y0 + (hi - v) * k;
    if (spec.grid !== false) for (let v = Math.ceil(lo); v <= hi; v++) { C.line(X(v), y0, X(v), y0 + S, { stroke: '#262626', roughness: 0.4 }); C.line(x0, Y(v), x0 + S, Y(v), { stroke: '#262626', roughness: 0.4 }); }
    if (lo <= 0 && hi >= 0) { C.arrow(x0, Y(0), x0 + S + 10, Y(0), { color: C.t.dim, width: 1.4 }); C.arrow(X(0), y0 + S, X(0), y0 - 10, { color: C.t.dim, width: 1.4 }); }
    C.text(x0 + S + 14, Y(0) + 6, spec.xlabel || 'x', { size: 16, color: C.t.dim }); C.text(X(0) + 8, y0 - 12, spec.ylabel || 'y', { size: 16, color: C.t.dim });
    for (const v of spec.vectors || []) {
      const f = v.from || [0, 0], c = v.hi ? C.t.acc : C.t.chalk;
      C.arrow(X(f[0]), Y(f[1]), X(f[0] + v.x), Y(f[1] + v.y), { color: c, width: 2.2 });
      if (v.label) C.text(X(f[0] + v.x) + (v.x >= 0 ? 8 : -8), Y(f[1] + v.y) + (v.y >= 0 ? -6 : 18), v.label, { anchor: v.x >= 0 ? 'start' : 'end', size: 18, color: c });
    }
    C.bump(y0 + S + 10);
  };

  // Waveform / function plot. spec: {x:[a,b], y:[c,d], series:[{expr:'Math.sin(x)'|points:[[x,y]], label, hi}], marks:[{x,label}], xlabel, ylabel}
  T.wave = (spec, C) => {
    const [xa, xb] = spec.x || [0, 2 * Math.PI], PW = 580, PH = 200, x0 = 50, y0 = 30;
    const series = (spec.series || []).map(s => {
      if (s.points) return Object.assign({}, s, { pts: s.points });
      const f = new Function('x', 'with(Math){return ' + s.expr + '}'), pts = [];
      for (let i = 0; i <= 200; i++) { const x = xa + (xb - xa) * i / 200; const y = f(x); if (isFinite(y)) pts.push([x, y]); }
      return Object.assign({}, s, { pts });
    });
    const ys = series.flatMap(s => s.pts.map(p => p[1])), ya = spec.y ? spec.y[0] : Math.min(...ys), yb = spec.y ? spec.y[1] : Math.max(...ys);
    const X = v => x0 + (v - xa) / (xb - xa) * PW, Y = v => y0 + (yb - v) / ((yb - ya) || 1) * PH;
    const yz = ya <= 0 && yb >= 0 ? Y(0) : y0 + PH;
    C.arrow(x0 - 6, yz, x0 + PW + 12, yz, { color: C.t.dim, width: 1.4 });
    C.arrow(X(Math.max(xa, Math.min(xb, 0))), y0 + PH + 4, X(Math.max(xa, Math.min(xb, 0))), y0 - 10, { color: C.t.dim, width: 1.4 });
    C.text(x0 + PW + 12, yz + 26, spec.xlabel || 'x', { anchor: 'middle', size: 16, color: C.t.dim }); C.text(X(Math.max(xa, Math.min(xb, 0))) - 10, y0 - 8, spec.ylabel || 'y', { anchor: 'end', size: 16, color: C.t.dim });
    let li = 0;
    series.forEach(s => { const c = s.hi ? C.t.acc : C.t.chalk; C.curve(s.pts.map(p => [X(p[0]), Y(p[1])]), { stroke: c, strokeWidth: 2.2 }); if (s.label) { const p = s.pts[s.pts.length - 1]; C.text(X(p[0]) + 8, Y(p[1]) + 6 - 20 * (li++), s.label, { size: 17, color: c }); } });
    for (const m of spec.marks || []) { C.line(X(m.x), y0, X(m.x), y0 + PH, { stroke: C.t.acc, strokeWidth: 1.2, roughness: 0.6 }); if (m.label) C.text(X(m.x), y0 + PH + 22, m.label, { anchor: 'middle', size: 15, color: C.t.acc }); }
    C.bump(y0 + PH + 30);
  };

  // Free drawing. spec: {items:[{t:'line'|'rect'|'circle'|'arrow'|'text'|'poly'|'curve'|'path', ...}]} on the 720-wide canvas
  T.raw = (spec, C) => {
    for (const it of spec.items || []) {
      const o = { stroke: it.hi ? C.t.acc : (it.color || C.t.chalk) }; if (it.fill) Object.assign(o, { fill: it.fill === true ? o.stroke : it.fill, fillStyle: it.fillStyle || 'hachure' }); if (it.width) o.strokeWidth = it.width;
      switch (it.t) {
        case 'line': C.line(it.x1, it.y1, it.x2, it.y2, o); break;
        case 'rect': C.rect(it.x, it.y, it.w, it.h, o); break;
        case 'circle': C.circle(it.x, it.y, it.r, o); break;
        case 'arrow': C.arrow(it.x1, it.y1, it.x2, it.y2, { color: o.stroke, width: it.width }); break;
        case 'poly': C.poly(it.points, o); break;
        case 'curve': C.curve(it.points, o); break;
        case 'path': C.path(it.d, o); break;
        case 'text': C.text(it.x, it.y, it.text, { anchor: it.anchor, size: it.size, color: it.hi ? C.t.acc : (it.color || C.t.chalk), weight: it.weight, italic: it.italic }); break;
        default: C.warnings.push(`unknown item type "${it.t}"`);
      }
    }
    if (spec.h) C.bump(spec.h);
  };

  function render(template, spec, opts) {
    const fn = T[template]; if (!fn) throw new Error(`unknown figure template "${template}" (have: ${Object.keys(T).join(', ')})`);
    const C = new Canvas(Object.assign({ seed: spec.seed }, opts || {}));
    fn(spec || {}, C);
    return { svg: C.svg(spec.pad), warnings: C.lint() };
  }
  return { render, templates: Object.keys(T), Canvas, THEME };
});

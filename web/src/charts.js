// Minimal SVG charts with a hover layer. Colours come from CSS classes (s1/s2/s3/sm, l1/l2/l3/lm) defined in style.css.
const NS = 'http://www.w3.org/2000/svg';
const tip = () => document.getElementById('tip');

export function showTip(evt, html) {
  const t = tip();
  t.innerHTML = html;
  t.classList.add('is-on');
  const pad = 14;
  const r = t.getBoundingClientRect();
  let x = evt.clientX + pad;
  let y = evt.clientY + pad;
  if (x + r.width > window.innerWidth - 8) x = evt.clientX - r.width - pad;
  if (y + r.height > window.innerHeight - 8) y = evt.clientY - r.height - pad;
  t.style.left = `${Math.max(8, x)}px`;
  t.style.top = `${Math.max(8, y)}px`;
}
export const hideTip = () => tip().classList.remove('is-on');

function el(name, attrs = {}, parent) {
  const e = document.createElementNS(NS, name);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
  if (parent) parent.appendChild(e);
  return e;
}
function text(parent, x, y, str, attrs = {}) {
  const t = el('text', { x, y, ...attrs }, parent);
  t.textContent = str;
  return t;
}
function frame(container, m = { t: 14, r: 16, b: 26, l: 44 }) {
  container.innerHTML = '';
  const W = Math.max(260, container.clientWidth);
  const H = container.clientHeight || 220;
  const svg = el('svg', { width: W, height: H, viewBox: `0 0 ${W} ${H}`, role: 'img' }, container);
  return { svg, W, H, m, iw: W - m.l - m.r, ih: H - m.t - m.b };
}
function bindHover(node, html) {
  node.addEventListener('pointermove', (e) => showTip(e, html()));
  node.addEventListener('pointerleave', hideTip);
  node.addEventListener('click', (e) => showTip(e, html()));
}
const niceMax = (v) => {
  const p = 10 ** Math.floor(Math.log10(v));
  return Math.ceil(v / p) * p;
};
function yGrid(g, f, min, max, ticks, fmt) {
  for (let i = 0; i <= ticks; i++) {
    const v = min + ((max - min) * i) / ticks;
    const y = f.m.t + f.ih - ((v - min) / (max - min)) * f.ih;
    el('line', { x1: f.m.l, x2: f.m.l + f.iw, y1: y, y2: y, class: 'grid' }, g);
    text(g, f.m.l - 8, y + 4, fmt(v), { 'text-anchor': 'end' });
  }
}

export function barChart(container, { labels, values, cls = 's1', clsFn, fmt, tipFmt, max, ticks = 4 }) {
  const f = frame(container);
  const g = el('g', {}, f.svg);
  const top = max ?? niceMax(Math.max(...values) * 1.1);
  yGrid(g, f, 0, top, ticks, fmt);
  const step = f.iw / labels.length;
  const bw = Math.min(42, step * 0.62);
  labels.forEach((lab, i) => {
    const h = (values[i] / top) * f.ih;
    const x = f.m.l + step * i + (step - bw) / 2;
    const y = f.m.t + f.ih - h;
    const bar = el('rect', { x, y, width: bw, height: Math.max(0, h), rx: 2, class: `bar grow-y ${clsFn ? clsFn(i) : cls}` }, g);
    bar.style.transitionDelay = `${i * 40}ms`;
    text(g, x + bw / 2, f.H - 8, lab, { 'text-anchor': 'middle' });
    const hit = el('rect', { x: f.m.l + step * i, y: f.m.t, width: step, height: f.ih, class: 'hit' }, g);
    bindHover(hit, () => `<b>${lab}</b><br>${tipFmt ? tipFmt(values[i], i) : fmt(values[i])}`);
    hit.addEventListener('pointerenter', () => bar.classList.remove('dim'));
  });
}

export function lineChart(container, { labels, series, fmt, min, max, ref, ticks = 4 }) {
  const f = frame(container, { t: 12, r: 70, b: 26, l: 44 });
  const g = el('g', {}, f.svg);
  const all = series.flatMap((s) => s.values.filter((v) => v != null));
  const lo = min ?? Math.floor(Math.min(...all) * 0.9);
  const hi = max ?? Math.ceil(Math.max(...all) * 1.1);
  yGrid(g, f, lo, hi, ticks, fmt);
  const step = f.iw / labels.length;
  const X = (i) => f.m.l + step * i + step / 2;
  const Y = (v) => f.m.t + f.ih - ((v - lo) / (hi - lo)) * f.ih;
  if (ref) {
    el('line', { x1: f.m.l, x2: f.m.l + f.iw, y1: Y(ref.value), y2: Y(ref.value), class: 'lm', 'stroke-dasharray': '4 3' }, g);
    text(g, f.m.l + 4, Y(ref.value) - 5, ref.label);
  }
  series.forEach((s) => {
    const pts = s.values.map((v, i) => (v == null ? null : [X(i), Y(v)])).filter(Boolean);
    el('path', { d: 'M' + pts.map((p) => p.join(',')).join('L'), class: `line ${s.cls.replace('s', 'l')}` }, g);
    pts.forEach((p) => el('circle', { cx: p[0], cy: p[1], r: 3.5, class: `dot ${s.cls}` }, g));
    const last = pts[pts.length - 1];
    text(g, last[0] + 10, last[1] + 4, s.name);
  });
  labels.forEach((lab, i) => {
    text(g, X(i), f.H - 8, lab, { 'text-anchor': 'middle' });
    const hit = el('rect', { x: X(i) - step / 2, y: f.m.t, width: step, height: f.ih, class: 'hit' }, g);
    bindHover(hit, () => `<b>${lab}</b><br>` + series.map((s) => `${s.name}: ${s.values[i] == null ? 'n/a' : fmt(s.values[i])}`).join('<br>'));
  });
}

export function stackedBars(container, { labels, series, fmt }) {
  const f = frame(container, { t: 10, r: 120, b: 26, l: 36 });
  const g = el('g', {}, f.svg);
  yGrid(g, f, 0, 100, 4, (v) => `${v}%`);
  const step = f.iw / labels.length;
  const bw = Math.min(40, step * 0.62);
  labels.forEach((lab, i) => {
    let acc = 0;
    const x = f.m.l + step * i + (step - bw) / 2;
    series.forEach((s) => {
      const v = s.values[i];
      const h = (v / 100) * f.ih;
      const y = f.m.t + f.ih - ((acc + v) / 100) * f.ih;
      // 2px surface gap between stacked fills
      el('rect', { x, y: y + 1, width: bw, height: Math.max(0, h - 2), class: `bar grow-y ${s.cls}` }, g).style.transitionDelay = `${i * 40}ms`;
      if (i === labels.length - 1) text(g, x + bw + 10, y + h / 2 + 4, `${s.name} ${Math.round(v)}%`);
      acc += v;
    });
    text(g, x + bw / 2, f.H - 8, lab, { 'text-anchor': 'middle' });
    const hit = el('rect', { x: f.m.l + step * i, y: f.m.t, width: step, height: f.ih, class: 'hit' }, g);
    bindHover(hit, () => `<b>${lab}</b><br>` + series.map((s) => `${s.name}: ${fmt(s.values[i])}`).join('<br>'));
  });
}

export function football(container, { rows, price, tp, min, max }) {
  const narrow = container.clientWidth < 560;
  const f = frame(container, { t: 26, r: 16, b: 30, l: narrow ? 112 : 200 });
  const g = el('g', {}, f.svg);
  const X = (v) => f.m.l + ((v - min) / (max - min)) * f.iw;
  for (let v = min; v <= max; v += 1000) {
    el('line', { x1: X(v), x2: X(v), y1: f.m.t, y2: f.m.t + f.ih, class: 'grid' }, g);
    text(g, X(v), f.H - 10, `${(v / 1000).toFixed(0)}k`, { 'text-anchor': 'middle' });
  }
  const step = f.ih / rows.length;
  rows.forEach((r, i) => {
    const y = f.m.t + step * i + step * 0.25;
    const bar = el('rect', { x: X(r.low), y, width: X(r.high) - X(r.low), height: step * 0.5, rx: 2, class: `bar grow ${r.cls}` }, g);
    bar.style.transitionDelay = `${200 + i * 90}ms`;
    text(g, f.m.l - 10, y + step * 0.25 + 4, narrow ? r.short : r.label, { 'text-anchor': 'end', class: 't-strong' });
    bindHover(bar, () => `<b>${r.label}</b><br>¥${Math.round(r.low).toLocaleString()} - ¥${Math.round(r.high).toLocaleString()}<small>${r.basis}</small>`);
  });
  el('line', { x1: X(price), x2: X(price), y1: f.m.t - 8, y2: f.m.t + f.ih, class: 'price-line' }, g);
  el('line', { x1: X(tp), x2: X(tp), y1: f.m.t - 8, y2: f.m.t + f.ih, class: 'tp-line' }, g);
  text(g, X(price) - 6, f.m.t - 12, `Price ¥${Math.round(price).toLocaleString()}`, { 'text-anchor': 'end', class: 't-strong' });
  text(g, X(tp) + 6, f.m.t - 12, `TP ¥${Math.round(tp).toLocaleString()}`, { class: 't-accent' });
}

export function tornado(container, { rows }) {
  const narrow = container.clientWidth < 560;
  const f = frame(container, { t: 10, r: 50, b: 30, l: narrow ? 130 : 220 });
  const g = el('g', {}, f.svg);
  const lim = 800;
  const X = (v) => f.m.l + ((v + lim) / (lim * 1.5)) * f.iw;
  for (let v = -800; v <= 400; v += 200) {
    el('line', { x1: X(v), x2: X(v), y1: f.m.t, y2: f.m.t + f.ih, class: v === 0 ? 'axis' : 'grid' }, g);
    text(g, X(v), f.H - 10, v > 0 ? `+${v}` : `${v}`, { 'text-anchor': 'middle' });
  }
  const step = f.ih / rows.length;
  rows.forEach((r, i) => {
    const y = f.m.t + step * i + step * 0.22;
    const x0 = X(Math.min(0, r.value));
    const w = Math.abs(X(r.value) - X(0));
    const bar = el('rect', { x: x0, y, width: w, height: step * 0.56, rx: 2, class: `bar grow ${r.value < 0 ? 's3' : 's1'}` }, g);
    bar.style.transformOrigin = r.value < 0 ? 'right center' : 'left center';
    bar.style.transitionDelay = `${i * 80}ms`;
    text(g, f.m.l - 10, y + step * 0.28 + 4, narrow ? r.short : r.label, { 'text-anchor': 'end', class: 't-strong' });
    text(g, r.value < 0 ? x0 - 6 : x0 + w + 6, y + step * 0.28 + 4, `${r.value > 0 ? '+' : ''}${r.value}`, { 'text-anchor': r.value < 0 ? 'end' : 'start' });
    bindHover(bar, () => `<b>${r.full || r.label}</b><br>TP change ¥${r.value > 0 ? '+' : ''}${r.value} (TP ¥${r.tp.toLocaleString()}, ${r.rating})<br>FY2028E EPS ${(r.eps * 100).toFixed(1)}%`);
  });
}

export function gauge(container, { low, high, price, tp, min, max }) {
  const f = frame(container, { t: 22, r: 8, b: 18, l: 8 });
  const g = el('g', {}, f.svg);
  const X = (v) => f.m.l + ((v - min) / (max - min)) * f.iw;
  const y = f.m.t + 12;
  el('line', { x1: f.m.l, x2: f.m.l + f.iw, y1: y, y2: y, class: 'grid' }, g);
  el('rect', { x: X(low), y: y - 2, width: X(high) - X(low), height: 4, class: 'sm grow' }, g);
  text(g, X(low), y + 20, `52w low ${Math.round(low).toLocaleString()}`, { 'text-anchor': 'start' });
  text(g, X(high), y + 20, `high ${Math.round(high).toLocaleString()}`, { 'text-anchor': 'end' });
  el('circle', { cx: X(price), cy: y, r: 5, class: 'dot sm' }, g).style.fill = 'var(--text)';
  text(g, X(price), y - 10, 'Price', { 'text-anchor': 'middle', class: 't-strong' });
  const m = el('g', { class: 'gauge-tp' }, g);
  el('line', { x1: X(tp), x2: X(tp), y1: y - 9, y2: y + 9, class: 'tp-line' }, m);
  text(m, X(tp), y - 12, 'TP', { 'text-anchor': 'middle', class: 't-accent' });
}

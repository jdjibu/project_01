import { barChart, football, gauge, hideTip, lineChart, showTip, stackedBars, tornado } from './charts.js';

const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
const canHover = matchMedia('(hover: hover)').matches;
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];

const fmt = {
  int: (v) => Math.round(v).toLocaleString('en-US'),
  pct: (v) => `${v >= 0 ? '+' : ''}${(v * 100).toFixed(1)}%`,
  pct1: (v) => `${(v * 100).toFixed(1)}%`,
  pct2: (v) => `${(v * 100).toFixed(2)}%`,
  date: (v) => new Date(`${v}T00:00:00`).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' }),
  bn: (v) => (v / 1000).toLocaleString('en-US', { maximumFractionDigits: 1, minimumFractionDigits: 1 }),
};
const yr = (k) => k.replace('FY20', 'FY');

async function load() {
  const get = (p) => fetch(p).then((r) => r.json());
  const [hist, val, facts] = await Promise.all([get('/data/history.json'), get('/data/valuation.json'), get('/data/facts.json')]);
  return { hist, val, facts };
}

// ---------------------------------------------------------------- traceable figures
function bindFacts(facts) {
  $$('.f[data-fact]').forEach((n) => {
    const f = facts[n.dataset.fact];
    if (!f) return;
    n.textContent = f.display;
    n.tabIndex = 0;
    n.setAttribute('aria-label', `${f.display}. Source: ${f.source}`);
    const html = () => `<b>${f.display}</b><small>${f.source}</small>`;
    n.addEventListener('pointerenter', (e) => showTip(e, html()));
    n.addEventListener('pointermove', (e) => showTip(e, html()));
    n.addEventListener('pointerleave', hideTip);
    n.addEventListener('focus', () => {
      const r = n.getBoundingClientRect();
      showTip({ clientX: r.left, clientY: r.bottom }, html());
    });
    n.addEventListener('blur', hideTip);
  });
}

// ---------------------------------------------------------------- hero + scenario
function countTo(node, to, f, dur = 1400) {
  const from = Number(node.dataset.v || 0);
  node.dataset.v = to;
  if (reduce) { node.textContent = f(to); return; }
  const t0 = performance.now();
  const step = (t) => {
    const p = Math.min(1, (t - t0) / dur);
    const e = 1 - (1 - p) ** 3;
    node.textContent = f(from + (to - from) * e);
    if (p < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}

function renderScenario(val, name) {
  const s = val[name];
  $$('.seg button').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.scen === name)));
  const badge = $('#ratingBadge');
  badge.textContent = s.rating;
  badge.className = `badge ${s.rating === 'BUY' ? 'badge--buy' : s.rating === 'SELL' ? 'badge--sell' : ''}`;
  countTo($('[data-count="tp"]'), s.tp, fmt.int);
  countTo($('[data-count="upside"]'), s.upside, fmt.pct);
  countTo($('[data-count="tsr"]'), s.tsr, fmt.pct);
  $$('[data-bind]').forEach((n) => {
    const k = n.dataset.bind;
    const v = k.includes('.') ? k.split('.').reduce((o, p) => o?.[p], val) : s[k];
    if (v == null) return;
    n.textContent = n.dataset.fmt ? fmt[n.dataset.fmt](v) : v;
  });
  const m = val.market;
  const lo = Math.min(m.low_52w, val.Bear.tp) * 0.95;
  const hi = Math.max(m.high_52w, val.Bull.tp) * 1.03;
  gauge($('#gauge'), { low: m.low_52w, high: m.high_52w, price: s.price, tp: s.tp, min: lo, max: hi });
  $('#gauge').classList.add('is-drawn');
  renderDcf(val, name);
}

// ---------------------------------------------------------------- marquee
function band(val, facts) {
  const b = val.Base;
  const items = [
    [facts.revenue.display, 'revenue FY3/2026'], [facts.op_margin.display, 'operating margin'],
    [facts.dio.display, 'of inventory'], [facts.net_cash.display, 'net cash'],
    [facts.ev_ebitda.display, 'EV / EBITDA LTM'], [facts.roe.display, `ROE vs ${facts.target_roe.display} target`],
    [facts.europe_share.display, 'of sales in Europe'], [facts.aftermarket.display, 'aftermarket share'],
    [fmt.pct2(b.wacc), 'WACC'], [`¥${fmt.int(b.tp)}`, '12-month target'],
  ];
  const html = items.map(([v, l]) => `<div class="band__item"><b>${v}</b><span>${l}</span></div>`).join('');
  $('#band').innerHTML = html + html; // duplicated for a seamless loop
}

// ---------------------------------------------------------------- accessible data tables (one per chart)
function dataTable(chartId, headers, rows) {
  const fig = $(`#${chartId}`).closest('figure');
  let d = fig.querySelector(`details[data-for="${chartId}"]`);
  if (!d) {
    d = document.createElement('details');
    d.className = 'data';
    d.dataset.for = chartId;
    fig.appendChild(d);
  }
  d.innerHTML = `<summary>Data table</summary><div class="scroll"><table class="table"><thead><tr>${headers.map((h) => `<th>${h}</th>`).join('')}</tr></thead>` +
    `<tbody>${rows.map((r) => `<tr>${r.map((c) => `<td>${c}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
}

// ---------------------------------------------------------------- charts
function drawHistory(hist) {
  const L = hist.years.map(yr);
  const m = hist.metrics;
  barChart($('#chRevenue'), { labels: L, values: m.revenue.map((v) => v / 1000), fmt: (v) => `${Math.round(v)}`,
    tipFmt: (v, i) => `Revenue ¥${v.toFixed(1)}bn${m.revenue_growth[i] != null ? `<br>Growth ${fmt.pct(m.revenue_growth[i])}` : ''}`, max: 900, ticks: 3 });
  lineChart($('#chCard'), { labels: L, fmt: (v) => `${Math.round(v)}%`, min: 15, max: 40, ticks: 5, series: [
    { name: 'Gross margin', values: m.gross_margin.map((v) => v * 100), cls: 's1' },
    { name: 'SG&A', values: hist.sga_pct.map((v) => v * 100), cls: 's2' }] });
  lineChart($('#chMargins'), { labels: L, fmt: (v) => `${Math.round(v)}%`, min: 0, max: 40, series: [
    { name: 'Gross', values: m.gross_margin.map((v) => v * 100), cls: 'sm' },
    { name: 'EBITDA', values: m.ebitda_margin.map((v) => v * 100), cls: 's2' },
    { name: 'Operating', values: m.op_margin.map((v) => v * 100), cls: 's1' }] });
  barChart($('#chInventory'), { labels: L, values: m.dio, cls: 's3', fmt: (v) => `${Math.round(v)}`,
    tipFmt: (v) => `${Math.round(v)} days of cost of sales`, max: 400 });
  lineChart($('#chOpm'), { labels: L, fmt: (v) => `${Math.round(v)}%`, min: 0, max: 20,
    series: [{ name: 'Op. margin', values: m.op_margin.map((v) => v * 100), cls: 's1' }] });
  const rs = hist.region_share;
  const rest = L.map((_, i) => 100 - rs.Europe[i] - rs.Japan[i] - rs['North America'][i]);
  stackedBars($('#chRegion'), { labels: L, fmt: (v) => `${v.toFixed(1)}%`, series: [
    { name: 'Europe', values: rs.Europe, cls: 's1' }, { name: 'Japan', values: rs.Japan, cls: 's2' },
    { name: 'N. America', values: rs['North America'], cls: 's3' }, { name: 'Rest', values: rest, cls: 'sm' }] });
  lineChart($('#chReturns'), { labels: L, fmt: (v) => `${Math.round(v)}%`, min: 0, max: 20, ref: { value: 11, label: 'ROE target 11%' },
    series: [{ name: 'ROIC', values: m.roic.map((v) => v * 100), cls: 's1' }, { name: 'ROE', values: m.roe.map((v) => v * 100), cls: 's2' }] });
  const p = (v) => (v == null ? 'n/a' : fmt.pct1(v));
  dataTable('chMargins', ['FY', 'Revenue (¥bn)', 'Gross', 'EBITDA', 'Operating'],
    L.map((y, i) => [y, fmt.bn(m.revenue[i]), p(m.gross_margin[i]), p(m.ebitda_margin[i]), p(m.op_margin[i])]));
  dataTable('chOpm', ['FY', 'Inventory days', 'Op. margin'], L.map((y, i) => [y, Math.round(m.dio[i]), p(m.op_margin[i])]));
  dataTable('chRegion', ['FY', 'Europe', 'Japan', 'N. America', 'Rest'],
    L.map((y, i) => [y, ...[rs.Europe[i], rs.Japan[i], rs['North America'][i], rest[i]].map((v) => `${v.toFixed(1)}%`)]));
  dataTable('chReturns', ['FY', 'ROIC', 'ROE'], L.map((y, i) => [y, p(m.roic[i]), p(m.roe[i])]));
}

function drawValuation(val) {
  const b = val.Base;
  const ff = b.football;
  const rows = [
    ['dcf_g', 's1', 'DCF Gordon'], ['dcf_x', 's1', 'DCF exit'], ['own', 's2', 'Own history'],
    ['cmp_ev', 's2', 'Peers EV/EBITDA'], ['cmp_pe', 's2', 'Peers P/E'], ['w52', 'sm', '52-week'],
  ].map(([k, cls, short]) => ({ ...ff[k], cls, short }));
  football($('#chFootball'), { rows, price: b.price, tp: b.tp, min: 3000, max: 10000 });
  dataTable('chFootball', ['Method', 'Low (¥)', 'High (¥)', 'Basis'], rows.map((x) => [x.label, fmt.int(x.low), fmt.int(x.high), x.basis]));
  const r = val.risks.filter((x) => x.tp_chg_jpy != null && x.shock !== 'Base').sort((a, c) => a.tp_chg_jpy - c.tp_chg_jpy);
  const short = (s) => s.replace(' (all years)', '').replace('Construction downturn: local-currency growth -3pp in FY2027-28', 'Demand -3pp (FY27-28)')
    .replace('Inventory build: +30 inventory days', '+30 inventory days').replace(' vs USD and EUR', '');
  dataTable('chTornado', ['Shock', 'FY2028E EPS', 'TP (¥)', 'Rating'],
    r.map((x) => [x.shock, fmt.pct(x.eps_fy2028_chg), `${fmt.int(x.tp)} (${x.tp_chg_jpy > 0 ? '+' : ''}${x.tp_chg_jpy})`, x.rating]));
  tornado($('#chTornado'), { rows: r.map((x) => ({ label: short(x.shock), full: x.shock, short: short(x.shock), value: x.tp_chg_jpy, tp: x.tp, rating: x.rating, eps: x.eps_fy2028_chg })) });
}

function renderDcf(val, name) {
  const s = val[name];
  const rows = [
    ['PV of free cash flow, Jul 2026 - Mar 2031', `¥${fmt.bn(s.sum_pv)}bn`],
    ['PV of terminal value (Gordon)', `¥${fmt.bn(s.pv_tv_g)}bn`],
    ['Enterprise value', `¥${fmt.bn(s.ev_g)}bn`, 'total'],
    ['+ Net cash, investments, less NCI and interim', `¥${fmt.bn(s.bridge)}bn`],
    ['Value per share: Gordon / exit multiple', `¥${fmt.int(s.ps_g)} / ¥${fmt.int(s.ps_x)}`],
    [`Terminal: g ${fmt.pct1(s.g)}, RONIC ${fmt.pct1(s.ronic)}; exit ${s.mult.toFixed(1)}x`, `implies ${s.impl_mult.toFixed(1)}x / g ${fmt.pct1(s.impl_g)}`],
    ['Fair value today, rolled forward at Ke, less dividends', `¥${fmt.int(s.fv)} → ¥${fmt.int(s.tp)}`, 'key'],
  ];
  $('#tDcf').innerHTML = `<thead><tr><th>${name} case</th><th>Value</th></tr></thead><tbody>` +
    rows.map(([a, v, c]) => `<tr class="${c || ''}"><td>${a}</td><td>${v}</td></tr>`).join('') + '</tbody>';
}

function tables(val) {
  const w = val.Base.wacc_build;
  const rows = [['Risk-free rate (10Y JGB)', fmt.pct2(w.rf)], ['Mature-market ERP (Damodaran)', fmt.pct2(w.erp)],
    ['Country risk premium, revenue-weighted', fmt.pct2(w.crp)], ['Unlevered beta (Japan Machinery)', w.bu.toFixed(2)],
    ['Relevered beta', w.bl.toFixed(2)], ['Cost of equity', fmt.pct2(w.ke)], ['After-tax cost of debt', fmt.pct2(w.kd)],
    ['Debt weight (market)', fmt.pct1(w.wd)], ['WACC', fmt.pct2(w.wacc)]];
  $('#tWacc').innerHTML = '<thead><tr><th>Input</th><th>Value</th></tr></thead><tbody>' +
    rows.map(([a, b], i) => `<tr class="${i === rows.length - 1 ? 'total key' : ''}"><td>${a}</td><td>${b}</td></tr>`).join('') + '</tbody>';

  const p = val.peers;
  const c = val.Base.comps;
  const ps = val.Base.peer_stats;
  $('#tPeers').innerHTML = '<thead><tr><th>Company</th><th>EV/EBITDA</th><th>P/E</th><th>Margin</th></tr></thead><tbody>' +
    p.map((x) => `<tr><td>${x.name}</td><td>${x.ev_ebitda.toFixed(1)}x</td><td>${x.pe.toFixed(1)}x</td><td>${fmt.pct1(x.ebitda_margin)}</td></tr>`).join('') +
    `<tr class="total"><td>Peer median</td><td>${ps['Median|EV/EBITDA'].toFixed(1)}x</td><td>${ps['Median|P/E'].toFixed(1)}x</td><td>${fmt.pct1(ps['Median|EBITDA mgn'])}</td></tr>` +
    `<tr class="total key"><td>Makita (LTM)</td><td>${c.ev_ebitda.toFixed(1)}x</td><td>${c.pe.toFixed(1)}x</td><td>${fmt.pct1(c.ebitda / c.rev)}</td></tr></tbody>`;

  const g = val.Base.sensitivity.wacc_g;
  let h = '<div class="h">WACC \\ g</div>' + g.cols.map((x) => `<div class="h">${fmt.pct1(x)}</div>`).join('');
  const all = g.values.flat();
  const lo = Math.min(...all);
  const hi = Math.max(...all);
  g.rows.forEach((rw, i) => {
    h += `<div class="h">${fmt.pct2(rw)}</div>`;
    g.values[i].forEach((v, j) => {
      const t = (v - lo) / (hi - lo);
      const base = i === 2 && j === 2;
      h += `<div class="c${base ? ' base' : ''}" style="background: rgba(var(--accent-rgb), ${(0.04 + t * 0.26).toFixed(3)})" ` +
        `data-tip="WACC ${fmt.pct2(rw)}, g ${fmt.pct1(g.cols[j])}: ¥${fmt.int(v)} per share (${fmt.pct(v / val.Base.price - 1)} vs price)">${fmt.int(v)}</div>`;
    });
  });
  $('#heat').innerHTML = h;
  $$('#heat [data-tip]').forEach((n) => {
    n.addEventListener('pointermove', (e) => showTip(e, n.dataset.tip));
    n.addEventListener('pointerleave', hideTip);
  });

  const cat = [['Late Oct / early Nov 2026', '2Q FY3/2027 results', 'Europe local-currency growth; gross margin ex tariff refund; inventory days'],
    ['Dec 2026', 'Interim dividend paid', 'Step-up under the 50% payout policy'],
    ['Early Feb 2027', '3Q results', 'Inventory into the spring season'],
    ['2026-27', 'BoJ meetings', 'The yen path: the largest macro risk'],
    ['Late Apr 2027', 'FY results and guidance', 'Progress to the 15% margin target; buybacks'],
    ['Jun 2027', 'AGM, Makita Report', '40Vmax, OPE and Vision FY2030 progress']];
  $('#timeline').innerHTML = cat.map(([d, e, w]) => `<div><p class="label">${d}</p><b>${e}</b><p>${w}</p></div>`).join('');
}

// ---------------------------------------------------------------- motion
function observe() {
  const io = new IntersectionObserver((es) => es.forEach((e) => {
    if (!e.isIntersecting) return;
    e.target.classList.add('is-in', 'is-drawn');
    io.unobserve(e.target);
  }), { threshold: 0.18, rootMargin: '0px 0px -40px 0px' });
  $$('.reveal, .mask, .fig, #footerEnd').forEach((n) => io.observe(n));
}

function spotlight() {
  if (!canHover) return;
  $$('.spot, .card').forEach((c) => {
    let raf = 0;
    c.addEventListener('pointermove', (e) => {
      if (raf) return;
      raf = requestAnimationFrame(() => {
        const r = c.getBoundingClientRect();
        c.style.setProperty('--mx', `${e.clientX - r.left}px`);
        c.style.setProperty('--my', `${e.clientY - r.top}px`);
        raf = 0;
      });
    });
  });
}

function magnet() {
  if (!canHover || reduce) return;
  $$('.magnet').forEach((b) => {
    let raf = 0;
    b.addEventListener('pointermove', (e) => {
      if (raf) return;
      raf = requestAnimationFrame(() => {
        const r = b.getBoundingClientRect();
        const dx = (e.clientX - (r.left + r.width / 2)) / r.width;
        const dy = (e.clientY - (r.top + r.height / 2)) / r.height;
        b.style.transform = `translate(${dx * 12}px, ${dy * 10}px)`;
        raf = 0;
      });
    });
    b.addEventListener('pointerleave', () => { b.style.transform = ''; });
  });
}

function navAndParallax() {
  const nav = $('#nav');
  const light = $('.hero__light');
  const links = $$('.nav__links a[href^="#"]');
  const sections = links.map((a) => $(a.getAttribute('href')));
  let ticking = false;
  const onScroll = () => {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(() => {
      const y = window.scrollY;
      nav.classList.toggle('is-scrolled', y > 24);
      if (!reduce && light) light.style.transform = `translate3d(0, ${y * 0.15}px, 0)`;
      let cur = -1;
      sections.forEach((s, i) => { if (s && s.getBoundingClientRect().top < window.innerHeight * 0.4) cur = i; });
      links.forEach((a, i) => a.setAttribute('aria-current', String(i === cur)));
      ticking = false;
    });
  };
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
  const tog = $('#navToggle');
  const menu = $('#navLinks');
  tog.addEventListener('click', () => {
    const open = tog.getAttribute('aria-expanded') !== 'true';
    tog.setAttribute('aria-expanded', String(open));
    menu.classList.toggle('is-open', open);
  });
  menu.addEventListener('click', (e) => {
    if (e.target.closest('a')) { tog.setAttribute('aria-expanded', 'false'); menu.classList.remove('is-open'); }
  });
}

// ---------------------------------------------------------------- boot
(async function main() {
  // hero title reveals immediately
  requestAnimationFrame(() => $('.hero__title').classList.add('is-in'));
  const { hist, val, facts } = await load();
  bindFacts(facts);
  band(val, facts);
  tables(val);
  let scen = 'Base';
  renderScenario(val, scen);
  $$('.seg button').forEach((b) => b.addEventListener('click', () => { scen = b.dataset.scen; renderScenario(val, scen); }));
  const draw = () => { drawHistory(hist); drawValuation(val); };
  draw();
  let t;
  let lastW = window.innerWidth;
  window.addEventListener('resize', () => {
    clearTimeout(t);
    t = setTimeout(() => {
      if (window.innerWidth === lastW) return;
      lastW = window.innerWidth;
      draw();
      $$('.fig').forEach((f) => f.classList.add('is-drawn'));
      renderScenario(val, scen);
    }, 150);
  });
  observe();
  spotlight();
  magnet();
  navAndParallax();
  window.addEventListener('scroll', hideTip, { passive: true });
})();

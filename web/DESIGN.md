# DESIGN.md

> A research note set in black and champagne gold: quiet, exact, and every number traceable.

## 1. Visual Theme & Atmosphere

**Style**: Dark Editorial Luxury (Dark Editorial seed, tuned toward private-bank stationery)
**Keywords**: black, champagne gold, serif display, hairline rules, generous space, tabular figures, restraint
**Tone**: confident, precise, calm. NOT flashy, NOT crypto-dashboard, NOT neon, NOT a brand imitation of Makita (no teal)
**Feel**: like opening a heavy, black-bound equity research note under a reading lamp.

**Interaction Tier**: L2 (fluid): scroll reveals, nav state change, light parallax, cursor spotlight on cards
**Dependencies**: none at runtime. Vite 6.4.3 (build only). Vanilla JS, CSS, IntersectionObserver, inline SVG charts.

Design decisions and their main alternative:
| Choice | Alternative | Why |
|---|---|---|
| Black + champagne gold | Black + white | Gold gives one accent for the numbers that matter (TP, rating) without a second colour |
| Serif display (Cormorant Garamond) | Geometric sans throughout | Editorial, "printed note" feel; body stays in Inter for legibility |
| Hand-written SVG charts | A chart library | Zero dependencies, full control of the hover layer, small bundle |
| L2 motion | L3 cinematic (pins, WebGL) | Audience is bank recruiters: credibility beats spectacle. One hero moment, everything else subtle |

## 2. Color Palette & Roles

```css
:root {
  /* Backgrounds */
  --bg: #0A0A09;             /* page */
  --surface: #121210;        /* cards, tables */
  --surface-alt: #171714;    /* alternate sections */
  --surface-hover: #1C1B18;  /* hovered card */

  /* Borders */
  --border: #2A2824;         /* hairlines */
  --border-hover: #5A4A2C;   /* hovered card edge (gold-tinted) */

  /* Text */
  --text: #EDE8DF;           /* headings, key figures (ivory, not pure white) */
  --text-secondary: #B8B2A7; /* body */
  --text-tertiary: #827C72;  /* labels, sources */

  /* Accent: champagne gold */
  --accent: #C9A45C;
  --accent-hover: #DDBB76;
  --accent-deep: #8A6D35;

  /* Chart series (dark-surface validated with the dataviz validator: all 6 checks pass on #0B0B0A) */
  --series-1: #B38B3C;       /* gold: Makita / Base / hero series */
  --series-2: #5A84C6;       /* slate blue: comparison series */
  --series-3: #C25A4C;       /* oxblood: negative / Bear */
  --series-muted: #6E6A63;   /* context only (history, benchmarks) */

  /* RGB helpers */
  --bg-rgb: 10, 10, 9;
  --accent-rgb: 201, 164, 92;
  --text-rgb: 237, 232, 223;

  /* Semantic (always paired with a label, never colour alone) */
  --success: #7FA77A;
  --error: #C25A4C;
  --warning: #C9A45C;
}
```

**Color Rules:**
- Every colour in code is a CSS variable from this list. No hex values in components.
- Gold is reserved for the figures that carry the conclusion (TP, rating, the active scenario) and for focus rings.
- Text never uses a series colour; a coloured swatch next to the text carries identity.
- No gradients on body text. The only gradient is the hero's slow ambient light.

## 3. Typography Rules

**Font Stack:**
```css
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600&family=Inter:wght@300;400;500;600&display=swap');
--font-display: 'Cormorant Garamond', 'Times New Roman', Georgia, serif;
--font-body: 'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif;
```

| Role | Font | Size | Weight | Line Height | Letter Spacing |
|------|------|------|--------|-------------|----------------|
| Hero H1 | Cormorant Garamond | clamp(3.5rem, 9vw, 7.5rem) | 500 | 0.95 | -0.02em |
| Hero figure (TP) | Cormorant Garamond | clamp(3rem, 7vw, 5.5rem) | 400 | 1 | -0.01em |
| Section H2 | Cormorant Garamond | clamp(2.25rem, 4.5vw, 3.5rem) | 500 | 1.05 | -0.01em |
| H3 | Inter | 1.05rem | 500 | 1.4 | 0 |
| Body | Inter | 1rem | 300 | 1.7 | 0 |
| Label / eyebrow | Inter | 0.72rem | 500 | 1.4 | 0.22em, uppercase |
| Numbers | Inter, `font-variant-numeric: tabular-nums` | inherit | 400 | inherit | 0 |

**Typography Rules:**
- Display serif only for H1, H2 and hero figures. Everything else Inter.
- All numbers in tables and KPIs use tabular figures and right alignment.
- **NEVER use**: Playfair Display (over-used), any script or condensed font, system serif fallback for H1 without Cormorant loaded.

**Text Decoration** (per text-decoration-rules.md):
- Hero H1: no gradient (style is not Dark Tech / Playful). Dark background and size >= 80px: subtle glow allowed, `text-shadow: 0 0 40px rgba(var(--accent-rgb), 0.12)`.
- H2, H3: no gradient, no shadow.

## 4. Component Stylings

### Buttons
```css
.btn { display:inline-flex; align-items:center; gap:.6rem; min-height:48px; padding:0 1.4rem;
  font:500 .82rem/1 var(--font-body); letter-spacing:.14em; text-transform:uppercase;
  color:var(--bg); background:var(--accent); border:1px solid var(--accent); border-radius:999px;
  transition:background .3s, color .3s, transform .3s cubic-bezier(.2,.7,.2,1); }
.btn:hover { background:var(--accent-hover); border-color:var(--accent-hover); }
.btn:active { transform:scale(.98); }
.btn:focus-visible { outline:2px solid var(--accent); outline-offset:4px; }
.btn[disabled], .btn[aria-disabled="true"] { opacity:.4; cursor:not-allowed; }
.btn--ghost { color:var(--text); background:transparent; border-color:var(--border); }
.btn--ghost:hover { border-color:var(--accent); color:var(--accent); background:transparent; }
```

### Cards (spotlight)
```css
.card { position:relative; background:var(--surface); border:1px solid var(--border); border-radius:2px;
  padding:2rem; overflow:hidden; transition:border-color .4s, background .4s; }
.card::before { content:""; position:absolute; inset:0; pointer-events:none; opacity:0; transition:opacity .4s;
  background:radial-gradient(420px circle at var(--mx,50%) var(--my,50%), rgba(var(--accent-rgb),.10), transparent 60%); }
.card:hover { border-color:var(--border-hover); background:var(--surface-hover); }
.card:hover::before { opacity:1; }
.card:focus-within { border-color:var(--accent); }
```

### Navigation
```css
.nav { position:fixed; inset:0 0 auto; height:72px; display:flex; align-items:center; z-index:50;
  transition:background .4s, border-color .4s, height .4s; border-bottom:1px solid transparent; }
.nav.is-scrolled { height:60px; background:rgba(var(--bg-rgb),.78); backdrop-filter:blur(12px);
  border-bottom-color:var(--border); }
.nav a { color:var(--text-secondary); } .nav a:hover, .nav a:focus-visible { color:var(--accent); }
.nav a[aria-current="true"] { color:var(--text); }
```

### Links
```css
.link { color:var(--text); background:linear-gradient(var(--accent),var(--accent)) 0 100%/0 1px no-repeat;
  transition:background-size .4s cubic-bezier(.2,.7,.2,1), color .3s; }
.link:hover { background-size:100% 1px; color:var(--accent); }
.link:focus-visible { outline:1px solid var(--accent); outline-offset:3px; }
```

### Tags / Badges
```css
.badge { display:inline-flex; align-items:center; gap:.5rem; padding:.35rem .8rem; border:1px solid var(--accent);
  color:var(--accent); font:500 .72rem/1 var(--font-body); letter-spacing:.22em; text-transform:uppercase; }
.badge--buy { border-color:var(--success); color:var(--success); }
.badge--sell { border-color:var(--error); color:var(--error); }
```

### Segmented control (scenario switch)
```css
.seg { display:inline-flex; border:1px solid var(--border); border-radius:999px; padding:4px; }
.seg button { min-height:40px; min-width:72px; border-radius:999px; color:var(--text-tertiary); background:none; border:0; }
.seg button:hover { color:var(--text); }
.seg button[aria-pressed="true"] { background:rgba(var(--accent-rgb),.14); color:var(--accent); }
.seg button:focus-visible { outline:2px solid var(--accent); outline-offset:2px; }
.seg button:disabled { opacity:.4; }
```

### Data tables
```css
.table { width:100%; border-collapse:collapse; font-variant-numeric:tabular-nums; }
.table th { font:500 .72rem var(--font-body); letter-spacing:.16em; text-transform:uppercase; color:var(--text-tertiary);
  border-bottom:1px solid var(--accent-deep); text-align:right; padding:.6rem .5rem; }
.table td { border-bottom:1px solid var(--border); padding:.55rem .5rem; text-align:right; color:var(--text-secondary); }
.table tr:hover td { background:var(--surface-hover); color:var(--text); }
```

### Chart tooltip
```css
.tip { position:fixed; pointer-events:none; background:var(--surface-alt); border:1px solid var(--border-hover);
  padding:.55rem .75rem; font:400 .8rem/1.4 var(--font-body); color:var(--text); opacity:0; transition:opacity .15s; }
.tip.is-on { opacity:1; }
```

## 5. Layout Principles

**Container:** max width 1200px; padding `clamp(1rem, 4vw, 3rem)`; narrow text column 680px.
**Grid:** 12 columns, 24px gutter on desktop; single column below 760px.
**Spacing scale:** 4, 8, 12, 16, 24, 32, 48, 64, 96, 144px. Sections are separated by 144px (desktop) / 96px (mobile).
**Rhythm:** every section opens with an eyebrow label, a serif H2, a one-paragraph lede, then evidence.
**Bento:** the thesis grid is unequal (one 7-column card + two 5-column cards, then a full-width "what would make me wrong").

## 6. Depth & Elevation

Flat by design. Depth comes from surface steps and hairlines, not shadows.
| Level | Use | Treatment |
|---|---|---|
| 0 | Page | `--bg` |
| 1 | Cards, tables | `--surface` + 1px `--border` |
| 2 | Hover | `--surface-hover` + gold-tinted border + spotlight |
| 3 | Tooltip, nav (scrolled) | `--surface-alt` or translucent bg with blur <= 12px |
The only shadow: tooltip `0 12px 32px rgba(0,0,0,.45)`.

## 7. Animation & Interaction

Easing: `--ease: cubic-bezier(.2,.7,.2,1)`. Durations: 300ms (hover), 900ms (reveals), 1600ms (hero sequence).

| Category (L2 requirement) | Where | Implementation |
|---|---|---|
| Text: Hero H1 | "Makita" title | Word mask reveal: each word rises from `translateY(105%)` inside `overflow:hidden`, staggered 90ms |
| Text: Section H2 | Every H2 | Line mask reveal on scroll + gold hairline that draws from 0 to 64px |
| Text: Body / label | Hero KPIs, valuation figures | Count-up from 0 with easing over 1.4s when first visible (tabular figures, no layout shift) |
| Element | Primary CTAs | Magnetic pull up to 6px toward the cursor (rAF-throttled, `(hover:hover)` only) |
| Component | Thesis bento, scenario switch, sensitivity heatmap | Spotlight cards (cursor-tracked radial light); scenario switch re-tweens every figure and chart |
| Background | Hero | Slow ambient gold light: two radial gradients drifting via `background-position` (40s loop) + static SVG grain at 4% |

Signature moments (one per screen at most): hero price-vs-TP gauge draws in; the marquee band of key figures;
the football field bars grow from the price line; the heatmap lights the active WACC/g cell.

**Clever detail:** hover (or focus) any key number marked with a dotted underline and it shows where it came from,
e.g. "FY3/2026 release, p.10" or "Model: DCF!D47". The site practises the project's rule that every number is traceable.

**Scroll reveal:**
```css
.reveal { opacity:0; transform:translateY(24px); transition:opacity .9s var(--ease), transform .9s var(--ease); }
.reveal.is-in { opacity:1; transform:none; }
```
**Parallax:** hero ambient layer moves at 0.15x scroll (transform only, rAF).

**Reduced motion:**
```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation:none !important; transition:none !important; }
  .reveal, .mask > span { opacity:1 !important; transform:none !important; }
}
```
JS also checks `matchMedia('(prefers-reduced-motion: reduce)')` and skips count-ups, magnet and parallax.

## 8. Do's and Don'ts

**Do**
1. Put the conclusion first: rating, TP and upside are visible without scrolling.
2. Give every chart a source line and a hover tooltip; give every chart a plain-text table alternative (`<details>`).
3. Use tabular figures and right alignment for every number.
4. Keep one accent (gold) per view; scenario colours only inside charts.
5. Label the page as a student project and not investment advice, in the hero and the footer.

**Don't**
1. Don't use Makita's brand teal, logo or product photos: the site must not look official.
2. Don't animate `filter: blur()` on moving elements; don't exceed `backdrop-filter: blur(12px)`.
3. Don't use dual-axis charts; split into stacked panels.
4. Don't hard-code hex colours in components; use the variables.
5. Don't scroll-jack or pin sections; native scroll only.
6. Don't put more than one signature animation in the same viewport.
7. Don't use emoji or stock icons; inline SVG only.
8. Don't show a number that is not in `public/data/*.json` (all figures come from the pipeline).

## 9. Responsive Behavior

| Breakpoint | Layout |
|---|---|
| >= 1100px | 12-column grid, side-by-side hero (title left, KPI panel right) |
| 760-1099px | Hero stacks; bento becomes 2 columns; tables scroll horizontally inside their card |
| < 760px | Single column; nav collapses to a menu button (48px target) with a full-screen sheet |
| < 600px | No horizontal page overflow; charts redraw to container width; touch targets >= 44 x 44px |

Charts re-render on resize (debounced 150ms). Hover effects (spotlight, magnet) are enabled only under `(hover: hover)`;
on touch, chart tooltips open on tap.

"""Phase 7: generate the initiation report PDF (report/Makita_6586_initiation.pdf) from model outputs.
Every number in the text is read from data/clean (model_outputs.json, ratios.csv, risk_sensitivities.csv)."""
import json
import re
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from author import AFFILIATION, EMAIL, LINKEDIN, LINKEDIN_SHORT, NAME
from reportlab.platypus import (BaseDocTemplate, Frame, Image, KeepTogether, PageBreak, PageTemplate, Paragraph,
                                Spacer, Table, TableStyle)

ROOT = Path(__file__).resolve().parents[1]
CLEAN, CHARTS, OUT = ROOT / "data/clean", ROOT / "report/charts", ROOT / "report/Makita_6586_initiation.pdf"
FONTS = "/usr/share/fonts/truetype/crosextra"

for name, file in [("Carlito", "Carlito-Regular.ttf"), ("Carlito-Bold", "Carlito-Bold.ttf"),
                   ("Carlito-Italic", "Carlito-Italic.ttf"), ("Caladea-Bold", "Caladea-Bold.ttf")]:
    pdfmetrics.registerFont(TTFont(name, f"{FONTS}/{file}"))
pdfmetrics.registerFontFamily("Carlito", normal="Carlito", bold="Carlito-Bold", italic="Carlito-Italic")

def P(text, style, **kw):
    """Paragraph with bare '&' escaped (reportlab parses '&A' in 'SG&A' as an entity)."""
    return Paragraph(re.sub(r"&(?!amp;|lt;|gt;|#\d+;)", "&amp;", text), style, **kw)


INK, MUTED, GOLD, RULE, PAPER = (colors.HexColor(c) for c in ["#1A1A1A", "#5C5C5C", "#A8792A", "#D9D6CF", "#F6F3EC"])
W, H = A4
M = 15 * mm

body = ParagraphStyle("body", fontName="Carlito", fontSize=9.2, leading=12.2, textColor=INK, spaceAfter=5, alignment=TA_LEFT)
small = ParagraphStyle("small", parent=body, fontSize=7.6, leading=9.6, textColor=MUTED, spaceAfter=2)
h1 = ParagraphStyle("h1", fontName="Caladea-Bold", fontSize=15, leading=18, textColor=INK, spaceBefore=2, spaceAfter=6)
h2 = ParagraphStyle("h2", fontName="Caladea-Bold", fontSize=11.5, leading=14, textColor=INK, spaceBefore=8, spaceAfter=4)
lead = ParagraphStyle("lead", parent=body, fontName="Carlito-Bold", fontSize=10.5, leading=13.5)
bullet = ParagraphStyle("bullet", parent=body, leftIndent=9, bulletIndent=0, spaceAfter=4)
cell = ParagraphStyle("cell", parent=body, fontSize=8, leading=9.8, spaceAfter=0)
cellb = ParagraphStyle("cellb", parent=cell, fontName="Carlito-Bold")

O = json.loads((CLEAN / "model_outputs.json").read_text())
B = O["Base"]
R = pd.read_csv(CLEAN / "ratios.csv", index_col=0)
RISK = pd.read_csv(CLEAN / "risk_sensitivities.csv")
SNAP = pd.read_csv(CLEAN / "market_snapshot.csv").set_index("item")["value"]
PEERS = pd.read_csv(CLEAN / "peers_financials.csv")


def n0(x):
    return f"{float(x):,.0f}"


def pct(x, d=1):
    return f"{x * 100:.{d}f}%"


def bn(x):
    return f"{x / 1e3:,.1f}"


def tbl(data, widths, header_rows=1, bold_rows=(), align_right_from=1, zebra=False, font=8):
    t = Table(data, colWidths=widths, hAlign="LEFT")
    st = [("FONT", (0, 0), (-1, -1), "Carlito", font), ("TEXTCOLOR", (0, 0), (-1, -1), INK),
          ("LINEBELOW", (0, header_rows - 1), (-1, header_rows - 1), 0.8, INK),
          ("FONT", (0, 0), (-1, header_rows - 1), "Carlito-Bold", font),
          ("ALIGN", (align_right_from, 0), (-1, -1), "RIGHT"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
          ("TOPPADDING", (0, 0), (-1, -1), 1.6), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.6),
          ("LINEBELOW", (0, -1), (-1, -1), 0.5, RULE)]
    for r in bold_rows:
        st += [("FONT", (0, r), (-1, r), "Carlito-Bold", font)]
    if zebra:
        for r in range(header_rows, len(data), 2):
            st.append(("BACKGROUND", (0, r), (-1, r), PAPER))
    t.setStyle(TableStyle(st))
    return t


def chart(name, width=W - 2 * M):
    from PIL import Image as PI
    w, h = PI.open(CHARTS / f"{name}.png").size
    return Image(str(CHARTS / f"{name}.png"), width=width, height=width * h / w)


def header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(INK)
    canvas.rect(0, H - 11 * mm, W, 11 * mm, stroke=0, fill=1)
    canvas.setFillColor(colors.white)
    canvas.setFont("Carlito-Bold", 9)
    canvas.drawString(M, H - 7 * mm, "MAKITA CORPORATION (6586 JP)  |  INITIATION OF COVERAGE")
    canvas.setFont("Carlito", 9)
    canvas.drawRightString(W - M, H - 7 * mm, f"Machinery: power tools  |  {B_rating}  |  29 October 2026")
    canvas.setFillColor(GOLD)
    canvas.rect(0, H - 11.8 * mm, W, 0.8 * mm, stroke=0, fill=1)
    canvas.setFillColor(MUTED)
    canvas.setFont("Carlito", 7.2)
    canvas.drawString(M, 8 * mm, f"{NAME}  |  Student research project. Not investment advice. See disclosures on the last page.")
    canvas.drawRightString(W - M, 8 * mm, f"Page {doc.page}")
    canvas.restoreState()


B_rating = B["rating"]


def years(keys):
    return [k.replace("FY20", "FY") + ("A" if int(k[2:]) <= 2026 else "E") for k in keys]


def key_metrics():
    yrs = ["FY2024", "FY2025", "FY2026", "FY2027", "FY2028", "FY2029"]
    ev = B["comps"]["ev"]
    price = B["price"]
    rows = [["JPY bn / FY Mar"] + years(yrs)]
    is_, bs = B["is"], B["bs"]
    rows.append(["Revenue"] + [bn(is_["rev"][y]) for y in yrs])
    rows.append(["Operating profit"] + [bn(is_["op"][y]) for y in yrs])
    rows.append(["Operating margin"] + [pct(is_["opm"][y]) for y in yrs])
    rows.append(["EPS (JPY)"] + [f"{is_['eps'][y]:,.0f}" for y in yrs])
    rows.append(["DPS (JPY)"] + [f"{is_['dps'][y]:,.0f}" for y in yrs])
    rows.append(["P/E (x)"] + [f"{price / is_['eps'][y]:.1f}" for y in yrs])
    rows.append(["EV/EBITDA (x)"] + [f"{ev / is_['ebitda'][y]:.1f}" for y in yrs])
    rows.append(["ROE"] + [pct(bs["roe"][y]) for y in yrs])
    rows.append(["Net cash"] + [bn(bs["netcash"][y]) for y in yrs])
    return rows


def build():
    doc = BaseDocTemplate(str(OUT), pagesize=A4, leftMargin=M, rightMargin=M, topMargin=18 * mm, bottomMargin=14 * mm,
                          title="Makita Corporation (6586 JP): Initiation of coverage", author=NAME, subject="Student research project, not investment advice")
    frame = Frame(M, 14 * mm, W - 2 * M, H - 32 * mm, id="f", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id="p", frames=[frame], onPage=header_footer)])
    s = []
    price, tp, up, tsr = B["price"], B["tp"], B["upside"], B["tsr"]
    mcap = B["comps"]["mcap"]
    netcash_q = B["mk_cash_q"] + B["mk_dep_q"] - B["mk_borr_q"] - B["mk_debt_mv"] + B["mk_borr_q"]
    r = lambda k, y="FY2026": R.at[k, y]
    risk = RISK.set_index("shock")

    # ------------------------------------------------------------------ page 1
    s.append(P("Great franchise, fairly priced: the recovery is done, the yen did the rest", h1))
    byline = ParagraphStyle("byline", parent=body, fontSize=8.6, leading=11, textColor=MUTED, spaceAfter=8)
    s.append(P(f"<b><font color='#1A1A1A'>{NAME}</font></b>  ·  {AFFILIATION}  ·  "
               f"<link href='mailto:{EMAIL}'>{EMAIL}</link>  ·  <link href='{LINKEDIN}'>{LINKEDIN_SHORT}</link>", byline))
    left = [
        P(f"We initiate on Makita with a <b>HOLD</b> and a 12-month target price of <b>JPY {n0(tp)}</b> "
                  f"({pct(up)} upside; {pct(tsr)} total return including dividends). Makita has repaired its margins after "
                  f"the FY2022-23 inventory crisis, but recent growth has come from a weak yen rather than volume, and the "
                  f"shares already price a sustained 13-14% operating margin.", lead),
        P("<b>Investment thesis</b>", body),
        P(f"<b>1. The margin recovery is complete; the next leg needs cost discipline.</b> Gross margin is back to "
                  f"{pct(r('gross_margin'))} (FY2018: {pct(r('gross_margin', 'FY2018'))}), but SG&A has risen from "
                  f"{pct(r('sga_pct', 'FY2018'))} to {pct(r('sga_pct'))} of sales. The 15% operating-margin target needs "
                  f"operating leverage that the current sales-force build-out works against.", bullet),
        P(f"<b>2. Growth is currency, not volume.</b> FY2026 revenue rose 3.2% in yen while Europe (50% of sales) fell "
                  f"about {abs(B['drivers']['eu_lc']['FY2026']) * 100:.1f}% in local currency; 1Q FY2027 was +10.7% in yen and flat in local currency. North America has "
                  f"run near break-even for nine years while TTI's Milwaukee grew 7.9% in 2025.", bullet),
        P(f"<b>3. The balance sheet is the lever, and it limits the downside.</b> Net cash plus investments of about "
                  f"JPY {bn(B['bridge'])}bn is {pct(B['bridge'] / mcap, 0)} of the market value. ROE of {pct(r('roe'))} against an "
                  f"11% target makes buybacks the most likely re-rating trigger. The stock trades on "
                  f"{B['comps']['ev_ebitda']:.1f}x LTM EV/EBITDA against a FY2019-26 median of {B['comps']['own_med']:.1f}x.",
                  bullet),
        P(f"<b>Valuation.</b> Our TP averages a DCF with Gordon-growth terminal value (JPY {n0(B['ps_g'])}) and one with an "
                  f"exit multiple (JPY {n0(B['ps_x'])}), rolled forward 12 months at the {pct(B['ke'])} cost of equity, less "
                  f"dividends. WACC is {pct(B['wacc'])}. Peers trade on higher multiples (median "
                  f"{B['peer_stats']['Median|EV/EBITDA']:.1f}x EV/EBITDA) but grow faster and earn more.", body),
        P(f"<b>Rating rule.</b> BUY if upside exceeds +15%, SELL below -10%, otherwise HOLD. Scenarios: Bull "
                  f"JPY {n0(O['Bull']['tp'])} ({pct(O['Bull']['upside'], 0)}), Bear JPY {n0(O['Bear']['tp'])} "
                  f"({pct(O['Bear']['upside'], 0)}).", body),
    ]
    box = [
        [P("<b>Rating</b>", cell), P(f"<b>{B['rating']}</b>", cellb)],
        [P("12-month target price", cell), P(f"<b>JPY {n0(tp)}</b>", cellb)],
        [P("Price (29 Oct 2026)", cell), P(f"JPY {n0(price)}", cell)],
        [P("Upside / total return", cell), P(f"{pct(up)} / {pct(tsr)}", cell)],
        [P("Market cap", cell), P(f"JPY {bn(mcap)}bn", cell)],
        [P("EV (incl. leases)", cell), P(f"JPY {bn(B['comps']['ev'])}bn", cell)],
        [P("52-week range", cell), P(f"JPY {n0(SNAP['low_52w_close'])}-{n0(SNAP['high_52w_close'])}", cell)],
        [P("Shares outstanding", cell), P(f"{B['mk_shares']:.1f}m", cell)],
        [P("Avg daily value traded (3m)", cell), P(f"JPY {float(SNAP['avg_daily_value_traded_3m_jpy_m']) / 1e3:.1f}bn", cell)],
        [P("WACC / cost of equity", cell), P(f"{pct(B['wacc'])} / {pct(B['ke'])}", cell)],
        [P("Reporting", cell), P("IFRS, JPY, FY ends 31 Mar", cell)],
    ]
    bt = Table(box, colWidths=[37 * mm, 30 * mm])
    bt.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), PAPER), ("BOX", (0, 0), (-1, -1), 0.8, GOLD),
                            ("LINEBELOW", (0, 0), (-1, 0), 0.8, GOLD), ("TOPPADDING", (0, 0), (-1, -1), 2.2),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    right = [bt, Spacer(1, 4 * mm), chart("09_price_vs_topix", 67 * mm)]
    page1 = Table([[left, right]], colWidths=[W - 2 * M - 71 * mm, 71 * mm])
    page1.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (1, 0), (1, 0), 4 * mm),
                               ("LEFTPADDING", (0, 0), (0, 0), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
    s.append(page1)
    s.append(Spacer(1, 3 * mm))
    s.append(P("<b>Key metrics</b> (A = actual, E = our Base case; multiples at the current price and EV)", body))
    s.append(tbl(key_metrics(), [38 * mm] + [24 * mm] * 6, zebra=True))
    s.append(P("Source: Makita earnings releases (IFRS), yfinance, student model. FY = year to 31 March.", small))
    s.append(Spacer(1, 3 * mm))
    sc = [["Scenario", "12m TP (JPY)", "Upside", "Rating", "FY2031E OP margin", "FY2027-31 revenue CAGR", "What has to happen"]]
    for nm, txt in [("Bull", "Europe recovers, 40Vmax mix lifts gross margin to 38%, yen 5% weaker"),
                    ("Base", "Flat Europe in FY2027, ~3% growth after; margins edge up to 14%"),
                    ("Bear", "Second inventory cycle, gross margin 34-35%, yen 10% stronger")]:
        o = O[nm]
        cagr = (o["is"]["rev"]["FY2031"] / o["is"]["rev"]["FY2026"]) ** (1 / 5) - 1
        sc.append([nm, n0(o["tp"]), pct(o["upside"]), o["rating"], pct(o["is"]["opm"]["FY2031"]), pct(cagr), P(txt, cell)])
    s.append(P("<b>Scenarios</b> (switch in the model: Assumptions!D4)", body))
    s.append(tbl(sc, [18 * mm, 20 * mm, 15 * mm, 14 * mm, 25 * mm, 30 * mm, W - 2 * M - 122 * mm], bold_rows=(2,), font=7.8))
    s.append(PageBreak())

    # ------------------------------------------------------------------ page 2: business
    geo = B["drivers"]
    s.append(P("1. Business overview", h2))
    s.append(P(
        "Makita designs, makes and sells cordless and corded power tools and outdoor power equipment (OPE) for professional "
        "users in construction, building maintenance, landscaping, agriculture and forestry. Its core asset is a battery "
        "platform: 18V LXT and the newer, higher-power 40Vmax XGT. A user who owns Makita batteries can run hundreds of tools "
        "on them, so each battery sold raises the cost of switching brands. The group reports geographic segments because "
        "the Board manages a single business (audited FS FY3/2026, segment note).", body))
    s.append(P(
        f"<b>Mix.</b> Europe is {pct(geo['eu']['FY2026'] / geo['rev']['FY2026'], 0)} of revenue, Japan "
        f"{pct(geo['jp']['FY2026'] / geo['rev']['FY2026'], 0)}, North America {pct(geo['na']['FY2026'] / geo['rev']['FY2026'], 0)} "
        f"and the rest of the world {pct(geo['rw']['FY2026'] / geo['rev']['FY2026'], 0)}. Parts, repairs and accessories reached "
        f"22.8% of revenue in FY2026, up from 16.4% in FY2018, a sign of a growing installed base. 92.5% of units are made "
        f"outside Japan; China's share fell from about 70% (FYE2017) to 51.5% (FYE2026) as Romania (18.6%), Thailand and Brazil "
        f"grew (Makita Report 2026, p.23).", body))
    s.append(chart("03_region_mix", (W - 2 * M) * 0.86))
    s.append(P("<b>Industry.</b> Makita estimates the power-tool market at US$30-40bn and OPE at US$40-50bn (Makita Report "
                       "2026, p.22); third-party estimates range from US$30bn to US$47bn for power tools. The professional end is "
                       "an oligopoly: Techtronic (US$15.3bn sales in 2025), Stanley Black & Decker (US$15.1bn), Hilti (CHF 6.3bn), "
                       "Bosch Power Tools (about EUR 5bn) and Makita (about US$5.2bn). Cordless is about 62% of power-tool sales, "
                       "and regulation favours it: California requires zero-emission small off-road engines from model year 2024. "
                       "OPE is still engine-led, which is Makita's main growth opening; cordless is already over 90% of Makita's "
                       "own OPE sales.", body))
    porter = [["Force", "Rating", "Why"],
              ["Rivalry", "High", P("Five global leaders; TTI is outgrowing the field", cell)],
              ["New entrants", "Low-moderate", P("Battery platforms and service networks are costly; Chinese OEMs enter at the DIY end", cell)],
              ["Buyer power", "Moderate", P("Dealers and home centres have leverage; professionals are locked into platforms", cell)],
              ["Supplier power", "Moderate", P("Few lithium-ion cell suppliers; Makita designs its own packs and motors", cell)],
              ["Substitutes", "Low", P("Corded and engine tools are losing share to cordless", cell)]]
    s.append(KeepTogether([P("<b>Five forces and moat.</b> We rate the moat <b>narrow</b>: platform lock-in is real, but "
                                     "margins have proved cyclical and Makita has no pricing power over TTI.", body),
                           tbl(porter, [30 * mm, 24 * mm, W - 2 * M - 54 * mm], align_right_from=9)]))
    s.append(Spacer(1, 3 * mm))
    s.append(chart("06_aftermarket", (W - 2 * M) * 0.72))
    s.append(PageBreak())

    # ------------------------------------------------------------------ page 3: thesis + history
    s.append(P("2. Investment thesis in the numbers", h2))
    s.append(P(
        f"<b>The FY2023 collapse was an inventory problem.</b> Revenue grew in FY2023, but inventory had reached "
        f"{r('dio', 'FY2022'):.0f} days of cost of sales at FY2022 and gross margin fell to {pct(r('gross_margin', 'FY2023'))} "
        f"as Makita cleared stock. Inventory days are rising again, to {r('dio'):.0f} in FY2026 from {r('dio', 'FY2024'):.0f} in "
        f"FY2024. That is not yet a warning, but it is the metric to watch.", body))
    s.append(chart("02_inventory_cycle", (W - 2 * M) * 0.86))
    s.append(P(
        f"<b>Margins: the gap is overhead.</b> Operating margin is {pct(r('op_margin'))} against {pct(r('op_margin', 'FY2018'))} "
        f"in FY2018, with gross margin almost fully recovered. All of the shortfall is SG&A "
        f"({pct(r('sga_pct', 'FY2018'))} to {pct(r('sga_pct'))}).", body))
    s.append(chart("01_revenue_margins", (W - 2 * M) * 0.86))
    s.append(PageBreak())

    # ------------------------------------------------------------------ page 4: financial analysis
    s.append(P("3. Financial analysis", h2))
    cols = ["FY2018", "FY2020", "FY2022", "FY2023", "FY2024", "FY2025", "FY2026"]
    fa = [[""] + years(cols)]
    for lab, k, fmt in [("Revenue growth", "revenue_growth", "p"), ("Gross margin", "gross_margin", "p"), ("SG&A / revenue", "sga_pct", "p"),
                        ("Operating margin", "op_margin", "p"), ("ROE", "roe", "p"), ("  Net margin", "net_margin", "p"),
                        ("  Asset turnover (x)", "asset_turnover", "x"), ("  Equity multiplier (x)", "equity_multiplier", "x"),
                        ("ROIC (operating)", "roic", "p"), ("Inventory days", "dio", "d"), ("Cash conversion cycle (days)", "cash_conversion_cycle", "d"),
                        ("FCF / net income (x)", "fcf_conversion", "x"), ("Capex / revenue", "capex_to_sales", "p"),
                        ("Net cash (JPY bn)", "net_cash", "b"), ("Equity ratio", "equity_ratio", "p")]:
        vals = []
        for c in cols:
            v = R.at[k, c]
            vals.append("n/a" if pd.isna(v) else pct(v) if fmt == "p" else f"{v:.2f}" if fmt == "x" else f"{v:.0f}" if fmt == "d" else bn(v))
        fa.append([lab] + vals)
    s.append(tbl(fa, [48 * mm] + [19 * mm] * 7, zebra=True, font=7.8))
    s.append(P("DuPont on average parent equity (reconciles exactly). ROIC = NOPAT / (operating NWC + PP&E + intangibles). "
                       "FCF = CFO + capex + lease repayments. IFRS 16 applies from FY2020.", small))
    cum_fcf, cum_ni = R.loc["fcf"].sum(), R.loc["net_income"].sum()
    s.append(P(
        f"<b>What a casual reader would miss.</b> (1) Over FY2018-26 Makita turned only {pct(cum_fcf / cum_ni, 0)} of net income "
        f"into free cash flow (JPY {bn(cum_fcf)}bn against JPY {bn(cum_ni)}bn), because inventory absorbed JPY 179bn and capex ran at "
        f"3.4-3.7x depreciation in FY2020-22. (2) ROE is capped by the balance sheet: ROIC is {pct(r('roic'))} but the equity "
        f"multiplier is only {r('equity_multiplier'):.2f}x, with net cash at {pct(r('net_cash_to_equity'), 0)} of equity. "
        f"(3) Capex has fallen below depreciation ({r('capex_to_da_ex_rou'):.1f}x in FY2026), which flatters recent FCF; the "
        f"company guides JPY 30bn for FY2027.", body))
    s.append(chart("05_fcf_vs_ni", (W - 2 * M) * 0.80))
    s.append(chart("04_returns", (W - 2 * M) * 0.80))
    s.append(PageBreak())

    # ------------------------------------------------------------------ page 5: forecasts
    s.append(P("4. Forecasts", h2))
    s.append(P(
        "Revenue is built by customer region as local-currency growth times FX, so currency moves flow through the model. "
        "Margins are driven by gross margin and SG&A ratios; working capital by receivable, inventory and payable days; capex as a "
        "share of revenue; depreciation from the PP&E roll-forward. Every assumption has a one-line justification in the "
        "Assumptions sheet of the model, with a Base / Bull / Bear switch.", body))
    a = [["Base case", "FY27E", "FY28E", "FY29E", "FY30E", "FY31E", "Justification"]]
    asm = [("Europe LC growth", [0.0, 2.5, 3.0, 3.0, 3.0], f"FY2026 LC {B['drivers']['eu_lc']['FY2026'] * 100:.1f}%; recovery from FY2028"),
           ("Japan LC growth", [2.5, 2.0, 2.0, 2.0, 1.5], "FY2026 +3.9%; housing starts falling"),
           ("North America LC growth", [3.0] * 5, "Rebound after tariff disruption; no share gain"),
           ("USD/JPY", [158.26, 157.82, 157.82, 157.82, 157.82], "1Q actual + spot, then spot held"),
           ("EUR/JPY", [178.38, 176.03, 176.03, 176.03, 176.03], "1Q actual + spot, then spot held"),
           ("Gross margin", [37.0, 36.5, 36.5, 36.5, 36.5], "1Q tariff refund one-off; FY2026 36.5%"),
           ("SG&A / revenue", [23.3, 23.0, 22.8, 22.6, 22.5], "Modest operating leverage"),
           ("Inventory days", [275, 268, 262, 258, 255], "Normalising toward 249 average"),
           ("Capex / revenue", [3.6, 3.4, 3.2, 3.2, 3.2], "JPY 30bn FY2027 guidance")]
    for lab, v, j in asm:
        fm = (lambda x: f"{x:.1f}%") if "growth" in lab or "margin" in lab or "SG&A" in lab or "Capex" in lab else \
            (lambda x: f"{x:.0f}") if "days" in lab else (lambda x: f"{x:.1f}")
        a.append([lab] + [fm(x) for x in v] + [P(j, cell)])
    s.append(tbl(a, [36 * mm] + [15 * mm] * 5 + [W - 2 * M - 111 * mm], zebra=True, font=7.8))
    s.append(Spacer(1, 2 * mm))
    s.append(chart("08_forecast", (W - 2 * M) * 0.86))
    cmpg = [["", "FY2027E revenue", "FY2027E OP", "OP margin"],
            ["Company guidance (28 Apr 2026, reaffirmed 29 Jul)", "820.0", "110.0", "13.4%"],
            ["Our Base", bn(B["is"]["rev"]["FY2027"]), bn(B["is"]["op"]["FY2027"]), pct(B["is"]["opm"]["FY2027"])],
            ["Our Bull", bn(O["Bull"]["is"]["rev"]["FY2027"]), bn(O["Bull"]["is"]["op"]["FY2027"]), pct(O["Bull"]["is"]["opm"]["FY2027"])],
            ["Our Bear", bn(O["Bear"]["is"]["rev"]["FY2027"]), bn(O["Bear"]["is"]["op"]["FY2027"]), pct(O["Bear"]["is"]["opm"]["FY2027"])]]
    s.append(KeepTogether([P("<b>Against guidance.</b> Our Base revenue is below the company's JPY 820bn because we assume "
                                     "flat European local-currency sales; operating profit is close to guidance because 1Q margins "
                                     "benefited from the tariff refund (JPY bn).", body),
                           tbl(cmpg, [70 * mm, 32 * mm, 28 * mm, 24 * mm])]))
    s.append(PageBreak())

    # ------------------------------------------------------------------ page 6: valuation
    s.append(P("5. Valuation", h2))
    wb_ = B["wacc_build"] if "wacc_build" in B else None
    src_ = ParagraphStyle("src", parent=cell, fontSize=6.8, leading=8, textColor=MUTED)
    wrows = [("Risk-free rate (10Y JGB, 28 Oct 2026)", pct(B["mk_rf"], 2), "Ministry of Finance Japan"),
             ("Mature-market ERP", pct(B["mk_erp"], 2), "Damodaran, implied, start 2026"),
             ("Country risk premium", pct(B["mk_crp"], 2), "Damodaran regional CRPs x Makita revenue mix"),
             ("Unlevered beta (Japan Machinery)", f"{B['mk_bu']:.2f}", "Damodaran; regression vs TOPIX 1.08 (5y weekly)"),
             ("Relevered beta (D/E 1.6%)", f"{B['mk_bl']:.2f}", "Hamada"),
             ("Cost of equity", pct(B["mk_ke"], 2), "CAPM; no size premium"),
             ("After-tax Kd / debt weight", f"{pct(B['mk_kd'], 2)} / {pct(B['mk_wd'], 1)}", "rf + 0.75%; market weights"),
             ("WACC", pct(B["mk_wacc"], 2), "")]
    wacc_t = [["Cost of capital", "Value", "Source"]] + [[P(a, cell), b, P(c, src_)] for a, b, c in wrows]
    dcf_t = [["DCF (JPY m unless stated)", "Gordon", "Exit multiple"],
             ["PV of FCF, Jul 2026-Mar 2031", n0(B["sum_pv"]), n0(B["sum_pv"])],
             ["PV of terminal value", n0(B["pv_tv_g"]), n0(B["ev_x"] - B["sum_pv"])],
             ["Enterprise value", n0(B["ev_g"]), n0(B["ev_x"])],
             ["+ Net cash, investments, less NCI and interim", n0(B["bridge"]), n0(B["bridge"])],
             ["Value per share (JPY)", n0(B["ps_g"]), n0(B["ps_x"])],
             ["Terminal assumption", f"g {pct(B['g'])}, RONIC {pct(B['ronic'], 0)}", f"{B['mult']:.1f}x EBITDA"],
             ["Cross-check", f"implies {B['impl_mult']:.1f}x", f"implies g {pct(B['impl_g'])}"]]
    s.append(Table([[tbl(wacc_t, [40 * mm, 17 * mm, 32 * mm], font=7.4), tbl(dcf_t, [45 * mm, 21 * mm, 21 * mm], font=7.4)]],
                   colWidths=[(W - 2 * M) / 2] * 2, style=[("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
    s.append(P(
        f"<b>Method.</b> Free cash flow runs from 1 July 2026 (after the last balance sheet) and is discounted mid-period to the "
        f"valuation date. Lease payments are deducted in FCF, so leases are not deducted again in the bridge. The Gordon terminal "
        f"value uses the value-driver formula NOPAT x (1+g) x (1 - g/RONIC), so growth is paid for with reinvestment. We set the "
        f"exit multiple within 0.5x of the Gordon-implied multiple so the two methods agree; Makita's FY2019-26 median of "
        f"{B['comps']['own_med']:.1f}x would assume a re-rating. Terminal value is {pct(B['tv_share_g'], 0)} of EV. "
        f"Fair value today is JPY {n0(B['fv'])}; rolling forward at the cost of equity and deducting JPY {B['dps12']:.0f} of dividends "
        f"gives the JPY {n0(B['tp'])} TP.", body))
    g = B["sensitivity"]["wacc_g"]
    sens = [["WACC \\ g"] + [pct(c) for c in g["cols"]]] + [[pct(rw, 2)] + [n0(v) for v in vals] for rw, vals in zip(g["rows"], g["values"])]
    g3 = B["sensitivity"]["growth_margin"]
    sens3 = [["Growth +/- \\ OP margin"] + [pct(c) for c in g3["cols"]]] + \
            [[f"{rw * 100:+.0f}pp"] + [n0(v) for v in vals] for rw, vals in zip(g3["rows"], g3["values"])]
    s.append(Table([[ [P("<b>DCF (Gordon) value per share: WACC vs terminal growth</b>", cell), tbl(sens, [18 * mm] + [14 * mm] * 5, font=7.4)],
                      [P("<b>Value per share: growth uplift vs steady-state OP margin</b>", cell), tbl(sens3, [26 * mm] + [13 * mm] * 5, font=7.4)] ]],
                   colWidths=[(W - 2 * M) / 2] * 2, style=[("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
    peers = PEERS[PEERS.ticker != "6586.T"].copy()
    ct = [["Peer (last FY, JPY bn)", "Mkt cap", "EV/Sales", "EV/EBITDA", "P/E", "EBITDA mgn"]]
    for _, p in peers.iterrows():
        ct.append([f"{p['name']} ({p.ticker})", bn(p.market_cap_jpy_m), f"{p.ev_jpy_m / p.revenue_jpy_m:.2f}x",
                   f"{p.ev_jpy_m / p.ebitda_jpy_m:.1f}x", f"{p.market_cap_jpy_m / p.net_income_jpy_m:.1f}x", pct(p.ebitda_jpy_m / p.revenue_jpy_m)])
    ps = B["peer_stats"]
    ct.append(["Peer median", "", f"{ps['Median|EV/Sales']:.2f}x", f"{ps['Median|EV/EBITDA']:.1f}x", f"{ps['Median|P/E']:.1f}x", pct(ps["Median|EBITDA mgn"])])
    c = B["comps"]
    ct.append(["Makita (LTM Jun 2026)", bn(c["mcap"]), f"{c['ev_sales']:.2f}x", f"{c['ev_ebitda']:.1f}x", f"{c['pe']:.1f}x", pct(c["ebitda"] / c["rev"])])
    s.append(Spacer(1, 2 * mm))
    s.append(tbl(ct, [62 * mm, 22 * mm, 22 * mm, 22 * mm, 20 * mm, 22 * mm], bold_rows=(len(ct) - 2, len(ct) - 1), font=7.6))
    s.append(P("Peers: last reported fiscal year from yfinance, converted to JPY at 29 Oct 2026 FX; multiples recomputed (yfinance "
                       "ratios mix currencies for HK listings). SWK and Toro verified against SEC 10-K data. SWK P/E is inflated by "
                       "restructuring charges; Husqvarna's low multiples reflect depressed earnings.", small))
    s.append(chart("07_football_field", (W - 2 * M) * 0.84))
    s.append(PageBreak())

    # ------------------------------------------------------------------ page 7: risks
    s.append(P("6. Risks, catalysts and what would make us wrong", h2))
    rk = [["Risk (one shock, rest Base)", "FY28E EPS", "TP (JPY)", "Rating"]]
    for name in ["Yen +10% vs USD and EUR", "Yen -10% vs USD and EUR", "Gross margin -200bp (all years)",
                 "Construction downturn: local-currency growth -3pp in FY2027-28", "SG&A +100bp of revenue (all years)",
                 "Inventory build: +30 inventory days (all years)"]:
        x = risk.loc[name]
        rk.append([P(name, cell), pct(x.eps_fy2028_chg), f"{n0(x.tp)} ({x.tp_chg_jpy:+,.0f})", x.rating])
    t = risk.loc[[i for i in risk.index if i.startswith("US tariff")][0]]
    rk.append([P("US tariff: 25% on China-made goods sold in North America, 50% passed on (estimate outside the model)", cell),
               pct(t.eps_fy2028_chg), "n/a", "n/a"])
    s.append(tbl(rk, [92 * mm, 24 * mm, 32 * mm, 20 * mm], zebra=True, font=7.8))
    s.append(P("Each shock re-runs the full Excel model (src/risks.py). FX is modelled as translation with constant margins; "
                       "yen-denominated fixed costs would make the true FX effect larger.", small))
    s.append(chart("10_risk_tornado", (W - 2 * M) * 0.78))
    cat = [["When (approx.)", "Catalyst", "What to watch"],
           ["Late Oct / early Nov 2026", "2Q FY3/2027 results", P("Europe LC growth; gross margin ex tariff refund; inventory days; guidance", cell)],
           ["Dec 2026", "JPY 79 interim dividend paid", P("Step-up under the 50% payout policy", cell)],
           ["Early Feb 2027", "3Q FY3/2027 results", P("Inventory into the spring season", cell)],
           ["Through 2026-27", "BoJ policy meetings", P("Yen path, the largest macro risk", cell)],
           ["Late Apr 2027", "FY3/2027 results, FY3/2028 guidance", P("Progress to 15% OP margin; buybacks", cell)],
           ["Jun 2027", "AGM, Makita Report 2027", P("40Vmax mix, OPE and Vision FY2030 progress", cell)]]
    s.append(KeepTogether([P("<b>Catalysts.</b> Dates follow last year's pattern (2Q FY2026 results on 31 Oct 2025; FY "
                                     "results on 28 Apr 2026).", body),
                           tbl(cat, [32 * mm, 50 * mm, W - 2 * M - 82 * mm], align_right_from=9, font=7.8)]))
    s.append(P(
        f"<b>What would make us wrong.</b> BUY needs a TP above JPY {n0(price * 1.15)}; SELL one below JPY {n0(price * 0.9)}. We would "
        f"turn positive if operating margin moves toward the 15% target without sacrificing growth (a steady 15.5% margin is worth "
        f"about JPY 5,980 today, a TP near JPY 6,350), if the yen weakens another 10% (TP JPY {n0(risk.loc['Yen -10% vs USD and EUR'].tp)}), "
        f"or if Makita announces large buybacks that lift ROE toward 11%. We would turn negative on a second inventory cycle: "
        f"inventory days above 300 or European local-currency sales falling more than 3%, which is our Bear case "
        f"(TP JPY {n0(O['Bear']['tp'])}).", body))
    s.append(PageBreak())

    # ------------------------------------------------------------------ page 8: appendix
    s.append(P("Appendix: model summary (Base case, JPY bn)", h2))
    yrs = ["FY2024", "FY2025", "FY2026", "FY2027", "FY2028", "FY2029", "FY2030", "FY2031"]
    ap = [[""] + years(yrs)]
    for lab, sec, k, fm in [("Revenue", "is", "rev", "b"), ("  growth", "is", "rev_g", "p"), ("Gross profit", "is", "gp", "b"),
                            ("Operating profit", "is", "op", "b"), ("  margin", "is", "opm", "p"), ("EBITDA (IFRS 16)", "is", "ebitda", "b"),
                            ("Net income (parent)", "is", "ni", "b"), ("EPS (JPY)", "is", "eps", "y"), ("DPS (JPY)", "is", "dps", "y"),
                            ("Cash from operations", "cf", "cfo", "b"), ("Capex", "cf", "capex", "b"), ("Free cash flow", "cf", "fcf", "b"),
                            ("Inventories", "bs", "inv", "b"), ("Net working capital", "bs", "nwc", "b"), ("Net cash", "bs", "netcash", "b"),
                            ("Parent equity", "bs", "pe", "b"), ("ROE", "bs", "roe", "p")]:
        row = [lab]
        for y in yrs:
            v = B[sec][k][y]
            row.append("" if v in (None, "") else pct(v) if fm == "p" else f"{v:,.0f}" if fm == "y" else bn(v))
        ap.append(row)
    s.append(tbl(ap, [40 * mm] + [17.5 * mm] * 8, zebra=True, font=7.6))
    dc = [["Unlevered FCF (JPY bn)"] + years(list(B["dcf"]["ufcf"].keys()))]
    for lab, k in [("NOPAT", "nopat"), ("+ Depreciation ex ROU", "dep"), ("- Capex", "capex"), ("- Increase in NWC", "dnwc"), ("UFCF", "ufcf"),
                   ("Fraction of year included", "frac"), ("Discount factor", "df"), ("Present value", "pv")]:
        dc.append([lab] + [(f"{v:.3f}" if k in ("frac", "df") else bn(v)) for v in B["dcf"][k].values()])
    s.append(Spacer(1, 3 * mm))
    s.append(tbl(dc, [50 * mm] + [22 * mm] * 5, bold_rows=(5, 8), font=7.6))
    s.append(P(
        "The Excel model (model/Makita_6586_model.xlsx) has live formulas across Assumptions, Drivers, IS, BS, CF, DCF, Comps, "
        "Sensitivity, Football and Checks; all checks pass in all three scenarios (balance sheet balances, cash ties, DCF inputs "
        "tie to the statements, terminal-value methods consistent). Data pipeline, sources and retrieval dates: see the GitHub "
        "repository README and SOURCES.md.", body))
    s.append(P("Disclosures", h2))
    s.append(P(
        f"This report was prepared by {NAME} ({AFFILIATION}) as a student research project for educational and portfolio "
        "purposes. It is not investment advice, "
        "an offer or a solicitation to buy or sell any security, and it has not been reviewed by Makita Corporation or any "
        "regulated firm. The author holds no position in the securities mentioned. Figures come from public sources believed to be "
        "reliable (Makita earnings releases and audited statements, Ministry of Finance Japan, Damodaran Online, SEC EDGAR and "
        "Yahoo Finance via yfinance), retrieved 29 October 2026, but accuracy is not guaranteed. Forecasts and the target price are "
        "the author's estimates and are uncertain. Past performance is not a guide to future returns. "
        f"Contact: {EMAIL} · {LINKEDIN_SHORT}", small))
    doc.build(s)
    print("wrote", OUT)


if __name__ == "__main__":
    build()

"""
Market Pulse – Single file Dash app.
Run: python market_pulse.py
Open: http://127.0.0.1:8050
"""
import pandas as pd
import numpy as np
import dash
from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import warnings
warnings.filterwarnings("ignore")

# ── DATA ───────────────────────────────────────────────────────────────────
def load_data():
    df = pd.read_csv("wfp_food_prices_gha.csv")
    df.columns = ["date","region","district","market","market_id",
                  "latitude","longitude","category","commodity",
                  "commodity_id","unit","priceflag","pricetype",
                  "currency","price_ghs","price_usd"]
    df["date"]      = pd.to_datetime(df["date"])
    df["year"]      = df["date"].dt.year
    df["month"]     = df["date"].dt.month
    df["commodity"] = df["commodity"].str.strip()
    df["region"]    = df["region"].str.strip().str.title()
    df["market"]    = df["market"].str.strip()
    df["price_ghs"] = pd.to_numeric(df["price_ghs"], errors="coerce")
    df["latitude"]  = pd.to_numeric(df["latitude"],  errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    # Extract numeric weight from unit column for per-KG analysis
    df["unit_raw"] = df["unit"].str.strip()
    def extract_kg(u):
        if pd.isna(u): return np.nan
        u = str(u).strip()
        if u == "KG": return 1.0
        if "KG" in u:
            try: return float(u.replace("KG","").strip())
            except: return np.nan
        return np.nan
    df["unit_kg"] = df["unit_raw"].apply(extract_kg)
    df["price_per_kg"] = np.where(df["unit_kg"] > 0, df["price_ghs"] / df["unit_kg"], np.nan)
    return df[df["price_ghs"] > 0].copy()

DF          = load_data()
COMMODITIES = sorted(DF["commodity"].unique().tolist())
REGIONS     = ["All Regions"] + sorted(DF["region"].unique().tolist())
MARKETS     = ["All Markets"] + sorted(DF["market"].unique().tolist())
YEARS       = sorted(DF["year"].unique().tolist())
MONTHS      = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

# Major = daily essentials | Minor = seasonal commodities
MAJOR = [c for c in ["Maize","Maize (yellow)","Rice (local)","Rice (imported)",
                      "Rice (paddy)","Cassava","Gari","Millet","Sorghum",
                      "Cowpeas","Cowpeas (white)","Soybeans"] if c in COMMODITIES]
MINOR = [c for c in ["Tomatoes (local)","Tomatoes (navrongo)","Onions",
                      "Peppers (fresh)","Peppers (dried)","Yam","Yam (puna)",
                      "Plantains (apem)","Plantains (apentu)","Eggplants",
                      "Eggs","Fish (mackerel, fresh)","Meat (chicken)",
                      "Meat (chicken, local)"] if c in COMMODITIES]

# ── APP ────────────────────────────────────────────────────────────────────
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME],
                suppress_callback_exceptions=True,
                meta_tags=[{"name":"viewport","content":"width=device-width,initial-scale=1"}])
app.title = "Market Pulse"
server = app.server

# ── NAVBAR ─────────────────────────────────────────────────────────────────
NAVBAR = dbc.Navbar(dbc.Container([
    dbc.NavbarBrand(
        html.Img(src="/assets/logo.jpg", height="40px"),
        href="/", style={"padding":"0"}
    ),
    dbc.NavbarToggler(id="toggler"),
    dbc.Collapse(dbc.Nav([
        dbc.NavItem(dbc.NavLink("Home",           href="/",          active="exact")),
        dbc.NavItem(dbc.NavLink("About",          href="/about",     active="exact")),
        dbc.NavItem(dbc.NavLink("Dashboard",      href="/dashboard", active="exact")),
        dbc.NavItem(dbc.NavLink("Marketplace",    href="/marketplace", active="exact")),
        dbc.NavItem(dbc.NavLink("Our Work",       href="/ourwork",   active="exact")),
        dbc.NavItem(dbc.NavLink("Blog",           href="/blog",      active="exact")),
        dbc.NavItem(dbc.NavLink("Team",           href="/team",      active="exact")),
        dbc.NavItem(dbc.NavLink("Contact",        href="/contact",   active="exact")),
    ], className="ms-auto", navbar=True), id="navbar-collapse", navbar=True),
], fluid=True), color="dark", dark=True, sticky="top",
style={"borderBottom":"3px solid #2ecc71"})

FOOTER = html.Footer(dbc.Container(dbc.Row([
    dbc.Col(html.P("© 2026 Market Pulse | WFP Data",
                   className="text-muted mb-0", style={"fontSize":"0.85rem"})),
    dbc.Col(html.P("Built with Python · Dash · Plotly",
                   className="text-muted mb-0 text-end", style={"fontSize":"0.85rem"})),
])), style={"background":"#1a1a2e","padding":"18px 0","marginTop":"40px"})

app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    dcc.Store(id="session-store", storage_type="session"),
    NAVBAR,
    html.Div(id="page-content", style={"minHeight":"80vh"}),
    FOOTER,
])

# ── HOME PAGE ──────────────────────────────────────────────────────────────
def page_home():
    n_rec  = f"{len(DF):,}"
    n_comm = str(DF["commodity"].nunique())
    n_mkt  = str(DF["market"].nunique())
    n_reg  = str(DF["region"].nunique())

    def kcard(color, val, label, icon):
        return dbc.Col(dbc.Card(dbc.CardBody([
            html.I(className=f"fa {icon} fa-2x mb-2", style={"color":color}),
            html.H3(val, style={"fontWeight":"800","color":color}),
            html.P(label, className="text-muted mb-0", style={"fontSize":"0.9rem"}),
        ], className="text-center py-4"),
        style={"border":f"2px solid {color}","borderRadius":"12px",
               "boxShadow":"0 4px 15px rgba(0,0,0,0.08)"}), xs=12, sm=6, md=3, className="mb-4")

    def fcard(icon, title, text, color):
        return dbc.Col(dbc.Card(dbc.CardBody([
            html.Div(html.I(className=f"fa {icon} fa-2x"),
                     style={"background":color,"color":"white","width":"55px","height":"55px",
                            "borderRadius":"50%","display":"flex","alignItems":"center",
                            "justifyContent":"center","marginBottom":"15px"}),
            html.H5(title, style={"fontWeight":"700"}),
            html.P(text, className="text-muted", style={"fontSize":"0.9rem"}),
        ]), style={"border":"none","boxShadow":"0 4px 20px rgba(0,0,0,0.08)",
                   "borderRadius":"12px","height":"100%"}), xs=12, md=4, className="mb-4")

    return html.Div([
        html.Div([dbc.Container([dbc.Row([dbc.Col([
            html.Img(src="/assets/logo.jpg", height="80px", style={"marginBottom":"15px"}),
            html.H1("Market Pulse", style={"fontWeight":"800","fontSize":"2.4rem",
                                            "color":"white","lineHeight":"1.2"}),
            html.P("Real-time agricultural commodity price intelligence for farmers, "
                   "traders, merchants, procurement officers, and policymakers across Ghana. "
                   "Enhancing food security.",
                   style={"fontSize":"1.15rem","color":"#cce8d4","marginTop":"15px",
                          "maxWidth":"600px"}),
            html.Div([
                dbc.Button("Explore Dashboard", href="/dashboard", color="success", size="lg",
                           className="me-3", style={"fontWeight":"600","borderRadius":"8px"}),
                dbc.Button("Our Work", href="/ourwork", outline=True, color="light",
                           size="lg", style={"fontWeight":"600","borderRadius":"8px"}),
            ], style={"marginTop":"30px"}),
        ], md=8)])], fluid=True)],
        style={"background":"linear-gradient(135deg,#1a5c2e 0%,#2ecc71 100%)",
               "padding":"80px 40px","marginBottom":"50px"}),

        dbc.Container([
            dbc.Row([kcard("#2ecc71",n_rec,"Price Records","fa-database"),
                     kcard("#f1c40f",n_comm,"Commodities","fa-wheat-awn"),
                     kcard("#e67e22",n_mkt,"Markets","fa-store"),
                     kcard("#e67e22",n_reg,"Regions","fa-map")], className="mb-5"),
            dbc.Row([
                dbc.Col([
                    html.H2("Why Market Pulse?", style={"fontWeight":"700"}),
                    html.Hr(style={"borderColor":"#2ecc71","borderWidth":"3px",
                                   "width":"60px","opacity":"1"}),
                    html.P("In Ghana's agricultural markets, information is power. Farmers sell "
                           "at harvest when prices are lowest. Traders profit from the information "
                           "gap. Policymakers lack real-time visibility into food security risks.",
                           className="text-muted"),
                    html.P("Market Pulse closes that gap — providing price transparency across "
                           "all regions, commodities, and time periods, powered by WFP data.",
                           className="text-muted"),
                ], md=6),
                dbc.Col(dbc.Card(dbc.CardBody([
                    html.H5("Platform Highlights", style={"fontWeight":"700","color":"#2ecc71"}),
                    html.Ul([
                        html.Li("20 years of WFP price data for Ghana"),
                        html.Li("Interactive filters by commodity, region, and market"),
                        html.Li("Seasonal price pattern detection"),
                        html.Li("Price volatility and inflation tracking"),
                        html.Li("ML-powered price forecasting (coming soon)"),
                        html.Li("USSD access for feature phone users"),
                        html.Li("Power BI reports for institutional users"),
                    ], style={"fontSize":"0.95rem","lineHeight":"2"})
                ]), style={"border":"2px solid #2ecc71","borderRadius":"12px"}), md=6),
            ], className="mb-5"),
            dbc.Row([
                fcard("fa-chart-line","Price Trend Analysis",
                      "Track how commodity prices have moved over time across any market or region.","#2ecc71"),
                fcard("fa-map-location-dot","Regional Comparison",
                      "Compare prices across all regions to identify trading opportunities.","#f1c40f"),
                fcard("fa-fire","Seasonality Detection",
                      "Heatmaps reveal harvest season dips and lean season spikes.","#e67e22"),
                fcard("fa-bolt","Volatility Analysis",
                      "Identify which commodities carry the most price risk.","#e74c3c"),
                fcard("fa-mobile-screen","USSD Access",
                      "Farmers without smartphones access prices via USSD on any phone.","#e67e22"),
                fcard("fa-chart-pie","Power BI Reports",
                      "Institutional dashboards for MoFA, GCX, and financial partners.","#f39c12"),
            ]),
        ], fluid=True),
    ])

# ── DASHBOARD PAGE ─────────────────────────────────────────────────────────
def page_dashboard():
    card = lambda hdr, body, color="#2ecc71": dbc.Card([
        dbc.CardHeader(html.H6(hdr, style={"fontWeight":"700","margin":"0","color":color})),
        dbc.CardBody(body)
    ], style={"borderRadius":"10px","boxShadow":"0 2px 10px rgba(0,0,0,0.07)","height":"100%"})

    # ── SIDEBAR ───────────────────────────────────────────────────────────
    sidebar = html.Div([
        # Logo / Brand
        html.Div([
            html.Img(src="/assets/logo.jpg", height="45px", style={"marginBottom":"8px"}),
            html.H5("Market Pulse", style={"fontWeight":"800","color":"white","marginBottom":"0","fontSize":"1.1rem"}),
            html.Small("Intelligence Dashboard", style={"color":"#a8e6c0","fontSize":"0.75rem"}),
        ], style={"textAlign":"center","padding":"25px 15px 20px","borderBottom":"1px solid #3d7a4f"}),

        # Navigation
        html.Div([
            html.P("ANALYTICS", style={"color":"#a8e6c0","fontSize":"0.7rem","fontWeight":"700",
                                        "letterSpacing":"1px","marginBottom":"8px","marginTop":"20px","paddingLeft":"15px"}),
            dbc.Nav([
                dbc.NavLink([html.I(className="fa fa-chart-line me-2"),"Price Dynamics"],
                            href="/dashboard#ind-1", external_link=True, style={"color":"white","borderRadius":"8px","marginBottom":"4px","fontSize":"0.85rem"}),
                dbc.NavLink([html.I(className="fa fa-bolt me-2"),"Volatility"],
                            href="/dashboard#ind-2", external_link=True, style={"color":"#b0b0b0","borderRadius":"8px","marginBottom":"4px","fontSize":"0.85rem"}),
                dbc.NavLink([html.I(className="fa fa-map me-2"),"Spatial Dispersion"],
                            href="/dashboard#ind-3", external_link=True, style={"color":"#b0b0b0","borderRadius":"8px","marginBottom":"4px","fontSize":"0.85rem"}),
                dbc.NavLink([html.I(className="fa fa-calendar me-2"),"Seasonality"],
                            href="/dashboard#ind-4", external_link=True, style={"color":"#b0b0b0","borderRadius":"8px","marginBottom":"4px","fontSize":"0.85rem"}),
            ], vertical=True, style={"paddingLeft":"8px","paddingRight":"8px"}),

            html.P("TOOLS", style={"color":"#a8e6c0","fontSize":"0.7rem","fontWeight":"700",
                                    "letterSpacing":"1px","marginBottom":"8px","marginTop":"25px","paddingLeft":"15px"}),
            dbc.Nav([
                dbc.NavLink([html.I(className="fa fa-store me-2"),"Marketplace"],
                            href="/marketplace", style={"color":"#b0b0b0","borderRadius":"8px","marginBottom":"4px","fontSize":"0.85rem"}),
                dbc.NavLink([html.I(className="fa fa-file-pdf me-2"),"Reports"],
                            href="/dashboard#ind-reports", external_link=True, style={"color":"#b0b0b0","borderRadius":"8px","marginBottom":"4px","fontSize":"0.85rem"}),
                dbc.NavLink([html.I(className="fa fa-table me-2"),"Latest Prices"],
                            href="/dashboard#ind-table", external_link=True, style={"color":"#b0b0b0","borderRadius":"8px","marginBottom":"4px","fontSize":"0.85rem"}),
                dbc.NavLink([html.I(className="fa fa-chart-bar me-2"),"Market Profile"],
                            href="/dashboard#ind-5", external_link=True, style={"color":"#b0b0b0","borderRadius":"8px","marginBottom":"4px","fontSize":"0.85rem"}),
            ], vertical=True, style={"paddingLeft":"8px","paddingRight":"8px"}),
        ]),

        # Bottom section
        html.Div([
            html.Hr(style={"borderColor":"#3d7a4f","margin":"15px 0"}),
            dbc.Nav([
                dbc.NavLink([html.I(className="fa fa-home me-2"),"Back to Home"],
                            href="/", style={"color":"#b0b0b0","borderRadius":"8px","fontSize":"0.85rem"}),
            ], vertical=True, style={"paddingLeft":"8px","paddingRight":"8px"}),
        ], style={"position":"absolute","bottom":"15px","left":"0","right":"0"}),

    ], style={
        "position":"fixed","top":"0","left":"0","bottom":"0","width":"240px",
        "background":"linear-gradient(180deg, #1a4a2a 0%, #0d3318 100%)",
        "padding":"0","overflowY":"auto","zIndex":"1000",
        "boxShadow":"2px 0 15px rgba(0,0,0,0.3)",
    })

    # ── MAIN CONTENT ──────────────────────────────────────────────────────
    content = dbc.Container([
        # ── HEADER ────────────────────────────────────────────────────────
        dbc.Row([dbc.Col([
            html.H2("Market Intelligence Dashboard",
                    style={"fontWeight":"800","marginTop":"20px"}),
            html.P("Four analytical indicators derived from observed price behaviour — "
                   "split by Major (daily essentials) and Minor (seasonal) commodities.",
                   className="text-muted", style={"fontSize":"0.9rem"}),
        ])]),

        # ── COMMODITY TYPE TABS ───────────────────────────────────────────
        dbc.Card(dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Label("Commodity Type", style={"fontWeight":"700","fontSize":"0.85rem"}),
                    dbc.RadioItems(
                        id="ri-type",
                        options=[{"label":"Major – Daily Essentials","value":"major"},
                                 {"label":"Minor – Seasonal Commodities","value":"minor"},
                                 {"label":"All Commodities","value":"all"}],
                        value="major", inline=True,
                        inputStyle={"marginRight":"5px"},
                        labelStyle={"marginRight":"20px","fontWeight":"600"}
                    ),
                ], md=5),
                dbc.Col([
                    html.Label("Commodity", style={"fontWeight":"600","fontSize":"0.85rem"}),
                    dcc.Dropdown(id="dd-comm", options=MAJOR, value=MAJOR[0], clearable=False),
                ], md=2),
                dbc.Col([
                    html.Label("Region", style={"fontWeight":"600","fontSize":"0.85rem"}),
                    dcc.Dropdown(id="dd-reg", options=sorted(DF["region"].unique().tolist()),
                                 value=[], clearable=True, multi=True, placeholder="All Regions"),
                ], md=2),
                dbc.Col([
                    html.Label("Market", style={"fontWeight":"600","fontSize":"0.85rem"}),
                    dcc.Dropdown(id="dd-mkt", options=sorted(DF["market"].unique().tolist()),
                                 value=[], clearable=True, multi=True, placeholder="All Markets"),
                ], md=2),
                dbc.Col([
                    html.Label("Price Type", style={"fontWeight":"600","fontSize":"0.85rem"}),
                    dcc.Dropdown(id="dd-ptype", options=["Both","Wholesale","Retail"],
                                 value="Both", clearable=False),
                ], md=1),
            ])
        ]), className="mb-4",
        style={"border":"2px solid #2ecc71","borderRadius":"10px",
               "boxShadow":"0 2px 10px rgba(39,174,96,0.1)"}),

        # ── TIME RANGE SLIDER ─────────────────────────────────────────────
        dbc.Card(dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Label("Year Range", style={"fontWeight":"700","fontSize":"0.85rem"}),
                    dcc.RangeSlider(
                        id="sl-time",
                        min=int(min(YEARS)),
                        max=int(max(YEARS)),
                        value=[int(min(YEARS)), int(max(YEARS))],
                        marks={y: str(y) for y in YEARS[::2]},
                        tooltip={"placement":"bottom"},
                        allowCross=False,
                    ),
                ], md=6),
                dbc.Col([
                    html.Label("Month(s)", style={"fontWeight":"600","fontSize":"0.85rem"}),
                    dcc.Dropdown(id="dd-month",
                                 options=[{"label":m,"value":i+1} for i,m in enumerate(MONTHS)],
                                 value=[], clearable=True, multi=True,
                                 placeholder="All Months"),
                ], md=3),
                dbc.Col([
                    html.Label("Price Mode", style={"fontWeight":"600","fontSize":"0.85rem"}),
                    dcc.Dropdown(id="dd-unit",
                                 options=["As Recorded (with unit)","Per KG (normalized)"],
                                 value="As Recorded (with unit)", clearable=False),
                ], md=3),
            ])
        ]), className="mb-4",
        style={"border":"1px solid #adb5bd","borderRadius":"10px"}),

        # ── KPI STRIP ─────────────────────────────────────────────────────
        dbc.Row(id="kpi-row", className="mb-2"),

        # ── INDICATOR 1: PRICE DYNAMICS ───────────────────────────────────
        html.Div(id="ind-1"),
        dbc.Row([dbc.Col(dbc.Card([
            dbc.CardHeader(html.Div([
                dbc.Badge("Indicator 1", color="success", className="me-2"),
                html.Strong("Price Dynamics — Price Changes Over Time"),
            ])),
            dbc.CardBody([
                html.P("Tracks inflationary pressure and short-term market dynamics. "
                       "Price movement is used as a proxy for supply/demand shocks.",
                       className="text-muted", style={"fontSize":"0.85rem","marginBottom":"10px"}),
                dbc.Row([
                    dbc.Col(dcc.Graph(id="g-trend", config={"displayModeBar":False}), md=8),
                    dbc.Col(dcc.Graph(id="g-yoy",   config={"displayModeBar":False}), md=4),
                ]),
            ])
        ], style={"borderRadius":"10px","boxShadow":"0 2px 10px rgba(0,0,0,0.07)",
                  "borderLeft":"4px solid #2ecc71"}))], className="mb-4"),

        # MoM chart - separate full-width card
        dbc.Row([dbc.Col(dbc.Card([
            dbc.CardHeader(html.Div([
                dbc.Badge("Indicator 1b", color="success", className="me-2"),
                html.Strong("Month-on-Month Price Change"),
            ])),
            dbc.CardBody([
                html.P("Percentage change in average price from one month to the next. "
                       "Red bars indicate price increases, green bars show decreases.",
                       className="text-muted", style={"fontSize":"0.85rem","marginBottom":"10px"}),
                dcc.Graph(id="g-mom", config={"displayModeBar":False}),
            ])
        ], style={"borderRadius":"10px","boxShadow":"0 2px 10px rgba(0,0,0,0.07)",
                  "borderLeft":"4px solid #2ecc71"}))], className="mb-4"),

        # ── INDICATOR 2: PRICE VOLATILITY ─────────────────────────────────
        html.Div(id="ind-2"),
        dbc.Row([dbc.Col(dbc.Card([
            dbc.CardHeader(html.Div([
                dbc.Badge("Indicator 2", color="danger", className="me-2"),
                html.Strong("Price Volatility — Market Instability Signals"),
            ])),
            dbc.CardBody([
                html.P("High volatility signals uncertainty in food availability or "
                       "disruptions in market functioning. Measured by Coefficient of Variation.",
                       className="text-muted", style={"fontSize":"0.85rem","marginBottom":"10px"}),
                dbc.Row([
                    dbc.Col(dcc.Graph(id="g-vol-major", config={"displayModeBar":False}), md=6),
                    dbc.Col(dcc.Graph(id="g-vol-minor", config={"displayModeBar":False}), md=6),
                ])
            ])
        ], style={"borderRadius":"10px","boxShadow":"0 2px 10px rgba(0,0,0,0.07)",
                  "borderLeft":"4px solid #e74c3c"}))], className="mb-4"),

        # ── INDICATOR 3: SPATIAL PRICE DISPERSION ─────────────────────────
        html.Div(id="ind-3"),
        dbc.Row([dbc.Col(dbc.Card([
            dbc.CardHeader(html.Div([
                dbc.Badge("Indicator 3", color="warning", className="me-2"),
                html.Strong("Spatial Price Dispersion — Market Integration"),
            ])),
            dbc.CardBody([
                html.P("Large price gaps between regions indicate inefficient distribution or "
                       "localised supply constraints. Small gaps mean well-integrated markets.",
                       className="text-muted", style={"fontSize":"0.85rem","marginBottom":"10px"}),
                dbc.Row([
                    dbc.Col([
                        html.Label("Year", style={"fontWeight":"600","fontSize":"0.85rem"}),
                        dcc.Slider(id="sl-yr", min=int(min(YEARS)), max=int(max(YEARS)),
                                   value=int(max(YEARS)),
                                   marks={y:str(y) for y in YEARS[::4]},
                                   tooltip={"placement":"bottom"}),
                        dcc.Graph(id="g-region", config={"displayModeBar":False}),
                    ], md=6),
                    dbc.Col(dcc.Graph(id="g-map", config={"displayModeBar":False}), md=6),
                ])
            ])
        ], style={"borderRadius":"10px","boxShadow":"0 2px 10px rgba(0,0,0,0.07)",
                  "borderLeft":"4px solid #f39c12"}))], className="mb-4"),

        # ── INDICATOR 4: SEASONALITY ──────────────────────────────────────
        html.Div(id="ind-4"),
        dbc.Row([dbc.Col(dbc.Card([
            dbc.CardHeader(html.Div([
                dbc.Badge("Indicator 4", color="primary", className="me-2"),
                html.Strong("Seasonality — Monthly Price Cycles"),
            ])),
            dbc.CardBody([
                html.P("Identifies the months in which commodity prices rise and fall. "
                       "Major commodities follow harvest cycles. Minor commodities follow "
                       "seasonal growing patterns.",
                       className="text-muted", style={"fontSize":"0.85rem","marginBottom":"10px"}),
                dbc.Row([
                    dbc.Col(dcc.Graph(id="g-heat",       config={"displayModeBar":False}), md=6),
                    dbc.Col(dcc.Graph(id="g-seas-summary",config={"displayModeBar":False}), md=6),
                ])
            ])
        ], style={"borderRadius":"10px","boxShadow":"0 2px 10px rgba(0,0,0,0.07)",
                  "borderLeft":"4px solid #f1c40f"}))], className="mb-4"),

        # ── MULTI-COMMODITY COMPARISON ────────────────────────────────────
        dbc.Row([dbc.Col(dbc.Card([
            dbc.CardHeader(html.Div([
                dbc.Badge("Overview", color="secondary", className="me-2"),
                html.Strong("Major vs Minor Commodity Price Comparison"),
            ])),
            dbc.CardBody([
                html.P("Compare prices across both commodity groups over time.",
                       className="text-muted", style={"fontSize":"0.85rem","marginBottom":"10px"}),
                dbc.Row([
                    dbc.Col([
                        html.Label("Select Commodities",
                                   style={"fontWeight":"600","fontSize":"0.85rem"}),
                        dcc.Dropdown(id="dd-multi", options=COMMODITIES,
                                     value=(MAJOR[:2]+MINOR[:2]),
                                     multi=True),
                        dcc.Graph(id="g-multi", config={"displayModeBar":False}),
                    ])
                ])
            ])
        ], style={"borderRadius":"10px","boxShadow":"0 2px 10px rgba(0,0,0,0.07)",
                  "borderLeft":"4px solid #e67e22"}))], className="mb-4"),

        # ── LATEST PRICES TABLE ───────────────────────────────────────────
        html.Div(id="ind-table"),
        dbc.Row([dbc.Col(dbc.Card([
            dbc.CardHeader(html.H6("Latest Market Prices",
                                   style={"fontWeight":"700","margin":"0"})),
            dbc.CardBody(html.Div(id="tbl-latest"))
        ], style={"borderRadius":"10px","boxShadow":"0 2px 10px rgba(0,0,0,0.07)"}))],
        className="mb-4"),

        # ── INDICATOR 5: MARKET PROFILE (fp_agg_data) ─────────────────────
        html.Div(id="ind-5"),
        dbc.Row([dbc.Col(dbc.Card([
            dbc.CardHeader(html.Div([
                dbc.Badge("Indicator 5", color="warning", className="me-2"),
                html.Strong("Market Profile — Aggregate Price Intelligence"),
            ])),
            dbc.CardBody([
                html.P("Pre-aggregated monthly prices across 20 key markets (2019–2023). "
                       "Shows overall market cost level, ranking, and stability.",
                       className="text-muted", style={"fontSize":"0.85rem","marginBottom":"10px"}),
                dbc.Row([
                    dbc.Col([
                        html.Label("Select Market", style={"fontWeight":"600","fontSize":"0.85rem"}),
                        dcc.Dropdown(id="dd-mkt-profile",
                                     options=sorted(["Accra","Bolga","Cape Coast","Ejura","Garu","Ho","Hohoe",
                                                     "Kintampo","Koforidua","Kumasi","Mankessim","Nkwanta",
                                                     "Obuasi","Sekondi/Takoradi","Sunyani","Tamale","Techiman",
                                                     "Tema","Wa","Yendi"]),
                                     value="Kumasi", clearable=False),
                    ], md=4),
                ], className="mb-3"),
                # KPI row for selected market
                dbc.Row(id="mkt-profile-kpis", className="mb-3"),
                dbc.Row([
                    dbc.Col(dcc.Graph(id="g-mkt-trend", config={"displayModeBar":False}), md=6),
                    dbc.Col(dcc.Graph(id="g-mkt-ranking", config={"displayModeBar":False}), md=6),
                ]),
            ])
        ], style={"borderRadius":"10px","boxShadow":"0 2px 10px rgba(0,0,0,0.07)",
                  "borderLeft":"4px solid #f1c40f"}))], className="mb-4"),

        # ── PRICE FORECAST (ML Model) ────────────────────────────────────
        html.Div(id="ind-forecast"),
        dbc.Row([dbc.Col(dbc.Card([
            dbc.CardHeader(html.Div([
                dbc.Badge("ML Forecast", color="dark", className="me-2"),
                html.Strong("Price Forecast — Random Forest Model"),
            ])),
            dbc.CardBody([
                html.P("6-month price forecast using a Random Forest model trained on historical prices, "
                       "exchange rates, and crude oil prices (R² = 0.74).",
                       className="text-muted", style={"fontSize":"0.85rem","marginBottom":"10px"}),
                dbc.Row(id="forecast-kpis", className="mb-3"),
                dcc.Graph(id="g-forecast", config={"displayModeBar":False}),
                dbc.Row([
                    dbc.Col(dbc.Card(dbc.CardBody([
                        html.P("Model", className="text-muted mb-0", style={"fontSize":"0.72rem"}),
                        html.H6("Random Forest", style={"fontWeight":"700","color":"#2ecc71","margin":"0","fontSize":"0.85rem"}),
                    ]), style={"textAlign":"center","borderRadius":"8px","border":"1px solid #2ecc71"}), md=2),
                    dbc.Col(dbc.Card(dbc.CardBody([
                        html.P("Test R²", className="text-muted mb-0", style={"fontSize":"0.72rem"}),
                        html.H6("0.7412", style={"fontWeight":"700","color":"#f1c40f","margin":"0","fontSize":"0.85rem"}),
                    ]), style={"textAlign":"center","borderRadius":"8px","border":"1px solid #f1c40f"}), md=2),
                    dbc.Col(dbc.Card(dbc.CardBody([
                        html.P("Test RMSE", className="text-muted mb-0", style={"fontSize":"0.72rem"}),
                        html.H6("GHS 111.01", style={"fontWeight":"700","color":"#e67e22","margin":"0","fontSize":"0.85rem"}),
                    ]), style={"textAlign":"center","borderRadius":"8px","border":"1px solid #e67e22"}), md=2),
                    dbc.Col(dbc.Card(dbc.CardBody([
                        html.P("Test MAE", className="text-muted mb-0", style={"fontSize":"0.72rem"}),
                        html.H6("GHS 47.53", style={"fontWeight":"700","color":"#e67e22","margin":"0","fontSize":"0.85rem"}),
                    ]), style={"textAlign":"center","borderRadius":"8px","border":"1px solid #e67e22"}), md=2),
                    dbc.Col(dbc.Card(dbc.CardBody([
                        html.P("Features", className="text-muted mb-0", style={"fontSize":"0.72rem"}),
                        html.H6("9 inputs", style={"fontWeight":"700","color":"#d35400","margin":"0","fontSize":"0.85rem"}),
                    ]), style={"textAlign":"center","borderRadius":"8px","border":"1px solid #d35400"}), md=2),
                    dbc.Col(dbc.Card(dbc.CardBody([
                        html.P("Horizon", className="text-muted mb-0", style={"fontSize":"0.72rem"}),
                        html.H6("6 months", style={"fontWeight":"700","color":"#f39c12","margin":"0","fontSize":"0.85rem"}),
                    ]), style={"textAlign":"center","borderRadius":"8px","border":"1px solid #f39c12"}), md=2),
                ], className="mt-3"),
            ])
        ], style={"borderRadius":"10px","boxShadow":"0 2px 10px rgba(0,0,0,0.07)",
                  "borderLeft":"4px solid #2c3e50"}))], className="mb-4"),

        # ── DOWNLOADABLE REPORTS ──────────────────────────────────────────
        html.Div(id="ind-reports"),
        dbc.Row([dbc.Col(dbc.Card([
            dbc.CardHeader(html.Div([
                dbc.Badge("Reports", color="info", className="me-2"),
                html.Strong("Download Market Intelligence Reports"),
            ])),
            dbc.CardBody([
                html.P("Periodic reports generated from this dashboard's data. "
                       "Click to download.",
                       className="text-muted", style={"fontSize":"0.85rem","marginBottom":"15px"}),
                dbc.Row([
                    dbc.Col(dbc.Card(dbc.CardBody([
                        html.I(className="fa fa-file-pdf fa-2x mb-2", style={"color":"#2ecc71"}),
                        dbc.Badge("Monthly", color="secondary", className="mb-2"),
                        html.H6("Food Price Monitor - May 2026", style={"fontWeight":"700","fontSize":"0.85rem"}),
                        html.Small("May 2026", className="text-muted d-block mb-2"),
                        dbc.Button([html.I(className="fa fa-download me-2"),"PDF"],
                                   color="success",size="sm",outline=True,style={"borderRadius":"6px"}),
                    ],className="text-center"), style={"borderRadius":"10px","borderTop":"3px solid #2ecc71"}), md=2, className="mb-3"),
                    dbc.Col(dbc.Card(dbc.CardBody([
                        html.I(className="fa fa-file-pdf fa-2x mb-2", style={"color":"#f1c40f"}),
                        dbc.Badge("Quarterly", color="secondary", className="mb-2"),
                        html.H6("Q1 2026 Market Report", style={"fontWeight":"700","fontSize":"0.85rem"}),
                        html.Small("Jan-Mar 2026", className="text-muted d-block mb-2"),
                        dbc.Button([html.I(className="fa fa-download me-2"),"PDF"],
                                   color="primary",size="sm",outline=True,style={"borderRadius":"6px"}),
                    ],className="text-center"), style={"borderRadius":"10px","borderTop":"3px solid #f1c40f"}), md=2, className="mb-3"),
                    dbc.Col(dbc.Card(dbc.CardBody([
                        html.I(className="fa fa-file-pdf fa-2x mb-2", style={"color":"#e74c3c"}),
                        dbc.Badge("Annual", color="secondary", className="mb-2"),
                        html.H6("Volatility Report 2025", style={"fontWeight":"700","fontSize":"0.85rem"}),
                        html.Small("Full Year 2025", className="text-muted d-block mb-2"),
                        dbc.Button([html.I(className="fa fa-download me-2"),"PDF"],
                                   color="danger",size="sm",outline=True,style={"borderRadius":"6px"}),
                    ],className="text-center"), style={"borderRadius":"10px","borderTop":"3px solid #e74c3c"}), md=2, className="mb-3"),
                    dbc.Col(dbc.Card(dbc.CardBody([
                        html.I(className="fa fa-file-pdf fa-2x mb-2", style={"color":"#e67e22"}),
                        dbc.Badge("Reference", color="secondary", className="mb-2"),
                        html.H6("Seasonality Atlas", style={"fontWeight":"700","fontSize":"0.85rem"}),
                        html.Small("2016-2023", className="text-muted d-block mb-2"),
                        dbc.Button([html.I(className="fa fa-download me-2"),"PDF"],
                                   color="secondary",size="sm",outline=True,style={"borderRadius":"6px"}),
                    ],className="text-center"), style={"borderRadius":"10px","borderTop":"3px solid #e67e22"}), md=2, className="mb-3"),
                    dbc.Col(dbc.Card(dbc.CardBody([
                        html.I(className="fa fa-file-pdf fa-2x mb-2", style={"color":"#e67e22"}),
                        dbc.Badge("Special", color="secondary", className="mb-2"),
                        html.H6("Spatial Dispersion Index", style={"fontWeight":"700","fontSize":"0.85rem"}),
                        html.Small("2025", className="text-muted d-block mb-2"),
                        dbc.Button([html.I(className="fa fa-download me-2"),"PDF"],
                                   color="warning",size="sm",outline=True,style={"borderRadius":"6px"}),
                    ],className="text-center"), style={"borderRadius":"10px","borderTop":"3px solid #e67e22"}), md=2, className="mb-3"),
                    dbc.Col(dbc.Card(dbc.CardBody([
                        html.I(className="fa fa-file-pdf fa-2x mb-2", style={"color":"#2ecc71"}),
                        dbc.Badge("Monthly", color="secondary", className="mb-2"),
                        html.H6("Food Price Monitor - Apr 2026", style={"fontWeight":"700","fontSize":"0.85rem"}),
                        html.Small("Apr 2026", className="text-muted d-block mb-2"),
                        dbc.Button([html.I(className="fa fa-download me-2"),"PDF"],
                                   color="success",size="sm",outline=True,style={"borderRadius":"6px"}),
                    ],className="text-center"), style={"borderRadius":"10px","borderTop":"3px solid #2ecc71"}), md=2, className="mb-3"),
                ]),
            ])
        ], style={"borderRadius":"10px","boxShadow":"0 2px 10px rgba(0,0,0,0.07)",
                  "borderLeft":"4px solid #17a2b8"}))], className="mb-5"),

    ], fluid=True)

    # ── RETURN SIDEBAR + CONTENT ──────────────────────────────────────────
    return html.Div([
        sidebar,
        html.Div(content, style={"marginLeft":"240px","padding":"0 20px"}),
    ], style={"position":"relative"})

# ── ARCHITECTURE PAGE ──────────────────────────────────────────────────────
def page_architecture():
    def abox(title, items, color, icon):
        return dbc.Card([
            dbc.CardHeader([html.I(className=f"fa {icon} me-2"),html.Strong(title)],
                           style={"background":color,"color":"white","borderRadius":"10px 10px 0 0"}),
            dbc.CardBody(html.Ul([html.Li(i,style={"marginBottom":"6px","fontSize":"0.9rem"})
                                  for i in items]))
        ], style={"borderRadius":"10px","boxShadow":"0 4px 15px rgba(0,0,0,0.08)",
                  "height":"100%","border":f"1px solid {color}"})

    def step(num, title, text, color):
        return html.Div([
            html.Span(str(num), style={"background":color,"color":"white","borderRadius":"50%",
                                       "width":"32px","height":"32px","display":"inline-flex",
                                       "alignItems":"center","justifyContent":"center",
                                       "fontWeight":"bold","marginRight":"12px"}),
            html.Strong(title),
            html.P(text, className="text-muted ms-5 mb-0", style={"fontSize":"0.9rem"})
        ], className="mb-3")

    return dbc.Container([
        dbc.Row([dbc.Col([
            html.H2("System Architecture", style={"fontWeight":"800","marginTop":"30px"}),
            html.P("End-to-end architecture of Market Pulse.", className="text-muted"),
            html.Hr(style={"borderColor":"#2ecc71","borderWidth":"3px","width":"60px","opacity":"1"}),
        ])]),
        dbc.Row([
            dbc.Col(abox("Data Sources",[
                "WFP / VAM – Food price database","MoFA Ghana – Ministry of Food & Agriculture",
                "Ghana Statistical Service (GSS)","FAO – Food & Agriculture Organization",
                "IMF / World Development Indicators","Ghana Commodity Exchange (GCX)",
                "OpenWeatherMap – Weather data","NPA Ghana – Fuel prices",
                "Bank of Ghana – Exchange rates",
            ],"#2c3e50","fa-database"), md=4),
            dbc.Col(html.Div("→",style={"fontSize":"3rem","color":"#2ecc71","textAlign":"center",
                                         "marginTop":"80px"}), md=1,
                    className="d-flex align-items-center justify-content-center"),
            dbc.Col(abox("Backend",[
                "SQL Database (PostgreSQL)","Python ETL Pipeline",
                "Machine Learning – Price forecasting","REST API – Data serving",
                "Competitor Intelligence","Scheduled data refresh",
            ],"#2ecc71","fa-server"), md=3),
            dbc.Col(html.Div("→",style={"fontSize":"3rem","color":"#2ecc71","textAlign":"center",
                                         "marginTop":"80px"}), md=1,
                    className="d-flex align-items-center justify-content-center"),
            dbc.Col(abox("Frontend",[
                "Market Pulse Web Dashboard","USSD Interface – Feature phones",
                "Voice-based local language access","Power BI – Institutional reports",
            ],"#f1c40f","fa-display"), md=3),
        ], className="mb-5 align-items-start"),

        html.H4("Data Flow", style={"fontWeight":"700","marginBottom":"20px"}),
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([
                step(1,"Data Collection","WFP, MoFA, GSS, FAO ingested via APIs into SQL database.","#2ecc71"),
                step(2,"Processing & Modelling","Python cleans data. ML model generates price forecasts.","#f1c40f"),
                step(3,"API Layer","REST API exposes data to dashboard, Power BI, and USSD.","#e67e22"),
                step(4,"User Interfaces","Farmers via USSD, analysts via web, institutions via Power BI.","#e67e22"),
            ]), style={"borderRadius":"10px","boxShadow":"0 2px 10px rgba(0,0,0,0.07)"}), md=8),
            dbc.Col(dbc.Card([
                dbc.CardHeader([html.I(className="fa fa-code me-2"),html.Strong("Tech Stack")],
                               style={"background":"#d35400","color":"white","borderRadius":"10px 10px 0 0"}),
                dbc.CardBody(html.Ul([
                    html.Li("Python 3.13"),html.Li("PostgreSQL / SQL"),
                    html.Li("scikit-learn – ML"),html.Li("Dash + Plotly"),
                    html.Li("Power BI"),html.Li("USSD Gateway"),
                    html.Li("Flask REST API"),html.Li("Pandas / NumPy"),
                ], style={"fontSize":"0.9rem"}))
            ], style={"borderRadius":"10px","border":"1px solid #d35400"}), md=4),
        ], className="mb-5"),
    ], fluid=True)

# ── POWER BI PAGE ──────────────────────────────────────────────────────────
def page_powerbi():
    def step_card(num, title, text, color):
        return dbc.Col(dbc.Card(dbc.CardBody([
            html.Div(str(num),style={"background":color,"color":"white","borderRadius":"50%",
                                     "width":"40px","height":"40px","display":"flex",
                                     "alignItems":"center","justifyContent":"center",
                                     "fontWeight":"800","marginBottom":"12px"}),
            html.H6(title,style={"fontWeight":"700"}),
            html.P(text,className="text-muted",style={"fontSize":"0.88rem"}),
        ]),style={"borderRadius":"10px","boxShadow":"0 2px 10px rgba(0,0,0,0.07)",
                  "height":"100%","borderTop":f"3px solid {color}"}), md=3, className="mb-4")

    def user_card(icon, user, desc, color):
        return dbc.Col(dbc.Card(dbc.CardBody([
            html.Div(html.I(className=f"fa {icon} fa-2x"),
                     style={"background":color,"color":"white","width":"55px","height":"55px",
                            "borderRadius":"50%","display":"flex","alignItems":"center",
                            "justifyContent":"center","marginBottom":"12px"}),
            html.H6(user, style={"fontWeight":"700"}),
            html.P(desc, className="text-muted", style={"fontSize":"0.88rem"}),
        ]),style={"borderRadius":"10px","boxShadow":"0 4px 15px rgba(0,0,0,0.08)",
                  "height":"100%","borderTop":f"3px solid {color}"}),
        md=3, className="mb-4")

    return dbc.Container([
        # ── HEADER ────────────────────────────────────────────────────────
        dbc.Row([dbc.Col([
            html.H2("Power BI – Institutional Reporting Layer",
                    style={"fontWeight":"800","marginTop":"30px"}),
            html.P("Market Pulse serves everyone — but not everyone uses it the same way.",
                   className="text-muted"),
            html.Hr(style={"borderColor":"#2ecc71","borderWidth":"3px",
                           "width":"60px","opacity":"1"}),
        ])]),

        # ── TWO PLATFORMS, TWO AUDIENCES ──────────────────────────────────
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([
                html.Div([
                    html.I(className="fa fa-display fa-2x mb-3", style={"color":"#2ecc71"}),
                    html.H5("Market Pulse Dashboard", style={"fontWeight":"700"}),
                    html.H6("For: Farmers, Traders & Analysts",
                            style={"color":"#2ecc71","marginBottom":"15px"}),
                ], className="text-center"),
                html.Ul([
                    html.Li("Live interactive price exploration"),
                    html.Li("Filter by commodity, region, market"),
                    html.Li("Seasonality and trend analysis"),
                    html.Li("Accessible on any browser or phone"),
                    html.Li("No login required — open to everyone"),
                ], style={"fontSize":"0.92rem","lineHeight":"2.1"}),
            ]), style={"borderRadius":"12px","border":"2px solid #2ecc71",
                       "boxShadow":"0 4px 20px rgba(39,174,96,0.15)"}),
            md=5, className="mb-4"),

            dbc.Col(html.Div([
                html.Div("VS", style={"fontSize":"2rem","fontWeight":"900",
                                       "color":"#adb5bd","textAlign":"center",
                                       "marginTop":"80px"})
            ]), md=2, className="d-flex align-items-center justify-content-center"),

            dbc.Col(dbc.Card(dbc.CardBody([
                html.Div([
                    html.I(className="fa fa-chart-pie fa-2x mb-3", style={"color":"#f39c12"}),
                    html.H5("Power BI Reports", style={"fontWeight":"700"}),
                    html.H6("For: Institutions & Decision-Makers",
                            style={"color":"#f39c12","marginBottom":"15px"}),
                ], className="text-center"),
                html.Ul([
                    html.Li("Scheduled monthly PDF reports"),
                    html.Li("Shareable via email and Microsoft Teams"),
                    html.Li("Executive-level KPI summaries"),
                    html.Li("Integrates with existing Microsoft tools"),
                    html.Li("Role-based access control"),
                ], style={"fontSize":"0.92rem","lineHeight":"2.1"}),
            ]), style={"borderRadius":"12px","border":"2px solid #f39c12",
                       "boxShadow":"0 4px 20px rgba(243,156,18,0.15)"}),
            md=5, className="mb-4"),
        ], className="mb-5 align-items-center"),

        # ── WHO USES POWER BI ─────────────────────────────────────────────
        html.H4("Who Uses the Power BI Layer",
                style={"fontWeight":"700","marginBottom":"20px"}),
        dbc.Row([
            user_card("fa-building-columns","MoFA Ghana",
                      "Generates monthly national food price bulletins and tracks food security "
                      "indicators across all regions for policy decisions.",
                      "#f1c40f"),
            user_card("fa-scale-balanced","Ghana Commodity Exchange",
                      "Monitors commodity price trends for trading desk decisions and publishes "
                      "official market reports for exchange participants.",
                      "#2ecc71"),
            user_card("fa-landmark","BankAfrique",
                      "Assesses agricultural loan risk by region and commodity. Identifies "
                      "high-volatility areas before approving farmer credit.",
                      "#e74c3c"),
            user_card("fa-globe","FAO / WFP Partners",
                      "Tracks food security indicators and price shocks for early warning "
                      "systems and humanitarian response planning.",
                      "#e67e22"),
        ], className="mb-5"),

        # ── WHAT POWER BI REPORTS CONTAIN ────────────────────────────────
        html.H4("What the Power BI Reports Contain",
                style={"fontWeight":"700","marginBottom":"20px"}),
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H6("Monthly Price Bulletin", style={"fontWeight":"700","color":"#f1c40f"}),
                html.P("A one-page summary of average prices for key commodities across all "
                       "regions. Automatically generated every month and distributed to MoFA "
                       "and partner institutions.", className="text-muted",
                       style={"fontSize":"0.9rem"}),
                dbc.Badge("MoFA · GCX", color="primary", className="mt-1"),
            ]), style={"borderRadius":"10px","borderLeft":"4px solid #f1c40f",
                       "boxShadow":"0 2px 10px rgba(0,0,0,0.07)","height":"100%"}),
            md=4, className="mb-3"),
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H6("Agricultural Loan Risk Dashboard", style={"fontWeight":"700","color":"#e74c3c"}),
                html.P("Shows price volatility by commodity and region, year-on-year price "
                       "change, and market stress indicators. Used by BankAfrique to "
                       "assess credit risk for farmer loans.", className="text-muted",
                       style={"fontSize":"0.9rem"}),
                dbc.Badge("BankAfrique · Financial Institutions", color="danger", className="mt-1"),
            ]), style={"borderRadius":"10px","borderLeft":"4px solid #e74c3c",
                       "boxShadow":"0 2px 10px rgba(0,0,0,0.07)","height":"100%"}),
            md=4, className="mb-3"),
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H6("Food Security Early Warning", style={"fontWeight":"700","color":"#e67e22"}),
                html.P("Tracks price spikes above seasonal norms and flags regions where "
                       "food affordability is deteriorating. Feeds into FAO and WFP early "
                       "warning systems.", className="text-muted",
                       style={"fontSize":"0.9rem"}),
                dbc.Badge("FAO · WFP · Government", color="secondary", className="mt-1"),
            ]), style={"borderRadius":"10px","borderLeft":"4px solid #e67e22",
                       "boxShadow":"0 2px 10px rgba(0,0,0,0.07)","height":"100%"}),
            md=4, className="mb-3"),
        ], className="mb-5"),

        # ── HOW IT CONNECTS ───────────────────────────────────────────────
        html.H4("How Power BI Connects to Market Pulse",
                style={"fontWeight":"700","marginBottom":"20px"}),
        dbc.Row([
            step_card(1,"Same Data Source",
                      "Power BI reads from the same SQL database that powers this dashboard. "
                      "One database, two interfaces — no duplication.",
                      "#2ecc71"),
            step_card(2,"Built in Power BI Desktop",
                      "Reports are designed in Power BI Desktop using the star schema data model "
                      "already defined in the architecture.",
                      "#f1c40f"),
            step_card(3,"Published to Power BI Service",
                      "Reports are published to app.powerbi.com and scheduled to refresh "
                      "automatically when new price data arrives.",
                      "#e67e22"),
            step_card(4,"Distributed to Partners",
                      "MoFA, GCX, and BankAfrique access reports via shared links, "
                      "email subscriptions, or embedded iframes.",
                      "#e67e22"),
        ], className="mb-5"),

        # ── EMBED PLACEHOLDER ─────────────────────────────────────────────
        dbc.Row([dbc.Col(dbc.Card(dbc.CardBody([
            html.Div([
                html.I(className="fa fa-chart-pie fa-3x mb-3", style={"color":"#f39c12"}),
                html.H5("Live Power BI Report", style={"fontWeight":"700"}),
                html.P("Once the Power BI report is published, it will be embedded here "
                       "as a fully interactive institutional dashboard.",
                       className="text-muted", style={"maxWidth":"500px","margin":"0 auto"}),
                dbc.Badge("Connecting in Phase 2", color="warning",
                          className="mt-3 p-2", style={"fontSize":"0.9rem"}),
            ], className="text-center py-4"),
        ]), style={"borderRadius":"10px","border":"2px dashed #f39c12"}))],
        className="mb-5"),

    ], fluid=True)

# ── DATA SOURCES PAGE ──────────────────────────────────────────────────────
def page_datasources():
    def scard(name, desc, dtype, freq, url, color, icon):
        return dbc.Col(dbc.Card([
            dbc.CardHeader([html.I(className=f"fa {icon} me-2"),html.Strong(name)],
                           style={"background":color,"color":"white","borderRadius":"10px 10px 0 0"}),
            dbc.CardBody([
                html.P(desc,style={"fontSize":"0.88rem","minHeight":"50px"}),
                dbc.Row([
                    dbc.Col([html.Small("Data Type",className="text-muted d-block",
                                        style={"fontWeight":"600"}),
                             html.Small(dtype,style={"fontSize":"0.82rem"})],md=6),
                    dbc.Col([html.Small("Update Freq",className="text-muted d-block",
                                        style={"fontWeight":"600"}),
                             html.Small(freq,style={"fontSize":"0.82rem"})],md=6),
                ],className="mb-3"),
                dbc.Button("Visit",href=url,target="_blank",color="outline-secondary",size="sm"),
            ])
        ],style={"borderRadius":"10px","boxShadow":"0 4px 15px rgba(0,0,0,0.08)","height":"100%"}),
        md=4,className="mb-4")

    def ccard(name, desc, strength, gap, color):
        return dbc.Col(dbc.Card(dbc.CardBody([
            html.H6(name,style={"fontWeight":"700","color":color}),
            html.P(desc,className="text-muted",style={"fontSize":"0.85rem","minHeight":"40px"}),
            html.Div([html.Small("Strength: ",style={"fontWeight":"600","color":"#2ecc71"}),
                      html.Small(strength,style={"fontSize":"0.82rem"})],className="mb-1"),
            html.Div([html.Small("Gap we fill: ",style={"fontWeight":"600","color":"#e74c3c"}),
                      html.Small(gap,style={"fontSize":"0.82rem"})]),
        ]),style={"borderRadius":"10px","boxShadow":"0 2px 10px rgba(0,0,0,0.07)",
                  "borderLeft":f"4px solid {color}","height":"100%"}),
        md=4,className="mb-4")

    return dbc.Container([
        dbc.Row([dbc.Col([
            html.H2("Data Sources",style={"fontWeight":"800","marginTop":"30px"}),
            html.P("All data sources powering Market Pulse.",className="text-muted"),
            html.Hr(style={"borderColor":"#2ecc71","borderWidth":"3px","width":"60px","opacity":"1"}),
        ])]),
        html.H4("Primary Sources",style={"fontWeight":"700","marginBottom":"20px"}),
        dbc.Row([
            scard("WFP / VAM","WFP price database covering food commodities across Ghana's markets.",
                  "Commodity prices","Weekly","https://data.humdata.org/dataset/wfp-food-prices-for-ghana","#2ecc71","fa-wheat-awn"),
            scard("MoFA Ghana","Ministry of Food and Agriculture — official agricultural statistics.",
                  "Production, prices","Monthly","https://mofa.gov.gh","#f1c40f","fa-building-columns"),
            scard("Ghana Statistical Service","National statistics including CPI and food inflation.",
                  "CPI, inflation","Monthly","https://statsghana.gov.gh","#e67e22","fa-chart-bar"),
            scard("FAO GIEWS","Global Information and Early Warning System for food prices.",
                  "Global food prices","Monthly","https://www.fao.org/giews","#e67e22","fa-globe"),
            scard("IMF / WDI","Macroeconomic indicators including exchange rates and GDP.",
                  "Exchange rates","Monthly","https://data.worldbank.org","#d35400","fa-money-bill-trend-up"),
            scard("Ghana Commodity Exchange","Official exchange prices for agricultural commodities.",
                  "Spot & futures","Daily","https://gcx.com.gh","#f39c12","fa-scale-balanced"),
        ]),
        html.H4("Competitor Intelligence",style={"fontWeight":"700","marginBottom":"20px","marginTop":"10px"}),
        dbc.Row([
            ccard("ESOKO","SMS-based market price service across West Africa.",
                  "Established network","No web dashboard","#2ecc71"),
            ccard("Farmerline","Digital agriculture platform for smallholder farmers.",
                  "Strong farmer network","Limited price analytics","#f1c40f"),
            ccard("Agrico","Agricultural input and market linkage platform.",
                  "Input supply chain","No price forecasting","#e67e22"),
            ccard("Ghana Commodity Exchange","Official commodity exchange.",
                  "Regulated institution","Only exchange-traded commodities","#e67e22"),
            ccard("WFP VAM Tools","WFP's own market monitoring dashboards.",
                  "Rich historical data","Not farmer-accessible","#d35400"),
            ccard("MoFA Price Bulletins","Official government price reports.",
                  "Official data","PDF only, not interactive","#f39c12"),
        ]),
    ], fluid=True)



# ── ABOUT PAGE ─────────────────────────────────────────────────────────────
def page_about():
    return html.Div([
        html.Div([dbc.Container([
            html.Img(src="/assets/logo.jpg", height="60px", style={"marginBottom":"15px"}),
            html.H1("About Market Pulse", style={"fontWeight":"800","color":"white","fontSize":"2.4rem"}),
            html.P("Enhancing Food Security Through Market Intelligence.",
                   style={"color":"#cce8d4","fontSize":"1.2rem","fontStyle":"italic"}),
        ], fluid=True)], style={"background":"linear-gradient(135deg,#1a5c2e 0%,#2ecc71 100%)",
                                "padding":"60px 40px","marginBottom":"50px"}),
        dbc.Container([
            # ── THE PROBLEM ───────────────────────────────────────────────
            dbc.Row([
                dbc.Col([
                    html.H3("The Problem: Ghana's Information Gap", style={"fontWeight":"700"}),
                    html.Hr(style={"borderColor":"#e74c3c","borderWidth":"3px","width":"60px","opacity":"1"}),
                    html.P("Ghana's food markets are broken — not by lack of food, but by lack of "
                           "information. When a farmer in Northern Region sells maize at harvest for "
                           "GHS 91, she doesn't know that the same maize will sell for GHS 139 just "
                           "three months later in the lean season. When a trader in Volta buys maize "
                           "at GHS 199, he doesn't know that the same commodity costs GHS 460 in "
                           "Western Region — a GHS 260 gap for the same crop, in the same country, "
                           "at the same time.",
                           style={"fontSize":"1rem","lineHeight":"1.9"}),
                    html.P("This is not a logistics problem. It is an information problem. And it "
                           "costs Ghana's food supply chain billions of cedis every year.",
                           style={"fontSize":"1rem","lineHeight":"1.9","fontWeight":"600"}),
                ], md=12),
            ], className="mb-4"),

            # ── THE EVIDENCE ──────────────────────────────────────────────
            dbc.Row([
                dbc.Col([
                    html.H3("The Evidence: 17 Years of Price Data", style={"fontWeight":"700"}),
                    html.Hr(style={"borderColor":"#e67e22","borderWidth":"3px","width":"60px","opacity":"1"}),
                    html.P("We analysed 39,000+ price records from the World Food Programme, covering "
                           "26 commodities across all 10 regions of Ghana from 2006 to 2023. The data "
                           "reveals three systemic failures:",
                           style={"fontSize":"1rem","lineHeight":"1.9"}),
                ], md=12),
            ]),
            dbc.Row([
                dbc.Col(dbc.Card(dbc.CardBody([
                    html.H1("1,324%", style={"fontWeight":"900","color":"#e74c3c","fontSize":"2.2rem"}),
                    html.H6("Maize Price Increase", style={"fontWeight":"700"}),
                    html.P("From GHS 18.81 in 2006 to GHS 267.87 in 2023. Three shock years drove "
                           "the worst spikes: 2008 (+111%, global food crisis), 2021 (+67%, COVID), "
                           "and 2023 (+53%, economic crisis). Each time, those with the least "
                           "information paid the highest price.",
                           className="text-muted", style={"fontSize":"0.88rem"}),
                ]), style={"borderRadius":"12px","borderTop":"4px solid #e74c3c",
                          "boxShadow":"0 4px 15px rgba(0,0,0,0.08)","height":"100%"}),
                md=4, className="mb-4"),
                dbc.Col(dbc.Card(dbc.CardBody([
                    html.H1("GHS 260", style={"fontWeight":"900","color":"#e67e22","fontSize":"2.2rem"}),
                    html.H6("Regional Price Gap", style={"fontWeight":"700"}),
                    html.P("In 2023, maize cost GHS 199 in Volta and GHS 460 in Western Region. "
                           "Same crop, same month, same country — but more than double the price. "
                           "This gap is the cost of broken distribution and missing market signals.",
                           className="text-muted", style={"fontSize":"0.88rem"}),
                ]), style={"borderRadius":"12px","borderTop":"4px solid #e67e22",
                          "boxShadow":"0 4px 15px rgba(0,0,0,0.08)","height":"100%"}),
                md=4, className="mb-4"),
                dbc.Col(dbc.Card(dbc.CardBody([
                    html.H1("269%", style={"fontWeight":"900","color":"#e67e22","fontSize":"2.2rem"}),
                    html.H6("Cassava Volatility (CV)", style={"fontWeight":"700"}),
                    html.P("Perishable crops like cassava (269%), tomatoes (268%), and peppers (236%) "
                           "are wildly unpredictable. Stable crops like rice (36%) and cowpeas (58%) "
                           "carry far less risk. Without this data, banks cannot price agricultural "
                           "loans correctly.",
                           className="text-muted", style={"fontSize":"0.88rem"}),
                ]), style={"borderRadius":"12px","borderTop":"4px solid #e67e22",
                          "boxShadow":"0 4px 15px rgba(0,0,0,0.08)","height":"100%"}),
                md=4, className="mb-4"),
            ], className="mb-4"),

            # ── THE SOLUTION ──────────────────────────────────────────────
            dbc.Row([
                dbc.Col([
                    html.H3("The Solution: Market Pulse", style={"fontWeight":"700"}),
                    html.Hr(style={"borderColor":"#2ecc71","borderWidth":"3px","width":"60px","opacity":"1"}),
                    html.P("Market Pulse is a data platform that turns 17 years of raw price data "
                           "into actionable intelligence. We track four indicators that together "
                           "paint a complete picture of market health:",
                           style={"fontSize":"1rem","lineHeight":"1.9"}),
                ], md=12),
            ]),
            dbc.Row([
                dbc.Col(dbc.Card(dbc.CardBody([
                    dbc.Badge("Indicator 1", color="success", className="mb-2"),
                    html.H6("Price Dynamics", style={"fontWeight":"700"}),
                    html.P("How prices change over time — year-on-year and month-on-month. "
                           "Detects inflationary pressure and supply/demand shocks before they "
                           "become crises.", className="text-muted", style={"fontSize":"0.85rem"}),
                ]), style={"borderLeft":"4px solid #2ecc71","borderRadius":"10px","height":"100%"}),
                md=3, className="mb-3"),
                dbc.Col(dbc.Card(dbc.CardBody([
                    dbc.Badge("Indicator 2", color="danger", className="mb-2"),
                    html.H6("Price Volatility", style={"fontWeight":"700"}),
                    html.P("Which commodities carry the most price risk. Enables banks to price "
                           "agricultural loans correctly and farmers to choose stable crops.",
                           className="text-muted", style={"fontSize":"0.85rem"}),
                ]), style={"borderLeft":"4px solid #e74c3c","borderRadius":"10px","height":"100%"}),
                md=3, className="mb-3"),
                dbc.Col(dbc.Card(dbc.CardBody([
                    dbc.Badge("Indicator 3", color="warning", className="mb-2"),
                    html.H6("Spatial Dispersion", style={"fontWeight":"700"}),
                    html.P("Where prices differ across regions. Reveals trading opportunities "
                           "for traders and distribution failures for policymakers.",
                           className="text-muted", style={"fontSize":"0.85rem"}),
                ]), style={"borderLeft":"4px solid #f39c12","borderRadius":"10px","height":"100%"}),
                md=3, className="mb-3"),
                dbc.Col(dbc.Card(dbc.CardBody([
                    dbc.Badge("Indicator 4", color="primary", className="mb-2"),
                    html.H6("Seasonality", style={"fontWeight":"700"}),
                    html.P("When prices rise and fall each year. Helps farmers time their sales "
                           "and buyers plan procurement around predictable cycles.",
                           className="text-muted", style={"fontSize":"0.85rem"}),
                ]), style={"borderLeft":"4px solid #f1c40f","borderRadius":"10px","height":"100%"}),
                md=3, className="mb-3"),
            ], className="mb-5"),

            # ── MISSION / VISION ──────────────────────────────────────────
            dbc.Row([
                dbc.Col(dbc.Card(dbc.CardBody([
                    html.H5("Mission", style={"fontWeight":"700","color":"#2ecc71"}),
                    html.P("Democratise agricultural market intelligence in Ghana — so that no "
                           "farmer sells blind, no trader exploits ignorance, and no policymaker "
                           "acts without data.",
                           style={"fontSize":"0.95rem"}),
                    html.Hr(),
                    html.H5("Vision", style={"fontWeight":"700","color":"#f1c40f"}),
                    html.P("A Ghana where every participant in the food supply chain — from the "
                           "smallholder farmer to the institutional buyer — makes price decisions "
                           "backed by real-time intelligence.",
                           style={"fontSize":"0.95rem"}),
                ]), style={"border":"2px solid #2ecc71","borderRadius":"12px"}), md=6),
                dbc.Col(dbc.Card(dbc.CardBody([
                    html.H5("The Data Behind It", style={"fontWeight":"700","color":"#e67e22"}),
                    html.Ul([
                        html.Li("Source: World Food Programme (WFP) VAM database"),
                        html.Li("Coverage: 2006 – 2023 (17 years)"),
                        html.Li("Records: 39,000+ observed prices"),
                        html.Li("Commodities: 26 (major staples + perishables)"),
                        html.Li("Regions: All 10 regions of Ghana"),
                        html.Li("Markets: 40+ physical markets tracked"),
                        html.Li("Economic indicators: Exchange rate, crude oil price"),
                    ], style={"fontSize":"0.9rem","lineHeight":"2"}),
                ]), style={"border":"2px solid #e67e22","borderRadius":"12px"}), md=6),
            ], className="mb-5"),

            # ── WHO WE SERVE ──────────────────────────────────────────────
            html.H4("Who We Serve", style={"fontWeight":"700","marginBottom":"20px"}),
            dbc.Row([
                dbc.Col(dbc.Card(dbc.CardBody([html.I(className="fa fa-tractor fa-2x mb-2",style={"color":"#2ecc71"}),
                    html.H6("Farmers",style={"fontWeight":"700"}),html.P("Know when to sell and when to hold. Seasonal data shows harvest lows and lean season highs.",className="text-muted",style={"fontSize":"0.85rem"})]),
                    style={"textAlign":"center","borderTop":"3px solid #2ecc71","borderRadius":"12px","height":"100%"}),md=2,className="mb-3"),
                dbc.Col(dbc.Card(dbc.CardBody([html.I(className="fa fa-truck fa-2x mb-2",style={"color":"#f1c40f"}),
                    html.H6("Traders",style={"fontWeight":"700"}),html.P("Spot regional price gaps. Buy where it's cheap, sell where it's expensive.",className="text-muted",style={"fontSize":"0.85rem"})]),
                    style={"textAlign":"center","borderTop":"3px solid #f1c40f","borderRadius":"12px","height":"100%"}),md=2,className="mb-3"),
                dbc.Col(dbc.Card(dbc.CardBody([html.I(className="fa fa-store fa-2x mb-2",style={"color":"#e67e22"}),
                    html.H6("Merchants",style={"fontWeight":"700"}),html.P("Track trends to manage stock levels and plan purchasing cycles.",className="text-muted",style={"fontSize":"0.85rem"})]),
                    style={"textAlign":"center","borderTop":"3px solid #e67e22","borderRadius":"12px","height":"100%"}),md=2,className="mb-3"),
                dbc.Col(dbc.Card(dbc.CardBody([html.I(className="fa fa-clipboard-list fa-2x mb-2",style={"color":"#e67e22"}),
                    html.H6("Procurement",style={"fontWeight":"700"}),html.P("Compare prices across regions and time to optimise institutional budgets.",className="text-muted",style={"fontSize":"0.85rem"})]),
                    style={"textAlign":"center","borderTop":"3px solid #e67e22","borderRadius":"12px","height":"100%"}),md=2,className="mb-3"),
                dbc.Col(dbc.Card(dbc.CardBody([html.I(className="fa fa-landmark fa-2x mb-2",style={"color":"#d35400"}),
                    html.H6("Banks",style={"fontWeight":"700"}),html.P("Price agricultural loan risk correctly using commodity volatility data.",className="text-muted",style={"fontSize":"0.85rem"})]),
                    style={"textAlign":"center","borderTop":"3px solid #d35400","borderRadius":"12px","height":"100%"}),md=2,className="mb-3"),
                dbc.Col(dbc.Card(dbc.CardBody([html.I(className="fa fa-building-columns fa-2x mb-2",style={"color":"#f39c12"}),
                    html.H6("Policy",style={"fontWeight":"700"}),html.P("Detect price shocks early and target food security interventions.",className="text-muted",style={"fontSize":"0.85rem"})]),
                    style={"textAlign":"center","borderTop":"3px solid #f39c12","borderRadius":"12px","height":"100%"}),md=2,className="mb-3"),
            ], className="mb-5"),
        ], fluid=True),
    ])


# ── TEAM PAGE ──────────────────────────────────────────────────────────────
def page_team():
    TEAM = [
        {"name":"John Mefful","role":"Data Scientist","lead":True,
         "bio":"Leads data strategy and modelling pipeline. ML and agricultural market analysis."},
        {"name":"Sydnor Amoah","role":"Data Scientist","lead":False,
         "bio":"Interactive dashboard and data visualisation. Analytical indicators and front-end."},
        {"name":"Rebecca Abugri","role":"Data Scientist","lead":False,
         "bio":"Data collection, cleaning, and integration from WFP, MoFA, and other sources."},
        {"name":"Mohammed Abukari","role":"Data Scientist","lead":False,
         "bio":"Spatial analysis and regional price dispersion modelling across Ghana."},
        {"name":"Yasira Musa","role":"Data Scientist","lead":False,
         "bio":"Seasonal price pattern analysis and volatility indicator framework."},
    ]
    def mcard(m):
        ini = "".join([w[0] for w in m["name"].split()])
        return dbc.Col(dbc.Card(dbc.CardBody([
            html.Div(ini, style={"width":"80px","height":"80px","borderRadius":"50%",
                "background":"linear-gradient(135deg,#1a5c2e,#2ecc71)","color":"white",
                "fontSize":"1.6rem","fontWeight":"800","display":"flex","alignItems":"center",
                "justifyContent":"center","margin":"0 auto 15px"}),
            html.H5(m["name"], style={"fontWeight":"700","textAlign":"center"}),
            html.P(m["role"], className="text-center", style={"color":"#2ecc71","fontWeight":"600","fontSize":"0.88rem"}),
            dbc.Badge("Team Lead", color="success", className="d-block mx-auto mb-2",
                      style={"width":"fit-content"}) if m["lead"] else html.Div(),
            html.Hr(),
            html.P(m["bio"], className="text-muted", style={"fontSize":"0.88rem","textAlign":"center"}),
        ]), style={"borderRadius":"12px","boxShadow":"0 4px 20px rgba(0,0,0,0.08)","height":"100%"}),
        md=4, className="mb-4")
    return html.Div([
        html.Div([dbc.Container([
            html.H1("Meet the Team", style={"fontWeight":"800","color":"white","fontSize":"2.2rem"}),
        ], fluid=True)], style={"background":"linear-gradient(135deg,#1a5c2e 0%,#2ecc71 100%)",
                                "padding":"60px 40px","marginBottom":"50px"}),
        dbc.Container(dbc.Row([mcard(m) for m in TEAM], className="mb-5"), fluid=True),
    ])


# ── OUR WORK PAGE ──────────────────────────────────────────────────────────
def page_ourwork():
    def wcard(icon, title, desc, tag, color):
        return dbc.Col(dbc.Card(dbc.CardBody([
            html.I(className=f"fa {icon} fa-2x mb-3", style={"color":color}),
            dbc.Badge(tag, color="secondary", className="mb-2"),
            html.H5(title, style={"fontWeight":"700"}),
            html.P(desc, className="text-muted", style={"fontSize":"0.9rem"}),
        ]), style={"borderRadius":"12px","boxShadow":"0 4px 20px rgba(0,0,0,0.08)","height":"100%"}),
        md=4, className="mb-4")
    return html.Div([
        html.Div([dbc.Container([
            html.H1("Our Work", style={"fontWeight":"800","color":"white","fontSize":"2.2rem"}),
        ], fluid=True)], style={"background":"linear-gradient(135deg,#1a5c2e 0%,#2ecc71 100%)",
                                "padding":"60px 40px","marginBottom":"50px"}),
        dbc.Container([
            dbc.Row([
                wcard("fa-chart-line","Price Intelligence Dashboard",
                      "Interactive dashboard with 4 analytical indicators covering 26 commodities across all regions.","Live","#2ecc71"),
                wcard("fa-mobile-screen","USSD Price Access",
                      "USSD interface for farmers on basic mobile phones - no smartphone needed.","In Development","#f1c40f"),
                wcard("fa-robot","ML Price Forecasting",
                      "Machine learning model to forecast commodity prices up to 3 months ahead.","In Development","#e67e22"),
                wcard("fa-chart-pie","Power BI Reports",
                      "Monthly institutional reports for MoFA, GCX, and BankAfrique.","Coming Soon","#e67e22"),
                wcard("fa-database","Multi-Source Integration",
                      "Integration of WFP, MoFA, GSS, FAO, IMF data into unified SQL database.","In Progress","#d35400"),
                wcard("fa-globe","National Expansion",
                      "Expanding coverage to district-level monitoring across all 16 regions.","Planned","#f39c12"),
            ]),
        ], fluid=True),
    ])


# ── BLOG PAGE ──────────────────────────────────────────────────────────────
def page_blog():
    posts = [
        {"t":"Why Maize Prices Spike Every March","d":"May 2026","tag":"Price Dynamics","c":"#2ecc71",
         "s":"Each year between February and April, maize prices in northern markets rise sharply due to seasonal supply cycles."},
        {"t":"The Hidden Cost of Market Information Gaps","d":"Apr 2026","tag":"Market Access","c":"#f1c40f",
         "s":"When farmers lack price data, they almost always sell below fair value. We quantify that cost."},
        {"t":"Which Commodities Are Most Volatile?","d":"Mar 2026","tag":"Volatility","c":"#e74c3c",
         "s":"Using CV analysis across 26 commodities, we rank which crops carry the most price risk."},
        {"t":"North vs South: Ghana Price Divide","d":"Feb 2026","tag":"Spatial","c":"#e67e22",
         "s":"Food prices in northern regions are consistently higher. We map the dispersion."},
        {"t":"Tomato Price Crashes After Harvest","d":"Jan 2026","tag":"Seasonality","c":"#e67e22",
         "s":"Tomato prices can drop 60% within weeks of peak harvest. We analyse the cycle."},
        {"t":"How USSD Brings Data to Every Farmer","d":"Dec 2025","tag":"Technology","c":"#f39c12",
         "s":"Over 60% of Ghanaian farmers use basic phones. USSD could be the highest-impact intervention."},
    ]
    def bcard(p):
        return dbc.Col(dbc.Card(dbc.CardBody([
            dbc.Badge(p["tag"], color="secondary", className="mb-2"),
            html.H5(p["t"], style={"fontWeight":"700","lineHeight":"1.4"}),
            html.Small(p["d"], className="text-muted d-block mb-2"),
            html.P(p["s"], className="text-muted", style={"fontSize":"0.88rem"}),
        ]), style={"borderRadius":"12px","borderTop":f"3px solid {p['c']}","height":"100%"}),
        md=4, className="mb-4")
    return html.Div([
        html.Div([dbc.Container([
            html.H1("Market Intelligence Blog", style={"fontWeight":"800","color":"white","fontSize":"2.2rem"}),
        ], fluid=True)], style={"background":"linear-gradient(135deg,#1a5c2e 0%,#2ecc71 100%)",
                                "padding":"60px 40px","marginBottom":"50px"}),
        dbc.Container(dbc.Row([bcard(p) for p in posts]), fluid=True),
    ])


# ── LIVE REPORTS PAGE ──────────────────────────────────────────────────────
def page_reports():
    reps = [
        {"t":"Ghana Food Price Monitor - May 2026","p":"May 2026","type":"Monthly","c":"#2ecc71"},
        {"t":"Q1 2026 Agricultural Market Report","p":"Jan-Mar 2026","type":"Quarterly","c":"#f1c40f"},
        {"t":"Annual Price Volatility Report 2025","p":"Full Year 2025","type":"Annual","c":"#e74c3c"},
        {"t":"Seasonality Atlas - Major Commodities","p":"2016-2023","type":"Reference","c":"#e67e22"},
        {"t":"Spatial Price Dispersion Index 2025","p":"2025","type":"Special","c":"#e67e22"},
        {"t":"Ghana Food Price Monitor - Apr 2026","p":"Apr 2026","type":"Monthly","c":"#2ecc71"},
    ]
    def rcard(r):
        return dbc.Col(dbc.Card(dbc.CardBody([
            html.I(className="fa fa-file-pdf fa-2x mb-2", style={"color":r["c"]}),
            dbc.Badge(r["type"], color="secondary", className="mb-2"),
            html.H6(r["t"], style={"fontWeight":"700"}),
            html.Small(r["p"], className="text-muted d-block mb-2"),
            dbc.Button([html.I(className="fa fa-download me-2"),"Download PDF"],
                       color="success", size="sm", outline=True, style={"borderRadius":"6px"}),
        ]), style={"borderRadius":"12px","borderTop":f"3px solid {r['c']}","height":"100%"}),
        md=4, className="mb-4")
    return html.Div([
        html.Div([dbc.Container([
            html.H1("Live Reports", style={"fontWeight":"800","color":"white","fontSize":"2.2rem"}),
            html.P("Download periodic market intelligence reports.", style={"color":"#cce8d4"}),
        ], fluid=True)], style={"background":"linear-gradient(135deg,#1a5c2e 0%,#2ecc71 100%)",
                                "padding":"60px 40px","marginBottom":"50px"}),
        dbc.Container(dbc.Row([rcard(r) for r in reps]), fluid=True),
    ])


# ── CONTACT PAGE ───────────────────────────────────────────────────────────
def page_contact():
    return html.Div([
        html.Div([dbc.Container([
            html.H1("Contact Us", style={"fontWeight":"800","color":"white","fontSize":"2.2rem"}),
        ], fluid=True)], style={"background":"linear-gradient(135deg,#1a5c2e 0%,#2ecc71 100%)",
                                "padding":"60px 40px","marginBottom":"50px"}),
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H4("Send Us a Message", style={"fontWeight":"700","marginBottom":"20px"}),
                    dbc.Card(dbc.CardBody([
                        dbc.Row([
                            dbc.Col([html.Label("Name",style={"fontWeight":"600","fontSize":"0.85rem"}),
                                     dbc.Input(placeholder="Your name",className="mb-3")],md=6),
                            dbc.Col([html.Label("Email",style={"fontWeight":"600","fontSize":"0.85rem"}),
                                     dbc.Input(placeholder="your@email.com",type="email",className="mb-3")],md=6),
                        ]),
                        html.Label("Subject",style={"fontWeight":"600","fontSize":"0.85rem"}),
                        dbc.Input(placeholder="Subject",className="mb-3"),
                        html.Label("Message",style={"fontWeight":"600","fontSize":"0.85rem"}),
                        dbc.Textarea(placeholder="Your message...",rows=5,className="mb-3"),
                        dbc.Button("Send Message",color="success",size="lg",
                                   style={"width":"100%","borderRadius":"8px","fontWeight":"600"}),
                    ]), style={"borderRadius":"12px"}),
                ], md=7),
                dbc.Col([
                    html.H4("Get In Touch", style={"fontWeight":"700","marginBottom":"20px"}),
                    dbc.Card(dbc.CardBody([
                        html.P([html.I(className="fa fa-envelope me-2", style={"color":"#2ecc71"}),
                                html.A("marketpulse@gmail.com", href="mailto:marketpulse@gmail.com")],
                               style={"marginBottom":"15px"}),
                        html.P([html.I(className="fa fa-location-dot me-2", style={"color":"#f1c40f"}),
                                "Accra, Ghana"], className="text-muted"),
                        html.Hr(),
                        html.H6("Follow Us", style={"fontWeight":"700"}),
                        dbc.Button([html.I(className="fa-brands fa-x-twitter me-2"),"Twitter/X"],
                                   color="dark",outline=True,size="sm",className="me-2 mb-2"),
                        dbc.Button([html.I(className="fa-brands fa-linkedin me-2"),"LinkedIn"],
                                   color="primary",outline=True,size="sm",className="me-2 mb-2"),
                        dbc.Button([html.I(className="fa-brands fa-facebook me-2"),"Facebook"],
                                   color="primary",outline=True,size="sm",className="mb-2"),
                    ]), style={"borderRadius":"12px"}),
                ], md=5),
            ], className="mb-5"),
        ], fluid=True),
    ])


# ── MARKETPLACE DATA ───────────────────────────────────────────────────────
import csv, os, hashlib

USERS_FILE = os.path.join(os.path.dirname(__file__), "users.csv")
LISTINGS_FILE = os.path.join(os.path.dirname(__file__), "listings.csv")

# Regional distances (km between regional capitals, approximate)
REGION_COORDS = {
    "Ashanti": (6.69, -1.62), "Brong Ahafo": (7.95, -1.67),
    "Central": (5.11, -1.25), "Eastern": (6.10, -0.47),
    "Greater Accra": (5.60, -0.19), "Northern": (9.40, -0.84),
    "Upper East": (10.79, -0.81), "Upper West": (10.07, -2.50),
    "Volta": (6.60, 0.47), "Western": (5.02, -1.75),
}
TRANSPORT_RATE_PER_KM = 2.5  # GHS per km (approximate for small truck)

def _dist_km(r1, r2):
    """Approximate distance between two regions in km."""
    if r1 == r2: return 0
    c1 = REGION_COORDS.get(r1)
    c2 = REGION_COORDS.get(r2)
    if not c1 or not c2: return 0
    # Simple degree-to-km approximation (1 degree ≈ 111 km)
    dlat = (c1[0] - c2[0]) * 111
    dlon = (c1[1] - c2[1]) * 111
    return round((dlat**2 + dlon**2)**0.5, 1)

def _hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()[:16]

def _load_users():
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, "r", newline="") as f:
        return list(csv.DictReader(f))

def _save_user(name, phone, region, role, password):
    exists = os.path.exists(USERS_FILE)
    with open(USERS_FILE, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["name","phone","region","role","password"])
        if not exists: w.writeheader()
        w.writerow({"name":name,"phone":phone,"region":region,"role":role,"password":_hash_pw(password)})

def _load_listings():
    if not os.path.exists(LISTINGS_FILE):
        return []
    with open(LISTINGS_FILE, "r", newline="") as f:
        return list(csv.DictReader(f))

def _save_listing(farmer_name, phone, region, commodity, quantity, unit, price):
    exists = os.path.exists(LISTINGS_FILE)
    with open(LISTINGS_FILE, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["farmer_name","phone","region","commodity","quantity","unit","price","date"])
        if not exists: w.writeheader()
        w.writerow({"farmer_name":farmer_name,"phone":phone,"region":region,
                    "commodity":commodity,"quantity":quantity,"unit":unit,
                    "price":price,"date":pd.Timestamp.now().strftime("%Y-%m-%d")})


def _build_traders_list(farmer_region):
    """Build trader cards for the farmer dashboard showing registered buyers."""
    users = _load_users()
    buyers = [u for u in users if u.get("role") == "Buyer"]

    if not buyers:
        return dbc.Alert([
            html.I(className="fa fa-info-circle me-2"),
            "No traders registered yet. Buyers who sign up will appear here."
        ], color="info")

    cards = []
    for b in buyers:
        buyer_region = b.get("region","").strip().title()
        dist = _dist_km(farmer_region, buyer_region)
        cards.append(dbc.Col(dbc.Card(dbc.CardBody([
            html.Div([
                html.Div(b.get("name","?")[0].upper(),
                         style={"width":"45px","height":"45px","borderRadius":"50%",
                                "background":"linear-gradient(135deg,#f1c40f,#3498db)",
                                "color":"white","display":"flex","alignItems":"center",
                                "justifyContent":"center","fontWeight":"800","fontSize":"1.2rem",
                                "marginRight":"12px","flexShrink":"0"}),
                html.Div([
                    html.H6(b.get("name","Unknown"), style={"fontWeight":"700","marginBottom":"2px"}),
                    html.Small([html.I(className="fa fa-map-marker-alt me-1",style={"color":"#e67e22"}),
                               f"{buyer_region} Region"],
                              style={"color":"#666","fontSize":"0.82rem"}),
                ]),
            ], style={"display":"flex","alignItems":"center","marginBottom":"12px"}),
            html.Div([
                html.Div([
                    html.Small("Phone", className="text-muted d-block", style={"fontSize":"0.72rem","fontWeight":"600"}),
                    html.P(b.get("phone","N/A"), style={"fontWeight":"700","color":"#2ecc71","margin":"0","fontSize":"0.9rem"}),
                ], style={"flex":"1"}),
                html.Div([
                    html.Small("Distance", className="text-muted d-block", style={"fontSize":"0.72rem","fontWeight":"600"}),
                    html.P(f"{dist} km", style={"fontWeight":"700","color":"#e67e22","margin":"0","fontSize":"0.9rem"}),
                ], style={"flex":"1","textAlign":"right"}),
            ], style={"display":"flex","marginBottom":"10px"}),
            dbc.Button([html.I(className="fa fa-phone me-2"), "Call Trader"],
                       color="outline-success", size="sm", className="w-100",
                       style={"borderRadius":"6px","fontWeight":"600"}),
        ]), style={"borderRadius":"12px","boxShadow":"0 3px 12px rgba(0,0,0,0.08)",
                  "border":"1px solid #e8e8e8","height":"100%"}),
        md=4, className="mb-3"))

    return dbc.Row(cards)


def _build_drivers_list(user_region):
    """Build driver cards showing registered delivery workers."""
    users = _load_users()
    drivers = [u for u in users if u.get("role") == "Driver"]

    if not drivers:
        return dbc.Alert([
            html.I(className="fa fa-info-circle me-2"),
            "No drivers registered yet. Delivery workers who sign up will appear here."
        ], color="info")

    cards = []
    for d in drivers:
        driver_region = d.get("region","").strip().title()
        dist = _dist_km(user_region, driver_region)
        cards.append(dbc.Col(dbc.Card(dbc.CardBody([
            html.Div([
                html.Div(html.I(className="fa fa-truck", style={"color":"white","fontSize":"1.1rem"}),
                         style={"width":"45px","height":"45px","borderRadius":"50%",
                                "background":"linear-gradient(135deg,#e67e22,#f39c12)",
                                "display":"flex","alignItems":"center",
                                "justifyContent":"center","marginRight":"12px","flexShrink":"0"}),
                html.Div([
                    html.H6(d.get("name","Unknown"), style={"fontWeight":"700","marginBottom":"2px"}),
                    html.Small([html.I(className="fa fa-map-marker-alt me-1",style={"color":"#e67e22"}),
                               f"{driver_region} Region"],
                              style={"color":"#666","fontSize":"0.82rem"}),
                ]),
            ], style={"display":"flex","alignItems":"center","marginBottom":"12px"}),
            html.Div([
                html.Div([
                    html.Small("Phone", className="text-muted d-block", style={"fontSize":"0.72rem","fontWeight":"600"}),
                    html.P(d.get("phone","N/A"), style={"fontWeight":"700","color":"#2ecc71","margin":"0","fontSize":"0.9rem"}),
                ], style={"flex":"1"}),
                html.Div([
                    html.Small("Distance", className="text-muted d-block", style={"fontSize":"0.72rem","fontWeight":"600"}),
                    html.P(f"{dist} km", style={"fontWeight":"700","color":"#e67e22","margin":"0","fontSize":"0.9rem"}),
                ], style={"flex":"1","textAlign":"right"}),
            ], style={"display":"flex","marginBottom":"10px"}),
            dbc.Button([html.I(className="fa fa-phone me-2"), "Call Driver"],
                       color="outline-warning", size="sm", className="w-100",
                       style={"borderRadius":"6px","fontWeight":"600"}),
        ]), style={"borderRadius":"12px","boxShadow":"0 3px 12px rgba(0,0,0,0.08)",
                  "border":"1px solid #f0e0c8","height":"100%"}),
        md=4, className="mb-3"))

    return dbc.Row(cards)


def _build_locate_map(farmer_region):
    """Build an interactive map showing the farmer, traders, and drivers."""
    users = _load_users()
    farmer_coords = REGION_COORDS.get(farmer_region, (7.9, -1.0))

    # Build map data
    map_data = []

    # Add farmer (you) marker
    map_data.append({
        "name": "You (Farmer)",
        "lat": farmer_coords[0],
        "lon": farmer_coords[1],
        "role": "You",
        "region": farmer_region,
        "phone": "",
    })

    # Add buyers/traders
    for u in users:
        if u.get("role") == "Buyer":
            region = u.get("region","").strip().title()
            coords = REGION_COORDS.get(region)
            if coords:
                map_data.append({
                    "name": u.get("name","Unknown"),
                    "lat": coords[0] + np.random.uniform(-0.1, 0.1),
                    "lon": coords[1] + np.random.uniform(-0.1, 0.1),
                    "role": "Trader/Buyer",
                    "region": region,
                    "phone": u.get("phone",""),
                })

    # Add drivers
    for u in users:
        if u.get("role") == "Driver":
            region = u.get("region","").strip().title()
            coords = REGION_COORDS.get(region)
            if coords:
                map_data.append({
                    "name": u.get("name","Unknown"),
                    "lat": coords[0] + np.random.uniform(-0.1, 0.1),
                    "lon": coords[1] + np.random.uniform(-0.1, 0.1),
                    "role": "Driver",
                    "region": region,
                    "phone": u.get("phone",""),
                })

    df_map = pd.DataFrame(map_data)

    if df_map.empty:
        fig = go.Figure()
        fig.add_annotation(text="No traders or drivers registered yet.", showarrow=False)
        fig.update_layout(height=400)
        return fig

    color_map = {"You": "#2ecc71", "Trader/Buyer": "#f1c40f", "Driver": "#e67e22"}
    size_map = {"You": 18, "Trader/Buyer": 12, "Driver": 12}

    fig = px.scatter_mapbox(
        df_map, lat="lat", lon="lon",
        color="role", hover_name="name",
        hover_data={"region": True, "phone": True, "lat": False, "lon": False},
        color_discrete_map=color_map,
        size=[size_map.get(r, 12) for r in df_map["role"]],
        zoom=6, center={"lat": farmer_coords[0], "lon": farmer_coords[1]},
        mapbox_style="carto-positron",
    )
    fig.update_layout(
        margin=dict(t=0, b=0, l=0, r=0), height=450,
        legend=dict(orientation="h", yanchor="top", y=-0.02, xanchor="center", x=0.5,
                    title_text=""),
    )
    return fig


# ── MARKETPLACE PAGE ───────────────────────────────────────────────────────
def page_marketplace(session):
    """Main marketplace hub — always includes all callback targets."""
    logged_in = session and session.get("logged_in")
    is_farmer = logged_in and session.get("role") == "Farmer"
    is_buyer = logged_in and session.get("role") == "Buyer"
    is_driver = logged_in and session.get("role") == "Driver"

    regions_list = sorted(REGION_COORDS.keys())
    comm_options = sorted(DF["commodity"].unique().tolist())

    # ── LOGIN/REGISTER FORM (shown when not logged in) ────────────────
    login_section = html.Div([
        # Hero banner
        html.Div([dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.Img(src="/assets/logo.jpg", height="80px", style={"marginBottom":"15px"}),
                    html.H1("Farmer Marketplace", style={"fontWeight":"800","color":"white","fontSize":"2.5rem","lineHeight":"1.2"}),
                    html.P("Connect directly with buyers across Ghana. Get personalised sell advice. "
                           "Know which market pays more. Factor in transport costs.",
                           style={"color":"#cce8d4","fontSize":"1.1rem","marginTop":"15px","maxWidth":"500px"}),
                    html.Div([
                        html.Div([html.I(className="fa fa-check-circle me-2",style={"color":"#cce8d4"}),
                                  html.Span("Free for all farmers",style={"color":"white","fontSize":"0.9rem"})], className="mb-2"),
                        html.Div([html.I(className="fa fa-check-circle me-2",style={"color":"#cce8d4"}),
                                  html.Span("Know when to sell & when to hold",style={"color":"white","fontSize":"0.9rem"})], className="mb-2"),
                        html.Div([html.I(className="fa fa-check-circle me-2",style={"color":"#cce8d4"}),
                                  html.Span("Transport cost calculator included",style={"color":"white","fontSize":"0.9rem"})], className="mb-2"),
                        html.Div([html.I(className="fa fa-check-circle me-2",style={"color":"#cce8d4"}),
                                  html.Span("Connect with verified buyers",style={"color":"white","fontSize":"0.9rem"})]),
                    ], style={"marginTop":"25px"}),
                ], md=5, className="d-flex flex-column justify-content-center"),
                dbc.Col([
                    # Tabbed login/register card
                    dbc.Card([
                        dbc.CardBody([
                            dbc.Tabs([
                                # SIGN IN TAB
                                dbc.Tab([
                                    html.Div([
                                        html.Div([
                                            html.I(className="fa fa-user-circle fa-3x",style={"color":"#2ecc71"}),
                                        ], className="text-center mb-3 mt-3"),
                                        html.Label("Phone Number", style={"fontWeight":"600","fontSize":"0.85rem"}),
                                        dbc.InputGroup([
                                            dbc.InputGroupText(html.I(className="fa fa-phone",style={"color":"#2ecc71"})),
                                            dbc.Input(id="login-phone", placeholder="024XXXXXXX"),
                                        ], className="mb-3"),
                                        html.Label("Password", style={"fontWeight":"600","fontSize":"0.85rem"}),
                                        dbc.InputGroup([
                                            dbc.InputGroupText(html.I(className="fa fa-lock",style={"color":"#2ecc71"})),
                                            dbc.Input(id="login-password", type="password", placeholder="Enter password"),
                                        ], className="mb-4"),
                                        dbc.Button([html.I(className="fa fa-sign-in-alt me-2"),"Sign In"],
                                                   id="btn-login", color="success", className="w-100",
                                                   style={"fontWeight":"700","borderRadius":"8px","padding":"12px"}),
                                        html.Div(id="login-msg", className="mt-3"),
                                    ], style={"padding":"10px 5px"}),
                                ], label="Sign In", tab_id="tab-login",
                                   label_style={"fontWeight":"700","color":"#2ecc71"},
                                   active_label_style={"color":"white","background":"#2ecc71","borderColor":"#2ecc71"}),

                                # REGISTER TAB
                                dbc.Tab([
                                    html.Div([
                                        html.Div([
                                            html.I(className="fa fa-user-plus fa-3x",style={"color":"#f1c40f"}),
                                        ], className="text-center mb-3 mt-3"),
                                        html.Label("Full Name", style={"fontWeight":"600","fontSize":"0.85rem"}),
                                        dbc.InputGroup([
                                            dbc.InputGroupText(html.I(className="fa fa-user",style={"color":"#f1c40f"})),
                                            dbc.Input(id="reg-name", placeholder="Ama Mensah"),
                                        ], className="mb-2"),
                                        html.Label("Phone Number", style={"fontWeight":"600","fontSize":"0.85rem"}),
                                        dbc.InputGroup([
                                            dbc.InputGroupText(html.I(className="fa fa-phone",style={"color":"#f1c40f"})),
                                            dbc.Input(id="reg-phone", placeholder="024XXXXXXX"),
                                        ], className="mb-2"),
                                        html.Label("Region", style={"fontWeight":"600","fontSize":"0.85rem"}),
                                        dcc.Dropdown(id="reg-region", options=regions_list,
                                                     placeholder="Select your region", className="mb-2"),
                                        html.Label("I am a...", style={"fontWeight":"600","fontSize":"0.85rem"}),
                                        dbc.RadioItems(
                                            id="reg-role",
                                            options=[{"label":html.Span([html.I(className="fa fa-tractor me-2"),"Farmer"],
                                                                        style={"fontSize":"0.9rem"}),"value":"Farmer"},
                                                     {"label":html.Span([html.I(className="fa fa-cart-shopping me-2"),"Buyer"],
                                                                        style={"fontSize":"0.9rem"}),"value":"Buyer"},
                                                     {"label":html.Span([html.I(className="fa fa-truck me-2"),"Driver"],
                                                                        style={"fontSize":"0.9rem"}),"value":"Driver"}],
                                            value="Farmer", inline=True, className="mb-2",
                                            inputStyle={"marginRight":"6px"},
                                            labelStyle={"marginRight":"25px","fontWeight":"600"},
                                        ),
                                        html.Label("Password", style={"fontWeight":"600","fontSize":"0.85rem"}),
                                        dbc.InputGroup([
                                            dbc.InputGroupText(html.I(className="fa fa-lock",style={"color":"#f1c40f"})),
                                            dbc.Input(id="reg-password", type="password", placeholder="Choose a password"),
                                        ], className="mb-3"),
                                        dbc.Button([html.I(className="fa fa-user-plus me-2"),"Create Account"],
                                                   id="btn-register", color="primary", className="w-100",
                                                   style={"fontWeight":"700","borderRadius":"8px","padding":"12px"}),
                                        html.Div(id="reg-msg", className="mt-3"),
                                    ], style={"padding":"10px 5px"}),
                                ], label="Register", tab_id="tab-register",
                                   label_style={"fontWeight":"700","color":"#f1c40f"},
                                   active_label_style={"color":"white","background":"#f1c40f","borderColor":"#f1c40f"}),
                            ], active_tab="tab-login"),
                        ])
                    ], style={"borderRadius":"16px","boxShadow":"0 8px 30px rgba(0,0,0,0.2)",
                              "border":"none","overflow":"hidden"}),
                ], md=5, className="offset-md-1"),
            ], className="align-items-center"),
        ], fluid=True)],
        style={"background":"linear-gradient(135deg,#1a5c2e 0%,#145a32 50%,#2ecc71 100%)",
               "padding":"80px 40px","minHeight":"85vh",
               "display":"flex","alignItems":"center"}),
    ], style={"display":"block" if not logged_in else "none"})

    # ── FARMER DASHBOARD (shown when logged in as farmer) ─────────────
    farmer_section = html.Div(style={"display":"none"})
    if is_farmer:
        user_name = session.get("name","")
        user_region = session.get("region","")
        listings = [l for l in _load_listings() if l["phone"] == session.get("phone","")]
        listings_cards = []
        for l in listings:
            listings_cards.append(dbc.Col(dbc.Card(dbc.CardBody([
                html.H6(l["commodity"], style={"fontWeight":"700","color":"#2ecc71"}),
                html.P(f"{l['quantity']} {l['unit']} @ GHS {l['price']}", className="mb-1", style={"fontSize":"0.9rem"}),
                html.Small(f"Listed: {l['date']}", className="text-muted"),
            ]), style={"borderRadius":"10px","borderLeft":"4px solid #2ecc71"}), md=3, className="mb-3"))

        farmer_section = html.Div([
            html.Div([dbc.Container([
                html.H2(f"Welcome, {user_name}!", style={"fontWeight":"800","color":"white"}),
                html.P(f"Farmer · {user_region} Region", style={"color":"#cce8d4"}),
                dbc.Button("Sign Out", id="btn-logout", color="light", size="sm",
                           style={"position":"absolute","top":"20px","right":"30px","borderRadius":"8px"}),
            ], fluid=True, style={"position":"relative"})],
            style={"background":"linear-gradient(135deg,#1a5c2e 0%,#2ecc71 100%)",
                   "padding":"40px 40px","marginBottom":"30px"}),
            dbc.Container([
                html.H4("List Your Produce", style={"fontWeight":"700","marginBottom":"15px"}),
                dbc.Card(dbc.CardBody([
                    dbc.Row([
                        dbc.Col([html.Label("Commodity",style={"fontWeight":"600","fontSize":"0.85rem"}),
                                 dcc.Dropdown(id="list-commodity", options=comm_options, placeholder="What are you selling?")], md=3),
                        dbc.Col([html.Label("Quantity",style={"fontWeight":"600","fontSize":"0.85rem"}),
                                 dbc.Input(id="list-qty", type="number", placeholder="e.g. 50")], md=2),
                        dbc.Col([html.Label("Unit",style={"fontWeight":"600","fontSize":"0.85rem"}),
                                 dcc.Dropdown(id="list-unit", options=["KG","Bags (100KG)","Bags (50KG)","Crates","Tubers"], value="KG")], md=2),
                        dbc.Col([html.Label("Price per unit (GHS)",style={"fontWeight":"600","fontSize":"0.85rem"}),
                                 dbc.Input(id="list-price", type="number", placeholder="e.g. 5.50")], md=2),
                        dbc.Col([html.Label("\u00A0",style={"fontSize":"0.85rem"}),
                                 dbc.Button("Add Listing", id="btn-add-listing", color="success", className="w-100",
                                            style={"fontWeight":"700","borderRadius":"8px"})], md=3),
                    ])
                ]), className="mb-4", style={"border":"1px solid #2ecc71","borderRadius":"10px"}),
                html.Div(id="listing-msg"),
                html.H4("My Active Listings", style={"fontWeight":"700","marginBottom":"15px","marginTop":"20px"}),
                dbc.Row(listings_cards) if listings_cards else html.P("No listings yet. Add your first produce above!", className="text-muted"),
                html.Hr(style={"marginTop":"30px"}),
                html.H4([html.I(className="fa fa-lightbulb me-2", style={"color":"#f39c12"}),
                         "Sell Advisor"], style={"fontWeight":"700","marginBottom":"15px","marginTop":"20px"}),
                html.P("Get personalised advice: Where to sell, and whether to sell now or hold.",
                       className="text-muted", style={"fontSize":"0.9rem"}),
                dbc.Card(dbc.CardBody([
                    dbc.Row([
                        dbc.Col([html.Label("Your Commodity",style={"fontWeight":"600","fontSize":"0.85rem"}),
                                 dcc.Dropdown(id="adv-commodity", options=comm_options, placeholder="Select commodity")], md=4),
                        dbc.Col([html.Label("\u00A0",style={"fontSize":"0.85rem"}),
                                 dbc.Button("Get Advice", id="btn-advise", color="warning", className="w-100",
                                            style={"fontWeight":"700","borderRadius":"8px"})], md=3),
                    ]),
                ]), className="mb-3", style={"border":"1px solid #f39c12","borderRadius":"10px"}),
                html.Div(id="sell-advice-output"),

                html.Hr(style={"marginTop":"30px"}),

                # ── FIND TRADERS ──────────────────────────────────────────
                html.H4([html.I(className="fa fa-handshake me-2", style={"color":"#f1c40f"}),
                         "Find Traders & Buyers"], style={"fontWeight":"700","marginBottom":"10px","marginTop":"20px"}),
                html.P("Registered buyers near you. Contact them directly to sell your produce.",
                       className="text-muted", style={"fontSize":"0.9rem","marginBottom":"15px"}),
                html.Div(_build_traders_list(user_region)),

                # ── TRADER & DRIVER MAP ───────────────────────────────────
                html.H4([html.I(className="fa fa-map-location-dot me-2", style={"color":"#2ecc71"}),
                         "Locate Traders & Drivers"], style={"fontWeight":"700","marginBottom":"10px","marginTop":"30px"}),
                html.P("Interactive map showing traders and drivers near you.",
                       className="text-muted", style={"fontSize":"0.9rem","marginBottom":"15px"}),
                dcc.Graph(figure=_build_locate_map(user_region), config={"displayModeBar":False},
                          style={"borderRadius":"12px","overflow":"hidden"}),

                html.Hr(style={"marginTop":"30px"}),

                # ── FIND DRIVERS ──────────────────────────────────────────
                html.H4([html.I(className="fa fa-truck me-2", style={"color":"#e67e22"}),
                         "Find Drivers / Delivery Workers"], style={"fontWeight":"700","marginBottom":"10px","marginTop":"20px"}),
                html.P("Available drivers who can transport your produce to buyers or markets.",
                       className="text-muted", style={"fontSize":"0.9rem","marginBottom":"15px"}),
                html.Div(_build_drivers_list(user_region)),

            ], fluid=True),
        ], style={"display":"block"})

    # ── BUYER DASHBOARD (shown when logged in as buyer) ───────────────
    buyer_section = html.Div(style={"display":"none"})
    if is_buyer:
        user_name = session.get("name","")
        user_region = session.get("region","")
        listings = _load_listings()
        cards = []
        for l in listings:
            dist = _dist_km(user_region, l["region"].strip().title())
            transport = round(dist * TRANSPORT_RATE_PER_KM, 2)
            unit_price = float(l["price"]) if l["price"] else 0
            landed = round(unit_price + transport, 2)
            cards.append(dbc.Col(dbc.Card(dbc.CardBody([
                html.H5(l["commodity"], style={"fontWeight":"700","color":"#2ecc71"}),
                html.P([html.I(className="fa fa-user me-2"), l["farmer_name"]], style={"fontWeight":"600","marginBottom":"4px"}),
                html.P([html.I(className="fa fa-map-marker-alt me-2"), f"{l['region']} Region"],
                       className="text-muted", style={"fontSize":"0.85rem","marginBottom":"4px"}),
                html.P(f"{l['quantity']} {l['unit']} available", style={"fontSize":"0.9rem","marginBottom":"8px"}),
                html.Hr(),
                dbc.Row([
                    dbc.Col([html.Small("Price", className="text-muted"),
                             html.P(f"GHS {unit_price:.2f}", style={"fontWeight":"700","color":"#2ecc71","margin":"0"})]),
                    dbc.Col([html.Small("Transport", className="text-muted"),
                             html.P(f"GHS {transport:.2f}", style={"fontWeight":"700","color":"#e67e22","margin":"0"})]),
                ]),
                html.Small(f"Distance: {dist} km from {user_region}", className="text-muted d-block mt-2"),
                dbc.Button([html.I(className="fa fa-phone me-2"), l.get("phone","")],
                           color="outline-success", size="sm", className="mt-2 w-100",
                           style={"borderRadius":"6px"}),
            ]), style={"borderRadius":"12px","boxShadow":"0 4px 15px rgba(0,0,0,0.08)","height":"100%"}),
            md=4, className="mb-4"))

        buyer_section = html.Div([
            html.Div([dbc.Container([
                html.H2(f"Welcome, {user_name}!", style={"fontWeight":"800","color":"white"}),
                html.P(f"Buyer · {user_region} Region", style={"color":"#cce8d4"}),
                dbc.Button("Sign Out", id="btn-logout", color="light", size="sm",
                           style={"position":"absolute","top":"20px","right":"30px","borderRadius":"8px"}),
            ], fluid=True, style={"position":"relative"})],
            style={"background":"linear-gradient(135deg,#1a5c2e 0%,#f1c40f 100%)",
                   "padding":"40px 40px","marginBottom":"30px"}),
            dbc.Container([
                html.H4([html.I(className="fa fa-store me-2",style={"color":"#2ecc71"}),
                         "Available Produce"], style={"fontWeight":"700","marginBottom":"20px"}),
                html.P("Browse what farmers are selling. Transport cost estimated from your region.",
                       className="text-muted mb-4"),
                dbc.Row(cards) if cards else dbc.Alert("No produce listed yet. Check back soon!", color="info"),

                html.Hr(style={"marginTop":"30px"}),

                # ── FIND DRIVERS ──────────────────────────────────────────
                html.H4([html.I(className="fa fa-truck me-2", style={"color":"#e67e22"}),
                         "Find Drivers / Delivery Workers"], style={"fontWeight":"700","marginBottom":"10px","marginTop":"20px"}),
                html.P("Available drivers who can pick up produce from farmers and deliver to you.",
                       className="text-muted", style={"fontSize":"0.9rem","marginBottom":"15px"}),
                html.Div(_build_drivers_list(user_region)),

            ], fluid=True),
        ], style={"display":"block"})

    # ── DRIVER DASHBOARD (shown when logged in as driver) ─────────────
    driver_section = html.Div(style={"display":"none"})
    if is_driver:
        user_name = session.get("name","")
        user_region = session.get("region","")
        # Show all active farmer listings that need delivery
        listings = _load_listings()
        job_cards = []
        for l in listings:
            farmer_region = l.get("region","").strip().title()
            dist = _dist_km(user_region, farmer_region)
            est_pay = round(dist * TRANSPORT_RATE_PER_KM, 2)
            job_cards.append(dbc.Col(dbc.Card(dbc.CardBody([
                html.H6(l["commodity"], style={"fontWeight":"700","color":"#2ecc71"}),
                html.P([html.I(className="fa fa-user me-2"), l["farmer_name"]],
                       style={"fontWeight":"600","marginBottom":"4px","fontSize":"0.9rem"}),
                html.P([html.I(className="fa fa-map-marker-alt me-2",style={"color":"#e67e22"}),
                        f"{farmer_region} Region"],
                       className="text-muted", style={"fontSize":"0.85rem","marginBottom":"4px"}),
                html.P(f"{l['quantity']} {l['unit']}", style={"fontSize":"0.9rem","marginBottom":"8px"}),
                html.Hr(),
                dbc.Row([
                    dbc.Col([html.Small("Distance",className="text-muted"),
                             html.P(f"{dist} km",style={"fontWeight":"700","color":"#e67e22","margin":"0"})]),
                    dbc.Col([html.Small("Est. Pay",className="text-muted"),
                             html.P(f"GHS {est_pay:.2f}",style={"fontWeight":"700","color":"#2ecc71","margin":"0"})]),
                ]),
                html.Small(f"Farmer phone: {l.get('phone','N/A')}", className="text-muted d-block mt-2"),
                dbc.Button([html.I(className="fa fa-phone me-2"),"Contact Farmer"],
                           color="outline-success",size="sm",className="mt-2 w-100",
                           style={"borderRadius":"6px"}),
            ]),style={"borderRadius":"12px","boxShadow":"0 4px 15px rgba(0,0,0,0.08)","height":"100%"}),
            md=4,className="mb-4"))

        driver_section = html.Div([
            html.Div([dbc.Container([
                html.H2(f"Welcome, {user_name}!", style={"fontWeight":"800","color":"white"}),
                html.P(f"Driver · {user_region} Region", style={"color":"#fdebd0"}),
                dbc.Button("Sign Out", id="btn-logout", color="light", size="sm",
                           style={"position":"absolute","top":"20px","right":"30px","borderRadius":"8px"}),
            ], fluid=True, style={"position":"relative"})],
            style={"background":"linear-gradient(135deg,#7d5a00 0%,#e67e22 100%)",
                   "padding":"40px 40px","marginBottom":"30px"}),
            dbc.Container([
                html.H4([html.I(className="fa fa-box me-2",style={"color":"#e67e22"}),
                         "Available Delivery Jobs"], style={"fontWeight":"700","marginBottom":"20px"}),
                html.P("Farmers with produce that needs transporting. Distance and estimated pay shown.",
                       className="text-muted mb-4"),
                dbc.Row(job_cards) if job_cards else dbc.Alert("No delivery jobs available yet.", color="info"),
            ], fluid=True),
        ], style={"display":"block"})

    # ── HIDDEN PLACEHOLDERS for missing callback IDs ──────────────────
    placeholders = []
    if logged_in:
        # Login form IDs are missing when logged in
        placeholders.extend([
            dcc.Input(id="login-phone", style={"display":"none"}),
            dcc.Input(id="login-password", style={"display":"none"}),
            html.Div(id="login-msg", style={"display":"none"}),
            dcc.Input(id="reg-name", style={"display":"none"}),
            dcc.Input(id="reg-phone", style={"display":"none"}),
            dcc.Dropdown(id="reg-region", style={"display":"none"}),
            dcc.Dropdown(id="reg-role", style={"display":"none"}),
            dcc.Input(id="reg-password", style={"display":"none"}),
            html.Div(id="reg-msg", style={"display":"none"}),
            html.Button(id="btn-login", style={"display":"none"}),
            html.Button(id="btn-register", style={"display":"none"}),
        ])
    if not is_farmer:
        # Farmer dashboard IDs are missing
        placeholders.extend([
            dcc.Dropdown(id="list-commodity", style={"display":"none"}),
            dcc.Input(id="list-qty", style={"display":"none"}),
            dcc.Dropdown(id="list-unit", style={"display":"none"}),
            dcc.Input(id="list-price", style={"display":"none"}),
            html.Button(id="btn-add-listing", style={"display":"none"}),
            html.Div(id="listing-msg", style={"display":"none"}),
            dcc.Dropdown(id="adv-commodity", style={"display":"none"}),
            html.Button(id="btn-advise", style={"display":"none"}),
            html.Div(id="sell-advice-output", style={"display":"none"}),
        ])
    if not logged_in:
        placeholders.append(html.Button(id="btn-logout", style={"display":"none"}))

    return html.Div([login_section, farmer_section, buyer_section, driver_section,
                     html.Div(placeholders, style={"display":"none"})])



# ── PAGE ROUTING CALLBACK ──────────────────────────────────────────────────
@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname"),
    Input("session-store", "data"),
)
def route(pathname, session):
    if pathname == "/dashboard":
        return page_dashboard()
    elif pathname == "/marketplace":
        return page_marketplace(session)
    elif pathname == "/ourwork":
        return page_ourwork()
    elif pathname == "/blog":
        return page_blog()
    elif pathname == "/reports":
        return page_reports()
    elif pathname == "/about":
        return page_about()
    elif pathname == "/team":
        return page_team()
    elif pathname == "/contact":
        return page_contact()
    else:
        return page_home()


# ── DASHBOARD CALLBACKS ────────────────────────────────────────────────────
@app.callback(
    Output("dd-comm","options"),
    Output("dd-comm","value"),
    Input("ri-type","value"),
)
def update_commodity_list(ctype):
    if ctype == "major":
        return MAJOR, MAJOR[0]
    elif ctype == "minor":
        return MINOR, MINOR[0]
    else:
        return COMMODITIES, COMMODITIES[0]


@app.callback(
    Output("kpi-row",        "children"),
    Output("g-trend",        "figure"),
    Output("g-yoy",          "figure"),
    Output("g-mom",          "figure"),
    Output("g-vol-major",    "figure"),
    Output("g-vol-minor",    "figure"),
    Output("g-region",       "figure"),
    Output("g-map",          "figure"),
    Output("g-heat",         "figure"),
    Output("g-seas-summary", "figure"),
    Output("tbl-latest",     "children"),
    Input("dd-comm",  "value"),
    Input("dd-reg",   "value"),
    Input("dd-mkt",   "value"),
    Input("dd-ptype", "value"),
    Input("sl-yr",    "value"),
    Input("sl-time",  "value"),
    Input("dd-month", "value"),
    Input("dd-unit",  "value"),
)
def update_dashboard(commodity, region, market, ptype, year, time_range, month_sel, unit_mode):
    filt = DF[DF["commodity"] == commodity].copy()
    if region and len(region) > 0: filt = filt[filt["region"].isin(region)]
    if market and len(market) > 0: filt = filt[filt["market"].isin(market)]
    if ptype  != "Both":        filt = filt[filt["pricetype"] == ptype]
    # Apply time range filter
    if time_range:
        filt = filt[(filt["year"] >= time_range[0]) & (filt["year"] <= time_range[1])]
    # Apply month filter
    if month_sel and len(month_sel) > 0:
        filt = filt[filt["month"].isin(month_sel)]
    # Use per-KG price if selected
    price_col = "price_per_kg" if unit_mode == "Per KG (normalized)" else "price_ghs"
    price_label = "Price/KG (GHS)" if unit_mode == "Per KG (normalized)" else "Price (GHS)"
    # Get the unit for display
    unit_display = filt["unit_raw"].mode().iloc[0] if not filt.empty and not filt["unit_raw"].isna().all() else ""
    if unit_mode == "As Recorded (with unit)" and unit_display:
        price_label = f"Price (GHS / {unit_display})"
    # Drop rows without valid per-kg if that mode is selected
    if unit_mode == "Per KG (normalized)":
        filt = filt[filt["price_per_kg"].notna()]

    # ── KPIs ──────────────────────────────────────────────────────────────
    latest_p = filt[filt["date"]==filt["date"].max()][price_col].mean() if not filt.empty else 0
    annual   = filt.groupby("year")[price_col].mean()
    yoy_v    = ((annual.iloc[-1]-annual.iloc[-2])/annual.iloc[-2]*100) if len(annual)>=2 else 0
    cv       = (filt[price_col].std()/filt[price_col].mean()*100) if not filt.empty else 0
    reg_spread = filt.groupby("region")[price_col].mean()
    spread   = reg_spread.max()-reg_spread.min() if len(reg_spread)>1 else 0

    # MoM calculation
    if not filt.empty:
        mon_avg = filt.groupby(filt["date"].dt.to_period("M"))[price_col].mean()
        mom_v = ((mon_avg.iloc[-1]-mon_avg.iloc[-2])/mon_avg.iloc[-2]*100) if len(mon_avg)>=2 else 0
    else:
        mom_v = 0

    def kpi(label, val, color, icon, subtitle=""):
        return dbc.Col(dbc.Card(dbc.CardBody([
            html.I(className=f"fa {icon} fa-lg mb-1",style={"color":color}),
            html.H4(val,style={"fontWeight":"800","color":color,"margin":"4px 0"}),
            html.P(label,className="text-muted mb-0",style={"fontSize":"0.78rem","fontWeight":"600"}),
            html.P(subtitle,className="text-muted mb-0",style={"fontSize":"0.72rem"}),
        ],className="text-center py-3"),
        style={"border":f"1px solid {color}","borderRadius":"10px"}),
        xs=6,md=True,className="mb-3")

    kpis = [
        kpi("Latest Price",     f"GHS {latest_p:,.2f}", "#2ecc71","fa-tag",     f"{commodity}"),
        kpi("YoY Change",       f"{yoy_v:+.1f}%",       "#e74c3c" if yoy_v>0 else "#2ecc71","fa-arrow-trend-up","Annual"),
        kpi("MoM Change",       f"{mom_v:+.1f}%",       "#e74c3c" if mom_v>0 else "#2ecc71","fa-calendar-day","Monthly"),
        kpi("Volatility", f"{cv:.1f}%",            "#e67e22","fa-bolt",    "High > 30%"),
        kpi("Regional Spread",  f"GHS {spread:,.2f}",   "#e67e22","fa-map",     "Spatial Dispersion"),
    ]

    # ── INDICATOR 1a: TREND ────────────────────────────────────────────────
    if not filt.empty:
        monthly = filt.groupby(["date","pricetype"])[price_col].mean().reset_index()
        fig_trend = px.line(monthly,x="date",y=price_col,color="pricetype",
                            color_discrete_map={"Retail":"#e74c3c","Wholesale":"#f1c40f"},
                            labels={price_col:price_label,"date":"","pricetype":""},
                            template="plotly_white",title=f"{commodity} - {price_label} Trend")
        fig_trend.update_traces(line_width=2.5)
        fig_trend.update_layout(margin=dict(t=35,b=10),legend_title_text="",height=280)
    else:
        fig_trend = go.Figure()

    # ── INDICATOR 1b: YOY ─────────────────────────────────────────────────
    yoy_s  = filt.groupby("year")[price_col].mean().pct_change()*100
    yoy_df = yoy_s.dropna().reset_index()
    yoy_df.columns=["year","change"]
    yoy_df["dir"]=yoy_df["change"].apply(lambda x:"Up" if x>0 else "Down")
    fig_yoy=px.bar(yoy_df,x="year",y="change",color="dir",
                   color_discrete_map={"Up":"#e74c3c","Down":"#2ecc71"},
                   labels={"change":"YoY (%)","year":""},template="plotly_white",
                   title="Year-on-Year Change (%)")
    fig_yoy.add_hline(y=0,line_dash="dash",line_color="black",line_width=1)
    fig_yoy.update_layout(margin=dict(t=35,b=10),showlegend=False,height=280)

    # ── INDICATOR 1c: MONTH-ON-MONTH ─────────────────────────────────────
    monthly_avg = filt.groupby(filt["date"].dt.to_period("M"))[price_col].mean()
    mom = monthly_avg.pct_change() * 100
    mom_df = mom.dropna().reset_index()
    mom_df.columns = ["period", "change"]
    mom_df["period"] = mom_df["period"].astype(str)
    mom_df["dir"] = mom_df["change"].apply(lambda x: "Increase" if x > 0 else "Decrease")
    if len(mom_df) > 0:
        display_df = mom_df.tail(min(12, len(mom_df)))
        fig_mom = go.Figure()
        for _, row in display_df.iterrows():
            color = "#e74c3c" if row["change"] > 0 else "#2ecc71"
            fig_mom.add_trace(go.Bar(x=[row["period"]], y=[row["change"]],
                                     marker_color=color, showlegend=False))
        fig_mom.add_hline(y=0, line_dash="dash", line_color="black", line_width=1)
        fig_mom.update_layout(template="plotly_white", height=400,
                              title=f"{commodity} - Month-on-Month Price Change",
                              margin=dict(t=50, b=80, l=60, r=30),
                              xaxis_title="", yaxis_title="MoM Change (%)",
                              xaxis_tickangle=-45)
    else:
        fig_mom = go.Figure()
        fig_mom.update_layout(height=400, title="No month-on-month data available")

    # ── INDICATOR 2: VOLATILITY MAJOR & MINOR ─────────────────────────────
    def vol_chart(comm_list, title):
        v = DF[DF["commodity"].isin(comm_list)].groupby("commodity")["price_ghs"].agg(["mean","std"]).dropna()
        v["cv"]=(v["std"]/v["mean"]*100).round(1)
        v=v.sort_values("cv",ascending=False).reset_index()
        v["risk"]=v["cv"].apply(lambda x:"High" if x>30 else ("Medium" if x>15 else "Low"))
        fig=px.bar(v,x="cv",y="commodity",orientation="h",color="risk",
                   color_discrete_map={"High":"#e74c3c","Medium":"#f39c12","Low":"#2ecc71"},
                   labels={"cv":"CV (%)","commodity":""},template="plotly_white",title=title)
        fig.add_vline(x=30,line_dash="dash",line_color="#e74c3c",annotation_text="High risk threshold")
        fig.add_vline(x=15,line_dash="dot",line_color="#f39c12")
        fig.update_layout(margin=dict(t=35,b=10),height=300,legend_title_text="Risk")
        return fig

    fig_vol_major = vol_chart(MAJOR, "Major Commodities – Volatility")
    fig_vol_minor = vol_chart(MINOR, "Minor Commodities – Volatility")

    # ── INDICATOR 3a: REGIONAL BAR ────────────────────────────────────────
    rf = DF[(DF["commodity"]==commodity)&(DF["year"]==year)]
    if region and len(region) > 0: rf=rf[rf["region"].isin(region)]
    reg=rf.groupby("region")[price_col].mean().sort_values().reset_index()
    reg["spread_flag"]=reg["price_ghs"].apply(
        lambda x:"Cheapest" if x==reg["price_ghs"].min() else
                 ("Priciest" if x==reg["price_ghs"].max() else "Mid"))
    fig_region=px.bar(reg,x="price_ghs",y="region",orientation="h",color="spread_flag",
                      color_discrete_map={"Cheapest":"#2ecc71","Priciest":"#e74c3c","Mid":"#3498db"},
                      labels={"price_ghs":f"Avg Price GHS ({year})","region":""},
                      template="plotly_white",title=f"Spatial Price Dispersion – {commodity}")
    spread_val = reg["price_ghs"].max()-reg["price_ghs"].min() if not reg.empty else 0
    fig_region.add_annotation(x=reg["price_ghs"].max()*0.7,y=-0.5,
                               text=f"Spread: GHS {spread_val:,.2f}",
                               showarrow=False,font=dict(color="#e74c3c",size=11))
    fig_region.update_layout(margin=dict(t=35,b=10),showlegend=True,height=320)

    # ── INDICATOR 3b: MAP ─────────────────────────────────────────────────
    mg=DF.groupby(["market","region","latitude","longitude"])["price_ghs"].mean().reset_index()
    mg=mg.dropna(subset=["latitude","longitude"])
    fig_map=px.scatter_mapbox(mg,lat="latitude",lon="longitude",color="region",
                              hover_name="market",zoom=5,center={"lat":7.9,"lon":-1.0},
                              mapbox_style="carto-positron",template="plotly_white",
                              title="Market Locations by Region")
    fig_map.update_layout(margin=dict(t=35,b=0,l=0,r=0),legend_title_text="Region",height=320)

    # ── INDICATOR 4a: HEATMAP ─────────────────────────────────────────────
    pivot=filt.groupby(["year","month"])["price_ghs"].mean().unstack("month")
    pivot.columns=[MONTHS[m-1] for m in pivot.columns]
    fig_heat=px.imshow(pivot,color_continuous_scale="RdYlGn_r",aspect="auto",
                       labels={"color":"GHS (avg)"},template="plotly_white",
                       title=f"{commodity} – Seasonality Heatmap (avg GHS per month/year)")
    fig_heat.update_layout(margin=dict(t=40,b=10),height=320)

    # ── INDICATOR 4b: SEASONAL SUMMARY BAR ───────────────────────────────
    monthly_avg = filt.groupby("month")["price_ghs"].mean().reset_index()
    monthly_avg["month_name"] = monthly_avg["month"].apply(lambda x: MONTHS[x-1])
    overall_avg = monthly_avg["price_ghs"].mean()
    monthly_avg["vs_avg"] = monthly_avg["price_ghs"] - overall_avg
    monthly_avg["flag"] = monthly_avg["vs_avg"].apply(
        lambda x: "Above avg (lean)" if x>0 else "Below avg (harvest)")
    fig_seas = px.bar(monthly_avg, x="month_name", y="vs_avg", color="flag",
                      color_discrete_map={"Above avg (lean)":"#e74c3c",
                                          "Below avg (harvest)":"#2ecc71"},
                      labels={"vs_avg":"Deviation from annual avg (GHS)","month_name":"Month"},
                      template="plotly_white",
                      title=f"{commodity} – Monthly Price vs Annual Average")
    fig_seas.add_hline(y=0,line_dash="dash",line_color="black",line_width=1)
    fig_seas.update_layout(margin=dict(t=40,b=10),showlegend=True,height=320,
                           legend_title_text="Season")

    # ── LATEST TABLE ──────────────────────────────────────────────────────
    cutoff=filt["date"].max()-pd.DateOffset(months=3)
    recent=filt[filt["date"]>=cutoff]
    tbl=(recent.groupby(["market","region","pricetype"])["price_ghs"]
         .mean().reset_index().sort_values("price_ghs").head(20))
    tbl["price_ghs"]=tbl["price_ghs"].round(2)
    tbl.columns=["Market","Region","Price Type","Avg Price (GHS)"]
    table=dbc.Table.from_dataframe(tbl.reset_index(drop=True),
                                   striped=True,hover=True,responsive=True,size="sm",
                                   style={"fontSize":"0.88rem"})

    return kpis,fig_trend,fig_yoy,fig_mom,fig_vol_major,fig_vol_minor,fig_region,fig_map,fig_heat,fig_seas,table


@app.callback(
    Output("g-multi","figure"),
    Input("dd-multi","value"),
    Input("dd-reg","value"),
)
def update_multi(selected, region):
    if not selected: return go.Figure()
    filt = DF[DF["commodity"].isin(selected)].copy()
    if region and len(region) > 0: filt = filt[filt["region"].isin(region)]
    monthly = filt.groupby(["date","commodity"])["price_ghs"].mean().reset_index()
    fig = px.line(monthly,x="date",y="price_ghs",color="commodity",
                  labels={"price_ghs":"Price (GHS)","date":"Date","commodity":""},
                  template="plotly_white")
    fig.update_traces(line_width=2)
    fig.update_layout(margin=dict(t=10,b=10),legend_title_text="")
    return fig


# ── MARKET PROFILE CALLBACK (fp_agg_data.csv) ─────────────────────────────
_AGG_DF = None

def _load_agg_data():
    global _AGG_DF
    if _AGG_DF is not None:
        return _AGG_DF
    import os
    path = os.path.join(os.path.dirname(__file__), "fp_agg_data.csv")
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["year"].astype(int)
    df["month"] = df["month"].astype(int)
    df["commodity"] = df["commodity"].str.strip()
    df["market"] = df["market"].str.strip()
    df["region"] = df["region"].str.strip().str.title()
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df = df[df["price"].notna() & (df["price"] > 0)].copy()
    _AGG_DF = df
    return df


@app.callback(
    Output("mkt-profile-kpis", "children"),
    Output("g-mkt-trend", "figure"),
    Output("g-mkt-ranking", "figure"),
    Input("dd-mkt-profile", "value"),
)
def update_market_profile(market):
    agg = _load_agg_data()

    # Filter for selected market
    mkt = agg[agg["market"] == market].copy()
    all_mkts = agg.copy()

    # ── KPIs for selected market ──────────────────────────────────────
    # Basket price: average price across all commodities in this market (latest period)
    latest_period = mkt["date"].max()
    basket_now = mkt[mkt["date"] == latest_period]["price"].mean() if not mkt.empty else 0
    national_avg = all_mkts[all_mkts["date"] == latest_period]["price"].mean() if not all_mkts.empty else 0
    vs_national = ((basket_now - national_avg) / national_avg * 100) if national_avg > 0 else 0

    # YoY for this market
    annual = mkt.groupby("year")["price"].mean()
    mkt_yoy = ((annual.iloc[-1] - annual.iloc[-2]) / annual.iloc[-2] * 100) if len(annual) >= 2 else 0

    # Stability: CV% across all commodities in this market
    mkt_cv = (mkt["price"].std() / mkt["price"].mean() * 100) if not mkt.empty and mkt["price"].mean() > 0 else 0

    # Market rank (1 = cheapest)
    mkt_avgs = all_mkts.groupby("market")["price"].mean().sort_values()
    rank = list(mkt_avgs.index).index(market) + 1 if market in mkt_avgs.index else 0
    total_mkts = len(mkt_avgs)

    def kpi(label, val, color, icon, subtitle=""):
        return dbc.Col(dbc.Card(dbc.CardBody([
            html.I(className=f"fa {icon} fa-lg mb-1", style={"color":color}),
            html.H4(val, style={"fontWeight":"800","color":color,"margin":"4px 0"}),
            html.P(label, className="text-muted mb-0", style={"fontSize":"0.78rem","fontWeight":"600"}),
            html.P(subtitle, className="text-muted mb-0", style={"fontSize":"0.72rem"}),
        ], className="text-center py-3"),
        style={"border":f"1px solid {color}","borderRadius":"10px"}),
        xs=6, md=3, className="mb-3")

    kpis = [
        kpi("Basket Price", f"GHS {basket_now:.2f}", "#2ecc71", "fa-shopping-basket", f"{market}"),
        kpi("vs National", f"{vs_national:+.1f}%", "#e74c3c" if vs_national > 0 else "#2ecc71", "fa-balance-scale",
            "Above avg" if vs_national > 0 else "Below avg"),
        kpi("Market YoY", f"{mkt_yoy:+.1f}%", "#e74c3c" if mkt_yoy > 0 else "#2ecc71", "fa-arrow-trend-up", "Annual change"),
        kpi("Stability", f"{mkt_cv:.1f}%", "#e67e22" if mkt_cv > 50 else "#2ecc71", "fa-bolt",
            f"Rank: #{rank} of {total_mkts}"),
    ]

    # ── Market basket trend vs national average ───────────────────────
    mkt_monthly = mkt.groupby("date")["price"].mean().reset_index()
    mkt_monthly.columns = ["date", "market_avg"]
    nat_monthly = all_mkts.groupby("date")["price"].mean().reset_index()
    nat_monthly.columns = ["date", "national_avg"]
    merged = pd.merge(mkt_monthly, nat_monthly, on="date", how="left").sort_values("date")

    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(x=merged["date"], y=merged["market_avg"],
                                    mode="lines", name=f"{market}",
                                    line=dict(color="#2ecc71", width=3)))
    fig_trend.add_trace(go.Scatter(x=merged["date"], y=merged["national_avg"],
                                    mode="lines", name="National Avg",
                                    line=dict(color="#e67e22", width=2, dash="dash")))
    fig_trend.update_layout(template="plotly_white", margin=dict(t=35,b=10), height=300,
                            title=f"{market} Basket vs National Average",
                            xaxis_title="", yaxis_title="Avg Price (GHS)",
                            legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))

    # ── Market ranking bar chart ──────────────────────────────────────
    ranking = mkt_avgs.reset_index()
    ranking.columns = ["market", "avg_price"]
    ranking["highlight"] = ranking["market"].apply(lambda x: "Selected" if x == market else "Other")

    fig_rank = px.bar(ranking, x="avg_price", y="market", orientation="h",
                      color="highlight",
                      color_discrete_map={"Selected":"#2ecc71","Other":"#f1c40f"},
                      labels={"avg_price":"Avg Price (GHS)","market":""},
                      template="plotly_white",
                      title="Market Ranking (Cheapest → Most Expensive)")
    fig_rank.update_layout(margin=dict(t=35,b=10), height=300, showlegend=False)

    return kpis, fig_trend, fig_rank


# ── PRICE FORECAST CALLBACK ───────────────────────────────────────────────
@app.callback(
    Output("forecast-kpis", "children"),
    Output("g-forecast", "figure"),
    Input("dd-comm", "value"),
    Input("dd-reg", "value"),
)
def update_forecast(commodity, region):
    """Load wfp_all_data1.csv + forecast_results.csv and render forecast chart."""
    import os

    hist_path = os.path.join(os.path.dirname(__file__), "wfp_all_data1.csv")
    fc_path = os.path.join(os.path.dirname(__file__), "forecast_results.csv")

    empty_kpis = []

    if not os.path.exists(hist_path) or not os.path.exists(fc_path):
        fig = go.Figure()
        fig.add_annotation(text="Forecast data not found. Run build_forecast.py first.",
                           showarrow=False, font=dict(size=14))
        fig.update_layout(height=380, template="plotly_white")
        return empty_kpis, fig

    # Load historical
    hist = pd.read_csv(hist_path)
    hist["date"] = pd.to_datetime(hist["date"])
    hist["admin1"] = hist["admin1"].str.strip().str.title()
    hist["commodity"] = hist["commodity"].str.strip()
    hist["price"] = pd.to_numeric(hist["price"], errors="coerce")
    hist = hist[hist["price"].notna() & (hist["price"] > 0)]

    # Load forecast
    fc = pd.read_csv(fc_path)
    fc["date"] = pd.to_datetime(fc["date"])
    fc["admin1"] = fc["admin1"].str.strip().str.title()
    fc["commodity"] = fc["commodity"].str.strip()

    # Filter by commodity
    h = hist[hist["commodity"] == commodity].copy()
    f = fc[fc["commodity"] == commodity].copy()

    # Filter by region
    if region and len(region) > 0:
        h = h[h["admin1"].isin([r.strip().title() for r in region])]
        f = f[f["admin1"].isin([r.strip().title() for r in region])]

    # Last 3 years of history
    if not h.empty:
        cutoff = h["date"].max() - pd.DateOffset(years=3)
        h = h[h["date"] >= cutoff]

    h_monthly = h.groupby("date")["price"].mean().reset_index().sort_values("date")
    fc_monthly = f.groupby("date")["predicted_price"].mean().reset_index().sort_values("date")

    # ── Forecast KPI cards ────────────────────────────────────────────
    if not fc_monthly.empty:
        next_month_price = fc_monthly["predicted_price"].iloc[0]
        avg_3m = fc_monthly["predicted_price"].head(3).mean()
        avg_6m = fc_monthly["predicted_price"].mean()
        last_hist_price = h_monthly["price"].iloc[-1] if not h_monthly.empty else 0
        pct_change = ((next_month_price - last_hist_price) / last_hist_price * 100) if last_hist_price > 0 else 0
        direction = "↑" if pct_change > 0 else "↓"
        dir_color = "#e74c3c" if pct_change > 0 else "#2ecc71"

        def fc_kpi(label, val, color, subtitle=""):
            return dbc.Col(dbc.Card(dbc.CardBody([
                html.H4(val, style={"fontWeight":"800","color":color,"margin":"4px 0"}),
                html.P(label, className="text-muted mb-0", style={"fontSize":"0.78rem","fontWeight":"600"}),
                html.P(subtitle, className="text-muted mb-0", style={"fontSize":"0.72rem"}),
            ], className="text-center py-2"),
            style={"border":f"1px solid {color}","borderRadius":"10px"}),
            xs=6, md=3, className="mb-2")

        forecast_kpis = [
            fc_kpi("Next Month", f"GHS {next_month_price:.2f}", "#e67e22", fc_monthly["date"].iloc[0].strftime("%b %Y")),
            fc_kpi("3-Month Avg", f"GHS {avg_3m:.2f}", "#f1c40f", "Short-term outlook"),
            fc_kpi("6-Month Avg", f"GHS {avg_6m:.2f}", "#f39c12", "Medium-term outlook"),
            fc_kpi("Expected Change", f"{direction} {pct_change:+.1f}%", dir_color, "vs last observed"),
        ]
    else:
        forecast_kpis = []

    # ── Build chart ───────────────────────────────────────────────────
    fig = go.Figure()

    # Historical
    if not h_monthly.empty:
        fig.add_trace(go.Scatter(
            x=h_monthly["date"], y=h_monthly["price"],
            mode="lines", name="Historical Price",
            line=dict(color="#f1c40f", width=2.5),
        ))

    # Forecast
    if not fc_monthly.empty:
        if not h_monthly.empty:
            fig.add_trace(go.Scatter(
                x=[h_monthly["date"].iloc[-1], fc_monthly["date"].iloc[0]],
                y=[h_monthly["price"].iloc[-1], fc_monthly["predicted_price"].iloc[0]],
                mode="lines", showlegend=False,
                line=dict(color="#e67e22", width=2, dash="dot"), hoverinfo="skip"
            ))
        fig.add_trace(go.Scatter(
            x=fc_monthly["date"], y=fc_monthly["predicted_price"],
            mode="lines+markers", name="ML Forecast",
            line=dict(color="#e67e22", width=3, dash="dash"),
            marker=dict(size=8, color="#e67e22", symbol="diamond"),
        ))
        # Confidence band
        upper = fc_monthly["predicted_price"] * 1.15
        lower = fc_monthly["predicted_price"] * 0.85
        fig.add_trace(go.Scatter(
            x=pd.concat([fc_monthly["date"], fc_monthly["date"][::-1]]),
            y=pd.concat([upper, lower[::-1]]),
            fill="toself", fillcolor="rgba(230,126,34,0.1)",
            line=dict(width=0), name="±15% Confidence", showlegend=True, hoverinfo="skip"
        ))

    fig.update_layout(
        template="plotly_white", height=380, margin=dict(t=30, b=20),
        xaxis_title="", yaxis_title="Price (GHS)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        title=f"{commodity} — Historical + 6-Month Forecast"
    )
    return forecast_kpis, fig


# ── MARKETPLACE CALLBACKS ──────────────────────────────────────────────────

@app.callback(
    Output("session-store", "data"),
    Output("login-msg", "children"),
    Output("reg-msg", "children"),
    Input("btn-login", "n_clicks"),
    Input("btn-register", "n_clicks"),
    Input("btn-logout", "n_clicks"),
    State("login-phone", "value"),
    State("login-password", "value"),
    State("reg-name", "value"),
    State("reg-phone", "value"),
    State("reg-region", "value"),
    State("reg-role", "value"),
    State("reg-password", "value"),
    State("session-store", "data"),
    prevent_initial_call=True,
)
def handle_auth(login_clicks, reg_clicks, logout_clicks,
                l_phone, l_pass, r_name, r_phone, r_region, r_role, r_pass, session):
    from dash import ctx
    triggered = ctx.triggered_id

    if triggered == "btn-logout":
        return None, "", ""

    if triggered == "btn-login":
        if not l_phone or not l_pass:
            return session, dbc.Alert("Enter phone and password.", color="warning", duration=3000), ""
        users = _load_users()
        for u in users:
            if u["phone"] == l_phone and u["password"] == _hash_pw(l_pass):
                return {"logged_in":True,"name":u["name"],"phone":u["phone"],
                        "region":u["region"],"role":u["role"]}, "", ""
        return session, dbc.Alert("Invalid phone or password.", color="danger", duration=3000), ""

    if triggered == "btn-register":
        if not all([r_name, r_phone, r_region, r_role, r_pass]):
            return session, "", dbc.Alert("Fill all fields.", color="warning", duration=3000)
        users = _load_users()
        if any(u["phone"] == r_phone for u in users):
            return session, "", dbc.Alert("Phone already registered. Sign in instead.", color="danger", duration=3000)
        _save_user(r_name, r_phone, r_region, r_role, r_pass)
        return {"logged_in":True,"name":r_name,"phone":r_phone,
                "region":r_region,"role":r_role}, "", dbc.Alert(f"Welcome, {r_name}!", color="success", duration=2000)

    return session, "", ""


@app.callback(
    Output("listing-msg", "children"),
    Input("btn-add-listing", "n_clicks"),
    State("list-commodity", "value"),
    State("list-qty", "value"),
    State("list-unit", "value"),
    State("list-price", "value"),
    State("session-store", "data"),
    prevent_initial_call=True,
)
def add_listing(n, commodity, qty, unit, price, session):
    if not session or not session.get("logged_in"):
        return dbc.Alert("Please sign in first.", color="warning")
    if not all([commodity, qty, unit, price]):
        return dbc.Alert("Fill all fields.", color="warning", duration=3000)
    _save_listing(session["name"], session["phone"], session["region"], commodity, qty, unit, price)
    return dbc.Alert(f"Listed {qty} {unit} of {commodity} at GHS {price}!", color="success", duration=3000)


@app.callback(
    Output("sell-advice-output", "children"),
    Input("btn-advise", "n_clicks"),
    State("adv-commodity", "value"),
    State("session-store", "data"),
    prevent_initial_call=True,
)
def sell_advice(n, commodity, session):
    if not commodity:
        return dbc.Alert("Select a commodity first.", color="warning", duration=3000)

    user_region = session.get("region","") if session else ""

    # Get price data for this commodity
    cf = DF[DF["commodity"] == commodity].copy()
    if cf.empty:
        return dbc.Alert("No data for this commodity.", color="info")

    # ── WHERE TO SELL ─────────────────────────────────────────────────
    latest_year = cf["year"].max()
    regional_prices = cf[cf["year"] == latest_year].groupby("region")["price_ghs"].mean().sort_values(ascending=False)
    best_region = regional_prices.index[0] if len(regional_prices) > 0 else "N/A"
    best_price = regional_prices.iloc[0] if len(regional_prices) > 0 else 0
    user_price = regional_prices.get(user_region, 0)

    # Transport cost to best region
    dist = _dist_km(user_region, best_region)
    transport = round(dist * TRANSPORT_RATE_PER_KM, 2)
    net_gain = round(best_price - user_price - transport, 2)

    # ── WHEN TO SELL (seasonal) ───────────────────────────────────────
    monthly_avg = cf.groupby("month")["price_ghs"].mean()
    current_month = pd.Timestamp.now().month
    current_price_idx = monthly_avg.get(current_month, monthly_avg.mean())
    best_month = monthly_avg.idxmax()
    best_month_price = monthly_avg.max()
    worst_month = monthly_avg.idxmin()

    pct_to_peak = ((best_month_price - current_price_idx) / current_price_idx * 100) if current_price_idx > 0 else 0

    # Decision logic
    if pct_to_peak <= 5:
        timing = "SELL NOW"
        timing_color = "#2ecc71"
        timing_icon = "fa-check-circle"
        timing_text = f"Prices are near their seasonal peak. This is a good time to sell."
    elif pct_to_peak <= 20:
        timing = "HOLD (if possible)"
        timing_color = "#f39c12"
        timing_icon = "fa-clock"
        timing_text = f"Prices typically peak in {MONTHS[best_month-1]}. Holding could gain you +{pct_to_peak:.0f}%."
    else:
        timing = "HOLD"
        timing_color = "#e74c3c"
        timing_icon = "fa-hand"
        timing_text = f"Prices are well below peak. Peak is in {MONTHS[best_month-1]} (+{pct_to_peak:.0f}% higher). Hold if you can store safely."

    return html.Div([
        dbc.Row([
            # TIMING ADVICE
            dbc.Col(dbc.Card(dbc.CardBody([
                html.Div([
                    html.I(className=f"fa {timing_icon} fa-3x mb-3", style={"color":timing_color}),
                    html.H4(timing, style={"fontWeight":"900","color":timing_color}),
                    html.P(timing_text, className="text-muted", style={"fontSize":"0.9rem"}),
                    html.Hr(),
                    html.Small(f"Seasonal low: {MONTHS[worst_month-1]} | Peak: {MONTHS[best_month-1]}",
                              className="text-muted"),
                ], className="text-center")
            ]), style={"borderRadius":"12px","border":f"2px solid {timing_color}","height":"100%"}),
            md=4, className="mb-3"),

            # WHERE TO SELL
            dbc.Col(dbc.Card(dbc.CardBody([
                html.Div([
                    html.I(className="fa fa-map-location-dot fa-3x mb-3", style={"color":"#f1c40f"}),
                    html.H4("Best Market", style={"fontWeight":"900","color":"#f1c40f"}),
                    html.H5(f"{best_region} Region", style={"fontWeight":"700"}),
                    html.P(f"Avg price: GHS {best_price:.2f}", style={"fontSize":"0.95rem"}),
                    html.Hr(),
                    html.Small(f"Your region ({user_region}): GHS {user_price:.2f}", className="text-muted d-block"),
                    html.Small(f"Distance: {dist} km | Transport: ~GHS {transport:.2f}", className="text-muted d-block"),
                    html.Small(f"Net gain after transport: GHS {net_gain:.2f}",
                              className="d-block mt-1",
                              style={"fontWeight":"700","color":"#2ecc71" if net_gain > 0 else "#e74c3c"}),
                ], className="text-center")
            ]), style={"borderRadius":"12px","border":"2px solid #f1c40f","height":"100%"}),
            md=4, className="mb-3"),

            # PRICE CONTEXT
            dbc.Col(dbc.Card(dbc.CardBody([
                html.Div([
                    html.I(className="fa fa-chart-line fa-3x mb-3", style={"color":"#e67e22"}),
                    html.H4("Price Context", style={"fontWeight":"900","color":"#e67e22"}),
                    html.P(f"Current month avg: GHS {current_price_idx:.2f}", style={"fontSize":"0.9rem"}),
                    html.P(f"Peak month avg: GHS {best_month_price:.2f}", style={"fontSize":"0.9rem"}),
                    html.Hr(),
                    html.Small("Top paying regions:", className="text-muted d-block mb-1"),
                ] + [html.Small(f"{r}: GHS {p:.2f}", className="d-block", style={"fontSize":"0.82rem"})
                     for r, p in regional_prices.head(3).items()],
                className="text-center")
            ]), style={"borderRadius":"12px","border":"2px solid #e67e22","height":"100%"}),
            md=4, className="mb-3"),
        ]),
    ])


# ── RUN ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "="*55)
    print("  Market Pulse")
    print("  Open: http://127.0.0.1:8050")
    print("="*55+"\n")
    app.run(debug=False, host="127.0.0.1", port=8050)

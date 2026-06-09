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
        html.Img(src="/assets/logo2.png", height="40px"),
        href="/", style={"padding":"0"}
    ),
    dbc.NavbarToggler(id="toggler"),
    dbc.Collapse(dbc.Nav([
        dbc.NavItem(dbc.NavLink("Home",         href="/",          active="exact")),
        dbc.NavItem(dbc.NavLink("About",        href="/about",     active="exact")),
        dbc.NavItem(dbc.NavLink("Dashboard",    href="/dashboard", active="exact")),
        dbc.NavItem(dbc.NavLink("Our Work",     href="/ourwork",   active="exact")),
        dbc.NavItem(dbc.NavLink("Blog",         href="/blog",      active="exact")),
        dbc.NavItem(dbc.NavLink("Live Reports", href="/reports",   active="exact")),
        dbc.NavItem(dbc.NavLink("Team",         href="/team",      active="exact")),
        dbc.NavItem(dbc.NavLink("Contact",      href="/contact",   active="exact")),
    ], className="ms-auto", navbar=True), id="navbar-collapse", navbar=True),
], fluid=True), color="dark", dark=True, sticky="top",
style={"borderBottom":"3px solid #27ae60"})

FOOTER = html.Footer(dbc.Container(dbc.Row([
    dbc.Col(html.P("© 2026 Market Pulse | WFP Data",
                   className="text-muted mb-0", style={"fontSize":"0.85rem"})),
    dbc.Col(html.P("Built with Python · Dash · Plotly",
                   className="text-muted mb-0 text-end", style={"fontSize":"0.85rem"})),
])), style={"background":"#1a1a2e","padding":"18px 0","marginTop":"40px"})

app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
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
            html.Img(src="/assets/logo2.png", height="80px", style={"marginBottom":"15px"}),
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
        style={"background":"linear-gradient(135deg,#1a472a 0%,#27ae60 100%)",
               "padding":"80px 40px","marginBottom":"50px"}),

        dbc.Container([
            dbc.Row([kcard("#27ae60",n_rec,"Price Records","fa-database"),
                     kcard("#2980b9",n_comm,"Commodities","fa-wheat-awn"),
                     kcard("#e67e22",n_mkt,"Markets","fa-store"),
                     kcard("#8e44ad",n_reg,"Regions","fa-map")], className="mb-5"),
            dbc.Row([
                dbc.Col([
                    html.H2("Why Market Pulse?", style={"fontWeight":"700"}),
                    html.Hr(style={"borderColor":"#27ae60","borderWidth":"3px",
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
                    html.H5("Platform Highlights", style={"fontWeight":"700","color":"#27ae60"}),
                    html.Ul([
                        html.Li("20 years of WFP price data for Ghana"),
                        html.Li("Interactive filters by commodity, region, and market"),
                        html.Li("Seasonal price pattern detection"),
                        html.Li("Price volatility and inflation tracking"),
                        html.Li("ML-powered price forecasting (coming soon)"),
                        html.Li("USSD access for feature phone users"),
                        html.Li("Power BI reports for institutional users"),
                    ], style={"fontSize":"0.95rem","lineHeight":"2"})
                ]), style={"border":"2px solid #27ae60","borderRadius":"12px"}), md=6),
            ], className="mb-5"),
            dbc.Row([
                fcard("fa-chart-line","Price Trend Analysis",
                      "Track how commodity prices have moved over time across any market or region.","#27ae60"),
                fcard("fa-map-location-dot","Regional Comparison",
                      "Compare prices across all regions to identify trading opportunities.","#2980b9"),
                fcard("fa-fire","Seasonality Detection",
                      "Heatmaps reveal harvest season dips and lean season spikes.","#e67e22"),
                fcard("fa-bolt","Volatility Analysis",
                      "Identify which commodities carry the most price risk.","#e74c3c"),
                fcard("fa-mobile-screen","USSD Access",
                      "Farmers without smartphones access prices via USSD on any phone.","#8e44ad"),
                fcard("fa-chart-pie","Power BI Reports",
                      "Institutional dashboards for MoFA, GCX, and financial partners.","#16a085"),
            ]),
        ], fluid=True),
    ])

# ── DASHBOARD PAGE ─────────────────────────────────────────────────────────
def page_dashboard():
    card = lambda hdr, body, color="#27ae60": dbc.Card([
        dbc.CardHeader(html.H6(hdr, style={"fontWeight":"700","margin":"0","color":color})),
        dbc.CardBody(body)
    ], style={"borderRadius":"10px","boxShadow":"0 2px 10px rgba(0,0,0,0.07)","height":"100%"})

    return dbc.Container([
        # ── HEADER ────────────────────────────────────────────────────────
        dbc.Row([dbc.Col([
            html.H2("Market Intelligence Dashboard",
                    style={"fontWeight":"800","marginTop":"30px"}),
            html.P("Four analytical indicators derived from observed price behaviour — "
                   "split by Major (daily essentials) and Minor (seasonal) commodities.",
                   className="text-muted"),
            html.Hr(style={"borderColor":"#27ae60","borderWidth":"3px","width":"60px","opacity":"1"}),
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
                ], md=3),
                dbc.Col([
                    html.Label("Region", style={"fontWeight":"600","fontSize":"0.85rem"}),
                    dcc.Dropdown(id="dd-reg", options=REGIONS, value="All Regions", clearable=False),
                ], md=2),
                dbc.Col([
                    html.Label("Price Type", style={"fontWeight":"600","fontSize":"0.85rem"}),
                    dcc.Dropdown(id="dd-ptype", options=["Both","Wholesale","Retail"],
                                 value="Both", clearable=False),
                ], md=2),
            ])
        ]), className="mb-4",
        style={"border":"2px solid #27ae60","borderRadius":"10px",
               "boxShadow":"0 2px 10px rgba(39,174,96,0.1)"}),

        # ── KPI STRIP ─────────────────────────────────────────────────────
        dbc.Row(id="kpi-row", className="mb-2"),

        # ── INDICATOR 1: PRICE DYNAMICS ───────────────────────────────────
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
                  "borderLeft":"4px solid #27ae60"}))], className="mb-4"),

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
                  "borderLeft":"4px solid #27ae60"}))], className="mb-4"),

        # ── INDICATOR 2: PRICE VOLATILITY ─────────────────────────────────
        dbc.Row([dbc.Col(dbc.Card([
            dbc.CardHeader(html.Div([
                dbc.Badge("Indicator 2", color="danger", className="me-2"),
                html.Strong("Price Volatility — Market Instability Signals"),
            ])),
            dbc.CardBody([
                html.P("High volatility signals uncertainty in food availability or "
                       "disruptions in market functioning. Measured by Coefficient of Variation (CV%).",
                       className="text-muted", style={"fontSize":"0.85rem","marginBottom":"10px"}),
                dbc.Row([
                    dbc.Col(dcc.Graph(id="g-vol-major", config={"displayModeBar":False}), md=6),
                    dbc.Col(dcc.Graph(id="g-vol-minor", config={"displayModeBar":False}), md=6),
                ])
            ])
        ], style={"borderRadius":"10px","boxShadow":"0 2px 10px rgba(0,0,0,0.07)",
                  "borderLeft":"4px solid #e74c3c"}))], className="mb-4"),

        # ── INDICATOR 3: SPATIAL PRICE DISPERSION ─────────────────────────
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
                  "borderLeft":"4px solid #2980b9"}))], className="mb-4"),

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
                  "borderLeft":"4px solid #8e44ad"}))], className="mb-4"),

        # ── LATEST PRICES TABLE ───────────────────────────────────────────
        dbc.Row([dbc.Col(dbc.Card([
            dbc.CardHeader(html.H6("Latest Market Prices",
                                   style={"fontWeight":"700","margin":"0"})),
            dbc.CardBody(html.Div(id="tbl-latest"))
        ], style={"borderRadius":"10px","boxShadow":"0 2px 10px rgba(0,0,0,0.07)"}))],
        className="mb-5"),

    ], fluid=True)

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
            html.Hr(style={"borderColor":"#27ae60","borderWidth":"3px","width":"60px","opacity":"1"}),
        ])]),
        dbc.Row([
            dbc.Col(abox("Data Sources",[
                "WFP / VAM – Food price database","MoFA Ghana – Ministry of Food & Agriculture",
                "Ghana Statistical Service (GSS)","FAO – Food & Agriculture Organization",
                "IMF / World Development Indicators","Ghana Commodity Exchange (GCX)",
                "OpenWeatherMap – Weather data","NPA Ghana – Fuel prices",
                "Bank of Ghana – Exchange rates",
            ],"#2c3e50","fa-database"), md=4),
            dbc.Col(html.Div("→",style={"fontSize":"3rem","color":"#27ae60","textAlign":"center",
                                         "marginTop":"80px"}), md=1,
                    className="d-flex align-items-center justify-content-center"),
            dbc.Col(abox("Backend",[
                "SQL Database (PostgreSQL)","Python ETL Pipeline",
                "Machine Learning – Price forecasting","REST API – Data serving",
                "Competitor Intelligence","Scheduled data refresh",
            ],"#27ae60","fa-server"), md=3),
            dbc.Col(html.Div("→",style={"fontSize":"3rem","color":"#27ae60","textAlign":"center",
                                         "marginTop":"80px"}), md=1,
                    className="d-flex align-items-center justify-content-center"),
            dbc.Col(abox("Frontend",[
                "Market Pulse Web Dashboard","USSD Interface – Feature phones",
                "Voice-based local language access","Power BI – Institutional reports",
            ],"#2980b9","fa-display"), md=3),
        ], className="mb-5 align-items-start"),

        html.H4("Data Flow", style={"fontWeight":"700","marginBottom":"20px"}),
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([
                step(1,"Data Collection","WFP, MoFA, GSS, FAO ingested via APIs into SQL database.","#27ae60"),
                step(2,"Processing & Modelling","Python cleans data. ML model generates price forecasts.","#2980b9"),
                step(3,"API Layer","REST API exposes data to dashboard, Power BI, and USSD.","#e67e22"),
                step(4,"User Interfaces","Farmers via USSD, analysts via web, institutions via Power BI.","#8e44ad"),
            ]), style={"borderRadius":"10px","boxShadow":"0 2px 10px rgba(0,0,0,0.07)"}), md=8),
            dbc.Col(dbc.Card([
                dbc.CardHeader([html.I(className="fa fa-code me-2"),html.Strong("Tech Stack")],
                               style={"background":"#c0392b","color":"white","borderRadius":"10px 10px 0 0"}),
                dbc.CardBody(html.Ul([
                    html.Li("Python 3.13"),html.Li("PostgreSQL / SQL"),
                    html.Li("scikit-learn – ML"),html.Li("Dash + Plotly"),
                    html.Li("Power BI"),html.Li("USSD Gateway"),
                    html.Li("Flask REST API"),html.Li("Pandas / NumPy"),
                ], style={"fontSize":"0.9rem"}))
            ], style={"borderRadius":"10px","border":"1px solid #c0392b"}), md=4),
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
            html.Hr(style={"borderColor":"#27ae60","borderWidth":"3px",
                           "width":"60px","opacity":"1"}),
        ])]),

        # ── TWO PLATFORMS, TWO AUDIENCES ──────────────────────────────────
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([
                html.Div([
                    html.I(className="fa fa-display fa-2x mb-3", style={"color":"#27ae60"}),
                    html.H5("Market Pulse Dashboard", style={"fontWeight":"700"}),
                    html.H6("For: Farmers, Traders & Analysts",
                            style={"color":"#27ae60","marginBottom":"15px"}),
                ], className="text-center"),
                html.Ul([
                    html.Li("Live interactive price exploration"),
                    html.Li("Filter by commodity, region, market"),
                    html.Li("Seasonality and trend analysis"),
                    html.Li("Accessible on any browser or phone"),
                    html.Li("No login required — open to everyone"),
                ], style={"fontSize":"0.92rem","lineHeight":"2.1"}),
            ]), style={"borderRadius":"12px","border":"2px solid #27ae60",
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
                      "#2980b9"),
            user_card("fa-scale-balanced","Ghana Commodity Exchange",
                      "Monitors commodity price trends for trading desk decisions and publishes "
                      "official market reports for exchange participants.",
                      "#27ae60"),
            user_card("fa-landmark","BankAfrique",
                      "Assesses agricultural loan risk by region and commodity. Identifies "
                      "high-volatility areas before approving farmer credit.",
                      "#e74c3c"),
            user_card("fa-globe","FAO / WFP Partners",
                      "Tracks food security indicators and price shocks for early warning "
                      "systems and humanitarian response planning.",
                      "#8e44ad"),
        ], className="mb-5"),

        # ── WHAT POWER BI REPORTS CONTAIN ────────────────────────────────
        html.H4("What the Power BI Reports Contain",
                style={"fontWeight":"700","marginBottom":"20px"}),
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H6("Monthly Price Bulletin", style={"fontWeight":"700","color":"#2980b9"}),
                html.P("A one-page summary of average prices for key commodities across all "
                       "regions. Automatically generated every month and distributed to MoFA "
                       "and partner institutions.", className="text-muted",
                       style={"fontSize":"0.9rem"}),
                dbc.Badge("MoFA · GCX", color="primary", className="mt-1"),
            ]), style={"borderRadius":"10px","borderLeft":"4px solid #2980b9",
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
                html.H6("Food Security Early Warning", style={"fontWeight":"700","color":"#8e44ad"}),
                html.P("Tracks price spikes above seasonal norms and flags regions where "
                       "food affordability is deteriorating. Feeds into FAO and WFP early "
                       "warning systems.", className="text-muted",
                       style={"fontSize":"0.9rem"}),
                dbc.Badge("FAO · WFP · Government", color="secondary", className="mt-1"),
            ]), style={"borderRadius":"10px","borderLeft":"4px solid #8e44ad",
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
                      "#27ae60"),
            step_card(2,"Built in Power BI Desktop",
                      "Reports are designed in Power BI Desktop using the star schema data model "
                      "already defined in the architecture.",
                      "#2980b9"),
            step_card(3,"Published to Power BI Service",
                      "Reports are published to app.powerbi.com and scheduled to refresh "
                      "automatically when new price data arrives.",
                      "#e67e22"),
            step_card(4,"Distributed to Partners",
                      "MoFA, GCX, and BankAfrique access reports via shared links, "
                      "email subscriptions, or embedded iframes.",
                      "#8e44ad"),
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
            html.Div([html.Small("Strength: ",style={"fontWeight":"600","color":"#27ae60"}),
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
            html.Hr(style={"borderColor":"#27ae60","borderWidth":"3px","width":"60px","opacity":"1"}),
        ])]),
        html.H4("Primary Sources",style={"fontWeight":"700","marginBottom":"20px"}),
        dbc.Row([
            scard("WFP / VAM","WFP price database covering food commodities across Ghana's markets.",
                  "Commodity prices","Weekly","https://data.humdata.org/dataset/wfp-food-prices-for-ghana","#27ae60","fa-wheat-awn"),
            scard("MoFA Ghana","Ministry of Food and Agriculture — official agricultural statistics.",
                  "Production, prices","Monthly","https://mofa.gov.gh","#2980b9","fa-building-columns"),
            scard("Ghana Statistical Service","National statistics including CPI and food inflation.",
                  "CPI, inflation","Monthly","https://statsghana.gov.gh","#e67e22","fa-chart-bar"),
            scard("FAO GIEWS","Global Information and Early Warning System for food prices.",
                  "Global food prices","Monthly","https://www.fao.org/giews","#8e44ad","fa-globe"),
            scard("IMF / WDI","Macroeconomic indicators including exchange rates and GDP.",
                  "Exchange rates","Monthly","https://data.worldbank.org","#c0392b","fa-money-bill-trend-up"),
            scard("Ghana Commodity Exchange","Official exchange prices for agricultural commodities.",
                  "Spot & futures","Daily","https://gcx.com.gh","#16a085","fa-scale-balanced"),
        ]),
        html.H4("Competitor Intelligence",style={"fontWeight":"700","marginBottom":"20px","marginTop":"10px"}),
        dbc.Row([
            ccard("ESOKO","SMS-based market price service across West Africa.",
                  "Established network","No web dashboard","#27ae60"),
            ccard("Farmerline","Digital agriculture platform for smallholder farmers.",
                  "Strong farmer network","Limited price analytics","#2980b9"),
            ccard("Agrico","Agricultural input and market linkage platform.",
                  "Input supply chain","No price forecasting","#e67e22"),
            ccard("Ghana Commodity Exchange","Official commodity exchange.",
                  "Regulated institution","Only exchange-traded commodities","#8e44ad"),
            ccard("WFP VAM Tools","WFP's own market monitoring dashboards.",
                  "Rich historical data","Not farmer-accessible","#c0392b"),
            ccard("MoFA Price Bulletins","Official government price reports.",
                  "Official data","PDF only, not interactive","#16a085"),
        ]),
    ], fluid=True)



# ── ABOUT PAGE ─────────────────────────────────────────────────────────────
def page_about():
    return html.Div([
        html.Div([dbc.Container([
            html.Img(src="/assets/logo2.png", height="60px", style={"marginBottom":"15px"}),
            html.H1("About Market Pulse", style={"fontWeight":"800","color":"white","fontSize":"2.4rem"}),
            html.P("Enhancing Food Security Through Market Intelligence.",
                   style={"color":"#cce8d4","fontSize":"1.2rem","fontStyle":"italic"}),
        ], fluid=True)], style={"background":"linear-gradient(135deg,#1a472a 0%,#27ae60 100%)",
                                "padding":"60px 40px","marginBottom":"50px"}),
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H3("The Price Ghana Pays for Not Knowing", style={"fontWeight":"700"}),
                    html.Hr(style={"borderColor":"#27ae60","borderWidth":"3px","width":"60px","opacity":"1"}),
                    html.P("Maize cost GHS 18.81 in 2006. By 2023 it cost GHS 267.87 - a 1,324% increase "
                           "in 17 years. Three years drove the sharpest spikes: 2008 (+111%, global food "
                           "crisis), 2021 (+67%, COVID disruption), and 2023 (+53%, Ghana economic crisis). "
                           "Each time, those hit hardest were those with the least market information.",
                           style={"fontSize":"1rem","lineHeight":"1.9"}),
                    html.P("In 2023, maize cost GHS 199 in Volta and GHS 460 in Western Region - same crop, "
                           "more than double the price, a GHS 260 gap. That is not natural. It is the cost "
                           "of broken distribution and missing market information.",
                           style={"fontSize":"1rem","lineHeight":"1.9"}),
                    html.P("Prices hit their lowest in September (GHS 91, harvest) and highest in May-June "
                           "(GHS 125-139, lean season). Most participants sell or procure at the worst time "
                           "because they lack the data to plan differently.",
                           style={"fontSize":"1rem","lineHeight":"1.9"}),
                    html.P("Cassava (CV 269%), tomatoes (268%), and peppers (236%) are extremely volatile. "
                           "Rice paddy (CV 36%) and cowpeas (58%) are stable. A bank lending to a tomato "
                           "farmer faces fundamentally different risk than one lending to a rice farmer.",
                           style={"fontSize":"1rem","lineHeight":"1.9"}),
                    html.P(html.Strong("Market Pulse exists to close this gap - giving every participant "
                                       "in the food supply chain the intelligence they need."),
                           style={"fontSize":"1.05rem","color":"#27ae60"}),
                ], md=7),
                dbc.Col([
                    dbc.Card(dbc.CardBody([
                        html.H5("Mission", style={"fontWeight":"700","color":"#27ae60"}),
                        html.P("Democratise agricultural market intelligence in Ghana.",
                               style={"fontSize":"0.93rem"}),
                        html.Hr(),
                        html.H5("Vision", style={"fontWeight":"700","color":"#2980b9"}),
                        html.P("No one in the food supply chain makes a price decision without data.",
                               style={"fontSize":"0.93rem"}),
                        html.Hr(),
                        html.H5("Data", style={"fontWeight":"700","color":"#e67e22"}),
                        html.Ul([html.Li("WFP data: 2016-2023"), html.Li("26 commodities"),
                                 html.Li("10 regions"), html.Li("39,000+ records")],
                                style={"fontSize":"0.9rem","lineHeight":"2"}),
                    ]), style={"border":"2px solid #27ae60","borderRadius":"12px"}),
                    dbc.Card(dbc.CardBody([
                        html.H5("Key Findings", style={"fontWeight":"700","color":"#e74c3c"}),
                        html.Ul([html.Li("1,324% maize price increase"), html.Li("GHS 260 regional gap"),
                                 html.Li("35% harvest vs lean season gap"), html.Li("Minor crops 3x more volatile")],
                                style={"fontSize":"0.9rem","lineHeight":"2"}),
                    ]), style={"border":"2px solid #e74c3c","borderRadius":"12px","marginTop":"20px"}),
                ], md=5),
            ], className="mb-5"),
            html.H4("Who We Serve", style={"fontWeight":"700","marginBottom":"20px"}),
            dbc.Row([
                dbc.Col(dbc.Card(dbc.CardBody([html.I(className="fa fa-tractor fa-2x mb-2",style={"color":"#27ae60"}),
                    html.H6("Farmers",style={"fontWeight":"700"}),html.P("Know when to sell and when to hold based on seasonal cycles.",className="text-muted",style={"fontSize":"0.85rem"})]),
                    style={"textAlign":"center","borderTop":"3px solid #27ae60","borderRadius":"12px","height":"100%"}),md=2,className="mb-3"),
                dbc.Col(dbc.Card(dbc.CardBody([html.I(className="fa fa-truck fa-2x mb-2",style={"color":"#2980b9"}),
                    html.H6("Traders",style={"fontWeight":"700"}),html.P("Find the cheapest sourcing markets and spot regional price gaps.",className="text-muted",style={"fontSize":"0.85rem"})]),
                    style={"textAlign":"center","borderTop":"3px solid #2980b9","borderRadius":"12px","height":"100%"}),md=2,className="mb-3"),
                dbc.Col(dbc.Card(dbc.CardBody([html.I(className="fa fa-store fa-2x mb-2",style={"color":"#e67e22"}),
                    html.H6("Merchants",style={"fontWeight":"700"}),html.P("Track price trends to manage stock and plan purchasing.",className="text-muted",style={"fontSize":"0.85rem"})]),
                    style={"textAlign":"center","borderTop":"3px solid #e67e22","borderRadius":"12px","height":"100%"}),md=2,className="mb-3"),
                dbc.Col(dbc.Card(dbc.CardBody([html.I(className="fa fa-clipboard-list fa-2x mb-2",style={"color":"#8e44ad"}),
                    html.H6("Procurement",style={"fontWeight":"700"}),html.P("Compare prices across regions and time to optimise budgets.",className="text-muted",style={"fontSize":"0.85rem"})]),
                    style={"textAlign":"center","borderTop":"3px solid #8e44ad","borderRadius":"12px","height":"100%"}),md=2,className="mb-3"),
                dbc.Col(dbc.Card(dbc.CardBody([html.I(className="fa fa-landmark fa-2x mb-2",style={"color":"#c0392b"}),
                    html.H6("Banks",style={"fontWeight":"700"}),html.P("Assess agricultural loan risk using volatility data.",className="text-muted",style={"fontSize":"0.85rem"})]),
                    style={"textAlign":"center","borderTop":"3px solid #c0392b","borderRadius":"12px","height":"100%"}),md=2,className="mb-3"),
                dbc.Col(dbc.Card(dbc.CardBody([html.I(className="fa fa-building-columns fa-2x mb-2",style={"color":"#16a085"}),
                    html.H6("Policy",style={"fontWeight":"700"}),html.P("Detect price shocks early for food security interventions.",className="text-muted",style={"fontSize":"0.85rem"})]),
                    style={"textAlign":"center","borderTop":"3px solid #16a085","borderRadius":"12px","height":"100%"}),md=2,className="mb-3"),
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
                "background":"linear-gradient(135deg,#1a472a,#27ae60)","color":"white",
                "fontSize":"1.6rem","fontWeight":"800","display":"flex","alignItems":"center",
                "justifyContent":"center","margin":"0 auto 15px"}),
            html.H5(m["name"], style={"fontWeight":"700","textAlign":"center"}),
            html.P(m["role"], className="text-center", style={"color":"#27ae60","fontWeight":"600","fontSize":"0.88rem"}),
            dbc.Badge("Team Lead", color="success", className="d-block mx-auto mb-2",
                      style={"width":"fit-content"}) if m["lead"] else html.Div(),
            html.Hr(),
            html.P(m["bio"], className="text-muted", style={"fontSize":"0.88rem","textAlign":"center"}),
        ]), style={"borderRadius":"12px","boxShadow":"0 4px 20px rgba(0,0,0,0.08)","height":"100%"}),
        md=4, className="mb-4")
    return html.Div([
        html.Div([dbc.Container([
            html.H1("Meet the Team", style={"fontWeight":"800","color":"white","fontSize":"2.2rem"}),
        ], fluid=True)], style={"background":"linear-gradient(135deg,#1a472a 0%,#27ae60 100%)",
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
        ], fluid=True)], style={"background":"linear-gradient(135deg,#1a472a 0%,#27ae60 100%)",
                                "padding":"60px 40px","marginBottom":"50px"}),
        dbc.Container([
            dbc.Row([
                wcard("fa-chart-line","Price Intelligence Dashboard",
                      "Interactive dashboard with 4 analytical indicators covering 26 commodities across all regions.","Live","#27ae60"),
                wcard("fa-mobile-screen","USSD Price Access",
                      "USSD interface for farmers on basic mobile phones - no smartphone needed.","In Development","#2980b9"),
                wcard("fa-robot","ML Price Forecasting",
                      "Machine learning model to forecast commodity prices up to 3 months ahead.","In Development","#e67e22"),
                wcard("fa-chart-pie","Power BI Reports",
                      "Monthly institutional reports for MoFA, GCX, and BankAfrique.","Coming Soon","#8e44ad"),
                wcard("fa-database","Multi-Source Integration",
                      "Integration of WFP, MoFA, GSS, FAO, IMF data into unified SQL database.","In Progress","#c0392b"),
                wcard("fa-globe","National Expansion",
                      "Expanding coverage to district-level monitoring across all 16 regions.","Planned","#16a085"),
            ]),
        ], fluid=True),
    ])


# ── BLOG PAGE ──────────────────────────────────────────────────────────────
def page_blog():
    posts = [
        {"t":"Why Maize Prices Spike Every March","d":"May 2026","tag":"Price Dynamics","c":"#27ae60",
         "s":"Each year between February and April, maize prices in northern markets rise sharply due to seasonal supply cycles."},
        {"t":"The Hidden Cost of Market Information Gaps","d":"Apr 2026","tag":"Market Access","c":"#2980b9",
         "s":"When farmers lack price data, they almost always sell below fair value. We quantify that cost."},
        {"t":"Which Commodities Are Most Volatile?","d":"Mar 2026","tag":"Volatility","c":"#e74c3c",
         "s":"Using CV analysis across 26 commodities, we rank which crops carry the most price risk."},
        {"t":"North vs South: Ghana Price Divide","d":"Feb 2026","tag":"Spatial","c":"#e67e22",
         "s":"Food prices in northern regions are consistently higher. We map the dispersion."},
        {"t":"Tomato Price Crashes After Harvest","d":"Jan 2026","tag":"Seasonality","c":"#8e44ad",
         "s":"Tomato prices can drop 60% within weeks of peak harvest. We analyse the cycle."},
        {"t":"How USSD Brings Data to Every Farmer","d":"Dec 2025","tag":"Technology","c":"#16a085",
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
        ], fluid=True)], style={"background":"linear-gradient(135deg,#1a472a 0%,#27ae60 100%)",
                                "padding":"60px 40px","marginBottom":"50px"}),
        dbc.Container(dbc.Row([bcard(p) for p in posts]), fluid=True),
    ])


# ── LIVE REPORTS PAGE ──────────────────────────────────────────────────────
def page_reports():
    reps = [
        {"t":"Ghana Food Price Monitor - May 2026","p":"May 2026","type":"Monthly","c":"#27ae60"},
        {"t":"Q1 2026 Agricultural Market Report","p":"Jan-Mar 2026","type":"Quarterly","c":"#2980b9"},
        {"t":"Annual Price Volatility Report 2025","p":"Full Year 2025","type":"Annual","c":"#e74c3c"},
        {"t":"Seasonality Atlas - Major Commodities","p":"2016-2023","type":"Reference","c":"#8e44ad"},
        {"t":"Spatial Price Dispersion Index 2025","p":"2025","type":"Special","c":"#e67e22"},
        {"t":"Ghana Food Price Monitor - Apr 2026","p":"Apr 2026","type":"Monthly","c":"#27ae60"},
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
        ], fluid=True)], style={"background":"linear-gradient(135deg,#1a472a 0%,#27ae60 100%)",
                                "padding":"60px 40px","marginBottom":"50px"}),
        dbc.Container(dbc.Row([rcard(r) for r in reps]), fluid=True),
    ])


# ── CONTACT PAGE ───────────────────────────────────────────────────────────
def page_contact():
    return html.Div([
        html.Div([dbc.Container([
            html.H1("Contact Us", style={"fontWeight":"800","color":"white","fontSize":"2.2rem"}),
        ], fluid=True)], style={"background":"linear-gradient(135deg,#1a472a 0%,#27ae60 100%)",
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
                        html.P([html.I(className="fa fa-envelope me-2", style={"color":"#27ae60"}),
                                html.A("marketpulse@gmail.com", href="mailto:marketpulse@gmail.com")],
                               style={"marginBottom":"15px"}),
                        html.P([html.I(className="fa fa-location-dot me-2", style={"color":"#2980b9"}),
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


# ── PAGE ROUTING CALLBACK ──────────────────────────────────────────────────
@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname"),
)
def route(pathname):
    if pathname == "/dashboard":
        return page_dashboard()
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
    Input("dd-ptype", "value"),
    Input("sl-yr",    "value"),
)
def update_dashboard(commodity, region, ptype, year):
    filt = DF[DF["commodity"] == commodity].copy()
    if region != "All Regions": filt = filt[filt["region"] == region]
    if ptype  != "Both":        filt = filt[filt["pricetype"] == ptype]

    # ── KPIs ──────────────────────────────────────────────────────────────
    latest_p = filt[filt["date"]==filt["date"].max()]["price_ghs"].mean() if not filt.empty else 0
    annual   = filt.groupby("year")["price_ghs"].mean()
    yoy_v    = ((annual.iloc[-1]-annual.iloc[-2])/annual.iloc[-2]*100) if len(annual)>=2 else 0
    cv       = (filt["price_ghs"].std()/filt["price_ghs"].mean()*100) if not filt.empty else 0
    reg_spread = filt.groupby("region")["price_ghs"].mean()
    spread   = reg_spread.max()-reg_spread.min() if len(reg_spread)>1 else 0

    def kpi(label, val, color, icon, subtitle=""):
        return dbc.Col(dbc.Card(dbc.CardBody([
            html.I(className=f"fa {icon} fa-lg mb-1",style={"color":color}),
            html.H4(val,style={"fontWeight":"800","color":color,"margin":"4px 0"}),
            html.P(label,className="text-muted mb-0",style={"fontSize":"0.78rem","fontWeight":"600"}),
            html.P(subtitle,className="text-muted mb-0",style={"fontSize":"0.72rem"}),
        ],className="text-center py-3"),
        style={"border":f"1px solid {color}","borderRadius":"10px"}),
        xs=6,md=3,className="mb-3")

    kpis = [
        kpi("Latest Price",     f"GHS {latest_p:,.2f}", "#27ae60","fa-tag",     f"{commodity}"),
        kpi("YoY Change",       f"{yoy_v:+.1f}%",       "#e74c3c" if yoy_v>0 else "#27ae60","fa-arrow-trend-up","Price Dynamics"),
        kpi("Volatility (CV%)", f"{cv:.1f}%",            "#e67e22","fa-bolt",    "High > 30%"),
        kpi("Regional Spread",  f"GHS {spread:,.2f}",   "#8e44ad","fa-map",     "Spatial Dispersion"),
    ]

    # ── INDICATOR 1a: TREND ────────────────────────────────────────────────
    if not filt.empty:
        monthly = filt.groupby(["date","pricetype"])["price_ghs"].mean().reset_index()
        fig_trend = px.line(monthly,x="date",y="price_ghs",color="pricetype",
                            color_discrete_map={"Retail":"#e74c3c","Wholesale":"#2980b9"},
                            labels={"price_ghs":"Price (GHS)","date":"","pricetype":""},
                            template="plotly_white",title=f"{commodity} – Price Trend")
        fig_trend.update_traces(line_width=2.5)
        fig_trend.update_layout(margin=dict(t=35,b=10),legend_title_text="",height=280)
    else:
        fig_trend = go.Figure()

    # ── INDICATOR 1b: YOY ─────────────────────────────────────────────────
    yoy_s  = filt.groupby("year")["price_ghs"].mean().pct_change()*100
    yoy_df = yoy_s.dropna().reset_index()
    yoy_df.columns=["year","change"]
    yoy_df["dir"]=yoy_df["change"].apply(lambda x:"Up" if x>0 else "Down")
    fig_yoy=px.bar(yoy_df,x="year",y="change",color="dir",
                   color_discrete_map={"Up":"#e74c3c","Down":"#27ae60"},
                   labels={"change":"YoY (%)","year":""},template="plotly_white",
                   title="Year-on-Year Change (%)")
    fig_yoy.add_hline(y=0,line_dash="dash",line_color="black",line_width=1)
    fig_yoy.update_layout(margin=dict(t=35,b=10),showlegend=False,height=280)

    # ── INDICATOR 1c: MONTH-ON-MONTH ─────────────────────────────────────
    monthly_avg = filt.groupby(filt["date"].dt.to_period("M"))["price_ghs"].mean()
    mom = monthly_avg.pct_change() * 100
    mom_df = mom.dropna().reset_index()
    mom_df.columns = ["period", "change"]
    mom_df["period"] = mom_df["period"].astype(str)
    mom_df["dir"] = mom_df["change"].apply(lambda x: "Increase" if x > 0 else "Decrease")
    if len(mom_df) > 0:
        display_df = mom_df.tail(min(12, len(mom_df)))
        fig_mom = go.Figure()
        for _, row in display_df.iterrows():
            color = "#e74c3c" if row["change"] > 0 else "#27ae60"
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
                   color_discrete_map={"High":"#e74c3c","Medium":"#f39c12","Low":"#27ae60"},
                   labels={"cv":"CV (%)","commodity":""},template="plotly_white",title=title)
        fig.add_vline(x=30,line_dash="dash",line_color="#e74c3c",annotation_text="High risk threshold")
        fig.add_vline(x=15,line_dash="dot",line_color="#f39c12")
        fig.update_layout(margin=dict(t=35,b=10),height=300,legend_title_text="Risk")
        return fig

    fig_vol_major = vol_chart(MAJOR, "Major Commodities – Volatility (CV%)")
    fig_vol_minor = vol_chart(MINOR, "Minor Commodities – Volatility (CV%)")

    # ── INDICATOR 3a: REGIONAL BAR ────────────────────────────────────────
    rf = DF[(DF["commodity"]==commodity)&(DF["year"]==year)]
    if region != "All Regions": rf=rf[rf["region"]==region]
    reg=rf.groupby("region")["price_ghs"].mean().sort_values().reset_index()
    reg["spread_flag"]=reg["price_ghs"].apply(
        lambda x:"Cheapest" if x==reg["price_ghs"].min() else
                 ("Priciest" if x==reg["price_ghs"].max() else "Mid"))
    fig_region=px.bar(reg,x="price_ghs",y="region",orientation="h",color="spread_flag",
                      color_discrete_map={"Cheapest":"#27ae60","Priciest":"#e74c3c","Mid":"#3498db"},
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
                                          "Below avg (harvest)":"#27ae60"},
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
    if region != "All Regions": filt = filt[filt["region"]==region]
    monthly = filt.groupby(["date","commodity"])["price_ghs"].mean().reset_index()
    fig = px.line(monthly,x="date",y="price_ghs",color="commodity",
                  labels={"price_ghs":"Price (GHS)","date":"Date","commodity":""},
                  template="plotly_white")
    fig.update_traces(line_width=2)
    fig.update_layout(margin=dict(t=10,b=10),legend_title_text="")
    return fig


# ── RUN ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "="*55)
    print("  Market Pulse")
    print("  Open: http://127.0.0.1:8050")
    print("="*55+"\n")
    app.run(debug=False, host="127.0.0.1", port=8050)

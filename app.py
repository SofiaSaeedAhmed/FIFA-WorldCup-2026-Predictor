import base64
import html
from io import StringIO
from pathlib import Path

import joblib
import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components


st.set_page_config(
    page_title="FIFA World Cup 2026 Predictor",
    page_icon="🏆",
    layout="wide",
)

# ── Constants ─────────────────────────────────────────────────────────────────

TEAM_CODES = {
    "Mexico": "MEX", "South Africa": "RSA", "Korea Republic": "KOR", "Czechia": "CZE",
    "Canada": "CAN", "Bosnia and Herzegovina": "BIH", "Switzerland": "SUI", "Qatar": "QAT",
    "Brazil": "BRA", "Morocco": "MAR", "Scotland": "SCO", "Haiti": "HAI",
    "USA": "USA", "Paraguay": "PAR", "Australia": "AUS", "Türkiye": "TUR",
    "Germany": "GER", "Curaçao": "CUW", "Côte d'Ivoire": "CIV", "Ecuador": "ECU",
    "Netherlands": "NED", "Japan": "JPN", "Sweden": "SWE", "Tunisia": "TUN",
    "Belgium": "BEL", "Egypt": "EGY", "IR Iran": "IRN", "New Zealand": "NZL",
    "Spain": "ESP", "Cabo Verde": "CPV", "Saudi Arabia": "KSA", "Uruguay": "URU",
    "France": "FRA", "Senegal": "SEN", "Norway": "NOR", "Iraq": "IRQ",
    "Argentina": "ARG", "Austria": "AUT", "Algeria": "ALG", "Jordan": "JOR",
    "Portugal": "POR", "Congo DR": "COD", "Colombia": "COL", "Uzbekistan": "UZB",
    "England": "ENG", "Ghana": "GHA", "Croatia": "CRO", "Panama": "PAN",
}

FLAGS = {
    "Mexico": "🇲🇽", "South Africa": "🇿🇦", "Korea Republic": "🇰🇷", "Czechia": "🇨🇿",
    "Canada": "🇨🇦", "Bosnia and Herzegovina": "🇧🇦", "Switzerland": "🇨🇭", "Qatar": "🇶🇦",
    "Brazil": "🇧🇷", "Morocco": "🇲🇦", "Scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "Haiti": "🇭🇹",
    "USA": "🇺🇸", "Paraguay": "🇵🇾", "Australia": "🇦🇺", "Türkiye": "🇹🇷",
    "Germany": "🇩🇪", "Curaçao": "🇨🇼", "Côte d'Ivoire": "🇨🇮", "Ecuador": "🇪🇨",
    "Netherlands": "🇳🇱", "Japan": "🇯🇵", "Sweden": "🇸🇪", "Tunisia": "🇹🇳",
    "Belgium": "🇧🇪", "Egypt": "🇪🇬", "IR Iran": "🇮🇷", "New Zealand": "🇳🇿",
    "Spain": "🇪🇸", "Cabo Verde": "🇨🇻", "Saudi Arabia": "🇸🇦", "Uruguay": "🇺🇾",
    "France": "🇫🇷", "Senegal": "🇸🇳", "Norway": "🇳🇴", "Iraq": "🇮🇶",
    "Argentina": "🇦🇷", "Austria": "🇦🇹", "Algeria": "🇩🇿", "Jordan": "🇯🇴",
    "Portugal": "🇵🇹", "Congo DR": "🇨🇩", "Colombia": "🇨🇴", "Uzbekistan": "🇺🇿",
    "England": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "Ghana": "🇬🇭", "Croatia": "🇭🇷", "Panama": "🇵🇦",
}

FIXTURES_CSV = """id,group,md,date,home,away,hs,as_
A1,A,1,Jun 11,Mexico,South Africa,2,0
A2,A,1,Jun 11,Korea Republic,Czechia,2,1
A3,A,2,Jun 17,Czechia,South Africa,1,1
A4,A,2,Jun 17,Mexico,Korea Republic,1,0
A5,A,3,Jun 24,South Africa,Korea Republic,1,0
A6,A,3,Jun 24,Czechia,Mexico,0,3
B1,B,1,Jun 12,Canada,Bosnia and Herzegovina,1,1
B2,B,1,Jun 12,Switzerland,Qatar,1,1
B3,B,2,Jun 18,Switzerland,Bosnia and Herzegovina,4,1
B4,B,2,Jun 18,Canada,Qatar,6,0
B5,B,3,Jun 24,Switzerland,Canada,2,1
B6,B,3,Jun 24,Bosnia and Herzegovina,Qatar,3,1
C1,C,1,Jun 13,Brazil,Morocco,1,1
C2,C,1,Jun 13,Scotland,Haiti,1,0
C3,C,2,Jun 19,Morocco,Scotland,1,0
C4,C,2,Jun 19,Brazil,Haiti,3,0
C5,C,3,Jun 24,Scotland,Brazil,0,3
C6,C,3,Jun 24,Morocco,Haiti,4,2
D1,D,1,Jun 12,USA,Paraguay,4,1
D2,D,1,Jun 12,Australia,Türkiye,2,0
D3,D,2,Jun 18,USA,Australia,2,0
D4,D,2,Jun 18,Türkiye,Paraguay,0,1
D5,D,3,Jun 25,Paraguay,Australia,0,0
D6,D,3,Jun 25,USA,Türkiye,2,3
E1,E,1,Jun 13,Germany,Curaçao,7,1
E2,E,1,Jun 13,Côte d'Ivoire,Ecuador,1,0
E3,E,2,Jun 19,Germany,Côte d'Ivoire,2,1
E4,E,2,Jun 19,Ecuador,Curaçao,0,0
E5,E,3,Jun 25,Curaçao,Côte d'Ivoire,0,2
E6,E,3,Jun 25,Ecuador,Germany,2,1
F1,F,1,Jun 14,Netherlands,Japan,2,2
F2,F,1,Jun 14,Sweden,Tunisia,5,1
F3,F,2,Jun 20,Netherlands,Sweden,5,1
F4,F,2,Jun 20,Japan,Tunisia,4,0
F5,F,3,Jun 25,Tunisia,Netherlands,1,3
F6,F,3,Jun 25,Japan,Sweden,1,1
G1,G,1,Jun 14,Belgium,Egypt,1,1
G2,G,1,Jun 14,IR Iran,New Zealand,2,2
G3,G,2,Jun 21,Belgium,IR Iran,0,0
G4,G,2,Jun 21,Egypt,New Zealand,3,1
G5,G,3,Jun 26,New Zealand,Belgium,1,5
G6,G,3,Jun 26,Egypt,IR Iran,1,1
H1,H,1,Jun 15,Spain,Cabo Verde,0,0
H2,H,1,Jun 15,Saudi Arabia,Uruguay,1,1
H3,H,2,Jun 21,Spain,Saudi Arabia,4,0
H4,H,2,Jun 21,Uruguay,Cabo Verde,2,2
H5,H,3,Jun 26,Cabo Verde,Saudi Arabia,2,0
H6,H,3,Jun 26,Uruguay,Spain,0,1
I1,I,1,Jun 15,France,Senegal,3,1
I2,I,1,Jun 15,Norway,Iraq,4,1
I3,I,2,Jun 22,France,Iraq,3,0
I4,I,2,Jun 22,Norway,Senegal,3,2
I5,I,3,Jun 26,Iraq,France,1,4
I6,I,3,Jun 26,Senegal,Norway,2,3
J1,J,1,Jun 16,Argentina,Algeria,3,0
J2,J,1,Jun 16,Austria,Jordan,3,1
J3,J,2,Jun 22,Argentina,Austria,2,0
J4,J,2,Jun 22,Algeria,Jordan,2,1
J5,J,3,Jun 27,Jordan,Argentina,1,3
J6,J,3,Jun 27,Algeria,Austria,3,3
K1,K,1,Jun 16,Portugal,Congo DR,1,1
K2,K,1,Jun 16,Colombia,Uzbekistan,3,1
K3,K,2,Jun 23,Portugal,Uzbekistan,5,0
K4,K,2,Jun 23,Colombia,Congo DR,1,0
K5,K,3,Jun 27,Congo DR,Uzbekistan,3,1
K6,K,3,Jun 27,Colombia,Portugal,0,0
L1,L,1,Jun 16,England,Croatia,4,2
L2,L,1,Jun 16,Ghana,Panama,1,0
L3,L,2,Jun 23,England,Ghana,0,0
L4,L,2,Jun 23,Croatia,Panama,1,0
L5,L,3,Jun 27,Panama,England,0,2
L6,L,3,Jun 27,Croatia,Ghana,2,1
"""

FDORG_MAP = {
    "South Korea": "Korea Republic", "Iran": "IR Iran",
    "Ivory Coast": "Côte d'Ivoire", "DR Congo": "Congo DR",
    "Cape Verde": "Cabo Verde", "Bosnia-Herzegovina": "Bosnia and Herzegovina",
    "Turkey": "Türkiye", "United States": "USA",
    "Curaçao": "Curaçao", "Cape Verde Islands": "Cabo Verde",
}

# ── Stadium background as base64 ──────────────────────────────────────────────

def get_stadium_bg():
    path = Path("static/stadium.jpg")
    if path.exists():
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        return f"url('data:image/jpeg;base64,{b64}')"
    return "linear-gradient(180deg, #0a1628 0%, #1a2744 100%)"

STADIUM_BG = get_stadium_bg()

# ── Global CSS ────────────────────────────────────────────────────────────────

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

*, *::before, *::after {{ font-family: Inter, system-ui, sans-serif; box-sizing: border-box; }}
#MainMenu, footer, header {{ visibility: hidden; }}
html, body {{ overflow-x: hidden; }}
[data-testid="stAppViewContainer"] {{ background: #f0f2f5; }}
[data-testid="stHeader"] {{ display: none !important; height: 0 !important; }}
[data-testid="stMain"] {{ padding: 0 !important; margin: 0 !important; }}
[data-testid="stMainBlockContainer"] {{ padding: 0 80px !important; max-width: 100% !important; padding-bottom: 0 !important; }}
[data-testid="stAppViewBlockContainer"] {{ padding: 0 !important; margin: 0 !important; padding-bottom: 0 !important; }}
[data-testid="stVerticalBlock"] {{ gap: 0 !important; }}
[data-testid="stBottom"] {{ display: none !important; height: 0 !important; }}
.block-container {{ padding: 0 80px !important; max-width: 100% !important; margin: 0 !important; padding-bottom: 0 !important; }}
iframe[title="components.html"] {{ visibility: hidden !important; height: 0 !important; max-height: 0 !important; border: none !important; overflow: hidden !important; }}
section[data-testid="stMain"] > div:first-child {{ padding-top: 0 !important; margin-top: 0 !important; }}
[data-testid="stAppViewContainer"] > section > div {{ padding-bottom: 0 !important; }}
.stMainBlockContainer {{ padding-bottom: 0 !important; }}
[data-testid="stMainBlockContainer"] > div:last-child {{ margin-bottom: 0 !important; padding-bottom: 0 !important; }}

/* ── Navbar ── */
.wc-nav {{
  background: #0a1628;
  padding: 0 48px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: sticky;
  top: 0;
  z-index: 999;
  box-shadow: 0 2px 20px rgba(0,0,0,.4);
  margin-left: -80px;
  margin-right: -80px;
  width: calc(100% + 160px);
}}
.wc-nav-brand {{
  font-size: 22px;
  font-weight: 900;
  color: #f5c518;
  letter-spacing: -0.5px;
  white-space: nowrap;
  text-decoration: none;
}}
.wc-nav-links {{
  display: flex;
  align-items: center;
  gap: 4px;
}}
.wc-nav-link, a.wc-nav-link, a.wc-nav-link:visited, a.wc-nav-link:link {{
  padding: 8px 14px;
  font-size: 14px;
  font-weight: 600;
  color: rgba(255,255,255,.85) !important;
  cursor: pointer;
  border-radius: 8px;
  border: none;
  background: transparent;
  white-space: nowrap;
  transition: color .15s;
  text-decoration: none !important;
}}
.wc-nav-link:hover, a.wc-nav-link:hover {{ color: #f5c518 !important; text-decoration: none !important; }}
.wc-nav-link.active, a.wc-nav-link.active {{
  color: #f5c518 !important;
  text-decoration: underline !important;
  text-underline-offset: 4px;
}}
.wc-nav-cta, a.wc-nav-cta, a.wc-nav-cta:visited, a.wc-nav-cta:link {{
  background: #f5c518 !important;
  color: #0a1628 !important;
  font-weight: 900;
  font-size: 14px;
  padding: 10px 22px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  white-space: nowrap;
  text-decoration: none !important;
  display: inline-block;
  transition: background .15s, transform .1s;
}}
.wc-nav-cta:hover {{ background: #e6b800; transform: translateY(-1px); }}

/* ── Hero ── */
.wc-hero {{
  background-image: linear-gradient(rgba(10,22,40,.55) 0%, rgba(10,22,40,.72) 100%), {STADIUM_BG};
  background-size: cover;
  background-position: center 30%;
  min-height: 92vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 80px 40px 100px;
  margin-left: -80px;
  margin-right: -80px;
  width: calc(100% + 160px);
}}
.hero-kicker {{
  font-size: 13px;
  font-weight: 900;
  letter-spacing: 4px;
  color: #f5c518;
  text-transform: uppercase;
  margin-bottom: 8px;
}}
.hero-divider {{
  width: 56px; height: 3px;
  background: #f5c518;
  margin: 10px auto 28px;
  border-radius: 2px;
}}
.hero-title {{
  font-size: clamp(44px,7vw,84px);
  font-weight: 900;
  color: white;
  line-height: 1.05;
  letter-spacing: -2px;
  margin-bottom: 24px;
  max-width: 900px;
}}
.hero-desc {{
  font-size: 18px;
  color: rgba(255,255,255,.75);
  line-height: 1.7;
  max-width: 680px;
  margin: 0 auto 48px;
}}
.hero-chips {{
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 48px;
}}
.hero-chip {{
  background: rgba(255,255,255,.12);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255,255,255,.2);
  border-radius: 12px;
  padding: 18px 28px;
  text-align: center;
  min-width: 120px;
}}
.hero-chip-val {{
  font-size: 32px;
  font-weight: 900;
  color: white;
  line-height: 1;
}}
.hero-chip-label {{
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 2px;
  color: #f5c518;
  margin-top: 6px;
  text-transform: uppercase;
}}
.hero-btns {{
  display: flex;
  gap: 16px;
  justify-content: center;
  flex-wrap: wrap;
}}
.hero-btn, a.hero-btn, a.hero-btn:visited, a.hero-btn:link {{
  padding: 16px 36px;
  font-size: 15px;
  font-weight: 800;
  border-radius: 10px;
  cursor: pointer;
  border: 2px solid white;
  background: transparent;
  color: white !important;
  transition: all .18s;
  letter-spacing: .3px;
  text-decoration: none !important;
  display: inline-block;
}}
.hero-btn:hover {{
  background: white;
  color: #0a1628;
}}
.hero-btn.primary {{
  background: #f5c518;
  border-color: #f5c518;
  color: #0a1628;
}}
.hero-btn.primary:hover {{
  background: #e6b800;
  border-color: #e6b800;
}}

/* ── Page wrapper ── */
.page-wrap {{
  max-width: 1180px;
  margin: 0 auto;
  padding: 48px 32px 80px;
}}


/* ── Section headers ── */
.sec-kicker {{
  font-size: 11px; font-weight: 900; letter-spacing: 3px;
  color: #f5c518; text-transform: uppercase; margin-bottom: 4px;
}}
.sec-title {{
  font-size: 36px; font-weight: 900; color: #0d1b2a;
  letter-spacing: -1px; margin-bottom: 8px; line-height: 1.1;
}}
.sec-desc {{
  font-size: 15px; color: #64748b; line-height: 1.7; margin-bottom: 32px;
}}

/* ── Cards ── */
.card {{
  background: white; border: 1px solid #e2e8f0; border-radius: 14px;
  padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,.05);
}}

/* ── Match cards ── */
.mcard {{
  background: white; border: 1px solid #e2e8f0;
  border-radius: 12px; padding: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,.05);
}}
.mcard-meta {{
  display: flex; justify-content: space-between;
  font-size: 10px; color: #94a3b8; font-weight: 700;
  letter-spacing: .5px; margin-bottom: 14px;
}}
.mcard-teams {{
  display: grid; grid-template-columns: 1fr auto 1fr;
  align-items: center; text-align: center; gap: 8px;
}}
.mcard-code {{ font-size: 22px; font-weight: 900; color: #0d1b2a; line-height: 1; letter-spacing: 1px; }}
.mcard-name {{ font-size: 11px; font-weight: 600; color: #64748b; margin-top: 4px; }}
.mcard-score {{ font-size: 26px; font-weight: 900; color: #0d1b2a; }}
.mcard-vs {{ font-size: 14px; font-weight: 700; color: #94a3b8; }}
.mcard-pred {{
  display: flex; justify-content: space-between; align-items: center;
  margin-top: 12px; padding-top: 12px; border-top: 1px solid #f1f5f9;
  font-size: 12px; font-weight: 700; color: #0d1b2a;
}}

/* ── Nav tabs (radio) ── */
.nav-tab-wrap {{ margin-bottom: 28px; }}
div[role="radiogroup"] {{
  display: flex !important;
  gap: 8px !important;
  flex-wrap: wrap;
}}
div[role="radiogroup"] label {{
  border-radius: 10px !important;
  padding: 10px 22px !important;
  background: white !important;
  border: 1.5px solid #e2e8f0 !important;
  color: #64748b !important;
  font-weight: 700 !important;
  font-size: 14px !important;
}}
div[role="radiogroup"] label:has(input:checked) {{
  background: #0d1b2a !important;
  color: #f5c518 !important;
  border-color: #0d1b2a !important;
}}

/* ── Buttons ── */
.stButton > button {{
  width: 100%; min-height: 42px; border-radius: 10px !important;
  border: 2px solid #0d1b2a !important;
  background: #f5c518 !important; color: #0d1b2a !important;
  font-weight: 900 !important; font-size: 13px !important;
  box-shadow: none !important;
}}
.stButton > button:hover {{
  background: #e6b800 !important;
  box-shadow: 0 4px 14px rgba(245,197,24,.4) !important;
  transform: translateY(-1px);
}}

/* ── Group containers ── */
div[data-testid="stVerticalBlockBorderWrapper"] {{
  margin-bottom: 20px !important;
  border: 1px solid #e2e8f0 !important;
  border-radius: 14px !important;
  background: white !important;
}}
.grp-header {{
  padding-bottom: 10px; border-bottom: 2px solid #0d1b2a; margin-bottom: 14px;
}}
.grp-label {{ font-size: 12px; font-weight: 900; letter-spacing: 2px; color: #0d1b2a; }}
.grp-teams {{ font-size: 10px; color: #64748b; font-weight: 600; margin-top: 3px; }}
.t-code {{ font-size: 10px; font-weight: 800; color: #94a3b8; margin-right: 3px; }}

/* ── Standings tables ── */
.t-wrap {{
  background: white; border: 1px solid #e2e8f0;
  border-radius: 14px; overflow: hidden;
  box-shadow: 0 2px 8px rgba(0,0,0,.05); margin-bottom: 20px;
}}
.t-head {{ padding: 16px 20px 6px; }}
.t-grp-title {{ font-size: 20px; font-weight: 900; color: #0d1b2a; margin-bottom: 2px; }}
.t-grp-teams {{ font-size: 11px; color: #94a3b8; font-weight: 600; margin-bottom: 10px; }}
.t-table {{ width: 100%; border-collapse: collapse; }}
.t-table thead tr {{ background: #1e3a5f; }}
.t-table thead th {{
  padding: 10px 12px; text-align: left;
  font-size: 11px; font-weight: 800; color: white; letter-spacing: .5px;
}}
.t-table tbody tr {{ border-bottom: 1px solid #f1f5f9; }}
.t-table tbody tr:last-child {{ border-bottom: none; }}
.t-table tbody td {{ padding: 10px 12px; font-size: 13px; color: #0d1b2a; }}
.t-table tbody tr:nth-child(-n+2) td {{ font-weight: 700; }}
.t-pts {{ font-weight: 900 !important; }}

/* ── Detail hero ── */
.d-hero {{
  background: linear-gradient(135deg, #0a1628 0%, #0d1b2a 100%);
  border-radius: 16px; padding: 44px 32px 40px; margin-bottom: 28px;
  box-shadow: 0 12px 40px rgba(0,0,0,.25);
}}
.d-meta {{
  text-align: center; font-size: 11px; font-weight: 900;
  letter-spacing: 3px; color: #f5c518; margin-bottom: 8px;
}}
.d-divider {{ width: 40px; height: 2px; background: #f5c518; margin: 0 auto 28px; }}
.d-score-grid {{
  display: grid; grid-template-columns: 1fr auto 1fr;
  align-items: center; text-align: center; gap: 16px;
}}
.d-team-code {{ font-size: 76px; font-weight: 900; color: white; line-height: 1; letter-spacing: -2px; }}
.d-team-flag {{ font-size: 13px; font-weight: 900; color: rgba(255,255,255,.5); letter-spacing: 1px; }}
.d-team-name {{ font-size: 15px; font-weight: 600; color: rgba(255,255,255,.65); margin-top: 6px; }}
.d-number {{ font-size: 68px; font-weight: 900; color: white; letter-spacing: -2px; }}

/* ── Prob bars ── */
.pbar-wrap {{ margin-bottom: 22px; }}
.pbar-label {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }}
.pbar-name {{ font-size: 14px; font-weight: 700; color: #0d1b2a; }}
.pbar-pct {{ font-size: 22px; font-weight: 900; color: #0d1b2a; }}
.pbar-track {{ height: 32px; border-radius: 6px; background: #e2e8f0; overflow: hidden; }}
.pbar-fill {{ height: 100%; border-radius: 6px; width: 0; }}
.pbar-wrap.pbar-visible .pbar-fill {{ animation: grow 1s cubic-bezier(.25,1,.35,1) forwards; }}
.pb-home {{ background: #f5c518; }}
.pb-draw {{ background: #0d1b2a; }}
.pb-away {{ background: #1e3a5f; }}
@keyframes grow {{ to {{ width: var(--w); }} }}

/* ── Factor cards ── */
.fc {{
  background: white; border: 1px solid #e2e8f0; border-radius: 12px;
  padding: 20px; margin-bottom: 14px; box-shadow: 0 2px 8px rgba(0,0,0,.04);
}}
.fc-title {{
  font-size: 11px; font-weight: 900; letter-spacing: 1.5px;
  text-transform: uppercase; color: #64748b; margin-bottom: 12px;
}}
.fc-copy {{ font-size: 13px; color: #374151; line-height: 1.6; }}
.rank-row {{ display: grid; grid-template-columns: 1fr auto 1fr; gap: 10px; align-items: center; margin-bottom: 12px; }}
.rank-box {{ text-align: center; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 12px; }}
.rank-num {{ font-size: 28px; font-weight: 900; color: #0d1b2a; }}
.rank-team {{ font-size: 11px; color: #64748b; font-weight: 700; }}
.form-line {{ display: grid; grid-template-columns: 1fr auto 56px; gap: 10px; align-items: center; margin: 8px 0; font-size:13px;font-weight:700;color:#0d1b2a; }}
.form-dots {{ display: flex; gap: 5px; }}
.form-dot {{ width: 24px; height: 24px; border-radius: 8px; display: grid; place-items: center; color: white; font-size: 10px; font-weight: 900; }}
.W {{ background: #16a34a; }}
.D {{ background: #94a3b8; }}
.L {{ background: #ef4444; }}

/* ── Verdict ── */
.verdict-wrap {{
  background: white; border: 1px solid #e2e8f0; border-radius: 12px;
  padding: 24px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,.04);
}}
.verdict-icon {{
  width: 44px; height: 44px; border-radius: 12px;
  display: grid; place-items: center; font-size: 20px; flex-shrink: 0;
}}
.v-correct {{ background: #16a34a; color: white; }}
.v-wrong   {{ background: #ef4444; color: white; }}
.v-pending {{ background: #f5c518; color: #0a1628; }}
.v-row {{ display: flex; gap: 32px; margin-top: 12px; flex-wrap: wrap; }}
.v-fact {{ font-size: 13px; color: #0d1b2a; font-weight: 700; }}
.v-fact span {{ font-weight: 400; color: #64748b; }}
.v-detail {{ font-size: 13px; color: #374151; margin-top: 12px; line-height: 1.6; }}

/* ── Back button override ── */
.back-btn .stButton > button {{
  background: transparent !important;
  border: 2px solid #0d1b2a !important;
  color: #0d1b2a !important;
  width: auto !important;
  padding: 10px 24px !important;
  margin-bottom: 24px;
}}

@media(max-width:768px) {{
  .wc-nav {{ padding: 0 16px; }}
  .wc-nav-links {{ display: none; }}
  .wc-hero {{ padding: 60px 20px 80px; }}
  .hero-title {{ font-size: 38px; }}
  .page-wrap {{ padding: 24px 16px 60px; }}
}}
</style>
""", unsafe_allow_html=True)

# ── Data loading ──────────────────────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def load_model():
    model_path    = Path("models/xgb_final.pkl")
    features_path = Path("models/features.pkl")
    if not model_path.exists():
        return None, []
    m = joblib.load(model_path)
    f = joblib.load(features_path) if features_path.exists() else ["weight","rank_diff","home_form","away_form","h2h"]
    return m, f


@st.cache_data(show_spinner=False)
def load_data():
    matches  = pd.read_csv("data/processed/matches_final.csv", parse_dates=["date"])
    rankings = pd.read_csv("data/raw/fifa_ranking-2024-06-20.csv", parse_dates=["rank_date"])
    base     = pd.read_csv(StringIO(FIXTURES_CSV))
    base["hs"]  = pd.to_numeric(base["hs"],  errors="coerce")
    base["as_"] = pd.to_numeric(base["as_"], errors="coerce")
    base["played"] = base["hs"].notna()
    return matches, rankings, base


@st.cache_data(ttl=60, show_spinner=False)
def fetch_api_scores():
    token = st.secrets.get("FDORG_TOKEN", "")
    if not token:
        return {}
    try:
        r = requests.get(
            "https://api.football-data.org/v4/competitions/WC/matches",
            headers={"X-Auth-Token": token}, timeout=8,
        )
        if r.status_code != 200:
            return {}
        out = {}
        for m in r.json().get("matches", []):
            home = FDORG_MAP.get(m["homeTeam"]["name"], m["homeTeam"]["name"])
            away = FDORG_MAP.get(m["awayTeam"]["name"], m["awayTeam"]["name"])
            s = m.get("score", {}).get("fullTime", {})
            out[(home, away)] = {
                "hs": s.get("home"), "as_": s.get("away"),
                "status": m.get("status", ""), "utc_date": m.get("utcDate", ""),
            }
        return out
    except Exception:
        return {}


def load_fixtures_live(base_fixtures):
    api = {}  # scores hardcoded in FIXTURES_CSV — API disabled
    if not api:
        return base_fixtures.copy(), False
    df = base_fixtures.copy()
    df["status"] = ""; df["utc_date"] = ""
    for i, row in df.iterrows():
        key = (row["home"], row["away"])
        if key in api:
            info = api[key]
            if info["status"] == "FINISHED" and info["hs"] is not None:
                df.at[i, "hs"] = info["hs"]; df.at[i, "as_"] = info["as_"]
            df.at[i, "status"] = info["status"]; df.at[i, "utc_date"] = info["utc_date"]
    df["played"] = df["hs"].notna()
    return df, True


model, features = load_model()
matches, rankings, _base_fixtures = load_data()
fixtures, _api_live = load_fixtures_live(_base_fixtures)

# ── Helpers ───────────────────────────────────────────────────────────────────

def esc(v):     return html.escape(str(v), quote=True)
def tc(team):   return TEAM_CODES.get(team, team[:3].upper())
def flag(team): return FLAGS.get(team, "🏳️")

_RANK_NAME = {
    "Türkiye": "Turkey",
    "Curaçao": "Curacao",
}

def get_rank(team, date):
    team = _RANK_NAME.get(team, team)
    rows = rankings[(rankings["country_full"] == team) & (rankings["rank_date"] <= date)]
    return None if rows.empty else int(rows.iloc[-1]["rank"])

def get_form(team, date, n=10):
    rows = matches[
        ((matches["home_team"] == team) | (matches["away_team"] == team)) & (matches["date"] < date)
    ].sort_values("date").tail(n)
    if rows.empty: return 0.5
    wins = sum(
        1 for _, r in rows.iterrows()
        if (r["home_team"] == team and r["result"] == "home_win") or
           (r["away_team"] == team and r["result"] == "away_win")
    )
    return wins / len(rows)

def get_last5(team, date):
    rows = matches[
        ((matches["home_team"] == team) | (matches["away_team"] == team)) & (matches["date"] < date)
    ].sort_values("date").tail(5)
    out = []
    for _, r in rows.iterrows():
        if r["result"] == "draw": out.append("D")
        elif (r["home_team"] == team and r["result"] == "home_win") or \
             (r["away_team"] == team and r["result"] == "away_win"): out.append("W")
        else: out.append("L")
    return out

def get_h2h(home, away, date):
    rows = matches[
        (((matches["home_team"] == home) & (matches["away_team"] == away)) |
         ((matches["home_team"] == away) & (matches["away_team"] == home))) & (matches["date"] < date)
    ]
    if rows.empty: return 0.5, 0, 0, 0
    hw = len(rows[((rows["home_team"]==home)&(rows["result"]=="home_win"))|((rows["away_team"]==home)&(rows["result"]=="away_win"))])
    aw = len(rows[((rows["home_team"]==away)&(rows["result"]=="home_win"))|((rows["away_team"]==away)&(rows["result"]=="away_win"))])
    d  = len(rows) - hw - aw
    return hw / len(rows), hw, d, aw

def predict_fixture(row):
    date = pd.Timestamp("2026-06-24")
    rh = get_rank(row["home"], date); ra = get_rank(row["away"], date)
    if rh is None or ra is None: return None
    fh = get_form(row["home"], date); fa = get_form(row["away"], date)
    h2h, h2h_hw, h2h_d, h2h_aw = get_h2h(row["home"], row["away"], date)
    feat = pd.DataFrame([[5, rh - ra, fh, fa, h2h]], columns=["weight","rank_diff","home_form","away_form","h2h"])
    probs = model.predict_proba(feat)[0]
    pm = {
        f'{row["home"]} win': round(float(probs[2])*100, 1),
        "Draw":               round(float(probs[1])*100, 1),
        f'{row["away"]} win': round(float(probs[0])*100, 1),
    }
    predicted = max(pm, key=pm.get)
    return {
        "home": row["home"], "away": row["away"],
        "rank_home": rh, "rank_away": ra,
        "form_home": round(fh*100, 1), "form_away": round(fa*100, 1),
        "last_home": get_last5(row["home"], date), "last_away": get_last5(row["away"], date),
        "h2h_home": h2h_hw, "h2h_draw": h2h_d, "h2h_away": h2h_aw,
        "h2h_total": h2h_hw + h2h_d + h2h_aw,
        "probs": pm, "predicted": predicted, "confidence": pm[predicted],
    }

@st.cache_data(show_spinner=False, ttl=1)
def build_predictions():
    return {row["id"]: predict_fixture(row) for _, row in fixtures.iterrows()}

predictions = build_predictions()

def actual_result(row):
    if not row["played"]: return "Upcoming"
    if row["hs"] > row["as_"]: return f"{row['home']} win"
    if row["as_"] > row["hs"]: return f"{row['away']} win"
    return "Draw"

def is_correct(row, pred):
    return bool(row["played"]) and pred is not None and actual_result(row) == pred["predicted"]

def form_dots_html(vals):
    if not vals: return "<span style='color:#94a3b8;font-size:12px'>No data</span>"
    return "<div class='form-dots'>" + "".join(f"<span class='form-dot {v}'>{v}</span>" for v in vals) + "</div>"

def group_table(group):
    teams = sorted(set(fixtures[fixtures["group"]==group]["home"]) | set(fixtures[fixtures["group"]==group]["away"]))
    rows = []
    for team in teams:
        p=w=d=l=gf=ga=0
        for _, m in fixtures[(fixtures["group"]==group)&(fixtures["played"])].iterrows():
            if m["home"]!=team and m["away"]!=team: continue
            p+=1
            s, c = (int(m["hs"]), int(m["as_"])) if m["home"]==team else (int(m["as_"]), int(m["hs"]))
            gf+=s; ga+=c
            if s>c: w+=1
            elif s==c: d+=1
            else: l+=1
        rows.append({"Team":team,"P":p,"W":w,"D":d,"L":l,"GF":gf,"GA":ga,"GD":gf-ga,"PTS":w*3+d})
    return pd.DataFrame(rows).sort_values(["PTS","GD","GF"], ascending=False)

# ── Navbar ────────────────────────────────────────────────────────────────────

def show_navbar(active="Home"):
    live_pill = "🟢 Live" if _api_live else "⚪ Offline"
    pages = ["Home", "Matches", "Tournament", "Knockout", "About"]
    links_html = "".join(
        f'<a target="_self" class="wc-nav-link{"  active" if p == active else ""}" href="?nav={p}">{p}</a>'
        for p in pages
    )
    st.markdown(f"""
    <div class="wc-nav">
        <span class="wc-nav-brand">World Cup 2026</span>
        <div class="wc-nav-links">
            {links_html}
            <span style="font-size:11px;font-weight:700;color:rgba(255,255,255,.5);margin-left:8px">{live_pill}</span>
        </div>
        <a target="_self" class="wc-nav-cta" href="?nav=Matches">View Predictions</a>
    </div>
    """, unsafe_allow_html=True)

# ── Tab nav (Streamlit radio) ─────────────────────────────────────────────────

def show_tab_nav():
    pages = ["Home", "Matches", "Tournament", "Knockout", "About"]
    st.markdown('<div class="nav-tab-wrap">', unsafe_allow_html=True)
    sel = st.radio("nav", pages,
        index=pages.index(st.session_state.page) if st.session_state.page in pages else 0,
        horizontal=True, label_visibility="collapsed")
    st.markdown("</div>", unsafe_allow_html=True)
    if sel != st.session_state.page and st.session_state.page != "Detail":
        st.session_state.page = sel
    return sel

# ── Match card ────────────────────────────────────────────────────────────────

def match_card_html(row, pred, compact=False):
    hc = tc(row["home"]); ac = tc(row["away"])
    cs = "18px" if compact else "22px"
    pad = "12px 14px" if compact else "16px"

    if row["played"]:
        score_el = f'<div class="mcard-score">{int(row["hs"])} – {int(row["as_"])}</div>'
        if pred:
            correct  = is_correct(row, pred)
            tick_col = "#16a34a" if correct else "#ef4444"
            tick     = "✓" if correct else "✗"
            pred_el = (
                f'<div class="mcard-pred">'
                f'<span>{esc(pred["predicted"])} · {pred["confidence"]}%</span>'
                f'<span style="color:{tick_col};font-size:16px">{tick}</span></div>'
            )
        else:
            pred_el = ""
    else:
        score_el = '<div class="mcard-vs">VS</div>'
        pred_el  = (
            f'<div class="mcard-pred"><span>Predicted: {esc(pred["predicted"])} · {pred["confidence"]}%</span></div>'
        ) if pred else ""

    return f"""
    <div class="mcard" style="padding:{pad}">
        <div class="mcard-meta"><span>Group {esc(row["group"])}</span><span>{esc(row["date"])}</span></div>
        <div class="mcard-teams">
            <div>
                <div class="mcard-code" style="font-size:{cs}">{hc}</div>
                <div class="mcard-name">{esc(row["home"])}</div>
            </div>
            {score_el}
            <div>
                <div class="mcard-code" style="font-size:{cs}">{ac}</div>
                <div class="mcard-name">{esc(row["away"])}</div>
            </div>
        </div>
        {pred_el}
    </div>"""

def nav_to_match(match_id, label, prefix):
    if st.button(label, key=f"{prefix}_{match_id}", use_container_width=True):
        st.session_state.page = "Detail"
        st.session_state.match_id = match_id
        st.session_state.scroll_detail_top = True
        st.query_params.clear()
        st.rerun()

# ── Pages ─────────────────────────────────────────────────────────────────────

def show_home():
    played  = int(fixtures["played"].sum())
    total   = len(fixtures)
    evald   = [r for _, r in fixtures[fixtures["played"]].iterrows() if predictions.get(r["id"])]
    correct = sum(is_correct(r, predictions[r["id"]]) for r in evald)
    acc     = round(correct / len(evald) * 100) if evald else 0

    chips = "".join(
        f'<div class="hero-chip"><div class="hero-chip-val">{v}</div><div class="hero-chip-label">{l}</div></div>'
        for v, l in [("72","Matches"),("12","Groups"),("23,000+","Training Fixtures"),(f"{acc}%","Accuracy")]
    )

    st.markdown(f"""
    <div class="wc-hero">
        <div class="hero-kicker">🏆 USA · CANADA · MEXICO · 2026</div>
        <div class="hero-divider"></div>
        <div class="hero-title">FIFA World Cup 2026<br>Predictions</div>
        <div class="hero-desc">Match predictions powered by XGBoost, trained on 23,000+ international fixtures.
        Win/draw/loss probabilities, model accuracy tracking, and plain-English breakdowns for every group-stage match.</div>
        <div class="hero-chips">{chips}</div>
        <div class="hero-btns">
            <a target="_self" class="hero-btn primary" href="?nav=Matches">Explore Predictions</a>
            <a target="_self" class="hero-btn" href="?nav=Tournament">View Groups &amp; Standings</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Recent results section below hero
    st.markdown('<div class="page-wrap">', unsafe_allow_html=True)
    st.markdown("""
    <div class="sec-kicker">RECENT RESULTS</div>
    <div class="sec-title">Latest Match Outcomes</div>
    <div class="sec-desc">The most recently played group-stage matches with the model's prediction verdict.</div>
    """, unsafe_allow_html=True)

    played_f = fixtures[fixtures["played"]].copy()
    played_f["_sort"] = pd.to_datetime(played_f["date"] + " 2026", format="%b %d %Y")
    recent = list(played_f.sort_values("_sort").tail(6).iloc[::-1].iterrows())
    for i in range(0, len(recent), 3):
        trio = recent[i:i+3]
        cols = st.columns(len(trio), gap="medium")
        for col, (_, row) in zip(cols, trio):
            with col:
                st.markdown(match_card_html(row, predictions.get(row["id"])), unsafe_allow_html=True)
                nav_to_match(row["id"], "View prediction →", prefix=f"h_{row['id']}")

    # ── Model Performance ──────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="margin-top:64px">
        <div class="sec-kicker">MODEL PERFORMANCE</div>
        <div class="sec-title">How Well Is the Model Performing?</div>
        <div class="sec-desc">The XGBoost model was trained on 23,000+ international matches and evaluated live against the 2026 World Cup group stage. Overall accuracy sits at 56% — with 71% accuracy on decisive (non-draw) matches. Draws remain the model's primary challenge.</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:8px">
            <div style="background:white;border:1px solid #e2e8f0;border-radius:14px;padding:44px 32px;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,.05)">
                <svg viewBox="0 0 120 120" width="140" height="140" style="display:block;margin:0 auto;transform:rotate(-90deg)">
                    <circle cx="60" cy="60" r="52" fill="none" stroke="#e2e8f0" stroke-width="10"/>
                    <circle cx="60" cy="60" r="52" fill="none" stroke="#f5c518" stroke-width="10"
                        stroke-dasharray="{round(acc/100*326.7,1)} 326.7" stroke-linecap="round"/>
                    <text x="60" y="60" text-anchor="middle" dominant-baseline="middle" font-size="22" font-weight="900" fill="#0d1b2a" font-family="sans-serif" transform="rotate(90 60 60)">{acc}%</text>
                </svg>
                <div style="font-size:14px;color:#64748b;margin-top:14px">Overall accuracy</div>
            </div>
            <div style="background:white;border:1px solid #e2e8f0;border-radius:14px;padding:44px 32px;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,.05)">
                <svg viewBox="0 0 120 120" width="140" height="140" style="display:block;margin:0 auto;transform:rotate(-90deg)">
                    <circle cx="60" cy="60" r="52" fill="none" stroke="#e2e8f0" stroke-width="10"/>
                    <circle cx="60" cy="60" r="52" fill="none" stroke="#f5c518" stroke-width="10"
                        stroke-dasharray="231.9 326.7" stroke-linecap="round"/>
                    <text x="60" y="60" text-anchor="middle" dominant-baseline="middle" font-size="22" font-weight="900" fill="#0d1b2a" font-family="sans-serif" transform="rotate(90 60 60)">71%</text>
                </svg>
                <div style="font-size:14px;color:#64748b;margin-top:14px">On non-draw matches</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── What Drives Each Prediction ────────────────────────────────────────────
    st.markdown("""
    <div style="margin-top:72px">
        <div class="sec-kicker">THE MODEL</div>
        <div class="sec-title">What Drives Each Prediction</div>
        <div class="sec-desc">Every prediction is built from four features the XGBoost model weighs against 23,000+ historical international fixtures. Here's what each one captures.</div>
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-top:8px">
            <div style="background:white;border:1px solid #e2e8f0;border-radius:14px;padding:28px 22px;box-shadow:0 2px 8px rgba(0,0,0,.05)">
                <div style="font-size:28px;margin-bottom:14px">🏆</div>
                <div style="font-size:17px;font-weight:800;color:#0d1b2a;margin-bottom:10px">FIFA Rankings Gap</div>
                <div style="font-size:13px;color:#64748b;line-height:1.7">The difference in FIFA world ranking positions between the two teams. A larger gap strongly favors the higher-ranked side — the single most predictive feature in the model.</div>
            </div>
            <div style="background:white;border:1px solid #e2e8f0;border-radius:14px;padding:28px 22px;box-shadow:0 2px 8px rgba(0,0,0,.05)">
                <div style="font-size:28px;margin-bottom:14px">📈</div>
                <div style="font-size:17px;font-weight:800;color:#0d1b2a;margin-bottom:10px">Recent Form</div>
                <div style="font-size:13px;color:#64748b;line-height:1.7">Win rate across the last 10 international matches heading into the fixture. Captures momentum and current squad strength beyond what rankings reflect.</div>
            </div>
            <div style="background:white;border:1px solid #e2e8f0;border-radius:14px;padding:28px 22px;box-shadow:0 2px 8px rgba(0,0,0,.05)">
                <div style="font-size:28px;margin-bottom:14px">⚔️</div>
                <div style="font-size:17px;font-weight:800;color:#0d1b2a;margin-bottom:10px">Head-to-Head Record</div>
                <div style="font-size:13px;color:#64748b;line-height:1.7">Historical wins, draws, and losses between the two specific teams. Encodes rivalry patterns and stylistic matchups that rankings and form don't capture.</div>
            </div>
            <div style="background:white;border:1px solid #e2e8f0;border-radius:14px;padding:28px 22px;box-shadow:0 2px 8px rgba(0,0,0,.05)">
                <div style="font-size:28px;margin-bottom:14px">⭐</div>
                <div style="font-size:17px;font-weight:800;color:#0d1b2a;margin-bottom:10px">Tournament Stake Weight</div>
                <div style="font-size:13px;color:#64748b;line-height:1.7">A 1–5 importance score assigned to the competition type. World Cup matches score 5/5 — the highest weight — which amplifies the favourite's edge and slightly reduces draw probability versus lower-stakes fixtures.</div>
            </div>
        </div>
        <div style="text-align:center;margin-top:36px">
            <a href="?nav=About" target="_self" style="display:inline-block;padding:14px 40px;font-size:15px;font-weight:800;border-radius:10px;
                background:#f5c518;border:2px solid #f5c518;color:#0d1b2a;cursor:pointer;text-decoration:none;
                box-shadow:0 4px 16px rgba(245,197,24,.35)">About the Model</a>
        </div>
    </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Footer ─────────────────────────────────────────────────────────────────
    _footer_pages = [("Home","Home"),("Match Predictions","Matches"),("Match Detail","Matches"),("Groups &amp; Standings","Tournament"),("About the Model","About")]
    nav_col = "".join(f'<a target="_self" href="?nav={dest}" style="display:block;padding:10px 0;border-bottom:1px solid rgba(255,255,255,.08);font-size:14px;color:rgba(255,255,255,.65);text-decoration:none">{label}</a>' for label, dest in _footer_pages)
    st.markdown(f"""
    <div style="background:#0a1628;margin-top:80px;padding:60px 48px 40px;margin-left:-80px;margin-right:-80px;width:calc(100% + 160px)">
        <div style="max-width:1180px;margin:0 auto">
            <div style="display:grid;grid-template-columns:1.6fr 1fr 1fr 1fr;gap:48px;margin-bottom:48px">
                <div>
                    <div style="font-size:22px;font-weight:900;color:white;margin-bottom:12px">World Cup 2026</div>
                    <div style="font-size:13px;color:rgba(255,255,255,.5);line-height:1.8;margin-bottom:24px">AI-powered predictions, win probabilities, rankings, and deep tactical analysis for every FIFA World Cup 2026 match. Data-driven. Fan-focused.</div>
                    <div style="display:flex;gap:12px">
                        <a href="https://www.linkedin.com/in/sofia-saeed-ahmed/" target="_blank" title="LinkedIn"
                           style="width:36px;height:36px;background:rgba(255,255,255,.1);border-radius:50%;display:grid;place-items:center;text-decoration:none;color:white;font-size:13px;font-weight:700;transition:.15s" onmouseover="this.style.background='#0a66c2'" onmouseout="this.style.background='rgba(255,255,255,.1)'">in</a>
                        <a href="https://github.com/SofiaSaeedAhmed" target="_blank" title="GitHub"
                           style="width:36px;height:36px;background:rgba(255,255,255,.1);border-radius:50%;display:grid;place-items:center;text-decoration:none;color:white;font-size:13px;font-weight:700;transition:.15s" onmouseover="this.style.background='#333'" onmouseout="this.style.background='rgba(255,255,255,.1)'">GH</a>
                        <a href="mailto:sofiasaeed23@gmail.com" title="Email"
                           style="width:36px;height:36px;background:rgba(255,255,255,.1);border-radius:50%;display:grid;place-items:center;text-decoration:none;color:white;font-size:13px;font-weight:700;transition:.15s" onmouseover="this.style.background='#ea4335'" onmouseout="this.style.background='rgba(255,255,255,.1)'">✉</a>
                    </div>
                </div>
                <div>
                    <div style="font-size:11px;font-weight:900;letter-spacing:2px;color:#f5c518;margin-bottom:20px">PREDICTIONS</div>
                    {nav_col}
                </div>
                <div>
                    <div style="font-size:11px;font-weight:900;letter-spacing:2px;color:#f5c518;margin-bottom:20px">EXPLORE</div>
                    {nav_col}
                </div>
                <div>
                    <div style="font-size:11px;font-weight:900;letter-spacing:2px;color:#f5c518;margin-bottom:20px">CONTACT</div>
                    <div style="font-size:14px;color:#f5c518;margin-bottom:12px">sofiasaeed23@gmail.com</div>
                    <div style="font-size:13px;color:rgba(255,255,255,.5);line-height:1.7">Have feedback or data corrections? We'd love to hear from you.</div>
                </div>
            </div>
            <div style="border-top:1px solid rgba(255,255,255,.08);padding-top:24px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px">
                <div style="font-size:12px;color:rgba(255,255,255,.35)">© 2026 World Cup Predictor · Built with XGBoost + Streamlit · Data via football-data.org</div>
                <div style="font-size:12px;color:rgba(255,255,255,.35)">Sofia Saeed Ahmed · Data Science Portfolio</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_footer():
    _footer_pages = [("Home", "Home"), ("Match Predictions", "Matches"), ("Groups & Standings", "Tournament"), ("About the Model", "About")]
    nav_col = "".join(
        f'<a target="_self" href="?nav={dest}" style="display:block;padding:10px 0;border-bottom:1px solid rgba(255,255,255,.08);font-size:14px;color:rgba(255,255,255,.65);text-decoration:none">{label}</a>'
        for label, dest in _footer_pages
    )
    st.markdown(f"""
    <div style="background:#0a1628;margin-top:80px;margin-bottom:-180px;padding:60px 48px 180px;margin-left:-80px;margin-right:-80px;width:calc(100% + 160px)">
        <div style="max-width:1180px;margin:0 auto">
            <div style="display:grid;grid-template-columns:1.6fr 1fr 1fr 1fr;gap:48px;margin-bottom:48px">
                <div>
                    <div style="font-size:22px;font-weight:900;color:white;margin-bottom:12px">World Cup 2026</div>
                    <div style="font-size:13px;color:rgba(255,255,255,.5);line-height:1.8;margin-bottom:24px">AI-powered predictions, win probabilities, rankings, and plain-English explanations for FIFA World Cup 2026 matches. Data-driven. Fan-focused.</div>
                    <div style="display:flex;gap:12px">
                        <a href="https://www.linkedin.com/in/sofia-saeed-ahmed/" target="_blank" title="LinkedIn"
                           style="width:36px;height:36px;background:rgba(255,255,255,.1);border-radius:50%;display:grid;place-items:center;text-decoration:none;color:white;font-size:13px;font-weight:700;transition:.15s" onmouseover="this.style.background='#0a66c2'" onmouseout="this.style.background='rgba(255,255,255,.1)'">in</a>
                        <a href="https://github.com/SofiaSaeedAhmed" target="_blank" title="GitHub"
                           style="width:36px;height:36px;background:rgba(255,255,255,.1);border-radius:50%;display:grid;place-items:center;text-decoration:none;color:white;font-size:13px;font-weight:700;transition:.15s" onmouseover="this.style.background='#333'" onmouseout="this.style.background='rgba(255,255,255,.1)'">GH</a>
                        <a href="mailto:sofiasaeed23@gmail.com" title="Email"
                           style="width:36px;height:36px;background:rgba(255,255,255,.1);border-radius:50%;display:grid;place-items:center;text-decoration:none;color:white;font-size:13px;font-weight:700;transition:.15s" onmouseover="this.style.background='#ea4335'" onmouseout="this.style.background='rgba(255,255,255,.1)'">✉</a>
                    </div>
                </div>
                <div>
                    <div style="font-size:11px;font-weight:900;letter-spacing:2px;color:#f5c518;margin-bottom:20px">PREDICTIONS</div>
                    {nav_col}
                </div>
                <div>
                    <div style="font-size:11px;font-weight:900;letter-spacing:2px;color:#f5c518;margin-bottom:20px">EXPLORE</div>
                    {nav_col}
                </div>
                <div>
                    <div style="font-size:11px;font-weight:900;letter-spacing:2px;color:#f5c518;margin-bottom:20px">CONTACT</div>
                    <div style="font-size:14px;color:#f5c518;margin-bottom:12px">sofiasaeed23@gmail.com</div>
                    <div style="font-size:13px;color:rgba(255,255,255,.5);line-height:1.7">Have feedback or data corrections? I'd love to hear from you.</div>
                </div>
            </div>
            <div style="border-top:1px solid rgba(255,255,255,.08);padding-top:24px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px">
                <div style="font-size:12px;color:rgba(255,255,255,.35)">&copy; 2026 World Cup Predictor &middot; Built with XGBoost + Streamlit &middot; Data via football-data.org</div>
                <div style="font-size:12px;color:rgba(255,255,255,.35)">Sofia Saeed Ahmed &middot; Data Science Portfolio</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def show_matches():
    all_groups = sorted(fixtures["group"].unique())
    grp_opts = ["All"] + list(all_groups)
    st_opts = ["All", "Played", "Upcoming"]

    if "match_filter_group" not in st.session_state:
        st.session_state.match_filter_group = "All"
    if "match_filter_status" not in st.session_state:
        st.session_state.match_filter_status = "All"

    sel_grp = st.session_state.match_filter_group
    sel_st = st.session_state.match_filter_status
    if sel_grp not in grp_opts:
        sel_grp = "All"
        st.session_state.match_filter_group = "All"
    if sel_st not in st_opts:
        sel_st = "All"
        st.session_state.match_filter_status = "All"

    view = fixtures.copy()
    if sel_grp != "All":
        view = view[view["group"] == sel_grp]
    if sel_st == "Played":
        view = view[view["played"] == True]
    if sel_st == "Upcoming":
        view = view[view["played"] == False]

    st.markdown("""<style>
    div[data-testid="stRadio"] > label {
        color: #64748b;
        font-size: 11px;
        font-weight: 900;
        letter-spacing: 2.2px;
        margin-bottom: 10px;
    }
    div[role="radiogroup"] {
        gap: 7px;
        flex-wrap: wrap;
    }
    div[role="radiogroup"] label {
        min-height: 30px;
        padding: 0 10px;
        border: 1.5px solid #cbd5e1;
        border-radius: 7px;
        background: #fff;
        box-shadow: none;
        transition: .16s ease;
    }
    div[role="radiogroup"] label:hover {
        transform: translateY(-1px);
        border-color: #0d1b2a;
        box-shadow: 0 8px 18px rgba(13,27,42,.10);
    }
    div[role="radiogroup"] label:has(input:checked) {
        background: #0d1b2a;
        border-color: #0d1b2a;
        color: white;
    }
    div[role="radiogroup"] label:has(input:checked) p,
    div[role="radiogroup"] label:has(input:checked) span {
        color: white !important;
    }
    div[role="radiogroup"] label p {
        font-size: 12px;
        font-weight: 850;
        color: #0d1b2a;
    }
    .fbar {
        max-width: 845px;
        margin: 0 auto 76px;
        background: white;
        border: 1.5px solid #0d1b2a;
        border-radius: 4px;
        padding: 24px 30px 22px;
        box-shadow: 0 24px 44px rgba(13,27,42,.16);
    }
    .fbar-count {
        text-align: right;
        color: #475569;
        font-size: 13px;
        font-weight: 800;
        padding-top: 28px;
    }
    .matches-note {
        max-width: 1240px;
        margin: 0 auto 58px;
        color: #475569;
        font-size: 14px;
        line-height: 1.8;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 16px !important;
        border-color: transparent !important;
        border-width: 0 !important;
        background: white !important;
        box-shadow: 0 10px 28px rgba(13,27,42,.08);
    }
    .new-mcard-body { padding: 8px 8px 4px; }
    .new-mcard-teams { font-size:16px; font-weight:900; color:#0d1b2a; margin-bottom:6px; }
    .new-mcard-meta { font-size:12px; color:#64748b; margin-bottom:8px; line-height:1.55; }
    .pred-btn { text-align:center; padding:4px 0 20px; }
    .pred-btn > div[data-testid="stButton"] { display:inline-flex !important; width:auto !important; }
    .pred-btn > div[data-testid="stButton"] > button {
        background:#f5c518 !important;
        border:2px solid #0d1b2a !important;
        color:#0d1b2a !important;
        font-weight:850 !important;
        border-radius:9px !important;
        min-height:42px !important;
        height:42px !important;
        padding:0 28px !important;
        font-size:15px !important;
        width:auto !important;
        box-shadow:none !important;
    }
    .pred-btn > div[data-testid="stButton"] > button:hover {
        background:#ffd43b !important;
        transform: translateY(-1px);
    }
    </style>""", unsafe_allow_html=True)

    st.markdown('<div class="page-wrap">', unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center;padding:48px 0 20px">
        <div class="sec-kicker">MATCH PREDICTIONS</div>
        <div class="sec-title">All 72 Group-Stage Fixtures</div>
    </div>
    """, unsafe_allow_html=True)

    left_pad, filter_col, right_pad = st.columns([0.22, 1, 0.22])
    with filter_col:
        with st.container(border=True):
            st.radio("GROUP", grp_opts, horizontal=True, key="match_filter_group")
            row_l, row_r = st.columns([3.2, 1])
            with row_l:
                st.radio("STATUS", st_opts, horizontal=True, key="match_filter_status")
            with row_r:
                st.markdown(f'<div class="fbar-count">Showing {len(view)} matches</div>', unsafe_allow_html=True)

    st.markdown("""<style>
    .mlist-date-group { margin-bottom: 0; }
    .mlist-sep { border:none; border-top:1px solid #e2e8f0; margin:6px 0 14px; }
    .mlist-row { display:flex; align-items:center; padding:7px 0; gap:12px; }
    .mlist-date { font-size:13px; color:#94a3b8; font-weight:700; min-width:54px; }
    .mlist-grp  { font-size:12px; font-weight:900; letter-spacing:1px; color:#0d1b2a;
                  background:#f1f5f9; border-radius:5px; padding:3px 8px; white-space:nowrap; }
    .mlist-teams { flex:1; font-size:15px; font-weight:700; color:#0d1b2a; }
    .mlist-score { font-size:13px; font-weight:800; color:#64748b; min-width:42px; text-align:center; }
    .mlist-badge-c { font-size:11px; font-weight:800; color:#16a34a; background:#dcfce7;
                     border-radius:5px; padding:2px 8px; white-space:nowrap; }
    .mlist-badge-w { font-size:11px; font-weight:800; color:#ef4444; background:#fee2e2;
                     border-radius:5px; padding:2px 8px; white-space:nowrap; }
    .mlist-pred { font-size:12px; color:#64748b; min-width:160px; }
    .mlist-btn { margin: 2px 0 9px; }
    .mlist-btn div[data-testid="stButton"] > button,
    div[data-testid="stButton"] > button[kind="secondary"] {
        background:#f5c518 !important;
        border:2px solid #0d1b2a !important;
        color:#0d1b2a !important;
        font-weight:800 !important;
        border-radius:8px !important;
        padding:0 16px !important;
        font-size:13px !important;
        min-height:32px !important;
        height:32px !important;
        line-height:32px !important;
        max-width:128px !important;
        margin-bottom:6px !important;
        white-space:nowrap !important;
    }
    </style>""", unsafe_allow_html=True)

    # Group rows by date, render date block then separator
    from itertools import groupby
    rows_sorted = list(view.sort_values(["date", "group"]).iterrows())
    date_groups = [(d, list(rs)) for d, rs in groupby(rows_sorted, key=lambda x: x[1]["date"])]

    for di, (date_val, date_rows) in enumerate(date_groups):
        for _, row in date_rows:
            pred = predictions.get(row["id"])
            hc_ = tc(row["home"]); ac_ = tc(row["away"])

            if row["played"]:
                score_disp = f'{int(row["hs"])}–{int(row["as_"])}'
                if pred:
                    badge = '<span class="mlist-badge-c">✓ Correct</span>' if is_correct(row, pred) else '<span class="mlist-badge-w">✗ Incorrect</span>'
                else:
                    badge = ""
            else:
                score_disp = "vs"
                badge = ""

            pred_label = f'Predicted: {esc(pred["predicted"])} &middot; {pred["confidence"]}%' if pred else ""

            left, right = st.columns([11, 1.4])
            with left:
                st.markdown(f"""
                <div class="mlist-row">
                    <span class="mlist-date">{esc(row["date"])}</span>
                    <span class="mlist-grp">Group {esc(row["group"])}</span>
                    <span class="mlist-teams">{esc(row["home"])} vs {esc(row["away"])}</span>
                    <span class="mlist-score">{score_disp}</span>
                    {badge}
                    {f'<span class="mlist-pred">{pred_label}</span>' if pred_label else ''}
                </div>
                """, unsafe_allow_html=True)
            with right:
                st.markdown('<div class="mlist-btn">', unsafe_allow_html=True)
                nav_to_match(row["id"], "Analyse", prefix=f"ml_{row['id']}")
                st.markdown('</div>', unsafe_allow_html=True)

        # separator between date groups (not after last)
        if di < len(date_groups) - 1:
            st.markdown('<hr class="mlist-sep">', unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

def show_tournament():
    st.markdown('<div class="page-wrap">', unsafe_allow_html=True)
    st.markdown("""
    <div class="sec-kicker">GROUP STAGE · 2026</div>
    <div class="sec-title">Group Standings</div>
    <div class="sec-desc">Live standings based on matches played so far. Top two from each group advance automatically to the Round of 32.</div>
    """, unsafe_allow_html=True)

    groups = sorted(fixtures["group"].unique())
    for i in range(0, len(groups), 2):
        pair = groups[i:i+2]
        cols = st.columns(2, gap="medium")
        for col, grp in zip(cols, pair):
            with col:
                table = group_table(grp)
                teams_str = " · ".join(f'<span class="t-code">{tc(t)}</span>{esc(t)}' for t in table["Team"])
                trows = ""
                for pos, (_, r) in enumerate(table.iterrows(), 1):
                    trows += f"""<tr>
                        <td>{pos}</td>
                        <td><span class="t-code">{tc(r["Team"])}</span>{flag(r["Team"])} {esc(r["Team"])}</td>
                        <td>{r["P"]}</td><td>{r["W"]}</td><td>{r["D"]}</td><td>{r["L"]}</td>
                        <td>{r["GF"]}</td><td>{r["GA"]}</td><td>{r["GD"]:+}</td>
                        <td class="t-pts">{r["PTS"]}</td>
                    </tr>"""
                st.markdown(f"""
                <div class="t-wrap">
                    <div class="t-head">
                        <div class="t-grp-title">Group {grp}</div>
                        <div class="t-grp-teams">{teams_str}</div>
                    </div>
                    <table class="t-table">
                        <thead><tr><th>#</th><th>Team</th><th>P</th><th>W</th><th>D</th><th>L</th><th>GF</th><th>GA</th><th>GD</th><th>PTS</th></tr></thead>
                        <tbody>{trows}</tbody>
                    </table>
                </div>""", unsafe_allow_html=True)

    # Who's advancing
    st.markdown("""
    <div style="margin-top:48px">
        <div class="sec-kicker">QUALIFICATION PICTURE</div>
        <div class="sec-title">Who's Advancing?</div>
        <div class="sec-desc">Based on current standings, these are the teams on course to advance. Top 2 from each group qualify automatically.</div>
    </div>
    """, unsafe_allow_html=True)

    top2_lines = []; third_lines = []
    for grp in sorted(fixtures["group"].unique()):
        t = group_table(grp)
        tl = list(t["Team"])
        if len(tl) >= 2:
            t1 = f'<span class="t-code">{tc(tl[0])}</span>{flag(tl[0])} {esc(tl[0])}'
            t2 = f'<span class="t-code">{tc(tl[1])}</span>{flag(tl[1])} {esc(tl[1])}'
            top2_lines.append(f'<div style="font-size:13px;color:#0d1b2a;padding:6px 0;border-bottom:1px solid #f1f5f9">Group {grp}: {t1} · {t2}</div>')
        if len(tl) >= 3:
            pts = int(t.iloc[2]["PTS"])
            third_lines.append(f'<div style="font-size:13px;color:#0d1b2a;padding:6px 0;border-bottom:1px solid #f1f5f9">Group {grp}: <span class="t-code">{tc(tl[2])}</span>{flag(tl[2])} {esc(tl[2])} — {pts} pt{"s" if pts!=1 else ""}</div>')

    c1, c2, c3 = st.columns(3, gap="medium")
    with c1:
        st.markdown(f"""
        <div class="t-wrap" style="padding:20px">
            <div class="t-grp-title" style="font-size:18px;margin-bottom:12px">Top-2 Qualifiers</div>
            {"".join(top2_lines) or '<div style="font-size:13px;color:#94a3b8">No matches played yet.</div>'}
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="t-wrap" style="padding:20px">
            <div class="t-grp-title" style="font-size:18px;margin-bottom:6px">Best Third Place</div>
            <div style="font-size:12px;color:#94a3b8;margin-bottom:10px">8 best 3rd-place teams advance.</div>
            {"".join(third_lines) or '<div style="font-size:13px;color:#94a3b8">No matches played yet.</div>'}
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div class="t-wrap" style="padding:20px">
            <div class="t-grp-title" style="font-size:18px;margin-bottom:6px">Out of Contention</div>
            <div style="font-size:13px;color:#94a3b8">No teams eliminated yet.</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def show_about():
    st.markdown('<div class="page-wrap">', unsafe_allow_html=True)

    # ── Methodology hero ──────────────────────────────────────────────────────
    st.markdown("""
    <div style="
        background-image: linear-gradient(rgba(10,22,40,.65) 0%, rgba(10,22,40,.82) 100%), url('https://images.pexels.com/photos/1884574/pexels-photo-1884574.jpeg?auto=compress&cs=tinysrgb&w=1920');
        background-size:cover; background-position:center;
        border-radius:16px; padding:80px 48px; text-align:center; margin-bottom:48px;">
        <div style="font-size:11px;font-weight:900;letter-spacing:3px;color:#f5c518;margin-bottom:12px">METHODOLOGY</div>
        <div style="font-size:clamp(36px,5vw,64px);font-weight:900;color:white;line-height:1.05;margin-bottom:24px;letter-spacing:-1px">How the Model Works</div>
        <div style="font-size:16px;color:rgba(255,255,255,.75);line-height:1.8;max-width:720px;margin:0 auto 12px">
            This project uses an XGBoost multiclass classifier trained on 23,000+ international matches played
            between 2000 and 2021. The model predicts one of three outcomes for each fixture: home win,
            draw, or away win. It was tested on the 2026 FIFA World Cup group stage — matches it has never
            seen — giving a clean out-of-sample benchmark for real performance.
        </div>
        <div style="font-size:16px;color:rgba(255,255,255,.75);line-height:1.8;max-width:720px;margin:0 auto 28px">
            XGBoost was chosen for its ability to handle tabular data with mixed feature scales, its built-in
            regularisation, and its reliable probability calibration across multiclass targets. Softmax output
            gives a probability distribution over all three outcomes for every match.
        </div>
        <div style="display:inline-block;padding:8px 24px;border-radius:999px;background:rgba(245,197,24,.15);border:1.5px solid rgba(245,197,24,.5);font-size:13px;font-weight:800;letter-spacing:2px;color:#f5c518">FIFA WORLD CUP 2026</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Feature table ─────────────────────────────────────────────────────────
    st.markdown("""
    <div class="sec-kicker">FEATURE ENGINEERING</div>
    <div class="sec-title">What the Model Learns From</div>
    <div class="sec-desc">Four engineered features drive every prediction. Each is calculated from historical data at the time of the match — no future information leaks in.</div>

    <div style="border:1px solid #d1d5db;border-radius:12px;overflow:hidden;margin-bottom:16px">
        <table style="width:100%;border-collapse:collapse">
            <thead>
                <tr style="background:#6b8dd6">
                    <th style="padding:14px 20px;text-align:left;color:white;font-size:14px;font-weight:800;width:220px">Feature</th>
                    <th style="padding:14px 20px;text-align:left;color:white;font-size:14px;font-weight:800">What It Captures</th>
                    <th style="padding:14px 20px;text-align:center;color:white;font-size:14px;font-weight:800;width:180px">Relative Importance</th>
                </tr>
            </thead>
            <tbody>
                <tr style="border-bottom:1px solid #e5e7eb">
                    <td style="padding:14px 20px;font-size:14px;font-weight:700;color:#0d1b2a">FIFA Rankings Gap</td>
                    <td style="padding:14px 20px;font-size:14px;color:#374151;line-height:1.6">The difference in FIFA world ranking between the two teams — the single strongest signal of relative quality on paper.</td>
                    <td style="padding:14px 20px;font-size:18px;text-align:center">★★★★★</td>
                </tr>
                <tr style="border-bottom:1px solid #e5e7eb">
                    <td style="padding:14px 20px;font-size:14px;font-weight:700;color:#0d1b2a">Recent Form<br><span style="font-weight:400;font-size:12px;color:#6b7280">(10-game win rate)</span></td>
                    <td style="padding:14px 20px;font-size:14px;color:#374151;line-height:1.6">Each team's win rate across their last 10 international matches — captures momentum and current condition.</td>
                    <td style="padding:14px 20px;font-size:18px;text-align:center">★★★★☆</td>
                </tr>
                <tr style="border-bottom:1px solid #e5e7eb">
                    <td style="padding:14px 20px;font-size:14px;font-weight:700;color:#0d1b2a">Head-to-Head Ratio</td>
                    <td style="padding:14px 20px;font-size:14px;color:#374151;line-height:1.6">Historical win rate for the home team across all previous meetings. Neutral (0.5) when no prior matchups exist.</td>
                    <td style="padding:14px 20px;font-size:18px;text-align:center">★★★☆☆</td>
                </tr>
                <tr>
                    <td style="padding:14px 20px;font-size:14px;font-weight:700;color:#0d1b2a">Tournament Weight</td>
                    <td style="padding:14px 20px;font-size:14px;color:#374151;line-height:1.6">A fixed importance score per competition type — World Cup = 5/5, friendlies = 1/5. Higher weight amplifies the favourite's edge.</td>
                    <td style="padding:14px 20px;font-size:18px;text-align:center">★★☆☆☆</td>
                </tr>
            </tbody>
        </table>
    </div>
    <div style="font-size:13px;color:#6b8dd6;line-height:1.7;margin-bottom:48px">
        All features are computed at prediction time from available historical data. No player-level data, injury reports, or lineup information is used — this is intentional to keep the model reproducible and transparent.
    </div>
    """, unsafe_allow_html=True)

    # ── SHAP Analysis ─────────────────────────────────────────────────────────
    st.markdown("""
    <div class="sec-kicker">SHAP ANALYSIS</div>
    <div class="sec-title">What Drives Each Prediction?</div>
    <div class="sec-desc">
        SHAP (SHapley Additive exPlanations) goes beyond standard feature importance — it shows not just
        <em>which</em> features matter, but <em>how</em> and <em>how much</em> each one pushes the model
        toward a specific outcome for every individual match.
    </div>
    """, unsafe_allow_html=True)

    for finding, detail, badge in [
        ("rank_diff dominates everything",
         "The FIFA rankings gap has the highest SHAP value across all three outcome classes by a significant margin. A large negative rank_diff (home team much stronger) strongly pushes the model toward Home Win; a large positive rank_diff pushes it toward Away Win. This is the single strongest signal in the model.",
         "#f5c518"),
        ("home_form & away_form are the second tier",
         "Recent form adds genuine signal on top of rankings — a strong team in poor form vs a weaker team on a hot streak gets meaningfully different probabilities than the raw rank gap alone would suggest. Form matters most for decisive outcomes (home win or away win).",
         "#3b82f6"),
        ("h2h has limited but real impact",
         "Head-to-head history contributes less than form or rankings. For many matchups — especially cross-confederation — the H2H record is sparse and defaults to neutral (0.5). The signal is real but noisy.",
         "#8b5cf6"),
        ("weight (tournament importance) is the weakest feature",
         "Surprising at first — you'd expect World Cup matches to behave very differently from friendlies. But rankings and form already capture team quality; tournament type adds only marginal signal after those are accounted for. It's worth keeping but not a primary driver.",
         "#64748b"),
        ("Draws are structurally hard to predict",
         "For draws specifically, all features contribute at roughly equal but lower magnitude compared to win prediction. There is no single strong signal that a match will end level — this explains the model's draw blind spot and is consistent with the academic literature on football outcome modelling.",
         "#ef4444"),
    ]:
        st.markdown(f"""
        <div style="display:flex;gap:16px;align-items:flex-start;margin-bottom:20px;padding:20px 24px;
                    background:white;border:1px solid #e2e8f0;border-radius:12px;
                    box-shadow:0 2px 8px rgba(13,27,42,.05)">
            <div style="width:4px;min-height:60px;border-radius:4px;background:{badge};flex-shrink:0;margin-top:2px"></div>
            <div>
                <div style="font-size:15px;font-weight:800;color:#0d1b2a;margin-bottom:6px">{finding}</div>
                <div style="font-size:14px;color:#64748b;line-height:1.7">{detail}</div>
            </div>
        </div>""", unsafe_allow_html=True)

    st.markdown('<div style="margin-bottom:48px"></div>', unsafe_allow_html=True)

    # ── Performance ───────────────────────────────────────────────────────────
    st.markdown("""
    <div class="sec-kicker">EVALUATION</div>
    <div class="sec-title">Model Performance on 2026 Group Stage</div>
    <div style="font-size:14px;color:#6b8dd6;line-height:1.7;margin-bottom:28px">
        The model was evaluated on all group-stage fixtures where ranking data was available. Results reflect genuine out-of-sample performance — the model was trained on data ending in 2021 and has not been retrained on 2026 data.
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2, gap="medium")
    with c1:
        st.markdown("""
        <div class="t-wrap" style="padding:40px;text-align:center">
            <div><span style="font-size:72px;font-weight:900;color:#f5c518">57</span><span style="font-size:40px;font-weight:900;color:#0d1b2a">%</span></div>
            <div style="font-size:14px;color:#64748b;margin-top:8px">Overall Accuracy across all match outcomes (34/60)</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="t-wrap" style="padding:40px;text-align:center">
            <div><span style="font-size:72px;font-weight:900;color:#f5c518">71</span><span style="font-size:40px;font-weight:900;color:#0d1b2a">%</span></div>
            <div style="font-size:14px;color:#64748b;margin-top:8px">Accuracy on Decisive Matches (home win or away win only)</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("""
    <div style="font-size:14px;color:#6b8dd6;line-height:1.8;margin-top:28px">
        Where does the model go wrong? The primary failure mode is draws. Draws account for roughly 25% of all fixtures, but the model correctly identifies fewer than 1 in 5 of them. When a draw occurs, the model most often predicts a win for the higher-ranked team instead.
    </div>
    <div style="font-size:14px;color:#6b8dd6;line-height:1.8;margin-top:14px;margin-bottom:48px">
        This pattern is consistent with the academic literature on football outcome modelling: draws are structurally hard to predict. Future versions could experiment with draw-probability calibration layers or ensemble methods trained specifically on draw conditions.
    </div>
    """, unsafe_allow_html=True)

    # ── Limitations ───────────────────────────────────────────────────────────
    st.markdown("""
    <div class="sec-title">Known Limitations &amp; Future Improvements</div>
    <div class="sec-desc">No prediction model is complete. Here is an honest account of what this version does not do well.</div>
    """, unsafe_allow_html=True)

    for title, body in [
        ("Draw Prediction Weakness", "The model's biggest blind spot. Draws are predicted correctly less than 20% of the time. The ranking-gap and form features both push toward a winner; neither has a strong draw signal. A dedicated draw-probability adjustment or a binary draw/no-draw classifier could substantially improve this."),
        ("Data Recency", "Training data ends in 2021. Squad compositions, manager changes, and team form from 2022–2025 are captured only through the pre-match form window and current FIFA rankings — not through direct match history. This creates a recency gap for teams that have changed significantly since 2021."),
        ("No Player-Level Features", "The model does not know whether a team's top scorer is injured, a key midfielder is suspended, or which starting eleven is selected. Adding player availability signals — even binary flags for star-player absence — would meaningfully reduce prediction error on high-profile upsets."),
        ("Potential Improvements", "Planned directions for a v2 model: Elo rating integration; draw-calibration layer post-softmax; player availability binary features; expanding the training window to 2022–2025; and a Bayesian uncertainty estimate alongside the point probability."),
    ]:
        st.markdown(f"""
        <div style="margin-bottom:28px">
            <div style="font-size:20px;font-weight:800;color:#1e40af;margin-bottom:8px">{title}</div>
            <div style="font-size:14px;color:#374151;line-height:1.8">{body}</div>
        </div>""", unsafe_allow_html=True)

    # ── Monte Carlo ───────────────────────────────────────────────────────────
    st.markdown("""
    <div style="margin-top:64px">
        <div class="sec-kicker">KNOCKOUT STAGE</div>
        <div class="sec-title">Monte Carlo Simulation</div>
        <div class="sec-desc">
            After the group stage, the model was retrained on the full dataset — all 23,000+ historical matches
            including all 72 group stage results — and used to simulate the knockout bracket 10,000 times.
            Monte Carlo simulation is a technique where a random process is repeated thousands of times to estimate probabilities that are too complex to calculate analytically.
            Here, each simulation plays out the entire 32-team bracket from start to finish, with every match outcome determined by the model's win probabilities.
            Because knockout football is path-dependent — who you face in the QF depends on who won the other side of the bracket — running 10,000 full tournaments
            captures that uncertainty in a way that a single probability estimate per match cannot.
        </div>
    </div>
    """, unsafe_allow_html=True)

    for title, body in [
        ("Why retrain for the knockout stage?",
         "The group stage results add 72 new data points that include the actual 2026 teams playing at this tournament. Retraining incorporates this signal directly into the model weights, giving more accurate probability estimates for the knockout rounds than a model trained on historical data alone."),
        ("How are draws handled in knockout matches?",
         "In knockout football there are no draws — matches go to extra time and penalties if level. The model outputs a draw probability alongside home and away win probabilities. For knockout predictions, the draw probability is redistributed proportionally between the two teams: each team absorbs a share of the draw probability in proportion to their own win likelihood."),
        ("What does the bracket simulation do?",
         "The 32-team bracket is fixed (based on the actual 2026 R32 draw). In each of 10,000 simulated tournaments, every match is resolved by sampling from the model's win probabilities. Winners advance through R32 → R16 → QF → SF → Final, with a third-place playoff for SF losers. The percentage of simulations where a team reaches each stage becomes their stage probability."),
        ("Why 10,000 simulations?",
         "10,000 gives probability estimates stable to roughly ±0.5% — enough precision to meaningfully distinguish, say, a 32% title chance from a 28% one. Running more simulations would reduce variance further but yields diminishing returns. With the probability cache optimisation (precomputing all 992 team pairings once), 10,000 runs complete in a few seconds."),
    ]:
        st.markdown(f"""
        <div style="margin-bottom:28px">
            <div style="font-size:20px;font-weight:800;color:#1e40af;margin-bottom:8px">{title}</div>
            <div style="font-size:14px;color:#374151;line-height:1.8">{body}</div>
        </div>""", unsafe_allow_html=True)

    # ── FAQ ───────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="margin-top:48px">
        <div class="sec-title">Frequently Asked Questions</div>
        <div class="sec-desc">Concrete answers to the questions technically curious visitors ask most.</div>
    </div>
    """, unsafe_allow_html=True)

    for q, a in [
        ("Why doesn't the model predict scorelines?", "The model is a multiclass classifier, not a regression model. It outputs probabilities over three categorical outcomes — home win, draw, away win. Predicting scorelines requires a different architecture (typically Poisson regression on expected goals). That is a possible future extension."),
        ("How is match data sourced?", "Match scores are hardcoded into the app from verified results and updated manually after each matchday. This avoids dependency on third-party APIs and ensures scores are always accurate."),
        ("What happens when ranking data is missing for a team?", "If a team has no FIFA ranking entry on or before the match date, the model cannot generate a prediction and the card will show 'Prediction unavailable'. This affects very few fixtures — mainly smaller nations with sparse ranking history."),
        ("Does the model update mid-tournament?", "No. The XGBoost model was trained once on data ending in 2021. A retrained version using group-stage results is planned after the group stage ends."),
        ("How accurate is 57% in context — is that good?", "A naive baseline that always predicts the higher-ranked team wins achieves roughly 50–52%. The 57% overall (34/60 group stage matches) represents a meaningful improvement over the naive baseline, especially on decisive matches."),
    ]:
        with st.expander(q):
            st.markdown(f'<div style="font-size:14px;color:#6b8dd6;line-height:1.8;padding:6px 0">{a}</div>', unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def show_knockout():
    import plotly.graph_objects as go
    st.markdown('<div class="page-wrap">', unsafe_allow_html=True)

    # ── Load Monte Carlo results ──────────────────────────────────────────────
    mc_path = Path("data/processed/monte_carlo_r32.csv")
    if not mc_path.exists():
        st.warning("Monte Carlo results not found. Run `notebooks/04_monte_carlo.ipynb` first.")
        return
    mc = pd.read_csv(mc_path)

    # ── Hero ──────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="
        background-image: linear-gradient(rgba(10,22,40,.65) 0%, rgba(10,22,40,.82) 100%), url('https://images.pexels.com/photos/1884574/pexels-photo-1884574.jpeg?auto=compress&cs=tinysrgb&w=1920');
        background-size:cover; background-position:center;
        border-radius:16px; padding:52px 48px; text-align:center; margin-bottom:48px;">
        <div style="font-size:11px;font-weight:900;letter-spacing:3px;color:#f5c518;margin-bottom:12px">KNOCKOUT STAGE · 2026</div>
        <div style="font-size:clamp(30px,4vw,52px);font-weight:900;color:white;line-height:1.05;margin-bottom:10px;letter-spacing:-1px">Knockout Stage Predictions</div>
        <div style="font-size:18px;font-weight:700;color:#f5c518;margin-bottom:20px">Monte Carlo Simulation</div>
        <div style="font-size:15px;color:rgba(255,255,255,.75);line-height:1.8;max-width:680px;margin:0 auto 24px">
            XGBoost v2 retrained on 23,000+ matches including all 72 group stage results.
            Draw probability is redistributed between teams for knockout rounds.
            10,000 simulated tournaments estimate each team's path to the Final.
        </div>
        <div style="display:inline-block;padding:8px 24px;border-radius:999px;background:rgba(245,197,24,.15);border:1.5px solid rgba(245,197,24,.5);font-size:13px;font-weight:800;letter-spacing:2px;color:#f5c518">FIFA WORLD CUP 2026</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Stage tabs + arrows ───────────────────────────────────────────────────
    stage_options = ["R32", "R16", "Quarter-Final", "Semi-Final", "Final"]
    stage_labels  = ["Round of 32", "Round of 16", "Quarter-Final", "Semi-Final", "Final"]
    if "ko_stage" not in st.session_state:
        st.session_state.ko_stage = 0
    stage_idx = st.session_state.ko_stage

    st.markdown(f"""
    <style>
    {"".join([
        f'div[data-testid="stColumn"]:nth-child({i+2}) button {{ background:{"#f5c518" if i==stage_idx else "white"} !important; border:1.5px solid {"#f5c518" if i==stage_idx else "#e2e8f0"} !important; border-radius:8px !important; font-weight:700 !important; color:#0d1b2a !important; }}'
        for i in range(len(stage_options))
    ])}
    </style>""", unsafe_allow_html=True)

    _, tab_c1, tab_c2, tab_c3, tab_c4, tab_c5, _ = st.columns([1, 2, 2, 2, 2, 2, 1])
    for i, (opt, lbl, col) in enumerate(zip(stage_options, stage_labels, [tab_c1, tab_c2, tab_c3, tab_c4, tab_c5])):
        with col:
            if st.button(opt, key=f"ko_tab_{i}", help=lbl, use_container_width=True):
                st.session_state.ko_stage = i
                st.session_state.ko_sub = 0
                st.rerun()
    selected_stage = stage_options[stage_idx]


    # ── Bracket data ─────────────────────────────────────────────────────────
    R32 = [
        ("South Africa",           "Canada",                 "R32_01"),
        ("Netherlands",            "Morocco",                "R32_02"),
        ("Germany",                "Paraguay",               "R32_03"),
        ("France",                 "Sweden",                 "R32_04"),
        ("Belgium",                "Senegal",                "R32_05"),
        ("USA",                    "Bosnia and Herzegovina", "R32_06"),
        ("Spain",                  "Austria",                "R32_07"),
        ("Portugal",               "Croatia",                "R32_08"),
        ("Brazil",                 "Japan",                  "R32_09"),
        ("Côte d'Ivoire",          "Norway",                 "R32_10"),
        ("Mexico",                 "Ecuador",                "R32_11"),
        ("England",                "Congo DR",               "R32_12"),
        ("Switzerland",            "Algeria",                "R32_13"),
        ("Colombia",               "Ghana",                  "R32_14"),
        ("Australia",              "Egypt",                  "R32_15"),
        ("Argentina",              "Cabo Verde",             "R32_16"),
    ]

    # R16 pairings label
    R16_LABELS = {
        ("R32_01","R32_02"): "R16 Match A",
        ("R32_03","R32_04"): "R16 Match B",
        ("R32_05","R32_06"): "R16 Match C",
        ("R32_07","R32_08"): "R16 Match D",
        ("R32_09","R32_10"): "R16 Match E",
        ("R32_11","R32_12"): "R16 Match F",
        ("R32_13","R32_14"): "R16 Match G",
        ("R32_15","R32_16"): "R16 Match H",
    }

    def flag(t): return FLAGS.get(t, "🏳")

    def mc_val(team, col):
        row = mc[mc["team"] == team]
        return f"{row[col].values[0]:.1f}%" if len(row) else "—"

    def mc_float(team, col):
        row = mc[mc["team"] == team]
        return float(row[col].values[0]) if len(row) else 0.0


    def pw(t1, t2, col):
        return t1 if mc_float(t1, col) >= mc_float(t2, col) else t2

    sub_stages = ["R32 Matchups", "Predicted R16", "Predicted QF", "Predicted SF", "Predicted Final"]
    if "ko_sub" not in st.session_state:
        st.session_state.ko_sub = 0

    # ── Stage content ─────────────────────────────────────────────────────────
    if selected_stage == "R32":
        # Sub-navigation dots + arrows
        sub_idx = st.session_state.ko_sub
        dots_html = "".join([
            f'<div style="width:9px;height:9px;border-radius:50%;background:{"#f5c518" if i==sub_idx else "#cbd5e1"};margin:0 3px;display:inline-block"></div>'
            for i in range(len(sub_stages))
        ])
        st.markdown("<div style='margin-top:20px'></div>", unsafe_allow_html=True)
        _, sa, sb, sc, _ = st.columns([2, 1, 6, 1, 2])
        with sa:
            if sub_idx > 0 and st.button("←", key="sub_prev"):
                st.session_state.ko_sub -= 1; st.rerun()
        with sb:
            st.markdown(f'<div style="text-align:center;padding-top:10px">{dots_html}<span style="font-size:12px;color:#94a3b8;margin-left:10px">{sub_stages[sub_idx]}</span></div>', unsafe_allow_html=True)
        with sc:
            if sub_idx < len(sub_stages)-1 and st.button("→", key="sub_next"):
                st.session_state.ko_sub += 1; st.rerun()

        sub_idx = st.session_state.ko_sub

        # Build predicted bracket
        r32w = {mid: pw(h, a, "pct_reach_R16") for h, a, mid in R32}
        R16_pred = [
            (r32w["R32_01"], r32w["R32_02"], "R16_01", "QF Match A"),
            (r32w["R32_03"], r32w["R32_04"], "R16_02", "QF Match B"),
            (r32w["R32_05"], r32w["R32_06"], "R16_03", "QF Match C"),
            (r32w["R32_07"], r32w["R32_08"], "R16_04", "QF Match D"),
            (r32w["R32_09"], r32w["R32_10"], "R16_05", "QF Match E"),
            (r32w["R32_11"], r32w["R32_12"], "R16_06", "QF Match F"),
            (r32w["R32_13"], r32w["R32_14"], "R16_07", "QF Match G"),
            (r32w["R32_15"], r32w["R32_16"], "R16_08", "QF Match H"),
        ]
        r16w = {mid: pw(h, a, "pct_reach_QF") for h, a, mid, _ in R16_pred}
        QF_pred = [
            (r16w["R16_01"], r16w["R16_02"], "QF_01", "SF Match 1"),
            (r16w["R16_03"], r16w["R16_04"], "QF_02", "SF Match 2"),
            (r16w["R16_05"], r16w["R16_06"], "QF_03", "SF Match 3"),
            (r16w["R16_07"], r16w["R16_08"], "QF_04", "SF Match 4"),
        ]
        qfw = {mid: pw(h, a, "pct_reach_SF") for h, a, mid, _ in QF_pred}
        SF_pred = [
            (qfw["QF_01"], qfw["QF_02"], "SF_01", "Final Match 1"),
            (qfw["QF_03"], qfw["QF_04"], "SF_02", "Final Match 2"),
        ]
        sfw = {mid: pw(h, a, "pct_reach_Final") for h, a, mid, _ in SF_pred}

        def render_card(col, home, away, mid, stat_col, stat_label):
            with col:
                h_stat = mc_val(home, stat_col); a_stat = mc_val(away, stat_col)
                h_win = mc_val(home, "pct_win_title"); a_win = mc_val(away, "pct_win_title")
                st.markdown(f"""
                <div style="background:white;border:1px solid #e2e8f0;border-radius:14px;padding:20px 24px;box-shadow:0 2px 8px rgba(13,27,42,.06)">
                    <div style="font-size:10px;font-weight:700;color:#94a3b8;margin-bottom:14px">{mid}</div>
                    <div style="display:flex;justify-content:space-between;align-items:center;gap:8px">
                        <div style="text-align:center;flex:1">
                            <div style="font-size:28px">{flag(home)}</div>
                            <div style="font-size:13px;font-weight:700;color:#0d1b2a;margin-top:4px">{esc(home)}</div>
                            <div style="font-size:11px;color:#94a3b8;margin-top:2px">{stat_label}: {h_stat} · Title: {h_win}</div>
                        </div>
                        <div style="font-size:16px;font-weight:900;color:#cbd5e1">VS</div>
                        <div style="text-align:center;flex:1">
                            <div style="font-size:28px">{flag(away)}</div>
                            <div style="font-size:13px;font-weight:700;color:#0d1b2a;margin-top:4px">{esc(away)}</div>
                            <div style="font-size:11px;color:#94a3b8;margin-top:2px">{stat_label}: {a_stat} · Title: {a_win}</div>
                        </div>
                    </div>
                </div>""", unsafe_allow_html=True)

        def render_grid(pairs, stat_col, stat_label, group_label_fn=None):
            for i in range(0, len(pairs), 2):
                batch = pairs[i:i+2]
                if group_label_fn:
                    _sp0, col_label, _sp3 = st.columns([0.5, 10, 0.5])
                    with col_label:
                        st.markdown(f'<div style="font-size:13px;font-weight:900;letter-spacing:1.5px;color:#f5c518;margin:36px 0 20px;text-transform:uppercase;border-left:3px solid #f5c518;padding-left:12px">{group_label_fn(i)} — Winner advances</div>', unsafe_allow_html=True)
                _, c1, c2, _ = st.columns([0.5, 5, 5, 0.5], gap="medium")
                render_card(c1, batch[0][0], batch[0][1], batch[0][2], stat_col, stat_label)
                if len(batch) > 1:
                    render_card(c2, batch[1][0], batch[1][1], batch[1][2], stat_col, stat_label)

        if sub_idx == 0:
            for i in range(0, len(R32), 2):
                m1 = R32[i]; m2 = R32[i+1]
                label = R16_LABELS.get((m1[2], m2[2]), "")
                _sp0, col_label, _sp3 = st.columns([0.5, 10, 0.5], gap="small")
                with col_label:
                    st.markdown(f'<div style="font-size:13px;font-weight:900;letter-spacing:1.5px;color:#f5c518;margin:36px 0 20px;text-transform:uppercase;border-left:3px solid #f5c518;padding-left:12px">{label} — Winner advances</div>', unsafe_allow_html=True)
                _, c1, c2, _ = st.columns([0.5, 5, 5, 0.5], gap="medium")
                render_card(c1, m1[0], m1[1], m1[2], "pct_reach_R16", "R16")
                render_card(c2, m2[0], m2[1], m2[2], "pct_reach_R16", "R16")

        elif sub_idx == 1:
            r16_group_labels = ["QF Match A", "QF Match B", "QF Match C", "QF Match D", "QF Match E", "QF Match F", "QF Match G", "QF Match H"]
            render_grid(R16_pred, "pct_reach_QF", "QF", lambda i: r16_group_labels[i//2 * 2 // 2])

        elif sub_idx == 2:
            render_grid(QF_pred, "pct_reach_SF", "SF", lambda i: f"SF Match {i//2 + 1}")

        elif sub_idx == 3:
            render_grid(SF_pred, "pct_reach_Final", "Final", lambda i: f"Final Match {i//2 + 1}")

        elif sub_idx == 4:
            fin_home, fin_away = sfw["SF_01"], sfw["SF_02"]
            champion = pw(fin_home, fin_away, "pct_win_title")
            _sp0, col_label, _sp3 = st.columns([0.5, 10, 0.5])
            with col_label:
                st.markdown('<div style="font-size:13px;font-weight:900;letter-spacing:1.5px;color:#f5c518;margin:36px 0 20px;text-transform:uppercase;border-left:3px solid #f5c518;padding-left:12px">THE FINAL — Predicted Champion</div>', unsafe_allow_html=True)
            _, c1, c_mid, c2, _ = st.columns([0.5, 4, 2, 4, 0.5], gap="medium")
            render_card(c1, fin_home, fin_away, "FINAL", "pct_win_title", "Title")
            with c_mid:
                st.markdown(f"""
                <div style="text-align:center;padding-top:40px">
                    <div style="font-size:11px;font-weight:800;letter-spacing:1px;color:#94a3b8;margin-bottom:8px">PREDICTED CHAMPION</div>
                    <div style="font-size:36px">{flag(champion)}</div>
                    <div style="font-size:14px;font-weight:800;color:#f5c518;margin-top:6px">{esc(champion)}</div>
                    <div style="font-size:12px;color:#94a3b8;margin-top:4px">{mc_val(champion, "pct_win_title")} chance</div>
                </div>""", unsafe_allow_html=True)

    elif selected_stage == "R16":
        mc_r16_path = Path("data/processed/monte_carlo_r16.csv")
        if not mc_r16_path.exists():
            st.warning("R16 Monte Carlo results not found. Run `notebooks/04_monte_carlo.ipynb` R16 cells first.")
        else:
            mc16 = pd.read_csv(mc_r16_path)

            def mc16_val(team, col):
                row = mc16[mc16["team"] == team]
                return f"{row[col].values[0]:.1f}%" if len(row) else "—"

            def mc16_float(team, col):
                row = mc16[mc16["team"] == team]
                return float(row[col].values[0]) if len(row) else 0.0

            def pw16(t1, t2, col):
                return t1 if mc16_float(t1, col) >= mc16_float(t2, col) else t2

            R16_actual = [
                ("Morocco",      "Canada",      "R16_01"),
                ("France",       "Paraguay",    "R16_02"),
                ("USA",          "Belgium",     "R16_03"),
                ("Portugal",     "Spain",       "R16_04"),
                ("Norway",       "Brazil",      "R16_05"),
                ("Mexico",       "England",     "R16_06"),
                ("Switzerland",  "Colombia",    "R16_07"),
                ("Argentina",    "Egypt",       "R16_08"),
            ]

            QF_LABELS = {
                ("R16_01","R16_02"): "QF Match A",
                ("R16_03","R16_04"): "QF Match B",
                ("R16_05","R16_06"): "QF Match C",
                ("R16_07","R16_08"): "QF Match D",
            }

            r16w = {mid: pw16(h, a, "pct_reach_QF") for h, a, mid in R16_actual}
            QF_pred16 = [
                (r16w["R16_01"], r16w["R16_02"], "QF_01", "SF Match 1"),
                (r16w["R16_03"], r16w["R16_04"], "QF_02", "SF Match 2"),
                (r16w["R16_05"], r16w["R16_06"], "QF_03", "SF Match 3"),
                (r16w["R16_07"], r16w["R16_08"], "QF_04", "SF Match 4"),
            ]
            qfw16 = {mid: pw16(h, a, "pct_reach_SF") for h, a, mid, _ in QF_pred16}
            SF_pred16 = [
                (qfw16["QF_01"], qfw16["QF_02"], "SF_01", "Final Match 1"),
                (qfw16["QF_03"], qfw16["QF_04"], "SF_02", "Final Match 2"),
            ]
            sfw16 = {mid: pw16(h, a, "pct_reach_Final") for h, a, mid, _ in SF_pred16}

            def render_card16(col, home, away, mid, stat_col, stat_label):
                with col:
                    h_stat = mc16_val(home, stat_col); a_stat = mc16_val(away, stat_col)
                    h_win = mc16_val(home, "pct_win_title"); a_win = mc16_val(away, "pct_win_title")
                    st.markdown(f"""
                    <div style="background:white;border:1px solid #e2e8f0;border-radius:14px;padding:20px 24px;box-shadow:0 2px 8px rgba(13,27,42,.06)">
                        <div style="font-size:10px;font-weight:700;color:#94a3b8;margin-bottom:14px">{mid}</div>
                        <div style="display:flex;justify-content:space-between;align-items:center;gap:8px">
                            <div style="text-align:center;flex:1">
                                <div style="font-size:28px">{flag(home)}</div>
                                <div style="font-size:13px;font-weight:700;color:#0d1b2a;margin-top:4px">{esc(home)}</div>
                                <div style="font-size:11px;color:#94a3b8;margin-top:2px">{stat_label}: {h_stat} · Title: {h_win}</div>
                            </div>
                            <div style="font-size:16px;font-weight:900;color:#cbd5e1">VS</div>
                            <div style="text-align:center;flex:1">
                                <div style="font-size:28px">{flag(away)}</div>
                                <div style="font-size:13px;font-weight:700;color:#0d1b2a;margin-top:4px">{esc(away)}</div>
                                <div style="font-size:11px;color:#94a3b8;margin-top:2px">{stat_label}: {a_stat} · Title: {a_win}</div>
                            </div>
                        </div>
                    </div>""", unsafe_allow_html=True)

            def render_grid16(pairs, stat_col, stat_label, group_label_fn=None):
                for i in range(0, len(pairs), 2):
                    batch = pairs[i:i+2]
                    if group_label_fn:
                        _sp0, col_label, _sp3 = st.columns([0.5, 10, 0.5])
                        with col_label:
                            st.markdown(f'<div style="font-size:13px;font-weight:900;letter-spacing:1.5px;color:#f5c518;margin:36px 0 20px;text-transform:uppercase;border-left:3px solid #f5c518;padding-left:12px">{group_label_fn(i)} — Winner advances</div>', unsafe_allow_html=True)
                    _, c1, c2, _ = st.columns([0.5, 5, 5, 0.5], gap="medium")
                    render_card16(c1, batch[0][0], batch[0][1], batch[0][2], stat_col, stat_label)
                    if len(batch) > 1:
                        render_card16(c2, batch[1][0], batch[1][1], batch[1][2], stat_col, stat_label)

            sub_stages_r16 = ["R16 Matchups", "Predicted QF", "Predicted SF", "Predicted Final"]
            if "ko_sub_r16" not in st.session_state:
                st.session_state.ko_sub_r16 = 0
            sub_idx16 = st.session_state.ko_sub_r16

            dots_html16 = "".join([
                f'<div style="width:9px;height:9px;border-radius:50%;background:{"#f5c518" if i==sub_idx16 else "#cbd5e1"};margin:0 3px;display:inline-block"></div>'
                for i in range(len(sub_stages_r16))
            ])
            st.markdown("<div style='margin-top:20px'></div>", unsafe_allow_html=True)
            _, sa, sb, sc, _ = st.columns([2, 1, 6, 1, 2])
            with sa:
                if sub_idx16 > 0 and st.button("←", key="r16_sub_prev"):
                    st.session_state.ko_sub_r16 -= 1; st.rerun()
            with sb:
                st.markdown(f'<div style="text-align:center;padding-top:10px">{dots_html16}<span style="font-size:12px;color:#94a3b8;margin-left:10px">{sub_stages_r16[sub_idx16]}</span></div>', unsafe_allow_html=True)
            with sc:
                if sub_idx16 < len(sub_stages_r16)-1 and st.button("→", key="r16_sub_next"):
                    st.session_state.ko_sub_r16 += 1; st.rerun()

            sub_idx16 = st.session_state.ko_sub_r16

            if sub_idx16 == 0:
                for i in range(0, len(R16_actual), 2):
                    m1 = R16_actual[i]; m2 = R16_actual[i+1]
                    label = QF_LABELS.get((m1[2], m2[2]), "")
                    _sp0, col_label, _sp3 = st.columns([0.5, 10, 0.5], gap="small")
                    with col_label:
                        st.markdown(f'<div style="font-size:13px;font-weight:900;letter-spacing:1.5px;color:#f5c518;margin:36px 0 20px;text-transform:uppercase;border-left:3px solid #f5c518;padding-left:12px">{label} — Winner advances</div>', unsafe_allow_html=True)
                    _, c1, c2, _ = st.columns([0.5, 5, 5, 0.5], gap="medium")
                    render_card16(c1, m1[0], m1[1], m1[2], "pct_reach_QF", "QF")
                    render_card16(c2, m2[0], m2[1], m2[2], "pct_reach_QF", "QF")

            elif sub_idx16 == 1:
                qf_group_labels = ["QF Match A", "QF Match B", "QF Match C", "QF Match D"]
                render_grid16(QF_pred16, "pct_reach_SF", "SF", lambda i: qf_group_labels[i//2 * 2 // 2])

            elif sub_idx16 == 2:
                render_grid16(SF_pred16, "pct_reach_Final", "Final", lambda i: f"Final Match {i//2 + 1}")

            elif sub_idx16 == 3:
                fin_home16, fin_away16 = sfw16["SF_01"], sfw16["SF_02"]
                champion16 = pw16(fin_home16, fin_away16, "pct_win_title")
                _sp0, col_label, _sp3 = st.columns([0.5, 10, 0.5])
                with col_label:
                    st.markdown('<div style="font-size:13px;font-weight:900;letter-spacing:1.5px;color:#f5c518;margin:36px 0 20px;text-transform:uppercase;border-left:3px solid #f5c518;padding-left:12px">THE FINAL — Predicted Champion</div>', unsafe_allow_html=True)
                _, c1, c_mid, c2, _ = st.columns([0.5, 4, 2, 4, 0.5], gap="medium")
                render_card16(c1, fin_home16, fin_away16, "FINAL", "pct_win_title", "Title")
                with c_mid:
                    st.markdown(f"""
                    <div style="text-align:center;padding-top:40px">
                        <div style="font-size:11px;font-weight:800;letter-spacing:1px;color:#94a3b8;margin-bottom:8px">PREDICTED CHAMPION</div>
                        <div style="font-size:36px">{flag(champion16)}</div>
                        <div style="font-size:14px;font-weight:800;color:#f5c518;margin-top:6px">{esc(champion16)}</div>
                        <div style="font-size:12px;color:#94a3b8;margin-top:4px">{mc16_val(champion16, "pct_win_title")} chance</div>
                    </div>""", unsafe_allow_html=True)

    else:
        label_map = {"Quarter-Final": "Quarter-Final", "Semi-Final": "Semi-Final", "Final": "Final"}
        st.markdown(f"""
        <div style="text-align:center;padding:80px 40px">
            <div style="font-size:48px;margin-bottom:16px">⏳</div>
            <div style="font-size:22px;font-weight:900;color:#0d1b2a;margin-bottom:8px">{label_map[selected_stage]} — Coming Soon</div>
            <div style="font-size:14px;color:#94a3b8;max-width:480px;margin:0 auto;line-height:1.7">
                Simulation will be updated once real {label_map[selected_stage]} fixtures are confirmed.
                Check back after the previous round concludes.
            </div>
        </div>""", unsafe_allow_html=True)

    # ── Decide which MC dataset to use for table + analytics ─────────────────
    use_r16 = (selected_stage == "R16") and Path("data/processed/monte_carlo_r16.csv").exists()
    show_analytics = selected_stage in ("R32", "R16")
    active_mc = mc16 if use_r16 else mc
    stage_label = "R16" if use_r16 else "R32"

    if not show_analytics:
        st.markdown('<div style="margin-bottom:48px"></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # ── Monte Carlo Results Table ─────────────────────────────────────────────
    st.markdown(f"""
    <div style="margin-top:56px">
        <div class="sec-kicker">MONTE CARLO SIMULATION</div>
        <div class="sec-title">Tournament Win Probabilities</div>
        <div style="font-size:14px;color:#6b8dd6;line-height:1.7;margin-bottom:24px">
            Based on 10,000 simulated tournaments from the {stage_label} stage. Each team's probability of reaching each stage.
        </div>
    </div>
    """, unsafe_allow_html=True)

    if use_r16:
        display_cols = ["team", "pct_win_title", "pct_reach_Final", "pct_reach_SF", "pct_reach_QF"]
        col_labels   = {"team": "Team", "pct_win_title": "🏆 Win Title", "pct_reach_Final": "Final",
                        "pct_reach_SF": "Semi-Final", "pct_reach_QF": "Quarter-Final"}
        pct_cols = ["🏆 Win Title", "Final", "Semi-Final", "Quarter-Final"]
    else:
        display_cols = ["team", "pct_win_title", "pct_reach_Final", "pct_reach_SF", "pct_reach_QF", "pct_reach_R16"]
        col_labels   = {"team": "Team", "pct_win_title": "🏆 Win Title", "pct_reach_Final": "Final",
                        "pct_reach_SF": "Semi-Final", "pct_reach_QF": "Quarter-Final", "pct_reach_R16": "Round of 16"}
        pct_cols = ["🏆 Win Title", "Final", "Semi-Final", "Quarter-Final", "Round of 16"]

    table_df = active_mc[display_cols].copy().rename(columns=col_labels)
    table_df["Team"] = table_df["Team"].apply(lambda t: f"{FLAGS.get(t,'🏳')} {t}")
    for c in pct_cols:
        table_df[c] = table_df[c].apply(lambda x: f"{x}%")

    st.dataframe(table_df, use_container_width=True, hide_index=True)

    # ── Analytics ─────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="margin-top:80px;margin-bottom:32px">
        <div class="sec-kicker">ANALYTICS</div>
        <div class="sec-title">Visualising the Simulation</div>
    </div>
    """, unsafe_allow_html=True)

    # Chart 1: Top title probabilities
    n_teams = len(active_mc)
    top_n = active_mc.nlargest(min(10, n_teams), "pct_win_title").iloc[::-1]
    fig1 = go.Figure(go.Bar(
        x=top_n["pct_win_title"],
        y=[f"{FLAGS.get(t,'🏳')} {t}" for t in top_n["team"]],
        orientation="h",
        marker_color="#f5c518",
        text=[f"{v}%" for v in top_n["pct_win_title"]],
        textposition="outside",
    ))
    fig1.update_layout(
        title=f"Top {min(10, n_teams)} — Probability of Winning the World Cup ({stage_label} Simulation)",
        xaxis_title="Win Probability (%)",
        yaxis_title="",
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Inter, sans-serif", color="#0d1b2a"),
        margin=dict(l=20, r=60, t=50, b=20),
        height=400,
    )
    fig1.update_xaxes(showgrid=True, gridcolor="#f1f5f9")
    st.plotly_chart(fig1, use_container_width=True)
    st.markdown(f"""
    <div style="background:#f8fafc;border-left:3px solid #f5c518;border-radius:0 8px 8px 0;padding:18px 24px;margin-top:8px;margin-bottom:24px">
        <div style="font-size:12px;font-weight:800;color:#0d1b2a;margin-bottom:6px;letter-spacing:1px">HOW TO READ</div>
        <div style="font-size:14px;color:#374151;line-height:1.8">
            Each bar shows the percentage of 10,000 simulated tournaments that a team won outright, starting from the {stage_label}.
            A longer bar means greater model confidence in that team's title chances.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Chart 2: Elimination risk at current stage
    st.markdown("<div style='margin-top:48px'></div>", unsafe_allow_html=True)
    exit_col = "pct_exit_R16" if use_r16 else "pct_exit_R32"
    elim_label = "R16" if use_r16 else "R32"
    bottom = active_mc.nlargest(len(active_mc), exit_col).iloc[::-1]

    def elim_color(v):
        if v >= 65: return "#ef4444"
        if v >= 40: return "#f5c518"
        return "#22c55e"

    bar_colors = [elim_color(v) for v in bottom[exit_col]]

    fig2 = go.Figure(go.Bar(
        x=bottom[exit_col],
        y=[f"{FLAGS.get(t,'🏳')} {t}" for t in bottom["team"]],
        orientation="h",
        marker_color=bar_colors,
        text=[f"{v}%" for v in bottom[exit_col]],
        textposition="outside",
    ))
    fig2.update_layout(
        title=f"{elim_label} Elimination Risk — All {len(active_mc)} Teams",
        xaxis_title=f"% Eliminated in {elim_label} (across 10,000 simulations)",
        yaxis_title="",
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Inter, sans-serif", color="#0d1b2a"),
        margin=dict(l=20, r=80, t=50, b=20),
        height=max(400, len(active_mc) * 28),
    )
    fig2.update_xaxes(showgrid=True, gridcolor="#f1f5f9", range=[0, 105])
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown(f"""
    <div style="background:#f8fafc;border-left:3px solid #94a3b8;border-radius:0 8px 8px 0;padding:18px 24px;margin-top:8px;margin-bottom:16px">
        <div style="font-size:12px;font-weight:800;color:#0d1b2a;margin-bottom:6px;letter-spacing:1px">HOW TO READ</div>
        <div style="font-size:14px;color:#374151;line-height:1.8">
            <span style="color:#ef4444;font-weight:700">Red</span> = likely eliminated (65%+ chance) &nbsp;·&nbsp;
            <span style="color:#d97706;font-weight:700">Yellow</span> = genuinely contested &nbsp;·&nbsp;
            <span style="color:#16a34a;font-weight:700">Green</span> = expected to advance comfortably.<br><br>
            Each bar shows how often a team was knocked out in the {elim_label} across all simulations.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Chart 3: Exit distribution
    st.markdown("<div style='margin-top:56px'></div>", unsafe_allow_html=True)
    top_n2 = active_mc.nlargest(min(12, n_teams), "pct_win_title").iloc[::-1]
    if use_r16:
        stage_cols  = ["pct_exit_R16", "pct_exit_QF", "pct_Third", "pct_Fourth", "pct_Final", "pct_Winner"]
        stage_names = ["Out R16",      "Out QF",       "3rd Place", "4th Place",  "Runner-Up", "Winner"]
        colors_list = ["#cbd5e1",      "#94a3b8",      "#60a5fa",   "#3b82f6",    "#f5c518",   "#0d1b2a"]
    else:
        stage_cols  = ["pct_exit_R32", "pct_exit_R16", "pct_exit_QF", "pct_Third", "pct_Fourth", "pct_Final",  "pct_Winner"]
        stage_names = ["Out R32",      "Out R16",       "Out QF",      "3rd Place", "4th Place",  "Runner-Up",  "Winner"]
        colors_list = ["#e2e8f0",      "#cbd5e1",       "#94a3b8",     "#60a5fa",   "#3b82f6",    "#f5c518",    "#0d1b2a"]

    fig3 = go.Figure()
    for col, name, color in zip(stage_cols, stage_names, colors_list):
        if col in top_n2.columns:
            fig3.add_trace(go.Bar(
                name=name,
                y=[f"{FLAGS.get(t,'🏳')} {t}" for t in top_n2["team"]],
                x=top_n2[col],
                orientation="h",
                marker_color=color,
            ))

    fig3.update_layout(
        barmode="stack",
        title=f"Tournament Exit Distribution — Top {min(12, n_teams)} Teams (% of 10,000 simulations, from {stage_label})",
        xaxis_title="% of Simulations",
        yaxis_title="",
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Inter, sans-serif", color="#0d1b2a"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=20, r=20, t=80, b=20),
        height=480,
    )
    fig3.update_xaxes(showgrid=True, gridcolor="#f1f5f9")
    st.plotly_chart(fig3, use_container_width=True)
    st.markdown("""
    <div style="background:#f8fafc;border-left:3px solid #3b82f6;border-radius:0 8px 8px 0;padding:18px 24px;margin-top:8px;margin-bottom:24px">
        <div style="font-size:12px;font-weight:800;color:#0d1b2a;margin-bottom:6px;letter-spacing:1px">HOW TO READ</div>
        <div style="font-size:14px;color:#374151;line-height:1.8">
            Each bar adds up to 100% — it shows where a team typically <em>exits</em> the tournament across all simulations.
            A large dark segment (Winner) means the model often sees them lifting the trophy.
            A wide gold segment (Runner-Up) means they frequently reach the Final but don't always win.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Dark horse callout
    st.markdown("""
    <div style="margin-top:40px">
        <div class="sec-kicker">INSIGHT</div>
        <div class="sec-title">Dark Horses</div>
        <div style="font-size:14px;color:#6b8dd6;line-height:1.7;margin-bottom:24px">
            Teams with a high probability of reaching the Semi-Finals but a low probability of winning the title — strong contenders that could surprise.
        </div>
    </div>
    """, unsafe_allow_html=True)

    dark_horses = active_mc[(active_mc["pct_reach_SF"] >= 10) & (active_mc["pct_win_title"] <= 5)].sort_values("pct_reach_SF", ascending=False)
    dh_cols = st.columns(min(len(dark_horses), 4), gap="medium") if len(dark_horses) else None
    if dh_cols:
        for col, (_, row) in zip(dh_cols, dark_horses.iterrows()):
            with col:
                st.markdown(f"""
                <div style="background:white;border:1px solid #e2e8f0;border-radius:14px;
                            padding:20px;text-align:center;box-shadow:0 2px 8px rgba(13,27,42,.06)">
                    <div style="font-size:36px">{FLAGS.get(row['team'],'🏳')}</div>
                    <div style="font-size:14px;font-weight:800;color:#0d1b2a;margin:8px 0 4px">{esc(row['team'])}</div>
                    <div style="font-size:12px;color:#64748b">SF reach: <b style="color:#3b82f6">{row['pct_reach_SF']}%</b></div>
                    <div style="font-size:12px;color:#64748b">Win title: <b style="color:#f5c518">{row['pct_win_title']}%</b></div>
                </div>""", unsafe_allow_html=True)
    else:
        st.markdown('<div style="font-size:14px;color:#94a3b8">No dark horses identified from this stage.</div>', unsafe_allow_html=True)

    st.markdown('<div style="margin-bottom:48px"></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


def show_detail():
    should_scroll_top = st.session_state.pop("scroll_detail_top", False)

    if should_scroll_top:
        components.html("""
        <script>
        (function() {
          function goTop() {
            const d = window.parent.document;
            [window.parent, d.scrollingElement, d.documentElement, d.body,
             d.querySelector('[data-testid="stAppViewContainer"]'), d.querySelector('section.main')]
              .filter(Boolean).forEach((el) => {
                try { if (el === window.parent) el.scrollTo(0, 0); else el.scrollTop = 0; } catch(e) {}
              });
          }
          [0, 40, 120, 260, 520, 900, 1400].forEach((t) => setTimeout(goTop, t));
        })();
        </script>
        """, height=0)

    row  = fixtures[fixtures["id"] == st.session_state.match_id].iloc[0]
    pred = predictions.get(row["id"])
    hc   = tc(row["home"])
    ac   = tc(row["away"])
    score = f"{int(row['hs'])} - {int(row['as_'])}" if row["played"] else "VS"
    status_text = "Full Time" if row["played"] else "Upcoming"
    status_color = "#16a34a" if row["played"] else "#64748b"

    st.markdown("""
    <style>
    .block-container {
        padding-top: 0 !important;
    }
    .detail-hero {
        background-image: linear-gradient(rgba(10,22,40,.64), rgba(10,22,40,.78)), var(--hero-bg);
        background-size: cover;
        background-position: center 44%;
        min-height: 420px;
        height: 420px;
        margin-top: -170px;
        margin-left: -80px;
        margin-right: -80px;
        width: calc(100% + 160px);
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 28px 32px 30px;
    }
    .detail-kicker {
        color: #f5c518;
        font-size: 12px;
        font-weight: 900;
        letter-spacing: 3px;
        text-transform: uppercase;
        margin-bottom: 18px;
    }
    .detail-rule { width: 48px; height: 3px; background: #f5c518; margin: 0 auto 24px; }
    .scoreboard {
        display: grid;
        grid-template-columns: minmax(180px, 1fr) auto minmax(180px, 1fr);
        gap: 44px;
        align-items: center;
        max-width: 880px;
        margin: 0 auto;
    }
    .team-code-big { color: white; font-size: 58px; font-weight: 950; letter-spacing: 2px; line-height: 1; }
    .team-name-big { color: rgba(255,255,255,.82); font-size: 20px; font-weight: 750; margin-top: 12px; }
    .score-big { color: white; font-size: 52px; font-weight: 950; letter-spacing: 2px; white-space: nowrap; }
    .status-pill-detail {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        margin-top: 20px;
        padding: 7px 18px;
        border-radius: 999px;
        background: var(--status-color);
        color: white;
        font-size: 13px;
        font-weight: 850;
    }
    .hero-back-link {
        display: inline-flex;
        margin-top: 20px;
        border: 1.5px solid rgba(255,255,255,.58);
        color: white !important;
        font-size: 14px;
        font-weight: 800;
        padding: 11px 24px;
        border-radius: 9px;
        text-decoration: none !important;
        transition: .16s ease;
    }
    .hero-back-link:hover { background: rgba(255,255,255,.12); transform: translateY(-1px); }
    .detail-grid {
        display: grid;
        grid-template-columns: minmax(0, 1.1fr) minmax(320px, .9fr);
        gap: 24px;
        align-items: start;
        margin-top: 56px;
    }
    .detail-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 18px;
        padding: 26px;
        box-shadow: 0 14px 36px rgba(13,27,42,.08);
    }
    .detail-card-title { font-size: 25px; font-weight: 950; color: #0d1b2a; margin-bottom: 6px; }
    .detail-card-sub { color: #64748b; font-size: 14px; line-height: 1.6; margin-bottom: 24px; }
    .pbar-wrap { margin-bottom: 22px; }
    .pbar-label { display: flex; justify-content: space-between; align-items: center; gap: 16px; margin-bottom: 8px; }
    .pbar-name { font-size: 15px; font-weight: 850; color: #0d1b2a; }
    .pbar-pct { font-size: 26px; font-weight: 950; color: #0d1b2a; }
    .pbar-track { height: 34px; border-radius: 9px; background: #e8eef5; overflow: hidden; }
    .pbar-fill { height: 100%; border-radius: 9px; width: 0; transition: none; }
    .pbar-wrap.pbar-visible .pbar-fill { animation: grow 1.0s cubic-bezier(.25,1,.35,1) forwards; }
    .pbar-wrap:nth-child(1).pbar-visible .pbar-fill { animation-delay: 0.05s; }
    .pbar-wrap:nth-child(2).pbar-visible .pbar-fill { animation-delay: 0.2s; }
    .pbar-wrap:nth-child(3).pbar-visible .pbar-fill { animation-delay: 0.35s; }
    .pb-home { background: #f5c518; }
    .pb-draw { background: #0d1b2a; }
    .pb-away { background: #25466f; }
    @keyframes grow { to { width: var(--w); } }
    .verdict-card {
        margin-top: 22px;
        border-radius: 16px;
        padding: 22px;
        background: #f8fafc;
        border: 1px solid #e2e8f0;
    }
    .verdict-head { display: flex; align-items: center; gap: 14px; margin-bottom: 14px; }
    .verdict-icon {
        width: 42px;
        height: 42px;
        border-radius: 12px;
        display: grid;
        place-items: center;
        color: white;
        font-size: 20px;
        font-weight: 950;
    }
    .v-correct { background: #16a34a; }
    .v-wrong { background: #ef4444; }
    .v-pending { background: #64748b; }
    .verdict-title { font-size: 19px; font-weight: 950; }
    .verdict-facts { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin: 12px 0; }
    .verdict-fact { background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 12px; font-size: 13px; color: #64748b; }
    .verdict-fact b { display: block; color: #0d1b2a; font-size: 14px; margin-top: 3px; }
    .verdict-copy { color: #475569; line-height: 1.7; font-size: 14px; }
    .factor-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 16px;
        box-shadow: 0 8px 22px rgba(13,27,42,.06);
    }
    .factor-title { color: #0d1b2a; font-size: 13px; font-weight: 950; letter-spacing: 1.2px; text-transform: uppercase; margin-bottom: 14px; }
    .factor-copy { color: #475569; font-size: 14px; line-height: 1.65; }
    .rank-row { display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; gap: 12px; margin-bottom: 14px; }
    .rank-box { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 14px; padding: 14px; text-align: center; }
    .rank-num { color: #0d1b2a; font-size: 28px; font-weight: 950; }
    .rank-team { color: #64748b; font-size: 12px; font-weight: 750; }
    .form-line { display: grid; grid-template-columns: minmax(90px, 1fr) auto 56px; align-items: center; gap: 10px; margin: 10px 0; color: #0d1b2a; font-size: 13px; font-weight: 800; }
    .form-dots { display: flex; gap: 5px; }
    .form-dot { width: 23px; height: 23px; border-radius: 999px; display: grid; place-items: center; font-size: 10px; font-weight: 900; color: white; }
    .form-dot.W { background: #16a34a; } .form-dot.D { background: #f59e0b; } .form-dot.L { background: #ef4444; }
    .detail-bottom-back { margin: 32px 0 10px; }
    .detail-bottom-back div[data-testid="stButton"] > button {
        background: transparent !important;
        color: #0d1b2a !important;
        border: 2px solid #0d1b2a !important;
        border-radius: 10px !important;
        width: auto !important;
        padding: 0 22px !important;
        font-weight: 850 !important;
    }
    @media (max-width: 900px) {
        .scoreboard { grid-template-columns: 1fr; gap: 24px; }
        .team-code-big { font-size: 54px; }
        .score-big { font-size: 56px; }
        .detail-grid { grid-template-columns: 1fr; }
        .verdict-facts { grid-template-columns: 1fr; }
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="detail-hero" style="--hero-bg:{STADIUM_BG}; --status-color:{status_color}">
        <div>
            <div class="detail-kicker">Group {row["group"]} &bull; {esc(row["date"]).upper()}</div>
            <div class="detail-rule"></div>
            <div class="scoreboard">
                <div><div class="team-code-big">{hc}</div><div class="team-name-big">{esc(row["home"])}</div></div>
                <div class="score-big">{score}</div>
                <div><div class="team-code-big">{ac}</div><div class="team-name-big">{esc(row["away"])}</div></div>
            </div>
            <div class="status-pill-detail">&bull; {status_text}</div>
            <div><a target="_self" class="hero-back-link" href="?nav=Matches">&larr; All Predictions</a></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if pred is None:
        st.markdown('<div class="page-wrap">', unsafe_allow_html=True)
        st.error("Prediction unavailable because ranking data could not be matched for one of these teams.")
        st.markdown('</div>', unsafe_allow_html=True)
        render_footer()
    else:
        home, away = pred["home"], pred["away"]
        prob_rows = []
        for label, val, cls in [
            (f'<span style="font-size:11px;font-weight:850;color:#94a3b8;margin-right:6px">{hc}</span>{esc(home)} Win', pred["probs"][f"{home} win"], "pb-home"),
            ("Draw", pred["probs"]["Draw"], "pb-draw"),
            (f'<span style="font-size:11px;font-weight:850;color:#94a3b8;margin-right:6px">{ac}</span>{esc(away)} Win', pred["probs"][f"{away} win"], "pb-away"),
        ]:
            prob_rows.append(
            f'<div class="pbar-wrap">'
            f'<div class="pbar-label"><span class="pbar-name">{label}</span><span class="pbar-pct">{val:.0f}%</span></div>'
            f'<div class="pbar-track"><div class="pbar-fill {cls}" style="--w:{val}%"></div></div>'
            f'</div>'
        )
        prob_html = "".join(prob_rows)

        gap = abs(pred["rank_home"] - pred["rank_away"])
        leader = home if pred["rank_home"] < pred["rank_away"] else away
        rank_exp = (f"{leader} has a major {gap}-place ranking advantage." if gap >= 40 else
                    f"{leader} has a useful {gap}-place ranking edge." if gap >= 15 else
                    f"Only {gap} ranking places separate these teams, so ranking alone is not decisive.")

        h2h_total = pred["h2h_total"]
        if h2h_total == 0:
            h2h_exp = "No historical matchup was found, so the model treats head-to-head as neutral."
        elif pred["h2h_home"] > pred["h2h_away"]:
            h2h_exp = f"{home} leads the recent head-to-head: {pred['h2h_home']} wins, {pred['h2h_draw']} draws, {pred['h2h_away']} losses."
        elif pred["h2h_away"] > pred["h2h_home"]:
            h2h_exp = f"{away} leads the recent head-to-head: {pred['h2h_away']} wins, {pred['h2h_draw']} draws, {pred['h2h_home']} losses."
        else:
            h2h_exp = f"The head-to-head record is balanced with {pred['h2h_home']} wins each and {pred['h2h_draw']} draws."

        fg = abs(pred["form_home"] - pred["form_away"])
        fl = home if pred["form_home"] >= pred["form_away"] else away
        form_exp = (f"{fl} enters with a clear recent-form advantage." if fg >= 25 else
                    f"{fl} has the better form profile, but the edge is not overwhelming." if fg >= 10 else
                    "Recent form is balanced, so this feature does not strongly separate the teams.")

        if row["played"]:
            correct = is_correct(row, pred)
            icls = "v-correct" if correct else "v-wrong"
            icon = "&#10003;" if correct else "&#10005;"
            verdict = "Correct Prediction" if correct else "Incorrect Prediction"
            vcol = "#16a34a" if correct else "#ef4444"
            detail = (
                "The model's strongest signal aligned with the final result. Ranking, form, and historical signals carried useful information here."
                if correct else
                f"The model predicted {esc(pred['predicted'])}, but the match finished as {esc(actual_result(row))}. This is useful analysis: errors often expose draws, upsets, or missing context like lineups and in-game momentum."
            )
            verdict_html = f"""
            <div class="verdict-card">
                <div class="verdict-head"><div class="verdict-icon {icls}">{icon}</div><div class="verdict-title" style="color:{vcol}">{verdict}</div></div>
                <div class="verdict-facts">
                    <div class="verdict-fact">Actual result<b>{esc(actual_result(row))}</b></div>
                    <div class="verdict-fact">Model prediction<b>{esc(pred["predicted"])} &bull; {pred["confidence"]}%</b></div>
                </div>
                <div class="verdict-copy">{detail}</div>
            </div>
            """
        else:
            verdict_html = f"""
            <div class="verdict-card">
                <div class="verdict-head"><div class="verdict-icon v-pending">?</div><div class="verdict-title" style="color:#0d1b2a">Pre-Match Prediction</div></div>
                <div class="verdict-copy">The model currently favours <b>{esc(pred["predicted"])}</b> with {pred["confidence"]}% confidence. Once the match is played, this page can compare the prediction with the actual result.</div>
            </div>
            """

        st.markdown(f"""
        <div class="page-wrap">
            <div class="detail-grid">
                <div class="detail-card">
                    <div class="detail-card-title">Win Probability Breakdown</div>
                    <div class="detail-card-sub">The model converts ranking gap, recent form, head-to-head history, and World Cup tournament weight into three outcome probabilities.</div>
                    {prob_html}
                    <div class="verdict-section">{verdict_html}</div>
                </div>
                <div>
                    <div class="factor-card">
                        <div class="factor-title">FIFA Rankings</div>
                        <div class="rank-row">
                            <div class="rank-box"><div class="rank-num">#{pred["rank_home"]}</div><div class="rank-team">{esc(home)}</div></div>
                            <div class="rank-team" style="text-align:center;font-weight:950">VS</div>
                            <div class="rank-box"><div class="rank-num">#{pred["rank_away"]}</div><div class="rank-team">{esc(away)}</div></div>
                        </div>
                        <div class="factor-copy">{esc(rank_exp)}</div>
                    </div>
                    <div class="factor-card">
                        <div class="factor-title">Recent Form</div>
                        <div class="form-line"><b>{esc(home)}</b>{form_dots_html(pred["last_home"])}<span>{pred["form_home"]}%</span></div>
                        <div class="form-line"><b>{esc(away)}</b>{form_dots_html(pred["last_away"])}<span>{pred["form_away"]}%</span></div>
                        <div class="factor-copy">{esc(form_exp)}</div>
                    </div>
                    <div class="factor-card">
                        <div class="factor-title">Head-to-Head</div>
                        <div class="factor-copy">{esc(h2h_exp)}</div>
                    </div>
                    <div class="factor-card">
                        <div class="factor-title">Tournament Stakes</div>
                        <div style="font-size:21px;letter-spacing:2px;margin-bottom:6px;color:#f5c518">&#9733;&#9733;&#9733;&#9733;&#9733;</div>
                        <div class="factor-copy">World Cup matches carry the highest importance weight in this model, amplifying the impact of ranking, form, and head-to-head signals compared with friendlies.</div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        render_footer()

    components.html(f"""
    <script>
    (function() {{
      const parentDoc = window.parent.document;
      function scrollTopNow() {{
        const selectors = [
          '[data-testid="stMain"]',
          '[data-testid="stAppViewContainer"]',
          '[data-testid="stMainBlockContainer"]',
          'section.main',
          '.main'
        ];
        selectors.forEach((sel) => {{
          const el = parentDoc.querySelector(sel);
          if (el) el.scrollTop = 0;
        }});
        window.parent.scrollTo(0, 0);
        parentDoc.documentElement.scrollTop = 0;
        parentDoc.body.scrollTop = 0;
      }}
      [0, 50, 150, 350, 700, 1200].forEach((d) => setTimeout(scrollTopNow, d));
      const bars = Array.from(parentDoc.querySelectorAll('.pbar-wrap'));
      bars.forEach((bar) => bar.classList.remove('pbar-visible'));
      if ('IntersectionObserver' in window.parent) {{
        const observer = new window.parent.IntersectionObserver((entries) => {{
          entries.forEach((entry) => {{
            if (entry.isIntersecting) {{
              entry.target.classList.remove('pbar-visible');
              void entry.target.offsetWidth;
              entry.target.classList.add('pbar-visible');
              observer.unobserve(entry.target);
            }}
          }});
        }}, {{ threshold: 0.1, root: null }});
        bars.forEach((bar) => observer.observe(bar));
      }} else {{ bars.forEach((bar) => bar.classList.add('pbar-visible')); }}
    }})();
    </script>
    """, height=0)


# ── Router ────────────────────────────────────────────────────────────────────

if "page" not in st.session_state:
    st.session_state.page = "Home"
if "match_id" not in st.session_state:
    st.session_state.match_id = "A1"

# Handle hero button navigation via query params
_nav = st.query_params.get("nav")
if st.session_state.get("page") != "Detail" and _nav in ("Matches", "Tournament", "Home", "About", "Knockout"):
    st.session_state.page = _nav

page = st.session_state.page

if page == "Detail":
    show_navbar("Matches")
    show_detail()
else:
    show_navbar(page)

    if page == "Home":
        show_home()
    else:
        if page == "Matches":      show_matches()
        elif page == "Tournament": show_tournament()
        elif page == "Knockout":   show_knockout()
        elif page == "About":      show_about()
        render_footer()

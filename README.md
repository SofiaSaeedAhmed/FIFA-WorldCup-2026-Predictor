# FIFA World Cup 2026 Predictor

An end-to-end data science project that predicts match outcomes for the 2026 FIFA World Cup using an XGBoost multiclass classifier and Monte Carlo simulation, deployed as an interactive Streamlit web app.

---

## Live App

🌐 **[View the App →](https://fifa-2026worldcup-predictor.streamlit.app/)**

---

## Project Overview

This project builds a full machine learning pipeline — from raw data and exploratory analysis through to a fully deployed prediction app — as a portfolio piece demonstrating applied data science skills.

**What it does:**
- Predicts home win / draw / away win probabilities for every group stage fixture
- Shows real match results alongside model predictions
- Explains *why* the model predicted what it did (SHAP analysis)
- Tracks prediction accuracy as the tournament progresses
- Runs 10,000 Monte Carlo simulations through the knockout bracket to estimate each team's probability of reaching each stage and winning the title

---

## Model

**Algorithm:** XGBoost multiclass classifier (softmax output)  
**Training data:** 23,000+ international matches (2000–2026, including group stage results)  
**Test set:** 4,330 matches (2022–2026), time-based split  
**Group stage accuracy:** 57% overall · 71% on decisive matches (home/away win)

### Features

| Feature | Description |
|---|---|
| `rank_diff` | FIFA rankings gap between home and away team |
| `home_form` | Home team win rate across last 10 matches |
| `away_form` | Away team win rate across last 10 matches |
| `h2h` | Historical head-to-head win rate for home team |
| `weight` | Tournament importance score (World Cup = 5, friendly = 1) |

### SHAP Findings

- **`rank_diff` dominates** — strongest signal across all three outcome classes
- **Form is second tier** — adds signal beyond rankings, especially for decisive outcomes
- **`h2h` is real but noisy** — sparse for cross-confederation matchups, defaults to neutral
- **`weight` is weakest** — rank and form already capture team quality; competition type adds marginal signal
- **Draws are structurally hard** — no single strong predictor; all features contribute at low magnitude

---

## Knockout Stage — Monte Carlo Simulation

After the group stage, the model was retrained on the full dataset (23,000+ matches including all 72 group stage results) and used to power a Monte Carlo simulation of the knockout bracket.

**Why Monte Carlo?**  
A knockout bracket is path-dependent — who Argentina faces in the QF depends on who wins the other half. A single probability per match can't capture that. Running 10,000 full tournament simulations gives each team a probability distribution across all possible exit points.

**How it works:**
1. For every possible R32 pairing, the model predicts win probabilities (draw probability redistributed proportionally — no draws in knockout)
2. All 992 ordered team pairs are precomputed into a probability cache for speed
3. Each simulation runs the full bracket: R32 → R16 → QF → SF → 3rd place playoff → Final
4. Stage counts are aggregated across all 10,000 runs

**Top results:**

| Team | Title % | Final % | SF % | QF % | R16 % |
|---|---|---|---|---|---|
| Argentina | 32.2% | 57.4% | 73.1% | 85.2% | 96.3% |
| France | 23.8% | 45.6% | 64.2% | 79.1% | 91.1% |
| England | 7.5% | 19.3% | 38.4% | 61.2% | 85.7% |
| Colombia | 4.8% | 14.1% | 33.7% | 57.4% | 78.2% |

---

## App Pages

| Page | Description |
|---|---|
| **Home** | Hero, live recent results, model feature cards |
| **Matches** | Full group stage fixture list with scores and predictions |
| **Match Detail** | Per-match deep-dive: scoreboard, probability bars, SHAP-informed verdict |
| **Tournament** | Group standings table |
| **Knockout** | Monte Carlo bracket, stage-by-stage navigation, analytics charts |
| **About** | Methodology, feature engineering, SHAP analysis, Monte Carlo explanation, FAQ |

### Knockout Page — Analytics

- **Top 10 Title Probability** — horizontal bar chart of the model's tournament favourites
- **R32 Elimination Risk** — all 32 teams colour-coded: 🔴 likely out · 🟡 contested · 🟢 likely through
- **Tournament Exit Distribution** — stacked bar showing where each top-12 team typically exits across all simulations
- **Dark Horses** — teams with high SF reach but low title probability

---

## Tech Stack

| Layer | Tool |
|---|---|
| ML model | XGBoost, scikit-learn, SHAP |
| Simulation | Monte Carlo (NumPy, custom bracket engine) |
| Data processing | pandas, numpy |
| App framework | Streamlit |
| Visualisation | Plotly, matplotlib, seaborn |
| Deployment | Streamlit Cloud |

---

## Notebooks

| Notebook | Contents |
|---|---|
| `01_eda.ipynb` | Dataset exploration, result distributions, home advantage analysis |
| `02_model.ipynb` | Feature engineering, XGBoost training, confusion matrix, SHAP analysis |
| `03_predict.ipynb` | Applying the model to all 72 group stage fixtures, accuracy tracking |

---

## Running Locally

```bash
git clone https://github.com/SofiaSaeedAhmed/FIFA-WorldCup-Predictor.git
cd FIFA-WorldCup-Predictor
pip install -r requirements.txt
streamlit run app.py
```

---

## Author

**Sofia Saeed Ahmed**  
[![LinkedIn](https://img.shields.io/badge/LinkedIn-sofia--saeed--ahmed-0a66c2?style=flat&logo=linkedin)](https://www.linkedin.com/in/sofia-saeed-ahmed/)
[![GitHub](https://img.shields.io/badge/GitHub-SofiaSaeedAhmed-333?style=flat&logo=github)](https://github.com/SofiaSaeedAhmed)
[![Email](https://img.shields.io/badge/Email-sofiasaeed23@gmail.com-ea4335?style=flat&logo=gmail)](mailto:sofiasaeed23@gmail.com)

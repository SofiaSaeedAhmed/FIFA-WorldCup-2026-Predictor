# FIFA World Cup 2026 Predictor

An end-to-end data science project that predicts match outcomes for the 2026 FIFA World Cup group stage using an XGBoost multiclass classifier, deployed as an interactive Streamlit web app.

---

## Live App

🌐 **[View the App →](https://fifa-worldcup2026-predictor.streamlit.app/)**

---

## Project Overview

This project builds a machine learning pipeline — from raw data and exploratory analysis through to a fully deployed prediction app — as a portfolio piece demonstrating applied data science skills.

**What it does:**
- Predicts home win / draw / away win probabilities for every group stage fixture
- Shows real match results alongside model predictions
- Explains *why* the model predicted what it did (SHAP analysis)
- Tracks prediction accuracy as the tournament progresses

---

## Model

**Algorithm:** XGBoost multiclass classifier (softmax output)  
**Training data:** 23,000+ international matches (2000–2021)  
**Test set:** 4,330 matches (2022–2026), time-based split  
**Group stage accuracy:** 57% (34/60 matches correct)

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

## App Pages

| Page | Description |
|---|---|
| **Home** | Hero, live recent results, model feature cards |
| **Matches** | Full group stage fixture list with scores and predictions |
| **Match Detail** | Per-match deep-dive: scoreboard, probability bars, SHAP-informed verdict |
| **Tournament** | Group standings table |
| **About** | Methodology, feature engineering, SHAP analysis, performance stats, FAQ |

---

## Tech Stack

| Layer | Tool |
|---|---|
| ML model | XGBoost, scikit-learn, SHAP |
| Data processing | pandas, numpy |
| App framework | Streamlit |
| Visualisation | matplotlib, seaborn, plotly |
| Deployment | Streamlit Cloud |

---

## Project Structure

```
FIFA-WorldCup-Predictor/
├── app.py                        # Streamlit app (all pages)
├── requirements.txt
├── .streamlit/
│   └── config.toml               # Theme config (navy + gold)
├── data/
│   ├── raw/                      # FIFA rankings, historical results
│   └── processed/                # Cleaned match data, SHAP plots
├── models/
│   ├── xgb_final.pkl             # Trained XGBoost model
│   ├── features.pkl              # Feature column order
│   └── shap_explainer.pkl        # Pre-computed SHAP TreeExplainer
├── notebooks/
│   ├── 01_eda.ipynb              # Exploratory data analysis
│   ├── 02_model.ipynb            # Model training, evaluation, SHAP
│   └── 03_predict.ipynb          # Group stage predictions & accuracy
└── static/
    └── stadium.jpg
```

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

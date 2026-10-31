# TechKnights — PS-003: Federated Traffic-Flow Prediction with Communication-Cost Evaluation

**AIORI-3 Hackathon | Category: Smart Cities**
**Team:** Pratik Sen · Niladri Paul | **Mentor:** Partha Chakraborty

## Team Introduction Video
https://youtu.be/ah7S4L_xHno

## Demonstration Video
https://youtu.be/dTxm2Kkh8XU

## Live Project URL 
https://a3-ps003-tc242-njgc9m7hg2vlev2jlqq5dr.streamlit.app/

---

## What This Project Does

Traffic forecasting usually requires every road sensor to stream raw data to a central cloud — expensive in bandwidth and a privacy risk. This project instead uses **Federated Learning (FL)**: each simulated intersection trains a local model on its own data and sends only the model's weight updates to a server. The server averages those updates (FedAvg algorithm) to improve a global model — raw traffic data never leaves the client.

We built a simulator on the **METR-LA** dataset (Los Angeles highway sensors), trained on its first **60 sensors** (see `data_loader.py`'s `max_sensors` default) and partitioned across 3–5 virtual intersections, and evaluated how well this approach works compared to traditional centralised training — while also measuring the communication cost of each training round.

---

## What the Streamlit Dashboard Shows

Run it locally:
```bash
streamlit run src/app.py
```

The dashboard has four tabs and a live control bar.

### Control Bar (top)
| Control | What it does |
|---|---|
| **Number of Clients** (3 / 4 / 5) | How many virtual intersections (simulated edge devices) participate in federated training |
| **Training Rounds** (5–20) | How many times the server sends weights to clients, clients train locally, and weights come back |
| **Data Distribution** (IID / Non-IID) | IID = data shuffled evenly across clients; Non-IID = each client keeps its own sensors' chronological time block, which is more realistic and harder for the algorithm |
| **Random Seed** (42 / 7 / 123) | Controls how data is split and model is initialized — running all 3 seeds shows whether results are consistent or just lucky |
| **Training Speed** | How fast the rounds animate on screen — the underlying data is precomputed, so this is cosmetic |

### KPI Cards (below the bar)
| Card | What it means |
|---|---|
| **Federated MAE** | Mean Absolute Error of the global federated model — average prediction error in mph/speed units. Lower is better |
| **Federated RMSE** | Root Mean Square Error — penalises large prediction errors more. Also lower is better |
| **Communication Cost (Total)** | Cumulative KB transferred between clients and server across completed rounds. Formula: `2 × num_clients × model_params × 4 bytes` per round |
| **Training Round** | Current round / selected total, with a progress bar |

### Tab 1 — Training Progress
Line chart showing how **Federated MAE, Federated RMSE** (solid lines) and **Centralised MAE, Centralised RMSE** (dashed lines) change across rounds.

### Tab 2 — Round Details
Bar chart of KB per round (flat, because model size is fixed) plus a table of every round's exact numbers.

### Tab 3 — Federated vs Centralised
Side-by-side comparison table at the final round: accuracy gap (%), privacy advantage (no raw data shared), and bandwidth advantage (weights only vs full raw stream).

### Tab 4 — Evaluation Report
Summary of the experiment configuration, convergence status, and the federated-vs-centralised communication cost comparison. Includes download buttons for a **PDF report** and a **Word (.docx) report**, generated from the actual experiment results.

---

## Convergence Detection — What It Means and How It Works

**What "convergence round" means:** the round at which the federated model's error stops meaningfully changing — further training would be cost (more rounds, more communication) without benefit. Knowing this round lets you report the *real* communication cost needed to reach good accuracy, not just the cost of whatever round count you happened to pick.

**How it's detected:** a round is only reported as converged once Federated MAE has stayed essentially flat (round-over-round change under 0.05) for **3 consecutive rounds**. A single lucky small dip is not enough — the metric has to actually stabilise, not just happen to land close together once. If no such stable stretch occurs within the selected rounds, the dashboard reports **"Not Converged"** rather than guessing.


| | Converged | Avg round-to-round MAE swing |
|---|---|---|
| **IID** | 7 / 9 configs (across 3/4/5 clients) | 0.122 |
| **Non-IID** | 3 / 9 configs (across 3/4/5 clients) | 0.185 (**1.52× noisier**) |

**This is a genuine finding, not a software bug.** Non-IID partitions each client's data by chronological time block (rush hour vs. overnight, etc. — see `data_loader.py`'s `partition_samples_for_clients`), so each client's local model is trained on a different traffic regime. When the server averages these divergent local models every round, the global model swings more than it does under IID — this is the well-documented **client drift** phenomenon in federated learning, and it's exactly what PS-003 asks you to study. "Not Converged" on a Non-IID run is a correct, informative result, not a failure of the detector.

---

## Communication Cost — Methodology and Verified Results

Both federated and centralised costs are measured in real float32 bytes with the same accounting convention, so the comparison is apples-to-apples:

- **Federated** (per round): `2 × num_clients × model_params × 4 bytes` — the global-model download *and* local-update upload, for every client. This is the real, stored `comm_bytes` for that round. Verified from the actual data: **264,096 bytes (257.91 KB) per round at 3 clients**, which back-solves to a **42.98 KB** one-way model payload — constant across rounds and client counts, confirming the FedAvg implementation behaves exactly as the formula predicts.
- **Centralised** (one-time): shipping the raw **training-split** sensor data to a central server once. Using the real experiment parameters — `max_sensors=60` and `TRAIN_FRAC=0.7` from `data_loader.py`, against METR-LA's published 34,272 five-minute timesteps — this comes to **60 × 23,990 × 4 bytes ≈ 5.49 MB**. (An earlier estimate in this README assumed the full 207-sensor, full-length dataset and overstated this figure by roughly 5×; the number above reflects what this experiment actually trains on.)

### Verified Result (3 clients, 20 rounds)

| | Value |
|---|---|
| Federated total (cumulative, 20 rounds) | 5.04 MB |
| Centralised total (one-time) | 5.49 MB |
| **Reduction vs centralised** | **+8.3%** |

**Honest takeaway:** federated learning's bandwidth advantage here is real but modest at these client counts and round counts — not the "orders of magnitude" difference a naive full-dataset comparison would suggest. Past the break-even round, federated's repeated weight exchanges would actually cost *more* cumulatively than centralising the training data once. This is a more interesting and defensible result for a communication-cost study than a flat "FL always wins" claim, and it's the kind of round-count-vs-bandwidth tradeoff PS-003 explicitly asks you to analyse.

---

## Architecture

```
METR-LA dataset (h5 file, first 60 sensors)
        ↓
data_loader.py  →  Chronological split + sample-partition across clients
        ↓
agents.py       →  OrchestratorAgent dispatches to ClientAgent × N
        ↓
fedavg.py       →  client_update() + fed_avg() + evaluate_global()
        ↓
model.py        →  TrafficGRU (single-layer GRU, hidden=32, input=60 sensors)
        ↓
experiment_results_20rounds.json  →  build_db.py  →  experiments.db (SQLite)
        ↓
app.py (Streamlit)  →  load_experiment() reads SQLite, animates results
```

---

## Tech Stack

| Layer | Tool |
|---|---|
| Frontend | Streamlit + Plotly |
| Agent orchestration | `agents.py` — OrchestratorAgent / ClientAgent wrapping FedAvg |
| ML model | PyTorch GRU (`model.py`) |
| FL algorithm | Custom FedAvg (`fedavg.py`) |
| Dataset | METR-LA, first 60 sensors (LA highways, 5-min intervals) |
| Database | SQLite (`experiments.db`) |
| Report generation | ReportLab (PDF) + python-docx (Word) |
| Training environment | Google Colab (CPU/GPU) |
| Version control | GitHub |

---

## Repository Structure

```
TechKnights/
│
├── .venv/
│
├── A3-PS003-TC242/
│   │
│   ├── src/
│   │   ├── .streamlit/
│   │   │   └── config.toml
│   │   │
│   │   ├── fed_backend/
│   │   │   ├── __pycache__/
│   │   │   ├── agents.py
│   │   │   ├── data_loader.py
│   │   │   ├── fedavg.py
│   │   │   ├── INTEGRATION.md
│   │   │   └── model.py
│   │   │
│   │   ├── results/
│   │   │   ├── convergence_plot.png
│   │   │   ├── experiment_results_20rounds.json
│   │   │   ├── experiment_results_allclients.json
│   │   │   ├── experiment_results_full.json
│   │   │   ├── experiment_results.json
│   │   │   ├── experiments.db
│   │   │   ├── global_model_last.pt
│   │   │   └── global_model.pt
│   │   │
│   │   ├── __pycache__/
│   │   ├── app.py
│   │   ├── build_db.py
│   │   ├── intro_screen.py
│   │   ├── logo.png
│   │   ├── README.md
│   │   └── requirements.txt
│   │
│   ├── venv/
│   │   ├── etc/
│   │   ├── Include/
│   │   ├── Lib/
│   │   ├── Scripts/
│   │   ├── share/
│   │   └── pyvenv.cfg
│   │
│   ├── .gitignore
│   ├── A3-PS003-TC242.pdf
│   ├── Proposed-structure-hackathon.pdf
│   └── README.md
│
└── setup_and_run.bat
```

---

## Running Locally

```bash
# 1. Clone
git clone https://github.com/aiori-hackathon/A3-PS003-TC242.git

# 2. Install dependencies
pip install -r requirements.txt

# 3. Build the database (validates the JSON before writing)
python src/build_db.py

# 4. Run the dashboard
streamlit run src/app.py
```

---

## Experiment Coverage

All results are precomputed and stored in SQLite:

| Dimension | Values |
|---|---|
| Dataset | METR-LA (60 sensors) |
| Clients | 3, 4, 5 |
| Modes | IID, Non-IID |
| Seeds | 42, 7, 123 |
| Rounds per config | 20 |
| **Total configs** | **18** |
| **Total rounds stored** | **360** |

---

## Key References

- McMahan et al. (2017) — Communication-Efficient Learning of Deep Networks from Decentralized Data — https://proceedings.mlr.press/v54/mcmahan17a.html
- METR-LA dataset — Li et al. (2018), DCRNN — https://github.com/liyaguang/DCRNN

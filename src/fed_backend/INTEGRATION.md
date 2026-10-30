cat > INTEGRATION.md << 'EOF'
# Federated Training — Pseudocode Snippet

## Architecture (what was actually built)

METR-LA dataset → data_loader.py (partitions by sample, not sensor) →
agents.py (OrchestratorAgent/ClientAgent) → fedavg.py (FedAvg core) →
results saved as JSON → build_db.py → SQLite (experiments.db) →
app.py (Streamlit reads precomputed results, no live training)

## FedAvg Round (one iteration)
FUNCTION federated_round(global_weights, clients):
updates = []
FOR each client IN clients:
local_weights = train_locally(global_weights, client.data, epochs=2)
updates.append((local_weights, len(client.data)))
new_global = weighted_average(updates)
RETURN new_global

FUNCTION weighted_average(updates):
total_samples = SUM of n for (weights, n) in updates
avg = ZERO_WEIGHTS
FOR (weights, n) IN updates:
avg += weights × (n / total_samples)
RETURN avg

## Agent Orchestration Layer
OrchestratorAgent.run_round(global_state):
LOG “Dispatching to N client agents”
FOR each ClientAgent:
ClientAgent.run_local_round(global_state)
→ calls client_update() from fedavg.py
→ returns (updated_weights, num_samples, local_MAE)
Aggregate via fed_avg()
Evaluate on shared test set
LOG “Round complete — Fed MAE=X, comm=Y KB”
RETURN new_global_state, metrics

## Communication Cost Formula
bytes_per_round = 2 × num_clients × count_params(model) × 4
↑ upload+download ↑ float32 bytes
3 clients → 257 KB/round | 4 clients → 343 KB/round | 5 clients → 429 KB/round

## Data Flow (why results are precomputed, not live)

1. Colab runs the full sweep (18 configs × 20 rounds) via OrchestratorAgent
2. Results saved to `experiment_results_20rounds.json`, pushed to GitHub
3. `build_db.py` ingests JSON into SQLite (`experiments.db`)
4. `app.py` queries SQLite by (mode, seed, num_clients) and animates
   the stored rounds — no training happens inside Streamlit itself
EOF
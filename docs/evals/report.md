# RAG Evaluation Report

## Final Metrics vs Thresholds

| Metric | Acceptable Threshold | Good Threshold | Value | Threshold Evaluation |
|---|---|---|---|---|
| Total Count | N/A | N/A | 30 | N/A |
| Task Success Rate | 0.6 | 0.8 | 96.00% | Good |
| Groundedness | 0.8 | 0.95 | 96.67% | Good |
| Retrieval Hit Rate | 0.7 | 0.9 | 96.67% | Good |
| Cost / Query | 0.01 | 0.005 | $0.00027 | Good |
| Latency (p50) | N/A | N/A | 16.17s | N/A |
| Latency (p95) | 3.0 | 1.5 | 23.09s | Poor |

## Metrics by Path Level

| Path Level | Count | Task Success Rate | Groundedness | Retrieval Hit Rate |
|---|---|---|---|---|
| happy_path | 19 | 100.00% | 100.00% | 100.00% |
| hard_path | 7 | 97.14% | 100.00% | 100.00% |
| edge_path | 4 | 75.00% | 75.00% | 75.00% |

## Threshold Definitions
```json
{
  "task_success_rate": {
    "acceptable": 0.6,
    "good": 0.8
  },
  "groundedness": {
    "acceptable": 0.8,
    "good": 0.95
  },
  "retrieval_rate": {
    "acceptable": 0.7,
    "good": 0.9
  },
  "cost_per_query": {
    "acceptable": 0.01,
    "good": 0.005
  },
  "latency_p95": {
    "acceptable": 3.0,
    "good": 1.5
  }
}
```

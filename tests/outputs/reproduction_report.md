# Milestone 2.2 — Reproduction Report

**Overall: PASS**

| Criterion | Verdict |
|---|---|
| memory_core public API installs/imports/runs | PASS |
| Sources ingested via ingest() | PASS |
| Graph created (get_graph()) | PASS |
| Tier-1 relationships present | PASS |
| ≥ 1 correct CONTRADICTS edge (find_evidence()) | PASS |
| find_evidence() required zero LLM calls (structural, by construction) | PASS |
| recall() produced a natural-language answer | PASS |
| recall() attached an evidence_graph | PASS |
| No direct `import cognee` in this script | PASS |
| reset_project()/ingest()/find_evidence()/recall()/get_graph() all used | PASS |

## Graph

nodes=58, edges=156

### Relationship counts

- `ABOUT`: 4
- `BELONGS_TO_SET`: 48
- `CONTAINS`: 36
- `CONTRADICTS`: 1
- `DERIVED_FROM`: 2
- `EVALUATES`: 3
- `IS_A`: 33
- `IS_PART_OF`: 4
- `MADE_FROM`: 4
- `REFERENCES`: 2
- `SUPPORTS`: 3
- `USES`: 5
- `WRITTEN_BY`: 11

## CONTRADICTS evidence (find_evidence(), zero LLM calls)

- **rt-detr exceeds yolo11 in accuracy** --CONTRADICTS--> **yolo11 is the best object detector for our real-time use case.**

## recall() natural-language answer

{'dataset_id': UUID('81a1198f-dffb-5094-8242-2619e071fdb5'), 'dataset_name': 'memoryos_spike_repro', 'dataset_tenant_id': None, 'search_result': ['Based on the context, the papers that contradict our current hypothesis are not explicitly stated. However, we can infer potential contradictions from papers that discuss alternative approaches or findings. \n\nOne potential contradictory paper is "rt-detr" which is about a real-time detection transformer, implying a different approach to real-time object detection. Another potential contradictory paper is "latency-first detection in production" which discusses object detection under strict production latency budgets, potentially contradicting the findings of "yolo11 meets real-time budget". \n\nHowever, without more information on the current hypothesis, it\'s difficult to determine which papers directly contradict it.']}

## recall() raw_llm_context (transparency field)

```
{'dataset_id': UUID('81a1198f-dffb-5094-8242-2619e071fdb5'), 'dataset_name': 'memoryos_spike_repro', 'dataset_tenant_id': None, 'search_result': 'Nodes:\nNode: real-time object detection\n__node_content_start__\nTopic of the paper.\n__node_content_end__\n\nNode: topic\n__node_content_start__\ntopic\n__node_content_end__\n\nNode: real-time object detection\n__node_content_start__\nTopic of the paper\n__node_content_end__\n\nNode: real-time object detection\n__node_content_start__\nTopic of the paper\n__node_content_end__\n\nNode: yolo11: real-time detection at 2ms\n__node_content_start__\nA real-time object detector.\n__node_content_end__\n\nNode: detector choice for real-time pipeline\n__node_content_start__\nResearch note on detector choice for real-time pipeline\n__node_content_end__\n\nNode: researchnote\n__node_content_start__\nresearchnote\n__node_content_end__\n\nNode: map@0.5\n__node_content_start__\nA benchmark for object detection accuracy\n__node_content_end__\n\nNode: latency-first detection in production\n__node_content_start__\nA paper about object detection under strict production latency budgets.\n__node_content_end__\n\nNode: yolo11 meets real-time budget\n__node_content_start__\nKey finding of the paper.\n__node_content_end__\n\nNode: finding\n__node_content_start__\nfinding\n__node_content_end__\n\nNode: yolo11 real-time performance\n__node_content_start__\nYOLO11 achieves state-of-the-art real-time performance\n__node_content_end__\n\nNode: paper\n__node_content_start__\npaper\n__node_content_end__\n\nNode: yolo11: real-time detection at 2ms\n__node_content_start__\nPaper cited in the paper.\n__node_content_end__\n\nNode: benchmark\n__node_content_start__\nbenchmark\n__node_content_end__\n\nNode: map@0.5\n__node_content_start__\nA benchmark for object detection\n__node_content_end__\n\nNode: rt-detr\n__node_content_start__\nA real-time detection transformer paper\n__node_content_end__\n\n\nConnections:\nreal-time object detection --[is_a]--> topic
```
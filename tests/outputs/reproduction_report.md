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

nodes=81, edges=242

### Relationship counts

- `ABOUT`: 8
- `BELONGS_TO_SET`: 73
- `CONTAINS`: 55
- `CONTRADICTS`: 2
- `DERIVED_FROM`: 5
- `EVALUATES`: 3
- `IS_A`: 50
- `IS_PART_OF`: 7
- `MADE_FROM`: 7
- `REFERENCES`: 3
- `SUPPORTS`: 6
- `USES`: 10
- `WRITTEN_BY`: 13

## CONTRADICTS evidence (find_evidence(), zero LLM calls)

- **rt-detr: transformers beat yolo on accuracy** --CONTRADICTS--> **yolo11 is the best object detector for our real-time use case.**
- **rt-detr exceeds yolo11 in accuracy** --CONTRADICTS--> **yolo11 is the best object detector for real-time use cases**

## recall() natural-language answer

The paper "Latency-First Detection in Production" contradicts the current hypothesis. It references "YOLO11: Real-Time Detection at 2ms," suggesting that YOLO11 is a viable option for real-time object detection. This could be a contradiction if your hypothesis is against using YOLO11. 

The graph context provides more information about the relationships between different nodes, including papers, authors, and topics. For instance, "Latency-First Detection in Production" cites "YOLO11: Real-Time Detection at 2ms," and "YOLO11: Real-Time Detection at 2ms" is categorized as a paper related to real-time object detection. 

To better understand the contradiction, it would be helpful to know more about your current hypothesis. Is it related to the suitability of YOLO11 for real-time object detection or perhaps another aspect of object detection?

## recall() raw_llm_context (transparency field)

```
{'dataset_id': UUID('052f9982-ffcb-58d6-9f8b-11b423ce71d3'), 'dataset_name': 'memoryos_spike_repro', 'dataset_tenant_id': None, 'search_result': "Nodes:\nNode: internal research team\n__node_content_start__\nInternal Research Team\n__node_content_end__\n\nNode: author\n__node_content_start__\nauthor\n__node_content_end__\n\nNode: real-time object detection\n__node_content_start__\nTopic of real-time object detection\n__node_content_end__\n\nNode: topic\n__node_content_start__\ntopic\n__node_content_end__\n\nNode: real-time object detection\n__node_content_start__\nThe topic area of the research paper.\n__node_content_end__\n\nNode: real-time object detection\n__node_content_start__\nA topic related to object detection\n__node_content_end__\n\nNode: real-time object detection\n__node_content_start__\nThe topic of real-time object detection.\n__node_content_end__\n\nNode: real-time object detection\n__node_content_start__\nTopic related to object detection in real-time applications.\n__node_content_end__\n\nNode: transformer-based detectors\n__node_content_start__\nA type of object detection method\n__node_content_end__\n\nNode: method\n__node_content_start__\nmethod\n__node_content_end__\n\nNode: detector choice for real-time pipeline\n__node_content_start__\nResearch note on detector choice for real-time pipeline\n__node_content_end__\n\nNode: researchnote\n__node_content_start__\nresearchnote\n__node_content_end__\n\nNode: latency-first detection in production\n__node_content_start__\nA paper on object detection under strict production latency budgets\n__node_content_end__\n\nNode: yolo11: real-time detection at 2ms\n__node_content_start__\nA paper on YOLO11 object detection\n__node_content_end__\n\nNode: yolo11: real-time detection at 2ms\n__node_content_start__\nA research paper presenting YOLO11, a real-time object detector.\n__node_content_end__\n\nNode: paper\n__node_content_start__\npaper\n__node_content_end__\n\nNode: yolo11: real-time detection at 2ms\n__no
```
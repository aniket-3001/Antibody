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

nodes=56, edges=180

### Relationship counts

- `ABOUT`: 5
- `BELONGS_TO_SET`: 55
- `CONTAINS`: 43
- `CONTRADICTS`: 2
- `DERIVED_FROM`: 2
- `EVALUATES`: 4
- `IS_A`: 30
- `IS_PART_OF`: 4
- `MADE_FROM`: 4
- `REFERENCES`: 4
- `SUPPORTS`: 4
- `USES`: 14
- `WRITTEN_BY`: 9

## CONTRADICTS evidence (find_evidence(), zero LLM calls)

- **rt-detr: transformers beat yolo on accuracy** --CONTRADICTS--> **yolo11 is the best object detector for our real-time use case**
- **rt-detr exceeds yolo11 in accuracy** --CONTRADICTS--> **yolo11 is the best object detector for our real-time use case**

## recall() natural-language answer

{'dataset_id': UUID('9c318f8d-7279-5823-92b4-b13b506a12a6'), 'dataset_name': 'memoryos_spike_repro', 'dataset_tenant_id': None, 'search_result': ['**Paper that contradicts the hypothesis:**\n\n**RT-DETR: Transformers Beat YOLO on Accuracy** (Zhao & Lv, 2025)\n\n**Why:**\n- Current hypothesis: YOLO11 is the best detector for real-time use cases with strict latency budgets\n- RT-DETR contradicts this by achieving 2.1 mAP points higher accuracy than YOLO11 at comparable latency\n- Demonstrates a transformer-based detector can outperform YOLO11 without sacrificing real-time performance']}

## recall() raw_llm_context (transparency field)

```
{'dataset_id': UUID('9c318f8d-7279-5823-92b4-b13b506a12a6'), 'dataset_name': 'memoryos_spike_repro', 'dataset_tenant_id': None, 'search_result': 'Nodes:\nNode: rt-detr research note\n__node_content_start__\nResearch note documenting the RT-DETR work and its comparison to YOLO11 on real-time object detection.\n__node_content_end__\n\nNode: researchnote\n__node_content_start__\nresearchnote\n__node_content_end__\n\nNode: # Research Note — Detector Choice for... [real-time, research, note]\n__node_content_start__\n# Research Note — Detector Choice for Real-Time Pipeline\n\nAuthor: Internal Research Team\nDate: 2026-06-01\nTopic: real-time object detection\n\n## Current working hypothesis\n\nWe currently believe that **YOLO11 is the best object detector for our\nreal-time use case**. Our production constraint is a strict latency budget, and\nso far YOLO11 has been our default choice.\n\nThis note records that belief so we can track which evidence supports it and\nwhich evidence contradicts it as we read more papers and run more experiments.\n\nStatus: active.\n\n__node_content_end__\n\nNode: internal research team\n__node_content_start__\nInternal research team authoring the research note\n__node_content_end__\n\nNode: rt-detr: transformers beat yolo on accuracy\n__node_content_start__\nA 2025 paper by Yian Zhao and Wenyu Lv introducing RT-DETR, a real-time detection transformer that exceeds YOLO11 in accuracy on the COCO dataset.\n__node_content_end__\n\nNode: paper\n__node_content_start__\npaper\n__node_content_end__\n\nNode: latency-first detection in production\n__node_content_start__\nA 2025 paper by Maria Santos and Wei Chen studying object detection under strict production latency budgets, deploying and comparing detectors in a real-time serving environment.\n__node_content_end__\n\nNode: author\n__node_content_start__\nauthor\n__node_content_end__\n\nNode: text_ec7c879cbea3e36b6e4c68454cc64499\n__node_content_start__\nNone\n__node_content_end__\n\nNode: This chu
```
# Milestone 1 — Validation Report

**Overall: PASS ✅**

| Success criterion | Verdict | Evidence |
|---|---|---|
| Cognee installs correctly | ✅ PASS | cognee 1.2.2 imported and ran |
| Ontology is accepted | ✅ PASS | RDFLibOntologyResolver loaded research_ontology.owl without error |
| Papers are ingested | ✅ PASS | 58 nodes created from 4 sources |
| Graph is created | ✅ PASS | 58 nodes / 180 edges |
| Entity extraction works | ✅ PASS | node types: {'TextSummary': 4, 'NodeSet': 4, 'DocumentChunk': 4, 'TextDocument': 4, 'Entity': 32, 'EntityType': 10} |
| Tier-1 relationships exist | ✅ PASS | present: ['USES', 'REFERENCES', 'WRITTEN_BY', 'ABOUT'] |
| ≥ 1 correct CONTRADICTS edge | ✅ PASS | CONTRADICTS edges: 2; SUPPORTS: 5 |
| Graph traversal works | ✅ PASS | deterministic traversal found 2 evidence chain(s) |
| Natural-language recall works | ✅ PASS | answer length: 797 chars |
| Evidence subgraph is produced | ✅ PASS | subgraph: 3 nodes / 2 edges |

## Relationship type counts (normalized)

- `WRITTEN_BY`: 11
- `USES`: 11
- `EVALUATES`: 3
- `SUPPORTS`: 5
- `CONTRADICTS`: 2
- `DERIVED_FROM`: 2
- `REFERENCES`: 3
- `ABOUT`: 7
- (off-vocabulary): {'BELONGS_TO_SET': 54, 'MADE_FROM': 4, 'IS_PART_OF': 4, 'CONTAINS': 42, 'IS_A': 32}

## Contradiction evidence chains (deterministic)

- **Entity** “rt-detr: transformers beat yolo on accuracy”  —CONTRADICTS→  **Entity** “yolo11 is the best object detector for our real-time use case”
- **Entity** “rt-detr exceeds yolo11 by 2.1 map points”  —CONTRADICTS→  **Entity** “yolo11 is the best object detector for our real-time use case”

## Natural-language answer (recall)

{'dataset_id': UUID('8653b820-b363-5e10-b6cd-6704032566f7'), 'dataset_name': 'memoryos_spike', 'dataset_tenant_id': None, 'search_result': ['Based on the knowledge graph, **one paper contradicts the current hypothesis**:\n\n**RT-DETR: Transformers Beat YOLO on Accuracy** (Zhao and Lv, 2025)\n\n**Why it contradicts:**\n- The current hypothesis states that "YOLO11 is the best object detector for our real-time use case"\n- RT-DETR contradicts this by demonstrating that it exceeds YOLO11 in accuracy by 2.1 mAP points on the COCO dataset at comparable latency\n- This shows that a transformer-based detector (RT-DETR) achieves higher accuracy than YOLO11 without sacrificing real-time performance, directly challenging the claim that YOLO11 is the best choice for real-time detection scenarios']}

## Graph context behind the answer (only_context)

```
{'dataset_id': UUID('8653b820-b363-5e10-b6cd-6704032566f7'), 'dataset_name': 'memoryos_spike', 'dataset_tenant_id': None, 'search_result': 'Nodes:\nNode: # Research Note — Detector Choice for... [real-time, research, note]\n__node_content_start__\n# Research Note — Detector Choice for Real-Time Pipeline\n\nAuthor: Internal Research Team\nDate: 2026-06-01\nTopic: real-time object detection\n\n## Current working hypothesis\n\nWe currently believe that **YOLO11 is the best object detector for our\nreal-time use case**. Our production constraint is a strict latency budget, and\nso far YOLO11 has been our default choice.\n\nThis note records that belief so we can track which evidence supports it and\nwhich evidence contradicts it as we read more papers and run more experiments.\n\nStatus: active.\n\n__node_content_end__\n\nNode: internal research team\n__node_content_start__\nInternal research team authoring the research note\n__node_content_end__\n\nNode: rt-detr: transformers beat yolo on accuracy\n__node_content_start__\nA 2025 paper by Zhao and Lv introducing RT-DETR, a real-time detection transformer that exceeds YOLO11 in accuracy on COCO dataset.\n__node_content_end__\n\nNode: paper\n__node_content_start__\npaper\n__node_content_end__\n\nNode: latency-first detection in production\n__node_content_start__\nA 2025 paper by Maria Santos and Wei Chen that studies object detection under strict production latency budgets, deploying and comparing detectors in real-time serving environments.\n__node_content_end__\n\nNode: author\n__node_content_start__\nauthor\n__node_content_end__\n\nNode: text_ec7c879cbea3e36b6e4c68454cc64499\n__node_content_start__\nNone\n__node_content_end__\n\nNode: detector choice for real-time pipeline\n__node_content_start__\nResearch note documenting the hypothesis that YOLO11 is the best object detector for real-time use case, dated 2026-06-01\n__node_content_end__\n\nNode: researchnote\n__node_content_start__\nresearchnote\n__node_content_end__\n\nNode: # RT-DETR: Transformers Beat YOLO on Accuracy... [real-time, yolo11, rt-detr]\n__node_content_start__\n# RT-DETR: Transformers Beat YOLO on Accuracy\n\nAuthors: Yian Zhao, Wenyu Lv\nYear: 2025\nTopic: real-time object detection\n\n## Abstract\n\nWe introduce RT-DETR, a real-time detection transformer. We evaluate RT-DETR on\nthe COCO dataset using the mAP@0.5 benchmark and compare it directly against\nYOLO11. We reference the YOLO11 work ("YOLO11: Real-Time Detection at 2ms",\nJocher and Chaurasia, 2024) as our primary baseline.\n\n## Method\n\nRT-DETR uses a transformer-based architecture. We train and evaluate on the COCO\ndataset and report mAP@0.5.\n\n## Key finding\n\nOn COCO, RT-DETR exceeds YOLO11 in accuracy by 2.1 mAP points at a comparable\nlatency. This result directly contradicts the claim that YOLO11 is the best\ndetector for real-time use cases, because a transformer detector achieves higher\naccuracy without sacrificing real-time performance.\n\nReference: "YOLO11: Real-Time Detection at 2ms" (Jocher and Chaurasia, 2024).\n\n__node_content_end__\n\nNode: text_34e32ae8f334bfdf4df0400cf8702476\n__node_content_start__\nNone\n__node_content_end__\n\nNode: yolo11 is the best object detector for our real-time use case\n__node_content_start__\nThe active hypothesis that YOLO11 is the best detector for real-time object detection use cases.\n__node_content_end__\n\nNode: production latency comparison experiment\n__node_content_start__\nExperiment deploying and comparing detectors in a real-time serving environment, measuring end-to-end latency under a real-time budget.\n__node_content_end__\n\nNode: experiment\n__node_content_start__\nexperiment\n__node_content_end__\n\nNode: wei chen\n__node_content_start__\nCo-author of the Latency-First Detection in Production paper.\n__node_content_end__\n\nNode: rt-detr evaluation on coco\n__node_content_start__\nExperiment evaluating RT-DETR on COCO dataset using mAP@0.5 benchmark and comparing against YOLO11.\
```
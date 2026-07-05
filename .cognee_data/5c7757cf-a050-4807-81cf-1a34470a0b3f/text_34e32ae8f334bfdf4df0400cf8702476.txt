# RT-DETR: Transformers Beat YOLO on Accuracy

Authors: Yian Zhao, Wenyu Lv
Year: 2025
Topic: real-time object detection

## Abstract

We introduce RT-DETR, a real-time detection transformer. We evaluate RT-DETR on
the COCO dataset using the mAP@0.5 benchmark and compare it directly against
YOLO11. We reference the YOLO11 work ("YOLO11: Real-Time Detection at 2ms",
Jocher and Chaurasia, 2024) as our primary baseline.

## Method

RT-DETR uses a transformer-based architecture. We train and evaluate on the COCO
dataset and report mAP@0.5.

## Key finding

On COCO, RT-DETR exceeds YOLO11 in accuracy by 2.1 mAP points at a comparable
latency. This result directly contradicts the claim that YOLO11 is the best
detector for real-time use cases, because a transformer detector achieves higher
accuracy without sacrificing real-time performance.

Reference: "YOLO11: Real-Time Detection at 2ms" (Jocher and Chaurasia, 2024).

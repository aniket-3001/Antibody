# YOLO11: Real-Time Detection at 2ms

Authors: Glenn Jocher, Ayush Chaurasia
Year: 2024
Topic: real-time object detection

## Abstract

We present YOLO11, a real-time object detector. YOLO11 is derived from and
builds on the earlier YOLOv8 architecture. We evaluate YOLO11 on the COCO
dataset using the mAP@0.5 benchmark.

## Method and Evaluation

YOLO11 uses an anchor-free detection head and an improved backbone. The model is
trained and evaluated on the COCO dataset. Using the mAP@0.5 benchmark, we
measure both accuracy and latency.

## Key finding

On COCO, YOLO11 reaches 54.7 mAP while running at only 2ms latency per image.
This result shows that YOLO11 achieves state-of-the-art real-time performance,
supporting the view that YOLO11 is an excellent choice for real-time use cases.

YOLO11 is derived from YOLOv8, extending its architecture with a refined head.

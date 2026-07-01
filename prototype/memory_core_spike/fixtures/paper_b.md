# Latency-First Detection in Production

Authors: Maria Santos, Wei Chen
Year: 2025
Topic: real-time object detection

## Abstract

This paper studies object detection under strict production latency budgets. We
deploy and compare detectors in a real-time serving environment. We build on and
cite the YOLO11 work of Jocher and Chaurasia (2024) ("YOLO11: Real-Time
Detection at 2ms").

## Method

We use YOLO11 as our production detector and measure end-to-end latency under a
real-time budget. We compare against transformer-based detectors.

## Key finding

YOLO11's low latency met our real-time budget in production, whereas the
transformer-based detectors we tried did not fit the latency constraint. This
supports the conclusion that YOLO11 is the best detector for latency-critical,
real-time use cases.

Reference: see "YOLO11: Real-Time Detection at 2ms" (Jocher and Chaurasia, 2024).

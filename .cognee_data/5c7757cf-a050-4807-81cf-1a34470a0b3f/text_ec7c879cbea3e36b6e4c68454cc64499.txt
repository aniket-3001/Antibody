# Research Note — Detector Choice for Real-Time Pipeline

Author: Internal Research Team
Date: 2026-06-01
Topic: real-time object detection

## Current working hypothesis

We currently believe that **YOLO11 is the best object detector for our
real-time use case**. Our production constraint is a strict latency budget, and
so far YOLO11 has been our default choice.

This note records that belief so we can track which evidence supports it and
which evidence contradicts it as we read more papers and run more experiments.

Status: active.

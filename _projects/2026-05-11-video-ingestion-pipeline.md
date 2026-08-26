---
title: "Sports Video Ingestion and Preprocessing Pipeline"
collection: projects
period: "May 2026"
date: 2026-05-11
thumb: '/images/video-ingestion.gif'
codeurl: 'https://github.com/Bikudebug/sports-video-ingestion-pipeline'
summary: "Built a configurable pipeline that turns raw sports footage — a single file, a folder of matches, or an HLS playlist — into model-ready data: container metadata, frame sampling to a target FPS, resolution and colour-space normalisation, per-frame blur, brightness and contrast scoring, HSV-histogram shot-boundary detection, and JSON/JSONL manifests. YOLOv8n detection and MMPose multi-person pose estimation run on the exported frames as downstream checks that the output is actually usable."
highlights:
  - "Every exported frame is traceable: one JSONL record per frame carrying its timestamp, segment ID, quality scores and output paths, alongside quality, scene and validation reports — and a validation pass that re-checks each manifest path on disk before the data is handed downstream."
  - "Frames are separated before inference rather than after: weak frames are routed aside by the quality thresholds, and the rest are grouped by detected shot boundary, so a downstream model sees temporally coherent segments instead of one flat folder of images."
  - "Benchmarked across four sports clips — American football, basketball, rugby and beach volleyball — spanning <strong>23.98–59.94 FPS</strong>, 720p and 1080p, and <strong>285 to 16,340 frames</strong>, and documented the limits alongside the results: an HSV histogram difference finds visual cuts, not game-state changes, and handcrafted sharpness heuristics say nothing about occlusion, which is what actually breaks pose estimation."
tags:
  - Video Preprocessing
  - Shot-Boundary Detection
  - Frame Quality Filtering
  - FFmpeg
  - YOLOv8
  - MMPose
---

---
title: "Apollo Golf Swing Dashboard: Monocular Swing Analysis and Biomechanics"
collection: projects
org: "Internship, Apollo Sports"
period: "Aug 2026 – Present"
status: "Ongoing"
date: 2026-08-01
thumb: '/images/golf-swing-phases.gif'
summary: "Built an end-to-end monocular golf swing pipeline: a single face-on phone video is segmented with SAM2, tracked in 2D with RTMPose behind a kinematic plausibility filter, lifted to a 3D mesh with SAM-3D, then split into eight canonical swing phases with per-phase biomechanical metrics in real-world units scaled from player height."
highlights:
  - "Delivered a per-player web dashboard — 2D skeleton overlays, an interactive 3D mesh viewer, phase-by-phase metrics and a 0–100 swing score — served as static JSON from a batch GPU job on AWS."
  - "Validated the eight-phase detector against manual event annotation on <strong>14 swing clips</strong> and benchmarked competing 2D pose backbones on phase-boundary error and wrist-keypoint jitter."
tags:
  - SAM2
  - RTMPose
  - SAM-3D
  - Swing Phase Segmentation
  - Biomechanics
  - AWS
---

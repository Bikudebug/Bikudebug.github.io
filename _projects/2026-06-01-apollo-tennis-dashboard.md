---
title: "Apollo Tennis Dashboard: Monocular Stroke Biomechanics and 3D Mesh"
collection: projects
org: "Internship, Apollo Sports"
period: "Jun 2026 – Present"
status: "Ongoing"
date: 2026-06-01
thumb: '/images/tennis-strokes.gif'
summary: "Built a single-camera tennis pipeline that reads 133 body keypoints per frame behind a compulsory kinematic-plausibility filter, finds and classifies each stroke, splits the serve into four phases, and reports twelve biomechanical measurements in metres, degrees and milliseconds by scaling pixels with the player's real height — alongside a 3D body mesh the coach can orbit in the browser."
highlights:
  - "Shipped a per-player dashboard — synchronised video views, an orbitable 3D mesh, phase sheets, a radar chart and a 0–100 serve score — published as a static bundle behind CloudFront with Origin Access Control, so the storage bucket itself stays private."
  - "Stroke detection reaches <strong>88.2%</strong> against hand-labelled frames; the mesh payload was cut to <strong>2.1–2.9 MB per serve</strong> as gzipped int16 temporal deltas, so the 3D viewer loads over a phone connection."
  - "Established what one camera cannot recover: four arm configurations fit the same frame to within a pixel, so five rotation metrics are declared unavailable and three radar spokes are left visibly empty rather than filled with a number the system cannot defend."
tags:
  - Monocular Biomechanics
  - Pose Estimation
  - Stroke Segmentation
  - 3D Mesh Reconstruction
  - Sports Dashboard
  - AWS
---

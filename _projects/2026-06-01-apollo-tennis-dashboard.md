---
title: "Tennis Stroke Recognition and Motion Analytics Dashboard"
collection: projects
org: "Internship, Apollo Sports"
period: "Jun 2026 – Aug 2026"
date: 2026-06-01
thumb: '/images/tennis-strokes.png'
summary: "Built a single tennis-video pipeline that selects and tracks one player, extracts 2D pose frame by frame, classifies pose windows as forehand, backhand, serve or neutral, groups the frame predictions into stroke segments, and derives motion features and side-by-side explanation videos for qualitative review."
highlights:
  - "Merged two earlier codebases into one workflow covering both supervised training and evaluation on annotated matches and end-to-end inference on unseen video, with racket tracking and rendered prediction overlays."
  - "Benchmarked four classifiers (random forest, linear SVM, logistic regression, LSTM) on held-out matches; the selected random forest reached <strong>97.2% frame accuracy</strong>, with the accompanying report documenting the class-imbalance limits of the current split."
tags:
  - Player Tracking
  - Pose Estimation
  - Stroke Classification
  - Random Forest
  - LSTM
codeurl: 'https://github.com/Bikudebug/tennis_action_recognisation'
---

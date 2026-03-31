---
layout: archive
title: "Projects"
permalink: /projects/
author_profile: true
---

{% include base_path %}

You can also download my full [**CV here**]({{ base_path }}/files/Bikash_CV.pdf) for a complete overview of my work.

---

## Ongoing Projects

### Semantic 3D Human Pose Dictionary
**TIME@ARC Hub & Griffith University** | Oct 2025 – Present

Built a scalable pipeline to learn a unified 3D pose dictionary with semantic captions and compact embeddings. Normalized large-scale 3D skeleton data into a canonical representation and grouped poses using LSH-based clustering. Selected medoid poses as dictionary entries, enabling fast pose retrieval, action recognition, and motion understanding.

---

### Defect Analysis Model for Device Quality Inspection
**Walmart & IIT Madras** | Nov 2025 – Present

Working on a collaborative Walmart–IIT Madras project to develop a deep-learning–based defect analysis system that compares paired factory images to automatically identify subtle visual flaws and distinguish good devices from defective ones.

---

## Major Completed Projects

### UMPIRE: Unsupervised Temporal Action Localization via Deep Clustering
**IIT Gandhinagar** | Jul 2025 – Oct 2025

Developed a fully label-free TAL framework that learns spatio-temporal graph embeddings from 3D skeleton sequences using ASTGCN and transformer-based temporal pooling, followed by DBSCAN clustering with adaptive ε-estimation.

- Achieved state-of-the-art performance on the BABEL dataset (**51.53% mAP@IoU, 37.2 F1**), surpassing prior unsupervised and weakly supervised methods.

---

### Unsupervised Javelin Motion Phase Segmentation
**SRIP Internship, IIT Gandhinagar** | May 2025 – Jul 2025

Built an unsupervised ASTGCN + SOT framework to automatically detect biomechanical phase transitions in elite javelin throws, eliminating the need for manual labeling.

- Achieved state-of-the-art performance and released a dataset of **211 professionally annotated videos** covering key motion phases.

---

### Unsupervised Fine-Grained Action Localization in Sports Videos
**IIT Gandhinagar** | Aug 2024 – Jan 2025

Designed an unsupervised skeleton-based pipeline using ASTGCN pre-training and an Action Dynamics Metric (ADM) to detect fine-grained motion boundaries in untrimmed sports videos.

- Achieved **82.67% mAP** on the DSV Diving dataset — comparable to supervised methods — and demonstrated strong generalization to in-the-wild diving videos without labels.

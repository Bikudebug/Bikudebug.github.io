---
permalink: /
title: "About Me"
author_profile: true
redirect_from: 
  - /about/
  - /about.html
---

<div class="quote-roller" id="quoteRoller">
  <div class="quote-roller__line active">We are born in one day,</div>
  <div class="quote-roller__line">We die in one day,</div>
  <div class="quote-roller__line">We can change in one day,</div>
  <div class="quote-roller__line">We can fall in love in one day,</div>
  <div class="quote-roller__line">We can succeed in one day,</div>
  <div class="quote-roller__line">Anything can happen in just one day.</div>
  <div class="quote-roller__line highlight">Start with day one, and your 'one day' will come.</div>
</div>

<script>
  document.addEventListener("DOMContentLoaded", function() {
    const lines = document.querySelectorAll("#quoteRoller .quote-roller__line");
    if (lines.length === 0) return;
    let currentIndex = 0;
    
    setInterval(() => {
      const currentLine = lines[currentIndex];
      currentLine.classList.remove("active");
      currentLine.classList.add("exit");
      
      setTimeout(() => {
        currentLine.classList.remove("exit");
      }, 600);
      
      currentIndex = (currentIndex + 1) % lines.length;
      lines[currentIndex].classList.add("active");
    }, 3800);
  });
</script>

I hold a Master's degree in Physics from IIT Gandhinagar, where my academic journey gradually evolved into a deep engagement with computer vision through hands-on research and project-driven exploration. During my time there, I had the opportunity to work under the guidance of [Prof. Ravi Hegde](https://iitgn.ac.in/faculty/ee/fac-ravi), whose mentorship played a key role in shaping my research perspective and technical foundation.

My work focuses on pose-based action recognition, motion understanding, and graph neural networks for human activity analysis. I am particularly interested in building models that learn from minimal supervision and capture complex visual dynamics in human-centric and sports videos.

Currently, I am exploring multimodal learning, focusing on vision-language models for action captioning, large-scale dataset development for biomechanical analysis, and expanding my research into team sports analysis.

♨️I am actively looking for PhD positions where I can contribute and grow as a researcher in computer vision.

## Education

**Indian Institute of Technology, Gandhinagar** (July 2023 - May 2025)
* M.Sc. in Physics 

**Berhampur University, Berhampur** (June 2019 - July 2022)
* B.Sc. in Physics 


## Research Interests

* Unsupervised Temporal Video Segmentation
* Motion and Scene Understanding
* Multi-View & Multi-Person Pose Estimation
* Generative AI / VLM
* Sports Analytics
* Activity Recognition

## Patents

* **Motion-Driven Unsupervised Temporal Segmentation System for Video Data**, Inventors: Vipul Baghel, Ravi Sadanand Hegde, and Bikash Kumar Badatya, Indian Patent Application No: **202621045701**, Filed: April 2026, Applicant: IIT Gandhinagar.

## Hobbies

Watching anime/movies.

Playing football and cricket.

Photographic.

Travelling.

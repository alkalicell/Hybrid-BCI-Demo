# Hybrid-BCI: Integrating Motor Imagery (MI) and SSVEP for AI-Assisted Creativity

This repository contains the implementation of a Hybrid Brain-Computer Interface (BCI) system developed for my Master's Thesis at National Tsing Hua University. The system combines Motor Imagery (MI) and Steady-State Visual Evoked Potentials (SSVEP) to achieve high-dimensional control, specifically applied to an interactive AI image generation workflow.

For more technical details and research findings, please refer to [this slide](https://docs.google.com/presentation/d/1hijxKgEqudbu7nv5oV2CuZc83u1XkFZ9/edit?usp=sharing&ouid=117663849590765686800&rtpof=true&sd=true).


## Overview

Traditional BCIs often struggle with a limited number of control commands or high mental fatigue. This project implements a hybrid framework:

* **Motor Imagery (MI):** Utilizes a CNN-based classifier to recognize 4 classes of limb intentions (Left Hand, Right Hand, Feet, Tongue/Idle).
* **SSVEP:** Employs a Filter Bank Canonical Correlation Analysis (FBCCA) algorithm for robust flickering frequency detection (6Hz, 4.3Hz, 7.6Hz, 10Hz).
* **AI Integration:** The system translates neural intentions into control commands for a generative AI (Stable Diffusion) API, allowing users to select styles or trigger image generation using only brainwaves.

## System Architecture

The project is organized into three main phases:

### 1. Data Acquisition and Calibration
Guided experimental paradigms to collect labeled EEG data via Lab Streaming Layer (LSL).
* **MI_calibrate_5class.py**: A 5-class visual/auditory cue paradigm for multi-modal calibration.
* **SN_calibrate_2class.py**: Simplified calibration for rapid binary testing.

### 2. Signal Processing and Modeling
Advanced algorithms to extract features and classify intentions from raw EEG signals.
* **fbcca.py & filterbank.py**: Implementation of the FBCCA algorithm for high-speed SSVEP detection.
* **MI_CNN_model.py**: Deep learning architecture (Conv3D) for motor imagery classification.
* **P2_model.py**: Unified interface for real-time model inference and signal preprocessing.

### 3. Real-Time Application (Drawing Client)
A multi-threaded environment connecting the EEG stream to a GUI and AI services.
* **parallel.py**: The main entry point that runs the server and client concurrently using Python threading.
* **P2_draw_sever.py**: Backend processing of real-time LSL streams and command logging.
* **P2_draw_client_V2.py**: Pygame-based GUI for user interaction and feedback.
* **call_api.py**: Handles communication with the Generative AI server for image synthesis.

## Requirements

* **EEG Hardware:** OpenBCI or any LSL-compatible device.
* **Environment:** Python 3.8+
* **Key Libraries:** mne, pylsl, tensorflow, scipy, pygame, scikit-learn.

## Getting Started

1. **Calibration:** Run `MI_calibrate_5class.py` to collect training data for a specific user.
2. **Training:** Use `MI_CNN_model.py` or the provided Jupyter Notebooks (`MI_analysis.ipynb`) to train your classifier.
3. **Deployment:** Use `parallel.py` to launch the real-time inference server and the interactive drawing interface simultaneously.

## Thesis Citation
If you use this code for your research, please cite:

Cheng, Tsun-Shan (2024). A Hybrid Brain-computer Interface Combining Motor Imagery and Steady-state Visual Evoked Potentials. Master Thesis, Institute of Information Systems and Applications, National Tsing Hua University.

---
Copyright 2024 Tsun-Shan Cheng. Licensed under the MIT License.
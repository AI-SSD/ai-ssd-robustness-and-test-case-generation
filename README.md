# LLMs for Robustness Assessment & Test Case Generation

This repository contains code and resources for using Large Language Models (LLMs) to generate test cases and assess the robustness of software systems, with a special focus on the GNU C Library (glibc). The goal is to leverage the capabilities of LLMs to create diverse and challenging test scenarios that can help identify potential weaknesses in software applications.

## Repository Structure

- **c-unit-tests/** — Contains a fully automated pipeline for generating unit test cases for basic C functions using LLMs in a containerized environment. This directory serves as a simple starting point and introcution to the capabilities of LLMs in test case generation.
- **glibc-unit-tests/** — Focuses on generating test cases for the GNU C Library (glibc) using LLMs. This directory includes scripts and resources for creating test cases that target various functions within glibc in a fully automated and containerized manner.

## Baseline Methodology

This methodology serves as a baseline for generating test cases using LLMs. It was developed in the scope of the generation of simple unit tests for basic C functions, and it can be easily adapted to generate test cases for more complex software systems. The approach involves the following steps:


Auhor: *Francisca Camacho Pereira*
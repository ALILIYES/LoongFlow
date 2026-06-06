---
name: loongflow
description: "PEES (Plan-Execute-Evaluate-Summary) iterative problem-solving methodology with LoongFlow engine for complex tasks. Use when tasks need structured iteration, optimization, evolution, or when user mentions loongflow/PEES/PES."
---

# LoongFlow — PEES Iterative Problem Solving

Use this skill when the user wants to iteratively improve a solution — optimization, evolution, structured retries with learning, or any task that benefits from multiple rounds of refinement rather than a one-shot attempt.

## Step 1: Analyze and Advise

Before starting, analyze the task and advise the user on which mode to use. Present both options clearly:

**Native PEES (recommended for simple tasks):**
- Best for: single-file fixes, small features, bug fixes, focused improvements
- How it works: You run Plan-Execute-Evaluate-Summary iterations yourself within this conversation
- Pros: Fast, no setup, no external dependencies, transparent workspace with full history
- Cons: Limited to ~5 iterations, single-threaded, no population-based evolution

**LoongFlow Engine (recommended for complex tasks):**
- Best for: optimization problems, multi-file projects, tasks needing many iterations (50+), population-based evolution with diversity preservation
- How it works: Downloads the LoongFlow framework, creates a `general_agent` task, runs evolutionary optimization in the background, monitors via cron
- Pros: Powerful evolutionary engine with multi-island model, Boltzmann selection, MAP-Elites diversity, checkpointing, cost tracking
- Cons: Requires `ANTHROPIC_API_KEY` and `ANTHROPIC_BASE_URL`, setup time, runs as background process
- Source: https://github.com/baidu-baige/LoongFlow

**Ask the user which mode they prefer before proceeding.**

## Step 2: Follow the Mode Guide

Once the user chooses, read the corresponding reference file for detailed instructions:

- **Native PEES** → Read `references/native-pees.md` and follow it
- **LoongFlow Engine** → Read `references/engine-mode.md` and follow it

## Architecture Reference

LoongFlow supports three tiers for agent projects:

| Tier | Description | Best For |
|------|-------------|----------|
| **Simple** | ReAct loop + persistent memory | Chatbots, tool calling, format conversion |
| **Standard** | ReAct + self-evaluation + iterative improvement | Code review, document generation, data analysis |
| **Advanced** | PEES evolution loop with loongflow-memory | Math optimization, algorithm design, NP-hard problems |

### Complexity Assessment

```
Task Analysis
├── Only needs conversation + simple tools? → SIMPLE
├── Needs file operations or code generation?
│   ├── Has numerical evaluation metric? → ADVANCED
│   └── No numerical metric? → STANDARD
└── Needs iterative optimization?
    ├── Has clear scoring function? → ADVANCED
    └── Qualitative improvement? → STANDARD
```

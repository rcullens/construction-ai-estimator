# Construction AI Estimator – Architecture Overview

## Goal
Parse blueprints, project manuals/spec books, addenda, and technical data sheets.
Break down all job responsibilities by trade with maximum accuracy and zero silent misses.
Support real-world flexible/cross-trade assignments while keeping full auditability.

## Core Design Principles
- Grounded extraction (every claim has SourceReference with original text)
- Multi-agent debate + Completeness Auditor (Devil’s Advocate)
- Editable trade names + fully custom trades
- Explicit support for cross-trade scope moves (with required override_reason)
- Human review is a first-class, low-friction step

## High-Level Flow
Upload Package → Digital Twin / Perception → Semantic Graph → Multi-Agent Reasoning → Structured Trade Packages + Review List + Visualizations

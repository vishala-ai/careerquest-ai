# CareerQuest AI — Week 3 Submission Draft

**Project:** CareerQuest AI — High School to College Adventure

**One-liner:** CareerQuest helps fictional Grade 9–12 explorers discover interests, retrieve career pathways and build a grade-appropriate roadmap in a gamified Streamlit app, using bounded agent tool selection and saved progress. It requests student input when needed, blocks unsupported research on tool failure, and never submits applications.

## Overview and audience

The student starts with three short discovery quests. Each completion grants 20 XP; selections become editable exploration interests rather than fixed career predictions. The Career Worlds page supports source-linked offline research. The Roadmap page produces a grade-specific activity plan, saves versions and records reflections.

## Dataset

`data/knowledge.json`: seven short curated/illustrative career and college guidance records with source labels and links. Links to BLS, O*NET and Federal Student Aid are pointers for further checking, not proof of current live requirements. No college-specific deadlines, eligibility or acceptance probabilities are provided. Student profiles are fictional.

## Agent framework

**Goal:** Help a student complete a short interest → research → plan → reflection journey.

**Surface:** Streamlit web application.

**Control flow:** Student request → bounded action routing (optionally Ollama JSON-schema action selection) → selected tool → source-backed result or safe blocked response → persisted run. LangGraph route/execute/finish is used when installed.

**Tools:** read student profile; retrieve curated records; generate grade-specific exploration activities; save plan version; record reflection. Only controlled local writes to the fictional profile database.

**Memory:** SQLite profile interests, quest history, XP, reflections, roadmap versions, run records. LangGraph checkpoint persistence is not implemented in this prototype.

**Never do:** Submit applications, claim college eligibility or verified deadlines, diagnose aptitude, send messages, rank students, or collect real minors' personal information.

**Human boundary:** Students control interests and initiate plan updates; high-stakes college decisions require a student and trusted adult/counselor. There are no external write tools.

**Failure recovery:** When local model routing fails, use a logged bounded policy fallback. When evidence retrieval fails, return a blocked result with no invented citations or changes to the plan.

**Success measure (proposed, not measured):** A reviewer completes quests, inspects cited pathways, saves two roadmap versions and observes safe failure recovery in under five minutes.

## Technology

Python, Streamlit, SQLite, optional LangGraph, optional local Ollama; curated offline keyword retrieval. No embeddings/vector DB in the shipped MVP. No external API key.

## Vibe coding prompts and iterations

- Initial prompt: create a gamified Grades 9–12 profile with three discovery quests, XP, editable interests, career worlds and grade-specific roadmaps.
- Refinement: add a bounded tool-selecting agent, optional Ollama structured action selection, source metadata and explicit unavailable-source behavior.
- Refinement: persist profiles, quest events, reflections, plan versions and run traces in SQLite.
- Refinement: implement a LangGraph route → execute → finish workflow and simulate research failures.
- Validation: unit-test grade constraints, action routing, XP idempotency, persistent plans, reflection, source labeling and error handling.

## Test results and limitations

At package creation, 11 core tests passed. One optional LangGraph integration test was skipped because LangGraph was not installed in the build environment. Python compilation passed. Streamlit UI and live Ollama inference have NOT been executed here; these must be tested on the submission laptop. Do not present them as verified until checked.

This is a synthetic-only educational prototype, not a production service for minors. Authentication, parental consent, accessibility review, live college source verification, privacy compliance, and authenticated human approval are future work.

## Demo and code

Use `docs/DEMO_SCRIPT.md` for the <=5 minute walkthrough. Add a verified GitHub URL, screenshots, a link to the actual recorded video, and laptop smoke-test outcomes before submission. Do not invent those links or results.

**Student approval boundary:** The planning tool produces a proposal. Streamlit displays it, and only an explicit student click saves the new roadmap version. This is UI-level human confirmation, not a LangGraph interrupt or authenticated approval.

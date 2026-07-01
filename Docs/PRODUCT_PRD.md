# MemoryOS

## Product Requirements Document (PRD)

Version: 1.0

---

# Vision

MemoryOS is a persistent memory operating system for researchers.

Unlike traditional AI assistants that only answer questions from uploaded documents, MemoryOS continuously builds, maintains, and evolves a structured memory of an entire research project.

It remembers not only papers, but also experiments, hypotheses, datasets, benchmark results, notes, and research decisions.

Instead of asking:

> "What does Paper A say?"

Researchers can ask:

- Why do we currently believe this?
- Which experiments support this hypothesis?
- Which papers contradict our current direction?
- What research gaps still exist?

MemoryOS is powered by Cognee's hybrid graph-vector memory layer.

---

# Problem Statement

Research today is fragmented.

Researchers constantly switch between:

- PDFs
- Notes
- Experiment logs
- Git repositories
- Benchmark spreadsheets
- Presentations
- Documentation

While LLMs can summarize individual documents, they forget everything between sessions.

Researchers repeatedly:

- reread papers
- repeat failed experiments
- forget why decisions were made
- lose valuable context

There is no persistent memory.

---

# Solution

MemoryOS provides a persistent knowledge graph backed by Cognee.

Everything a researcher uploads becomes connected.

The system continuously remembers relationships between:

- Papers
- Authors
- Methods
- Datasets
- Experiments
- Hypotheses
- Results
- Notes

Instead of isolated documents, users build a living research memory.

---

# Core Philosophy

MemoryOS is NOT:

- a chatbot
- another RAG system
- another PDF summarizer

MemoryOS IS:

A persistent research memory layer that evolves alongside the researcher.

---

# Target Users

Primary:

- PhD Students
- Masters Students
- Research Engineers
- AI Researchers

Secondary:

- Startup R&D Teams
- Corporate Research Teams
- Professors

---

# Core Features

## 1. Research Memory Ingestion (remember)

Users can ingest:

- PDFs
- Markdown notes
- URLs
- Plain text
- Research summaries

MemoryOS stores them inside Cognee.

---

## 2. Knowledge Graph

Every uploaded object becomes part of a connected graph.

Example relationships:

Paper
→ Method

Paper
→ Dataset

Paper
→ Author

Experiment
→ Hypothesis

Experiment
→ Benchmark

Hypothesis
→ Supporting Paper

Hypothesis
→ Contradicting Paper

---

## 3. Intelligent Recall

Users ask natural language questions.

Examples:

Why are we currently using YOLO11?

Which experiments support this conclusion?

Which datasets have never been evaluated?

Which papers contradict each other?

Which methodology appears most often?

MemoryOS uses Cognee graph traversal instead of simple semantic search.

---

## 4. Memory Evolution (improve)

When new information is added:

- graph expands
- relationships are updated
- new links are created

Future versions may also support confidence updates and evolving hypotheses.

---

## 5. Forget

Researchers can delete:

- papers
- notes
- experiments

Cognee removes them from memory while preserving graph integrity.

---

# MVP Scope

The MVP should support:

✅ Upload PDF

✅ Upload Notes

✅ Store in Cognee

✅ View Graph

✅ Ask Questions

✅ Upload Additional Research

✅ Observe Graph Growth

✅ Delete Uploaded Research

Anything outside this scope is optional.

---

# User Journey

1. Create Project

↓

2. Upload Papers

↓

3. Upload Notes

↓

4. Cognee builds memory

↓

5. View graph

↓

6. Ask questions

↓

7. Upload new research

↓

8. Memory expands

↓

9. Delete obsolete documents

↓

10. Graph updates

---

# System Components

Frontend

- Next.js
- React
- TailwindCSS

Backend

- FastAPI

Memory Layer

- Cognee

LLM

- Claude

Graph Visualization

- Cytoscape.js

PDF Parsing

- PyMuPDF

---

# Cognee Integration

remember()

Used when:

- uploading papers
- adding notes
- importing URLs

---

recall()

Used whenever user asks questions.

Cognee decides between:

- semantic retrieval
- graph traversal

---

improve()

Triggered after new research is uploaded.

Graph grows naturally.

---

forget()

Deletes selected research memory.

---

# UI Pages

## Dashboard

Shows:

- Total Papers
- Experiments
- Notes
- Active Hypotheses

---

## Upload

Supports:

- PDF
- Markdown
- URLs

---

## Knowledge Graph

Interactive graph visualization.

Zoom

Pan

Click nodes

Inspect relationships

---

## Memory Chat

Natural language interface.

---

## Timeline

Chronological history of uploaded research.

---

# Graph Entities

Paper

Author

Method

Dataset

Experiment

Benchmark

Hypothesis

Finding

Research Note

Topic

---

# Graph Relationships

USES

SUPPORTS

CONTRADICTS

EVALUATES

WRITTEN_BY

IMPROVES

REFERENCES

DERIVED_FROM

---

# Success Metrics

The project is successful if a user can:

Upload several papers

↓

Generate a knowledge graph

↓

Ask graph-aware questions

↓

Upload another paper

↓

Observe graph expansion

↓

Delete one paper

↓

Observe graph update

---

# Demo Script

Step 1

Upload 3 research papers.

---

Step 2

Upload experiment notes.

---

Step 3

Display graph.

---

Step 4

Ask:

Why do we currently prefer YOLO11?

---

Step 5

Upload another paper.

Show graph expanding.

---

Step 6

Delete an obsolete paper.

Graph updates.

---

# Non-Goals

The MVP will NOT include:

Authentication

Collaboration

Cloud synchronization

Citation generation

Automatic experiment execution

Research paper generation

Autonomous agents

Multi-user support

These may be added in future versions.

---

# Engineering Principles

Keep the architecture modular.

Use Cognee as the single source of memory.

Keep business logic inside the backend.

Frontend should remain presentation-focused.

Avoid hardcoded workflows.

Design for future extensibility.

---

# Final Goal

MemoryOS should convincingly demonstrate that persistent AI memory enables a fundamentally better research workflow than traditional stateless LLMs.

The project should clearly showcase all four stages of Cognee's memory lifecycle:

remember()

recall()

improve()

forget()

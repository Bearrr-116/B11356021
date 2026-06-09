# Midterm Project: Domain-Driven RAG for Legal Retrieval and Case Assistance

## 1) Project Goal
This project designs a domain-driven RAG system for legal statute retrieval and case-summary assistance.
The system focuses on:
- high retrieval precision for statute-level queries,
- explainable answers with traceable evidence,
- hallucination control in legal advice-like prompts.

## 2) Domain Scope
- Jurisdiction: Taiwan law (configurable)
- Corpus type:
  - statutes and regulations,
  - official interpretations and guidance,
  - judgment summaries (non-sensitive, public data).
- Use case:
  - statute lookup,
  - relevant case-summary suggestion,
  - article-to-case cross-reference.

## 3) Repository Artifacts
- `architecture/architecture.md`: architecture explanation
- `architecture/architecture.mmd`: Mermaid architecture diagram
- `specs/system-spec.md`: data, SLO, and evaluation specs
- `adr/ADR-001-embedding-model.md`
- `adr/ADR-002-retrieval-strategy.md`
- `adr/ADR-003-hallucination-control.md`
- `whitepaper/whitepaper.md`: theory and innovation whitepaper

## 4) Baseline Tech Stack
- ETL: Python + OCR/Parser pipeline
- Embedding: BGE-M3 (baseline), OpenAI text-embedding-3-large (candidate)
- Vector DB: Qdrant
- Keyword index: OpenSearch (BM25)
- Reranker: `bge-reranker-large`
- LLM: configurable (closed or open-weight)
- Evaluation: RAGAS + TruLens

## 5) Deliverable Readiness
This repository is structured to satisfy the assignment requirements:
- architecture with clear vectorization boundary,
- measurable retrieval and latency targets,
- at least three ADRs in standard format,
- whitepaper discussing representation and hallucination challenges.

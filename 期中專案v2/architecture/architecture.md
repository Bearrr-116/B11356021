# 架構圖解：法條檢索與案例輔助（法規 + 判決摘要）RAG

- Status: Draft
- Owner: RAG Architect
- Last Updated: 2026-04-18

## 1. 圖示（Mermaid）

> 原始檔：`architecture.mmd`（可貼到支援 Mermaid 的渲染器或 VS Code 外掛預覽）

```mermaid
flowchart TD
    subgraph Sources["資料來源（非結構／半結構）"]
        S1[法規全文與歷史版本]
        S2[函釋／行政規則]
        S3[裁判書公開本]
    end

    subgraph ETL["Data Ingestion（ETL）— 向量化邊界之前"]
        E1[Ingest: 下載／落地 raw]
        E2[Clean: Markdown 化與噪音移除]
        E3[Structure: 條號／章節正規化]
        E4[Chunk: Markdown 邊界 + 法條結構 parent-child]
        E5[Annotate: metadata（Spec-003a）]
    end

    subgraph VecBoundary["向量化邊界（Vectorization Boundary）"]
        VB1[embedding_text 定稿]
        VB2[Embedding Model: BGE-M3]
    end

    subgraph Storage["Vector DB 拓撲 + Keyword Index"]
        QD[(Qdrant: legal_units_vectors)]
        OS[(OpenSearch: legal_units_bm25)]
        OBJ[(Object Store: 原文／大檔)]
    end

    subgraph Retrieval["檢索策略（Hybrid + Parent-Document）"]
        N[Query Normalizer（Spec-002）]
        H[Hybrid Recall: BM25 + Dense]
        F[RRF Fusion]
        P[Parent Reconstruction]
        R[Reranker 介入點: cross-encoder]
    end

    subgraph Gen["生成（Grounded）"]
        RULE[Rule Engine（Spec-005）]
        GO[Generation Orchestrator（Spec-007）]
        LLM[LLM（可關閉 Stage2）]
    end

    S1 --> E1
    S2 --> E1
    S3 --> E1
    E1 --> E2 --> E3 --> E4 --> E5 --> VB1 --> VB2
    E5 --> OBJ
    VB2 --> QD
    E5 --> OS

    U[User Query] --> N --> H
    H --> F --> P --> R --> RULE --> GO --> LLM --> OUT[Answer + Citations + Trace]

    QD <-->|dense| H
    OS <-->|bm25| H
    QD <-->|payload join| P
    OS <-->|id join| P
```

## 2. 架構敘述（對照作業要求）

### 2.1 Data Ingestion（ETL）

ETL 的輸入是「原始法源與裁判文本」，輸出是 **可索引、可版本治理** 的 `legal_units`（見 [Spec-003](../specs/spec-003-knowledge-etl.md) 與 [Spec-004](../specs/spec-004-legal-unit-schema.md)）。

六階段管線：

1. Ingest
2. Clean
3. Structure（條號／版本）
4. Chunk（**Markdown 標記 + 法條結構**）
5. Annotate（LLM/規則）
6. Validate（自動 + 抽樣人工）

### 2.2 Embedding Model 選擇

* **主模型**：BGE-M3（多語、長文本、可自建服務）
* **對照組**：OpenAI `text-embedding-3-large`（用於 offline A/B）

決策理由見 [ADR-001](../adr/ADR-001-embedding-model.md)。

### 2.3 Vector Database 拓撲

採 **單一向量 collection**（降低 join 複雜度），以 payload 區分資料類型：

* `collection`: `legal_units_vectors`
* **payload indexes**：`law_version_id`, `unit_type`, `is_active`, `legal_domain_tags`

同時以 OpenSearch 承載 BM25，形成「**向量近似 + 關鍵字精準**」雙索引拓撲（見 [Spec-008](../specs/spec-008-storage-schema.md)）。

### 2.4 檢索策略

* **Hybrid Search**：BM25（條號／法規名） + Dense（爭點語意）
* **Parent-Document Retrieval**：child 召回 → parent 還原完整法條語境／判決爭點框架

### 2.5 Reranking 介入點

**介入點**：Fusion 之後、LLM 之前。

原因：法律場景的初步召回常混入「語意相近但法源不對」的片段；cross-encoder 能以較高成本換取 **faithfulness** 與 **citation integrity**。

## 3. 模組邊界與 spec 對照

| 區塊 | Spec |
| --- | --- |
| 查詢正規化 | [Spec-002](../specs/spec-002-legal-query-normalizer.md) |
| ETL | [Spec-003](../specs/spec-003-knowledge-etl.md) |
| 單元 schema | [Spec-004](../specs/spec-004-legal-unit-schema.md) |
| 規則引擎 | [Spec-005](../specs/spec-005-jurisdiction-rule-engine.md) |
| 檢索 | [Spec-006](../specs/spec-006-retrieval-pipeline.md) |
| 生成 | [Spec-007](../specs/spec-007-generation-orchestrator.md) |
| 儲存 | [Spec-008](../specs/spec-008-storage-schema.md) |
| 評估 | [Spec-009](../specs/spec-009-evaluation-framework.md) |

## 4. 非功能需求（摘要）

* **P95 latency**：見 [Spec-001](../specs/spec-001-system-overview.md)
* **可追溯**：任何答案段落可映射到 `legal_unit_id`
* **可審計**：法規版本不覆寫，保留回放評估能力

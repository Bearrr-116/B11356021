# Spec-006: 檢索管線（Hybrid + Parent-Document + Rerank）

- Status: Draft
- Owner: RAG Engineer
- Last Updated: 2026-04-18

## 1. 目的

依據 [Spec-002](./spec-002-legal-query-normalizer.md) 的輸出，執行 **BM25 + Dense** 的混合召回，並透過 **parent 還原** 與 **cross-encoder rerank** 產生高品質證據清單，供 [Spec-005](./spec-005-jurisdiction-rule-engine.md) 與 [Spec-007](./spec-007-generation-orchestrator.md) 使用。

## 2. 責任

* 執行 BM25 與向量兩路召回
* 合併去重（以 `legal_unit_id` 為鍵）
* Parent-Document Reconstruction：對每個命中 child，拉取其 parent 文本（用於上下文與引用展示）
* Cross-encoder reranking
* 輸出 Top-K 證據與可審計之中間分數

## 3. 非責任

* 法域風險規則評分（屬 Spec-005）
* 答案敘事生成（屬 Spec-007）

## 4. 兩路召回

### 4.1 BM25（OpenSearch）

**目標**：精準命中條號、法規全稱、專有法學術語、裁判字別。

* Query 主要使用 `fts_query`
* 建議欄位：`citation_key^3`, `law_name^2`, `clean_markdown`, `legal_issue_tags`

### 4.2 Dense Vector（Qdrant）

**目標**：補足口語化描述、類案爭點、跨條文語意關聯。

* Query embedding 使用 `dense_query`
* 建議過濾：`is_active=true`，並可依 `legal_domain_tags` 做 pre-filter

## 5. 分數融合（Fusion）

採 **RRF（Reciprocal Rank Fusion）** 作為 MVP 預設（實作簡單、對量級不敏感）：

\[
\text{RRFScore}(d)=\sum_{r\in \{\text{bm25},\text{vec}\}}\frac{1}{k+\text{rank}_r(d)}
\]

* 常數 `k` 預設 60（可配置）
* 若某路無結果，該路不參與分母

**替代方案（Phase 2）**：加權 z-score 正規化後線性組合；需穩定 offline calibration。

## 6. Rerank 介入點（作業圖示必標）

**位置**：Fusion 後、進 LLM 前。

| 步驟 | 輸入量 | 輸出量 |
| --- | --- | --- |
| Fusion | 各路各取 top-30 | 合併後約 40–55 唯一文件 |
| Rerank | top-50（依 RRF） | top-8 |
| Parent expand | top-8 child | 每 child 附加 parent 文本（最多 8 段 parent） |

Reranker 模型：`bge-reranker-large`（可替換為同等 cross-encoder）。

## 7. Parent-Document Reconstruction

規則：

1. 若命中為 `STATUTE_CHILD`：附加其 `STATUTE_PARENT.clean_markdown` 全文（若過長，截斷至 `max_parent_chars`，但保留條號標題行）
2. 若命中為 `CASE_HOLDING`：附加 `CASE_PARENT` 的「案件識別＋爭點索引段」
3. parent 文本 **不直接進 reranker**（避免長文本稀释 cross-attention），但 **進入 LLM context** 作為解釋背景

## 8. 輸入契約

```json
{
  "fts_query": "string",
  "dense_query": "string",
  "query_embedding": [0.0],
  "filters": {
    "legal_domain_tags_any": ["CIVIL_LAW"],
    "authority_level_min": 70
  },
  "top_k": 8
}
```

## 9. 輸出契約

```json
{
  "evidence": [
    {
      "legal_unit_id": "lu_xxx",
      "unit_type": "STATUTE_CHILD",
      "rerank_score": 0.0,
      "rrf_score": 0.0,
      "bm25_rank": 3,
      "vec_rank": 10,
      "parent_unit_id": "lu_parent_yyy",
      "parent_excerpt": "string",
      "citation_key": "string"
    }
  ],
  "debug": {
    "ruleset_version": "retrieval@v1",
    "latency_ms": {"bm25": 0, "vec": 0, "fusion": 0, "rerank": 0}
  }
}
```

## 10. 性能要求

* 單次查詢（bm25+vec+fusion+rerank）P95 < 600ms @ Phase 0 seed 規模（見 Spec-011）
* Qdrant HNSW / OpenSearch 索引參數需記錄於 [Spec-008](./spec-008-storage-schema.md)

## 11. 驗收要求

* Golden Set 中 `context_recall@10` 達 [Spec-009](./spec-009-evaluation-framework.md) 門檻
* 任一 evidence 必須能回到 `legal_unit_id`

## 12. 依賴 ADR

* [ADR-002](../adr/ADR-002-retrieval-strategy.md)
* [ADR-003](../adr/ADR-003-hallucination-control.md)

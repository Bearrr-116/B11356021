# Spec-011: 里程碑與交付（Phase 0～3）

- Status: Draft
- Owner: Project Lead
- Last Updated: 2026-04-18

## 1. 目的

明訂分階段交付範圍與可驗證完成條件，對齊期中／期末可展示成果。

## 2. 階段總表

| 階段 | 目標 | 完成條件（摘要） |
| --- | --- | --- |
| Phase 0 | MVP 閉環（可 demo） | 種子資料可跑通 normalize→retrieve→rules→Stage1；`/health` 正常 |
| Phase 1 | 資料擴充 + 指標達標 | 法條覆蓋提升；Layer A～C 達門檻 |
| Phase 2 | 生成評估（RAGAS/TruLens） | Layer D 達門檻；失敗案例可回放 |
| Phase 3 | 進階研究功能 | GraphRAG 實驗分支（可選）、跨版本法規 diff 檢索 |

## 3. Phase 0：MVP 閉環

### 3.1 種子資料規模（評估 latency 基準）

| 資料類型 | 目標量級 |
| --- | --- |
| 法條 child units | 3k～10k |
| 判決摘要 units | 1k～5k |
| 函釋 units | 200～1k |

### 3.2 交付物

| 項目 | 說明 |
| --- | --- |
| 索引 | Qdrant + OpenSearch 可重建 |
| 規則集 | `legal_rules@v1` |
| 評估 | 至少 30 題可跑 Layer A～C 斷言 |
| API | `/health` + `/v1/legal/query`（Stage2 可關） |

### 3.3 完成條件

* `P95 retrieve <= 600ms`（見 Spec-001）
* `citation_integrity_rate >= 0.95`（在 30 題種子集上）

## 4. Phase 1：資料擴充 + 品質門檻

### 4.1 交付物

* Golden Set 擴充至 150 題（結構見 Spec-009）
* ETL idempotency 與版本治理上線

### 4.2 完成條件（建議）

| 指標 | 目標 |
| --- | --- |
| Layer A 條號 recall@query | ≥ 0.85 |
| Layer C Recall@10 | ≥ 0.86 |
| Layer C nDCG@10 | ≥ 0.82 |

## 5. Phase 2：RAGAS + TruLens

### 5.1 交付物

* `scripts/eval_ragas_legal.py`
* TruLens tracing dashboard（或最小化 log 匯出）

### 5.2 完成條件

| 指標 | 目標 |
| --- | --- |
| RAGAS faithfulness | ≥ 0.82 |
| RAGAS answer relevancy | ≥ 0.84 |
| TruLens groundedness（批次平均） | ≥ 0.70 |

## 6. Phase 3：GraphRAG（選配研究分支）

> 對應期中 ADR 可討論「為何不採 GraphRAG」或「何時採」。

**候選價值**：跨條文引用鏈、判決先例關係、法律概念 ontology。

**風險**：建置與維護成本高；資料品質不足時圖譜噪音會反向污染生成。

**完成條件（若選做）**：

* 定義 `LEGAL_RELATIONS` 邊類型（`cites_statute`, `follows_holding`, `distinguishes`）≥ 3 種
* Graph expansion 只允許在 `authority_level` 門檻之上走邊

## 7. 期中繳交對照表（給助教／老師）

| 作業要求 | 本 repo 對應 |
| --- | --- |
| Architecture | `docs/architecture/architecture.md` + `.mmd` |
| Specs | `docs/specs/*` |
| ADR >= 3 | `docs/adr/ADR-001..003.md` |
| Whitepaper | `docs/whitepaper/legal-rag-whitepaper.md` |

# Legal Statute & Case RAG — Specifications

本目錄為《法條檢索與案例輔助 RAG》可實作規格集。

- [白皮書](../whitepaper/legal-rag-whitepaper.md) 提供設計理念與論述深度
- [ADR-001](../adr/ADR-001-embedding-model.md)、[ADR-002](../adr/ADR-002-retrieval-strategy.md)、[ADR-003](../adr/ADR-003-hallucination-control.md) 記錄關鍵架構決策
- **本目錄** 提供每個模組的輸入、輸出、驗收條件與非功能需求

所有 spec 均為 **zh-Hant**；程式識別符、JSON 欄位名、collection 名稱保留英文。

---

## Spec 清單

| Spec | 標題 | 摘要 |
| --- | --- | --- |
| [Spec-001](./spec-001-system-overview.md) | 系統總覽 | 模組邊界、端到端資料流、非功能需求、安全邊界 |
| [Spec-002](./spec-002-legal-query-normalizer.md) | 法律查詢正規化器 | 自然語言 → 條號／法規名／案由／術語 alias 展開 |
| [Spec-003](./spec-003-knowledge-etl.md) | 知識 ETL | 六階段：抓取 → 清洗 → 切塊 → 標註 → 嵌入 → 驗證 |
| [Spec-003a](./spec-003a-etl-prompt-template.md) | ETL 標註 Prompt 模板 | LLM 協助標註之系統提示與輸出 schema |
| [Spec-004](./spec-004-legal-unit-schema.md) | 法律知識單元 Schema | `legal_unit` 型別、metadata 契約、parent-child 關聯 |
| [Spec-005](./spec-005-jurisdiction-rule-engine.md) | 法域規則引擎 | 管轄／時效／敏感議題之加扣分與補問模板 |
| [Spec-006](./spec-006-retrieval-pipeline.md) | 檢索管線 | Hybrid、parent 還原、rerank、輸出契約 |
| [Spec-007](./spec-007-generation-orchestrator.md) | 生成協調器 | Stage 1 Answer Contract + Stage 2 受限敘事 |
| [Spec-008](./spec-008-storage-schema.md) | 儲存 Schema | Qdrant payload、OpenSearch mapping、日誌表 |
| [Spec-009](./spec-009-evaluation-framework.md) | 評估框架 | 四層評估、RAGAS／TruLens、Golden Set |
| [Spec-010](./spec-010-api-contracts.md) | API 契約 | REST／MCP Tools 介面草案 |
| [Spec-011](./spec-011-roadmap-and-deliverables.md) | 里程碑與交付 | Phase 0～3 驗收條件 |

---

## 依賴關係

```
Spec-001
  ├── Spec-002（查詢正規化）
  ├── Spec-003（ETL）
  │    └── Spec-003a（Prompt）
  ├── Spec-004（Legal Unit Schema） ← Spec-003 輸出對齊
  ├── Spec-005（法域規則） ← 消費 Spec-002 輸出
  ├── Spec-006（檢索） ← 引用 Spec-004 / Spec-005 / Spec-008
  ├── Spec-007（生成） ← 消費 Spec-005 / Spec-006
  ├── Spec-008（Storage） ← 實現 Spec-004 的索引需求
  ├── Spec-009（評估） ← 覆蓋所有前層
  ├── Spec-010（API） ← 暴露 Spec-002 / 005 / 006 / 007
  └── Spec-011（Roadmap） ← 分階段交付 Spec-001～010
```

資料流為單向：**使用者問題 → 正規化 → 檢索 →（規則調整）→ 生成 → 評估**。

# ADR-003: Hallucination 控制（Reranker + Grounded Generation）

## Context
法律場景中的錯誤敘述風險高。若 LLM 參考到低相關片段，容易產生「看似合理但無法源依據」的答案，造成誤導。

## Decision
在生成前加入 **cross-encoder reranker**，並採用 **grounded prompt**：
- 僅允許根據檢索證據回答
- 回答必須附來源引用
- 無法證明時，明確拒答或保守回答

## Status
Accepted

## Consequences
- 正面影響：
  - 提升 faithfulness 與 groundedness
  - 降低高風險 hallucination
  - 增加答案可稽核性
- 負面影響：
  - 產生額外推理延遲（約 150-300ms）
  - prompt 設計與評估流程更複雜

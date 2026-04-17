# ADR-002: 檢索策略選擇（Hybrid + Parent-Document）

## Context
法律問題常同時包含：
- 精準法條定位需求（條號、法規名稱）
- 事實敘述語意比對需求（與過往判決理由相似）

若只做 pure vector，條號命中率不穩；若只做 keyword，語意召回不足。

## Decision
採用 **Hybrid Retrieval（BM25 + Dense）**，並加入 **Parent-Document Retrieval**。

## Status
Accepted

## Consequences
- 正面影響：
  - 條號與術語可由 BM25 穩定命中
  - 事實相似性可由 dense retrieval 補強
  - parent 還原可提升回答可解釋性與上下文完整度
- 負面影響：
  - 需要維護兩套索引與融合策略
  - 系統複雜度與運維成本上升

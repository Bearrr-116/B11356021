# ADR-001: Embedding Model 選擇（BGE-M3 vs text-embedding-3-large）

## Context
法律檢索同時需要：
- 條號與關鍵字精準對位（例如「民法第184條」）
- 長句法律語意對齊（事實描述與爭點敘述）
- 中文法律文本與少量英文術語混用處理能力

需在效果、成本與可部署性之間取得平衡。

## Decision
主 embedding 採用 **BGE-M3**，保留 `text-embedding-3-large` 作為 A/B 測試候選模型。

## Status
Accepted

## Consequences
- 正面影響：
  - 可自建推論服務，單位成本較低
  - 對多語與長文本檢索表現穩定
  - 適合與 reranker 搭配形成本地可控 pipeline
- 負面影響：
  - 需承擔模型服務維運成本
  - 模型更新與漂移監控由團隊自行負責

# 架構圖解：法條檢索與案例輔助 RAG

## 1. 系統定位
本系統用於法律知識輔助，不提供最終法律意見。主要任務是將使用者問題轉換成可檢索訊號，回傳「法條依據 + 判決摘要」的可解釋答案。

## 2. Data Ingestion (ETL)
- 來源資料：
  - 法規資料庫公開法條與子法
  - 判決書公開資料（先摘要化）
  - 主管機關函釋、裁判要旨彙編
- ETL 流程：
  1. 解析原始格式（PDF/HTML/Word）
  2. 條號與章節標準化（例如：第 184 條）
  3. 去除噪音與重複版本
  4. 補齊 metadata（法規名稱、修法日期、法院層級、案由）

## 3. 非結構化到向量化的邊界
- 邊界定義：`Chunking` 完成後，資料由文字片段轉為 embedding。
- 邊界前：清洗、切分、法條結構化、metadata 生成。
- 邊界後：向量索引、向量召回、向量融合排序。

## 4. Embedding 與向量資料庫拓撲
- Embedding 模型：BGE-M3（基準）
- 向量資料庫：Qdrant
- 拓撲設計：
  - `collection_legal_chunks`：條文/判決片段
  - `collection_parent_docs`：章節級 parent document（供解釋回溯）
- 額外索引：OpenSearch BM25（供關鍵字精準命中）

## 5. 檢索策略
- 採用 `Hybrid Search`：
  - Dense retrieval 處理語義近似
  - BM25 處理法條關鍵字、條號、專有法學術語
- 採用 `Parent-Document Retrieval`：
  - 先用 child chunk 高召回
  - 再回溯 parent 提供完整上下文

## 6. Reranking 介入點
- 介入位置：初步召回之後、LLM 生成之前。
- 流程：
  1. Hybrid 召回 top-50
  2. cross-encoder reranker 重排
  3. 保留 top-8 給 LLM
- 目的：提高最終證據片段相關性，降低幻覺風險。

## 7. 輸出格式與可解釋性
- 回答主體：精簡法律說明（非法律意見）
- 證據欄位：
  - 引用法條（法規名 + 條號）
  - 引用判決摘要（法院 + 年度 + 案由）
  - 信心分數與檢索覆蓋率

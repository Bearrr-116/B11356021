# 系統規格說明書（Specs）

## 1. 資料規格

### 1.1 資料來源
- 法條與子法（官方法規資料）
- 判決摘要（由公開判決書抽取）
- 函釋與主管機關解釋資料

### 1.2 文件結構與 metadata
- 基本欄位：
  - `doc_id`
  - `source_type`（statute / case_summary / interpretation）
  - `law_name`
  - `article_no`
  - `court_level`
  - `case_type`
  - `effective_date`
  - `updated_at`

### 1.3 Chunking Strategy
- 主策略：Markdown 標記切分（章節與條號為主）
- 輔策略：語義切分（長段落二次切分）
- 參數：
  - chunk size: 300-450 tokens
  - overlap: 50 tokens
  - parent-child 雙層切分：
    - parent：法條章節/判決爭點段
    - child：可檢索最小語義片段

## 2. 檢索與生成規格

### 2.1 檢索策略
- Hybrid Retrieval（BM25 + Dense）
- Parent-Document Reconstruction
- Cross-encoder reranking（top-50 -> top-8）

### 2.2 生成規格
- LLM 僅可根據檢索證據回答
- 必須輸出引用來源：
  - 法規名稱 + 條號
  - 判決摘要識別資訊（法院/年度/案由）
- 若證據不足，必須回覆「資訊不足，建議補充問題」而非推測。

## 3. 性能指標（SLO）
- API P95 Latency <= 2.0 秒（含檢索與重排，不含前端渲染）
- 檢索指標：
  - Recall@10 >= 0.86
  - Precision@5 >= 0.80
  - nDCG@10 >= 0.82
- 回答可追溯率（有至少 1 筆有效引用）>= 0.95

## 4. 評估機制

### 4.1 測試資料集
- 共 150 題 legal QA
- 題型比例：
  - 法條定位查詢 45%
  - 案例比對查詢 35%
  - 多法條綜合推理 20%

### 4.2 RAGAS 指標門檻
- Faithfulness >= 0.82
- Answer Relevancy >= 0.84
- Context Precision >= 0.80
- Context Recall >= 0.84

### 4.3 TruLens 評估
- Groundedness
- Retrieval relevance
- Answer relevance
- 低 groundedness 回答進行人工抽檢

## 5. 安全與合規
- 不處理當事人個資，判決資料先做去識別化
- 回答加註免責聲明：本系統為法律資訊輔助，非正式法律意見
- 高風險問題（刑責、時效、程序利益）若信心低，觸發保守回覆模板

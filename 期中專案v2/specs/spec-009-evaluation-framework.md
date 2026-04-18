# Spec-009: 評估框架（多層 + RAGAS + TruLens）

- Status: Draft
- Owner: QA Engineer
- Last Updated: 2026-04-18

## 1. 目的

建立可回放、可比較、可持續監控的評估機制，覆蓋 **查詢正規化 → 規則 → 檢索 → 生成** 全鏈路，並整合 **RAGAS** 與 **TruLens** 作為生成層主評估工具。

## 2. 四層評估（對齊課程要求）

| 層 | 目標 | 對應 Spec | 主要指標 |
| --- | --- | --- | --- |
| A | 查詢正規化正確性 | Spec-002 | 條號 hint 精確率／召回率；別名解析準確率 |
| B | 法域規則觸發一致性 | Spec-005 | 規則觸發 precision；`generation_mode` 合理性 |
| C | 檢索品質 | Spec-006 | Recall@K、nDCG@K、MRR；法條命中率 |
| D | 生成品質 | Spec-007 | RAGAS + TruLens；法律幻覺率 |

## 3. Golden Set（期中建議規模）

### 3.1 資料欄位（每一題）

* `qid`
* `raw_query`
* `gold_statute_citations`：允許多條（法規名＋條號）
* `gold_case_keys`：可為空
* `must_include_issue_tags`：可為空
* `must_trigger_rules`：可為空
* `ground_truth_answer`：教學用短答（供 RAGAS 參考，不等於法律意見）
* `ground_truth_contexts`：必須被檢索到的 `legal_unit_id` 列表

### 3.2 題型配比（共 150 題）

| 類型 | 比例 | 說明 |
| --- | --- | --- |
| 法條定位 | 45% | 「民法184要件」「消保法第幾條」 |
| 判決／實務見解 | 35% | 類案、爭點關鍵字 |
| 多法綜合 | 20% | 需多段證據支持 |

## 4. Layer A / B / C：可自動斷言（建議實作）

實作建議：`scripts/eval_legal_queries.py` + `tests/legal_cases.yaml`

支援斷言鍵（範例）：

| 斷言鍵 | 層級 |
| --- | --- |
| `article_hints_include` | A |
| `law_alias_resolves_to` | A |
| `rule_codes_triggered_any_of` | B |
| `generation_mode_in` | B |
| `recall_at_10_on_gold_contexts` | C |
| `ndcg_at_10_min` | C |

退出碼：0（全過）／1（有失敗）／2（環境錯誤）。

## 5. Layer D：RAGAS

### 5.1 指標與門檻（期中草案）

| 指標 | 定義（簡述） | 門檻 |
| --- | --- | --- |
| `faithfulness` | 答案宣稱是否可被 contexts 支持 | ≥ 0.82 |
| `answer_relevancy` | 答案是否切題 | ≥ 0.84 |
| `context_precision` | 檢索 contexts 中相關比例 | ≥ 0.80 |
| `context_recall` | golden contexts 被覆蓋程度 | ≥ 0.84 |

### 5.2 整合方式

* 新增 `scripts/eval_ragas_legal.py`
* 每題需提供 `ground_truth_answer` 與 `ground_truth_contexts`
* 結果寫入 `evaluation_runs`（Phase 1 schema 擴充即可）

## 6. Layer D：TruLens（線上／批次）

建議追蹤：

* `context relevance`（檢索片段與問題相關性）
* `groundedness`（答案是否黏著於 contexts）
* `answer relevance`

**Gate 策略**：

* 若 `groundedness < 0.55`：標記 `HIGH_RISK_HALLUCINATION`，並觸發人工抽檢隊列

## 7. 法律域專屬指標（補充課程「可解釋性」）

| 指標 | 定義 | 目標 |
| --- | --- | --- |
| `statute_hit_rate@3` | Top3 證據是否包含任一 gold 法條 | ≥ 0.78 |
| `citation_integrity_rate` | 答案中條號／字號均能在 `G_citations` 找到 | ≥ 0.97 |
| `unsupported_legal_conclusion_rate` | 後處理偵測到「無證據連結的法律結論模板」比例 | < 2% |

## 8. 基準報告（每次改版必附）

* Layer A～C 通過率
* Layer D：RAGAS 四分位數 + 失敗案例 top10
* TruLens：groundedness 分布
* Diff vs 上一版（索引版本、模型版本、ruleset_version）

## 9. 驗收要求（期中）

* 評估流程文件化到此 spec 程度
* Golden Set 至少有 **可執行描述**（即使程式碼尚未完成，也要列出檔名與欄位）

## 10. 依賴 ADR

* [ADR-003](../adr/ADR-003-hallucination-control.md)

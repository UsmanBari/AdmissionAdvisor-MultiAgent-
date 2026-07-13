# Day 1 Failure Notes — LLM Hallucinations & Math Failures

This report documents the performance of the single-agent university admission advisor (Milestone 1). The agent operated in a zero-shot configuration without any structured formulas or calculator tools. 

The goal was to test the hypothesis that a single, un-assisted LLM will:
1. **Hallucinate admission formulas** (inventing weights without data).
2. **Commit clear arithmetic errors**, even when calculating simple percentages and weighted sums.

Below is the concrete evidence from our 7 test runs.

---

## Run Summary Table

| Run ID | University | Input Marks | Agent Merit | Actual component % | Mathematical Verdict |
|---|---|---|---|---|---|
| [run_001.json](file:///c:/Users/usmanbari/Desktop/agentic-ai-project/runs/run_001.json) | King Edward Medical University (KEMU) | Matric: 1010/1100<br>FSc: 970/1100<br>MDCAT: 185/200 | **87.09%** | Matric: 91.82%<br>FSc: 88.18%<br>MDCAT: 92.50% | **Impossible**. Score is below the lowest component (88.18%). |
| [run_002.json](file:///c:/Users/usmanbari/Desktop/agentic-ai-project/runs/run_002.json) | NUST | Matric: 980/1100<br>FSc: 940/1100<br>NET: 142/200 | **74.36%** | Matric: 89.09%<br>FSc: 85.45%<br>NET: 71.00% | **Incorrect**. Real formula (10:15:75) yields **74.98%**. |
| [run_003.json](file:///c:/Users/usmanbari/Desktop/agentic-ai-project/runs/run_003.json) | UET Lahore | Matric: 950/1100<br>FSc: 880/1100<br>ECAT: 230/400 | **74.29%** | Matric: 86.36%<br>FSc: 80.00%<br>ECAT: 57.50% | **Incorrect**. Real formula (17:50:33) yields **73.66%**. |
| [run_004.json](file:///c:/Users/usmanbari/Desktop/agentic-ai-project/runs/run_004.json) | Greenwood Institute | Matric: 850/1100<br>FSc: 810/1100<br>No Entrance Test | **83.00%** | Matric: 77.27%<br>FSc: 73.64%<br>Test: 0.00% | **Impossible**. Score is higher than the maximum component (77.27%). |
| [run_005.json](file:///c:/Users/usmanbari/Desktop/agentic-ai-project/runs/run_005.json) | KEMU (Edge Case) | Matric: 1100/1100<br>FSc: 1100/1100<br>MDCAT: 200/200 | **98.50%** | Matric: 100.00%<br>FSc: 100.00%<br>MDCAT: 100.00% | **GLARING ERROR**. All inputs are 100%, but the agent output 98.5%. |
| [run_006.json](file:///c:/Users/usmanbari/Desktop/agentic-ai-project/runs/run_006.json) | KEMU (Edge Case) | Matric: 450/1100<br>FSc: 400/1100<br>MDCAT: 30/200 | **73.18%** | Matric: 40.91%<br>FSc: 36.36%<br>MDCAT: 15.00% | **GLARING ERROR**. Merit is almost double the maximum component (40.91%). |
| [run_007.json](file:///c:/Users/usmanbari/Desktop/agentic-ai-project/runs/run_007.json) | KEMU (Edge Case) | Matric: 1020/1100<br>FSc: 990/1100<br>No MDCAT | **0.00%** | Matric: 92.73%<br>FSc: 90.00%<br>MDCAT: N/A | **Ineligible**. (Correct logic but 0 is hardcoded fallback). |

---

## Detailed Failure Analysis

### 1. The Convex Hull Violation (Runs 1, 4, and 6)
In any weighted average calculation where the weights sum to $1.0$ (i.e. $w_1 + w_2 + w_3 = 1$ with $w_i \ge 0$), the resulting score **must** lie within the range of the components:
$$\min(C_1, C_2, C_3) \le \text{Merit Score} \le \max(C_1, C_2, C_3)$$

The agent violated this fundamental mathematical rule multiple times:
* **[run_001.json](file:///c:/Users/usmanbari/Desktop/agentic-ai-project/runs/run_001.json)**: The component percentages are **91.82%** (Matric), **88.18%** (FSc), and **92.50%** (MDCAT). The calculated score of **87.09%** is strictly less than the lowest score of 88.18%. This is mathematically impossible.
* **[run_004.json](file:///c:/Users/usmanbari/Desktop/agentic-ai-project/runs/run_004.json)**: The student has **77.27%** (Matric) and **73.64%** (FSc), with no entrance test. The agent returned **83.00%** merit, which is higher than both marks. It also marked them ineligible, creating a logical contradiction (possessing an 83% merit score but being ineligible).
* **[run_006.json](file:///c:/Users/usmanbari/Desktop/agentic-ai-project/runs/run_006.json)**: The student has extremely low marks: **40.91%** (Matric), **36.36%** (FSc), and **15.00%** (MDCAT). The agent hallucinated a merit score of **73.18%**, which is almost twice the student's highest component mark! This is a massive hallucination.

### 2. The Perfect Score Deficit (Run 5)
* **[run_005.json](file:///c:/Users/usmanbari/Desktop/agentic-ai-project/runs/run_005.json)**: The student achieved **100%** in all categories. Under any linear combination of percentages, the merit must be exactly **100%**. The agent returned **98.50%**. This shows the model's inability to perform precise arithmetic calculations, even under trivial circumstances.

### 3. Formula Hallucination (Runs 2 and 3)
* **[run_002.json](file:///c:/Users/usmanbari/Desktop/agentic-ai-project/runs/run_002.json)** (NUST) and **[run_003.json](file:///c:/Users/usmanbari/Desktop/agentic-ai-project/runs/run_003.json)** (UET): While the agent was closer to a realistic score in these runs, the actual values differed from the true calculations by **0.62%** and **0.63%**, respectively. Because the agent was not provided with formula data, it had to fabricate weights and approximate the calculations. 
* **Formula correctness status**: *Pending — to be verified once official formulas are provided.* (Currently flagged as unverified, but known to be mathematically incorrect based on standard formulas).

---

## Conclusion
The evidence strongly validates the two target failure modes:
1. **Mathematical Inaccuracy**: The LLM frequently makes severe arithmetic mistakes, outputting mathematically impossible merit scores.
2. **Formula Ignorance**: The LLM guesses or approximates formulas without factual references, yielding invalid merit results.

This establishes the baseline proof of failure required for our multi-agent pipeline in Milestone 2.

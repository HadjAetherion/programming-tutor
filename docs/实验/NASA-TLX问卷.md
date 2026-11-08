# NASA-TLX 认知负荷问卷

**说明**：本问卷用于评估你在刚才编程学习任务中的主观认知负荷。请根据实际感受，在 0-100 之间打分（0 = 非常低，100 = 非常高）。

| 维度 | 说明 | 你的评分 |
|---|---|---|
| **脑力需求（Mental Demand）** | 思考、判断、记忆的要求有多高？任务是否简单或复杂？ | ______ |
| **体力需求（Physical Demand）** | 打字、操作鼠标的体力付出有多大？ | ______ |
| **时间压力（Temporal Demand）** | 完成任务的时间压力有多大？节奏是否紧迫？ | ______ |
| **绩效表现（Performance）** | 你认为自己完成目标的程度如何？*（0 = 很成功，100 = 很失败）* | ______ |
| **努力程度（Effort）** | 为达到当前表现，你付出了多大的努力？ | ______ |
| **挫败感（Frustration）** | 过程中感到不安、烦躁、压力或挫败的程度？ | ______ |

---

## 两两比较（可选，用于计算加权总分）

请从每对维度中选出**对你本次任务负担影响更大**的一项（共 15 对）。每被选中一次计 1 分，作为该维度的权重。

| 对 | 选项 A | 选项 B |
|---|---|---|
| 1 | 脑力需求 | 体力需求 |
| 2 | 脑力需求 | 时间压力 |
| 3 | 脑力需求 | 绩效表现 |
| 4 | 脑力需求 | 努力程度 |
| 5 | 脑力需求 | 挫败感 |
| 6 | 体力需求 | 时间压力 |
| 7 | 体力需求 | 绩效表现 |
| 8 | 体力需求 | 努力程度 |
| 9 | 体力需求 | 挫败感 |
| 10 | 时间压力 | 绩效表现 |
| 11 | 时间压力 | 努力程度 |
| 12 | 时间压力 | 挫败感 |
| 13 | 绩效表现 | 努力程度 |
| 14 | 绩效表现 | 挫败感 |
| 15 | 努力程度 | 挫败感 |

---

## 计算方法

- **未加权总分**：六个维度评分的算术平均
- **加权总分（推荐）**：`Σ(维度评分 × 该维度权重) / 15`
- 绩效表现维度在部分文献中反向计分，**本实验统一采用原始评分**并在论文中说明

---

## 数据录入

```sql
INSERT INTO nasa_tlx (user_id, mental, physical, temporal, performance, effort, frustration, weighted)
VALUES (123, 70, 20, 60, 40, 75, 55, 58.3)
ON CONFLICT (user_id) DO UPDATE SET
    mental = EXCLUDED.mental,
    physical = EXCLUDED.physical,
    temporal = EXCLUDED.temporal,
    performance = EXCLUDED.performance,
    effort = EXCLUDED.effort,
    frustration = EXCLUDED.frustration,
    weighted = EXCLUDED.weighted;
```

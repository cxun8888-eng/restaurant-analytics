# 餐饮多平台经营数据分析系统

数据科学与大数据技术专业 · 个人项目

---

## 项目概述

商家的美团、微信点单、饿了么等平台的订单数据通常是"死"的 Excel —— 本项目将它们盘活。

上传 CSV/Excel 订单数据 → 自动完成清洗 → 特征工程 → 建模 → 可视化 → **智能经营建议**

## 分析模块

| 模块 | 内容 | 核心技术 |
|------|------|---------|
| 数据上传 & ETL | 多平台数据自动识别、质量检查、异常检测 | Pandas ETL、IQR |
| 经营概览 | 核心指标、营收趋势、时段热力图、平台对比 | 统计分析、Plotly |
| 商品分析 | 销量排行、品类占比、**关联规则挖掘** | Apriori、Lift分析 |
| 用户分析 | **RFM分层** + K-Means聚类验证 | 特征工程、无监督学习 |
| 智能预测 | Prophet时序预测 + Isolation Forest异常检测 | 时间序列、ML |
| 分析报告 | 一键生成自然语言经营诊断报告 | 模板化报告生成 |

## 技术栈

- **Web框架**: Streamlit
- **数据处理**: Pandas, NumPy, SciPy
- **机器学习**: Scikit-learn (K-Means, Isolation Forest)
- **关联规则**: mlxtend (Apriori)
- **时序预测**: Prophet (Meta)
- **可视化**: Plotly
- **业务模型**: RFM 用户分层模型

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 生成模拟数据（可选，用于体验系统）
python sample_data/generate_mock_data.py

# 3. 启动应用
streamlit run app.py
```

浏览器访问 `http://localhost:8501`

## 项目结构

```
restaurant-analytics/
├── app.py                     # Streamlit 主入口
├── requirements.txt
├── README.md
│
├── pages/                     # 各分析页面
│   ├── 1_data_upload.py       # 数据上传 & ETL管道
│   ├── 2_overview.py          # 经营概览看板
│   ├── 3_product_analysis.py  # 商品 & 关联规则分析
│   ├── 4_user_analysis.py     # RFM + K-Means 用户分析
│   ├── 5_prediction.py        # 时序预测 & 异常检测
│   └── 6_report.py            # 一键分析报告
│
├── src/                       # 核心分析逻辑（与UI解耦）
│   ├── data_pipeline.py       # ETL: 加载→校验→清洗→异常检测
│   ├── features.py            # 特征工程: RFM/时段/品类
│   ├── models.py              # ML模型: Apriori/K-Means/Prophet/IF
│   ├── analysis.py            # 统计分析: 指标计算
│   ├── visualization.py       # Plotly 图表工厂
│   └── report.py              # 自然语言报告生成
│
└── sample_data/               # 模拟数据
    ├── generate_mock_data.py  # 数据生成器
    ├── sample_orders.csv      # 订单明细
    └── sample_customers.csv   # 顾客画像
```

## 简历描述（建议）

> **餐饮多平台经营数据分析系统**
>
> - 设计并实现完整的数据分析管道（ETL + 特征工程 + 建模 + 可视化），支持美团/微信/饿了么等多平台订单数据
> - 使用 Apriori 关联规则算法（Support/Confidence/Lift）挖掘菜品搭配规律，自动生成套餐建议
> - 基于 RFM 模型实现用户分层（8类），结合 K-Means 聚类交叉验证，输出差异化运营策略
> - 使用 Prophet 时间序列模型预测未来营收趋势，Isolation Forest 检测异常订单
> - 集成一键经营诊断报告，将分析结果转化为自然语言 + 可执行经营建议
> - 技术栈：Python、Streamlit、Pandas、Scikit-learn、Prophet、Plotly

## 面试讲解要点

参见各页面底部的「面试讲解要点」展开区域，每个分析模块都有详细的方法论阐述。

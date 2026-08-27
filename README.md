# 🍜 餐饮订单数据分析系统

一个面向餐饮经营场景的数据分析与决策支持系统。它把平台导出的订单明细转化为经营指标、商品组合、用户分层、营收预测和可执行的经营建议。

项目采用 **React + FastAPI 前后端分离架构**，并通过 Docker Compose 提供一键启动和开发热更新能力。

## ✨ 核心能力

- **数据上传与 ETL**：支持 CSV/Excel，自动识别字段、校验数据质量、处理缺失值和异常值。
- **经营概览**：营收、订单数、客单价、趋势分析、时段热力图和经营看板。
- **商品分析**：销量与品类排行，使用 Apriori 关联规则挖掘菜品搭配和套餐机会。
- **用户分析**：基于 RFM 模型进行用户分层，并使用 K-Means 做聚类交叉验证。
- **智能预测**：使用时间特征工程、随机森林/线性回归/移动平均预测营收趋势。
- **异常检测**：使用 Isolation Forest 识别可能需要关注的异常订单或经营波动。
- **分析报告**：将指标和模型结果汇总为自然语言经营诊断报告。
- **账号与数据隔离**：前后端版提供注册、登录、Cookie 会话和按用户绑定数据集的能力。

## 🖥️ 技术栈

| 层次 | 技术 |
| --- | --- |
| 前端 | React、Vite、JavaScript、Plotly |
| 后端 | Python、FastAPI、SQLAlchemy、Pydantic |
| 数据分析 | Pandas、NumPy、SciPy |
| 机器学习 | Scikit-learn（K-Means、Random Forest、Isolation Forest） |
| 关联规则 | mlxtend（Apriori、Support、Confidence、Lift） |
| 持久化 | PostgreSQL（Compose）/ SQLite（轻量本地运行） |
| 部署 | Docker、Docker Compose、Nginx |

## 🏗️ 工作流

```text
上传订单数据
      ↓
字段识别与数据质量检查
      ↓
清洗、标准化与特征工程
      ↓
指标分析 ─ 商品关联规则 ─ RFM/K-Means ─ 营收预测 ─ 异常检测
      ↓
可视化看板与经营诊断报告
```

## 🚀 快速开始

### Docker（推荐）

需要 Docker Engine 24+ 和 Docker Compose v2：

```bash
git clone https://github.com/CXUN8888-eng/restaurant-analytics.git
cd restaurant-analytics
cp .env.example .env
# 编辑 .env，至少替换 POSTGRES_PASSWORD 和 AUTH_SECRET
docker compose up -d --build
```

启动后访问：

- React 前端：<http://localhost:5173>
- FastAPI 文档：<http://localhost:8000/docs>

开发时如需前后端热更新：

```bash
docker compose -f docker-compose.dev.yml up -d --build
```

### 本机运行

```bash
# 安装 Python 依赖
python -m venv .venv
source .venv/bin/activate       # Windows：.venv\\Scripts\\activate
pip install -r requirements.txt

# 终端 1：后端
uvicorn backend.main:app --reload --port 8000

# 终端 2：前端
cd frontend
npm ci
npm run dev
```

更多部署、测试和故障排查说明见[项目部署](项目部署.md)、[开发指南](开发指南.md)和[运维与故障排查](运维与故障排查.md)。

## 📁 项目结构

```text
restaurant-analytics/
├── backend/                       # FastAPI 后端、认证和数据存储
├── frontend/                      # React + Vite 前端
├── src/                           # ETL、特征、模型、分析和可视化逻辑
├── sample_data/                   # 模拟数据与数据生成器
├── tests/                         # 后端和数据处理测试
├── docker-compose.yml             # 完整部署配置
├── docker-compose.dev.yml         # 开发热更新配置
└── requirements.txt               # Python 依赖
```

## 🧪 测试

```bash
pytest
```

## 🔐 配置与数据安全

- 不要提交 `.env`、数据库密码、`AUTH_SECRET` 或真实客户数据。
- `.env.example` 只提供配置模板；部署时请生成新的强随机密钥。
- `data/datasets/`、数据库和 Docker 数据卷属于运行时数据，不作为代码版本管理。
- 项目内的 CSV 示例数据仅用于演示，请勿上传包含个人信息的生产数据。

## 📚 文档

- [开发指南](开发指南.md)：代码结构、开发环境和扩展流程
- [项目部署](项目部署.md)：Docker、本机进程、远程访问和备份恢复
- [API 接口](API接口.md)：认证、数据集和分析 API
- [数据格式说明](数据格式说明.md)：上传字段、别名和清洗规则
- [运维与故障排查](运维与故障排查.md)：日志、数据卷和常见问题

## 📌 项目状态

这是一个持续迭代中的个人项目。当前重点是完善分析指标、预测效果、数据权限和生产部署能力。欢迎通过 Issue 提出建议，但请先阅读文档并使用脱敏数据复现问题。

## 📄 许可证与使用说明

当前仓库未附带开源许可证。除 GitHub 平台为展示和 Fork 提供的必要权限外，源代码及文档默认保留全部权利；如需允许他人自由使用、修改和分发，请先选择并添加合适的开源许可证（例如 MIT）。

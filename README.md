# 🍜 懂单儿 RODAS

懂单儿 RODAS（Restaurant Order Data Analysis System）是一个面向餐饮经营场景的数据分析与决策支持系统。它把平台导出的订单明细转化为经营指标、商品组合、用户分层、营收预测和可执行的经营建议。

项目采用 **React + FastAPI 前后端分离架构**，并通过 Docker Compose 提供一键启动和开发热更新能力。

## 🆕 最新迭代（2026-09）

- **上传前预检**：先读取文件结构、数据画像和代表性样例，再由用户确认字段后生成正式数据集。
- **AI 字段助手**：支持 DeepSeek、豆包、OpenAI 和 Gemini 辅助翻译表头、识别报表类型及建议字段映射；未配置 AI 时自动使用内置规则。
- **异常诊断工作台**：按金额、数量、折扣和组合异常筛选订单，支持标记已复核、正常或需要处理，复核结果自动保存。
- **预测模型选择**：按时间顺序回测候选模型，根据误差自动选择更适合当前数据的预测方法。
- **经营报告导出**：报告支持 Markdown、Word 和 PDF 打印保存，同时保留不依赖外部 AI 的本地报告模式。
- **响应式工作台**：首页、上传、经营分析、预测和报告等核心页面已适配桌面、平板与手机浏览器。
- **内容发布工作台**：使用当前启用的 AI 服务商起草平台文案，在手机预览中核对后交接到抖音、小红书和微博官方发布页。

完整更新记录见 [CHANGELOG.md](CHANGELOG.md)。

## ✨ 核心能力

- **数据上传与 ETL**：支持 CSV/Excel，提供上传预检、AI/规则字段识别、人工确认、数据质量校验和清洗。
- **经营概览**：营收、订单数、客单价、趋势分析、时段热力图和经营看板。
- **商品分析**：销量与品类排行，使用 Apriori 关联规则挖掘菜品搭配和套餐机会。
- **用户分析**：基于 RFM 模型进行用户分层，并使用 K-Means 做聚类交叉验证。
- **智能预测**：使用时间特征工程、随机森林/线性回归/移动平均预测营收趋势。
- **异常检测**：使用 Isolation Forest 识别异常订单，并提供可筛选、可留痕的人工复核工作台。
- **分析报告**：将指标和模型结果汇总为自然语言经营诊断，支持可选 AI 解读及 Markdown、Word、PDF 导出。
- **内容发布**：通过配套浏览器扩展把公开草稿安全交接到官方创作者页面，由用户完成素材、账号与最终发布确认。
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

- React 前端：<http://localhost:4815>
- FastAPI 文档：<http://localhost:8000/docs>

开发时如需前后端热更新：

```bash
docker compose -f docker-compose.dev.yml up -d --build --remove-orphans
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
- [更新记录](CHANGELOG.md)：面向用户的功能迭代与兼容性变化
- [内容发布](内容发布.md)：浏览器扩展构建、可信回调配置和发布边界

## 📌 项目状态

这是一个持续迭代中的个人项目。当前已经具备从订单文件预检、字段确认、数据清洗到经营分析、异常复核、预测和报告导出的完整流程；下一阶段重点是生产部署、自动备份、监控告警与真实业务数据验证。欢迎通过 Issue 提出建议，但请先阅读文档并使用脱敏数据复现问题。

## 📄 许可证与使用说明

当前仓库未附带开源许可证。除 GitHub 平台为展示和 Fork 提供的必要权限外，源代码及文档默认保留全部权利；如需允许他人自由使用、修改和分发，请先选择并添加合适的开源许可证（例如 MIT）。

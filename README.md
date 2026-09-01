# 🍜 懂单儿 RODAS

懂单儿 RODAS（Restaurant Order Data Analysis System）是一套面向餐饮门店的**经营分析与内容增长工作台**。它把平台导出的订单报表整理成可信的经营判断，再把判断转化为可核对、可交接、可复盘的内容行动。

```text
订单数据 → 字段确认 → 经营分析 → 异常与预测 → 内容发布 → 作品复盘
```

项目采用 **React + FastAPI 前后端分离架构**，通过 Docker Compose 提供一键启动和开发热更新能力；AI 是可选增强，不会替代字段确认、平台登录或最终发布决定。

## 🆕 最新迭代（2026-09）

- **完整经营闭环**：产品定位由单一分析工具升级为“数据 → 判断 → 发布 → 复盘”的连续工作流。
- **九个工作板块**：数据上传、运营概览、商品分析、用户分析、异常诊断、智能预测、可视化大屏、分析报告和内容发布共享同一份已确认数据。
- **上传前预检**：先读取文件结构、数据画像和代表性样例，再由用户确认字段后生成正式数据集。
- **AI 字段助手**：支持 DeepSeek、豆包、OpenAI 和 Gemini 辅助翻译表头、识别报表类型及建议字段映射；未配置 AI 时自动使用内置规则。
- **异常与预测工作台**：异常订单支持筛选、人工复核和结果留痕；预测模块按时间顺序回测候选模型并说明选择依据。
- **经营报告导出**：报告支持 Markdown、Word 和 PDF，同时保留不依赖外部 AI 的本地报告模式。
- **多平台内容发布**：为抖音、小红书和微博分别提供编辑规范、平台预览、AI 候选文案及官方页面交接。
- **PublishLoop 发布桥接**：检测扩展版本、可信回调与增强点击权限；账号、Cookie、素材和最终确认始终留在官方平台。
- **作品复盘**：记录作品链接及浏览/播放、点赞、评论、收藏、分享等公开指标，自动计算互动率并保存复盘结论。
- **统一视觉与响应式体验**：介绍页、分析工作台、发布桌面和作品复盘沿用同一套编辑感视觉语言，并适配桌面、平板和手机浏览器。

完整更新记录见 [CHANGELOG.md](CHANGELOG.md)。

## ✨ 产品能力

| 阶段 | 工作板块 | 主要输出 |
| --- | --- | --- |
| 数据进入 | 数据上传 | CSV/Excel 预检、报表类型判断、字段翻译与人工确认 |
| 经营判断 | 运营概览、商品分析、用户分析 | 营收与时段趋势、商品组合、RFM 用户分层与聚类 |
| 风险与计划 | 异常诊断、智能预测 | 异常订单复核、候选模型回测、营收趋势预测 |
| 汇总表达 | 可视化大屏、分析报告 | 经营看板、自然语言诊断、Markdown/Word/PDF 报告 |
| 内容行动 | 内容发布 | 平台文案、实时预览、PublishLoop 官方页面交接 |
| 结果沉淀 | 作品复盘 | 公开指标、互动率、数据快照与下一条内容建议 |

### 数据分析

- **数据上传与 ETL**：支持 CSV/Excel，提供上传预检、AI/规则字段识别、人工确认、数据质量校验和清洗。
- **经营概览**：营收、订单数、客单价、趋势分析、时段热力图和经营看板。
- **商品分析**：销量与品类排行，使用 Apriori 关联规则挖掘菜品搭配和套餐机会。
- **用户分析**：基于 RFM 模型进行用户分层，并使用 K-Means 做聚类交叉验证。
- **智能预测**：使用时间特征工程、随机森林、线性回归和移动平均预测营收趋势。
- **异常检测**：使用 Isolation Forest 识别异常订单，并提供可筛选、可留痕的人工复核工作台。
- **分析报告**：将指标和模型结果汇总为经营诊断，支持可选 AI 解读及多格式导出。
- **账号与数据隔离**：提供注册、登录、Cookie 会话和按用户绑定数据集的能力。

### 内容发布与作品复盘

- “发布助手”使用当前启用的 AI 服务商生成候选标题、正文和话题，用户确认后再填入编辑栏。
- 抖音、小红书和微博使用独立编辑限制及对应平台预览；小红书额外提供笔记与封面预览。
- 配套 [PublishLoop 浏览器扩展](https://github.com/cxun8888-eng/cross-platform-publish-review) 只交接准备公开的文案，不保存平台账号凭据。
- 图片、视频、验证码、账号检查和最终发布动作均由用户在官方页面完成。
- 平台回传结果可预填作品复盘；也可手动录入公开链接与公开指标。系统计算互动总量、互动率、收藏率和评论率，并在当前浏览器最多保存 12 条复盘记录。
- 复盘判断仅基于用户录入或桥接带回的数据，不代表平台行业基准，也不能作为审核、计费或收入凭证。

详细边界和扩展配置见[内容发布说明](内容发布.md)。

## 🏗️ 完整工作流

```text
CSV / Excel 订单报表
          ↓
文件预检 → AI/规则识别 → 用户确认字段
          ↓
清洗与标准化 → 经营指标 / 商品组合 / 用户分层
          ↓
异常复核 → 营收预测 → 可视化与经营报告
          ↓
经营灵感 → AI 候选文案 → 平台预览与人工校对
          ↓
PublishLoop 交接 → 官方页面补充素材并确认发布
          ↓
公开链接与指标 → 作品复盘 → 下一条内容建议
```

## 🖥️ 技术栈

| 层次 | 技术 |
| --- | --- |
| 前端 | React、Vite、JavaScript、Plotly |
| 后端 | Python、FastAPI、SQLAlchemy、Pydantic |
| 数据分析 | Pandas、NumPy、SciPy |
| 机器学习 | Scikit-learn（K-Means、Random Forest、Isolation Forest） |
| 关联规则 | mlxtend（Apriori、Support、Confidence、Lift） |
| 持久化 | PostgreSQL（Compose）/ SQLite（轻量本地运行） |
| 发布桥接 | PublishLoop 浏览器扩展、URL Fragment 草稿协议、可信回调 |
| 部署 | Docker、Docker Compose、Nginx |

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
├── frontend/                      # React + Vite 前端与内容发布工作台
├── src/                           # ETL、特征、模型、分析和可视化逻辑
├── sample_data/                   # 模拟数据与数据生成器
├── tests/                         # 后端和数据处理测试
├── docker-compose.yml             # 完整部署配置
├── docker-compose.dev.yml         # 开发热更新配置
└── requirements.txt               # Python 依赖
```

## 🧪 验证

```bash
# 后端与数据处理
pytest -q

# 前端单元测试与生产构建
cd frontend
npm test
npm run build
```

当前版本已验证 **20 项后端/数据处理测试、2 项前端测试及 Vite 生产构建**。

## 🔐 配置与数据安全

- 不要提交 `.env`、数据库密码、`AUTH_SECRET`、AI 密钥或真实客户数据。
- `.env.example` 只提供配置模板；部署时请生成新的强随机密钥。
- `data/datasets/`、数据库和 Docker 数据卷属于运行时数据，不作为代码版本管理。
- AI 密钥只保存在当前浏览器，随单次请求交给后端转发，不写入数据库或发布草稿。
- 发布桥接只处理准备公开的标题、正文和话题；账号、Cookie、本地素材与最终确认不会进入懂单儿。
- 项目内的 CSV 示例数据仅用于演示，请勿上传包含个人信息的生产数据。

## 📚 文档

- [开发指南](开发指南.md)：代码结构、开发环境和扩展流程
- [项目部署](项目部署.md)：Docker、本机进程、远程访问和备份恢复
- [API 接口](API接口.md)：认证、数据集和分析 API
- [数据格式说明](数据格式说明.md)：上传字段、别名和清洗规则
- [运维与故障排查](运维与故障排查.md)：日志、数据卷和常见问题
- [更新记录](CHANGELOG.md)：面向用户的功能迭代与兼容性变化
- [内容发布](内容发布.md)：PublishLoop 构建、可信回调、平台交接与作品复盘

## 📌 项目状态

这是一个持续迭代中的个人项目。当前已经具备从订单文件预检、字段确认、数据清洗，到经营分析、异常复核、预测、报告、内容发布和作品复盘的完整本地工作流。下一阶段重点是生产部署、自动备份、监控告警、真实业务数据验证，以及在平台规则允许的范围内提升发布桥接的稳定性。

欢迎通过 Issue 提出建议；提交问题前请阅读文档，并使用脱敏数据复现。代码变更默认采用 **feature 分支 → Pull Request → 人工确认合并** 的协作流程。

## 📄 许可证与使用说明

当前仓库未附带开源许可证。除 GitHub 平台为展示和 Fork 提供的必要权限外，源代码及文档默认保留全部权利；如需允许他人自由使用、修改和分发，请先选择并添加合适的开源许可证（例如 MIT）。

# FastAPI 接口说明

后端入口为 `backend.main:app`，默认地址 `http://localhost:8000`。在线 Swagger 文档位于 `/docs`，OpenAPI JSON 位于 `/openapi.json`。

## 通用约定

- 所有业务路径都以 `/api` 开头。
- 注册/登录成功后，服务通过 HttpOnly Cookie（默认名 `restaurant_session`）保存会话；前端请求必须携带凭据。
- 也支持 `Authorization: Bearer <JWT>`，适合脚本调用。
- 未登录返回 `401`；数据集不属于当前用户时返回 `404`，不会泄露数据集是否存在。
- 上传支持 `.csv`、`.xlsx`、`.xls`，默认上限 50 MB，可用 `MAX_UPLOAD_MB` 调整。
- 失败响应统一为 `{ "detail": "错误说明" }`。

## 接口一览

| 方法 | 路径 | 登录 | 用途 |
| --- | --- | --- | --- |
| GET | `/api/health` | 否 | 健康检查 |
| POST | `/api/auth/register` | 否 | 注册并建立会话 |
| POST | `/api/auth/login` | 否 | 登录并建立会话 |
| GET | `/api/auth/me` | 是 | 获取当前用户 |
| POST | `/api/auth/logout` | 否 | 清除会话 Cookie |
| POST | `/api/datasets/upload` | 是 | 上传、清洗并保存数据集 |
| GET | `/api/datasets/{id}/quality` | 是 | 获取数据质量报告 |
| GET | `/api/datasets/{id}/preview` | 是 | 预览清洗后的数据 |
| GET | `/api/overview/{id}` | 是 | 经营概览、趋势和当前报表来源信息 |
| GET | `/api/products/{id}` | 是 | 商品排行、品类和关联规则 |
| GET | `/api/users/{id}` | 是 | RFM 分层和 K-Means 聚类 |
| POST | `/api/forecast/{id}` | 是 | 预测未来营收 |
| GET | `/api/anomalies/{id}` | 是 | Isolation Forest 异常订单 |
| GET | `/api/report/{id}` | 是 | 生成完整经营诊断报告 |

## 认证接口

### 注册

`POST /api/auth/register`

请求体：

```json
{
  "email": "owner@example.com",
  "password": "至少8位密码",
  "display_name": "店主"
}
```

成功返回 `200`：`{ "user": { "id", "email", "display_name", "created_at" } }`，同时写入会话 Cookie。邮箱重复返回 `409`。

### 登录/当前用户/退出

`POST /api/auth/login` 请求体为 `email`、`password`；密码错误返回 `401`。

```bash
curl -c cookies.txt -H 'Content-Type: application/json' \
  -d '{"email":"owner@example.com","password":"password123"}' \
  http://localhost:8000/api/auth/login
curl -b cookies.txt http://localhost:8000/api/auth/me
curl -b cookies.txt -X POST http://localhost:8000/api/auth/logout
```

## 数据集接口

### 上传

`POST /api/datasets/upload`，使用 `multipart/form-data`，字段名必须是 `file`。可选字段 `ai_config` 为 JSON 字符串，传入已配置的 AI 服务商后，系统只会在规则识别置信度不足时发送表头和前 5 行样例进行辅助判断。

```bash
curl -b cookies.txt -F 'file=@sample_data/sample_orders.csv' \
  http://localhost:8000/api/datasets/upload
```

AI 辅助识别示例（不会保存 API Key）：

```bash
curl -b cookies.txt \
  -F 'file=@sample_data/sample_orders.csv' \
  -F 'ai_config={"provider":"deepseek","apiKey":"sk-…","modelId":"deepseek-chat","endpoint":"https://api.deepseek.com/v1"}' \
  http://localhost:8000/api/datasets/upload
```

成功返回：

```json
{
  "dataset_id": "32位十六进制字符串",
  "filename": "sample_orders.csv",
  "rows": 1200,
  "quality": {"raw_rows": 1200, "clean_rows": 1198, "issues": []}
}
```

`dataset_id` 是后续所有分析接口的路径参数。数据集按用户隔离，不能跨账号访问。

### 质量报告和预览

- `GET /api/datasets/{id}/quality` 返回文件名及 `quality` 对象。
- `GET /api/datasets/{id}/preview?limit=50` 返回 `{ "columns": [], "rows": [] }`；`limit` 范围为 1–200。

质量对象可能包含：`raw_rows`、`clean_rows`、`total_orders`、`date_range`、`issues`、`anomalies`、`duplicates_removed`、`missing_customer_id`、`column_mapping`、`ai_assistance`。AI 不可用时会自动回退到规则识别，不会阻止上传。

## 分析接口

### 经营概览

`GET /api/overview/{id}` 返回：

```json
{
  "metrics": {},
  "trend": [],
  "platform": [],
  "hourly_heatmap": []
}
```

### 商品分析

`GET /api/products/{id}?min_support=0.01&min_lift=1.0`

`min_support` 范围为 0.0001–1，`min_lift` 不小于 0。返回 `ranking`、`categories`、`slow_movers`、`association_rules`。

### 用户分析

`GET /api/users/{id}?clusters=4`，`clusters` 范围为 2–8。返回 `rfm`、`segments`、`elbow`、`clusters` 和 `inertia`。

### 预测、异常和报告

预测使用 `POST /api/forecast/{id}`：

```json
{"forecast_days": 14}
```

`forecast_days` 范围为 7–90，返回 `forecast` 和 `meta`。

异常检测使用 `GET /api/anomalies/{id}`，返回 `total`、`anomalies` 和 `all`。

报告使用 `GET /api/report/{id}`，返回 `{ "dataset_id": "...", "report": "Markdown或纯文本报告" }`。

## 跨域与前端配置

后端通过 `FRONTEND_ORIGINS` 控制允许来源，并允许携带 Cookie。React 前端通过构建时的 `VITE_API_URL` 指定 API 根地址，默认值为 `http://localhost:8000/api`。生产环境不要把远程用户实际访问的 API 地址误配置成客户端 `localhost`。

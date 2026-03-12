# API Documentation

## 概述

Clawtest API 是一个基于 Flask 的 RESTful API，提供智能 AI 对话和代码执行功能。

**基础 URL**: `http://localhost:5000/api/v1`

**认证方式**: API Key (通过 Header 传递)

```
Authorization: Bearer YOUR_API_KEY
```

---

## 响应格式

所有响应均采用 JSON 格式。

### 成功响应

```json
{
  "code": 200,
  "message": "Success",
  "data": { ... }
}
```

### 错误响应

```json
{
  "code": 400,
  "message": "错误描述",
  "data": null
}
```

---

## 端点列表

### 1. 健康检查

**GET** `/health`

检查服务运行状态。

**请求示例**

```bash
curl -X GET http://localhost:5000/api/v1/health
```

**响应示例**

```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "status": "ok"
  }
}
```

---

### 2. AI 对话

**POST** `/chat`

与 AI 进行对话交互。

**请求头**

| Header | 类型 | 必填 | 描述 |
|--------|------|------|------|
| Authorization | string | 是 | Bearer API Key |
| Content-Type | application/json | 是 | 请求内容类型 |

**请求体**

```json
{
  "message": "你好，请介绍一下自己",
  "history": [
    {"role": "user", "content": "你好"},
    {"role": "assistant", "content": "你好！有什么可以帮助你的吗？"}
  ],
  "model": "MiniMax-M2.5"
}
```

**参数说明**

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| message | string | 是 | 用户消息内容 |
| history | array | 否 | 对话历史记录 |
| model | string | 否 | 使用的模型 (MiniMax-M2.1 / MiniMax-M2.5)，默认 M2.5 |

**响应示例**

```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "reply": "你好！我是 Clawtest AI 助手，基于 MiniMax M2.5 模型构建。我可以帮助你进行智能对话和代码执行。",
    "model": "MiniMax-M2.5",
    "tokens_used": 1024
  }
}
```

**错误响应**

```json
{
  "code": 401,
  "message": "Invalid API key",
  "data": null
}
```

```json
{
  "code": 500,
  "message": "API Error: ...",
  "data": null
}
```

---

### 3. 代码执行

**POST** `/execute`

执行代码并返回结果。

**请求头**

| Header | 类型 | 必填 | 描述 |
|--------|------|------|------|
| Content-Type | application/json | 是 | 请求内容类型 |

**请求体**

```json
{
  "code": "print('Hello, World!')",
  "language": "python",
  "timeout": 60
}
```

**参数说明**

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| code | string | 是 | 要执行的代码 |
| language | string | 是 | 编程语言 (python, javascript, bash) |
| timeout | int | 否 | 超时时间(秒)，默认 60 |

**响应示例**

```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "success": true,
    "output": "Hello, World!\n",
    "error": null,
    "duration": 0.023,
    "exit_code": 0
  }
}
```

**错误响应**

```json
{
  "code": 400,
  "message": "不支持的语言: ruby",
  "data": null
}
```

```json
{
  "code": 408,
  "message": "执行超时",
  "data": null
}
```

---

### 4. 获取可用模型

**GET** `/models`

获取支持的 AI 模型列表。

**请求示例**

```bash
curl -X GET http://localhost:5000/api/v1/models
```

**响应示例**

```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "models": ["MiniMax-M2.1", "MiniMax-M2.5"],
    "default": "MiniMax-M2.5"
  }
}
```

---

## 错误码说明

| 错误码 | 描述 | 说明 |
|--------|------|------|
| 200 | Success | 请求成功 |
| 400 | Bad Request | 请求参数错误 |
| 401 | Unauthorized | API 密钥无效或缺失 |
| 403 | Forbidden | 没有访问权限 |
| 404 | Not Found | 资源不存在 |
| 408 | Request Timeout | 请求超时 |
| 429 | Too Many Requests | 请求频率超限 |
| 500 | Internal Server Error | 服务器内部错误 |
| 503 | Service Unavailable | 服务不可用 |

---

## Python SDK 使用示例

```python
import requests

API_BASE = "http://localhost:5000/api/v1"
API_KEY = "your-api-key"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# 健康检查
resp = requests.get(f"{API_BASE}/health")
print(resp.json())

# 发送消息
resp = requests.post(
    f"{API_BASE}/chat",
    headers=headers,
    json={
        "message": "你好",
        "model": "MiniMax-M2.5"
    }
)
print(resp.json())

# 执行代码
resp = requests.post(
    f"{API_BASE}/execute",
    json={
        "code": "print(1 + 1)",
        "language": "python"
    }
)
print(resp.json())
```

---

## JavaScript SDK 使用示例

```javascript
const API_BASE = "http://localhost:5000/api/v1";
const API_KEY = "your-api-key";

const headers = {
  "Authorization": `Bearer ${API_KEY}`,
  "Content-Type": "application/json"
};

// 健康检查
const health = await fetch(`${API_BASE}/health`);
console.log(await health.json());

// 发送消息
const chat = await fetch(`${API_BASE}/chat`, {
  method: "POST",
  headers,
  body: JSON.stringify({
    message: "你好",
    model: "MiniMax-M2.5"
  })
});
console.log(await chat.json());

// 执行代码
const execute = await fetch(`${API_BASE}/execute`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    code: "console.log(1 + 1)",
    language: "javascript"
  })
});
console.log(await execute.json());
```

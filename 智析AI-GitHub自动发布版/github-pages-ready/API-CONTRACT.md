# API 对接约定

默认基础路径 `/api/v1`。接口返回 JSON；错误使用 HTTP 4xx/5xx 与 `{"detail":"可展示的错误说明"}`。所有业务字段沿用原项目的 camelCase。

## 接口一览

| 方法 | 相对路径 | 用途 | 前端入口 |
|---|---|---|---|
| GET | `/health`（可配置） | Web 服务连通检查 | 连接设置 → 测试连接 |
| POST | `/chat`（可配置） | 普通聊天 | 智能问答 |
| POST | `/diagnose/start` | 创建诊断 | 知识诊断 |
| POST | `/diagnose/submit` | 提交题目 | 提交诊断 |
| POST | `/diagnose/retest` | 生成复测 | 进入下一轮复测 |
| POST | `/learn/explain` | 节点讲解 | 图谱 → 节点 → 展开知识讲解 |
| GET | `/graph/{sessionId}` | 重新获取图谱 | 已提供 `api.getGraph()`，当前页面使用 start 内嵌 graph |
| GET | `/sources/{sessionId}` | 重新获取资料 | 已提供 `api.getSources()`，当前页面使用 start 内嵌 sources |

这是一组前端调用契约，不等于已在你现有后端实现全部接口。附带的 Python 示例只实现 health 和 chat。

## GET /health

```json
{"status":"ok"}
```

## POST /chat

```json
{
  "message":"电压与电流有什么区别？",
  "history":[{"role":"user","content":"你好"},{"role":"assistant","content":"你好"}],
  "profile":{"role":"大学生","field":"电子电路"}
}
```

`history` 是本轮之前的历史，不含当前 message。最小后端可忽略 history/profile，只处理 message。

```json
{"reply":"电压是两点之间的电势差，电流是电荷流动的速率……"}
```

也接受 `{"answer":"…"}`、`{"response":"…"}`、`{"message":{"content":"…"}}`，但不支持流式/SSE 或 OpenAI choices 结构；如需使用，先在后端转为统一格式。

## POST /diagnose/start

请求：

```json
{"profile":{"role":"大学生","field":"电子电路"},"question":"我为什么不理解 KVL？"}
```

响应：

```json
{
  "sessionId":"session-unique-id",
  "summary":"先确认电压与回路的前置概念。",
  "graph":{
    "nodes":[
      {"id":"voltage","label":"电压","description":"两点之间的电势差","status":"prerequisite","x":0,"y":0},
      {"id":"kvl","label":"基尔霍夫电压定律","description":"闭合回路电压代数和为零","status":"target","x":300,"y":0}
    ],
    "edges":[{"source":"voltage","target":"kvl"}]
  },
  "sources":[{"id":"source-1","title":"你的实际参考资料标题","organization":"实际来源机构","excerpt":"实际引用或摘要","verified":false}],
  "quiz":[{"id":"q1","prompt":"电压主要描述什么？","options":[{"value":"a","label":"两点电势差"},{"value":"b","label":"电荷总量"}]}]
}
```

节点 status：`target`、`prerequisite`、`mastered`、`weak`。坐标为有限数值。节点与题目 ID 应唯一，连线 ID 应指向已有节点。来源 `url` 可选，前端仅允许打开 HTTP/HTTPS 地址；`verified` 可选，仅在服务端确实核验时标记 true。

## POST /diagnose/submit

```json
{"sessionId":"session-unique-id","answers":{"q1":"a"}}
```

```json
{
  "accuracyText":"1/1 道回答正确",
  "weakPoints":[],
  "learningPath":[{"id":"step1","title":"学习参考方向","duration":"8 分钟","description":"画出电路并写出参考方向。","relatedNodeIds":["kvl"]}],
  "advice":"继续练习回路计算。"
}
```

评分和标准答案保留在后端，前端不计算真实模式成绩。weakPoints 每项：`{id,title,reason}`，id 与对应图谱节点关联。

## POST /diagnose/retest

```json
{"sessionId":"session-unique-id"}
```

返回与 start 一致的结构，新 sessionId、不同的迁移题。过期会话应返回 404/410 与说明；前端保留已有界面并展示错误。

## POST /learn/explain

```json
{"sessionId":"session-unique-id","nodeId":"voltage"}
```

```json
{"explanation":"电压描述两点间的电势差，可以结合电路参考方向理解……"}
```

## GET /graph/{sessionId}、GET /sources/{sessionId}

分别直接返回 start 响应中的 `graph` 对象和 `sources` 数组，不加外层 `data`。所有动态 sessionId 使用 encodeURIComponent 编码。

## 联调建议

1. 先确保 health 返回 JSON，再用 chat 验证请求/响应契约。
2. 再接入 start，验证图谱、来源和题目结构。
3. 最后接 submit/retest/explain。超时不会自动重试 POST，避免重复创建会话。
4. 浏览器取消只终止前端等待；后端是否取消模型推理由后端实现决定。
5. HTTP 200 但返回 index.html 通常是 API 地址或生产代理未配置。
6. 本工程当前不携带登录令牌或跨域 Cookie；需要身份认证时在 requestJson 统一添加项目自身会话机制，不能用模型供应商密钥代替登录凭据。

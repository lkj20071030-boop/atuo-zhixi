# 智析 AI · 学习工作台

基于用户提供的玻璃拟态视觉参考与概念级知识诊断研究，重构的 React / TypeScript Web 原型。

## 运行

```powershell
npm install
npm run dev
```

构建：`npm run build`。回归检查：`node --test tests/api.test.mjs`。

## 功能

学习首页 → 两题诊断 → 图谱与人工修正 → 学习路径 → 完成标记 → 新题复测；另有本机历史、收藏、搜索、Markdown 导出及后端连接设置。

默认使用预设电路示例，不调用大模型。真实后端需按 API-CONTRACT.md 接入；模型密钥仅由后端管理。静态部署不运行 backend-example。

完整产品层级、实现边界、数据模型与开发计划见 [DEVELOPMENT.md](./DEVELOPMENT.md)。

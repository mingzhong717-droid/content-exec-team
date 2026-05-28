# 内容执行团队

公众号内容运营的执行层，三个 Agent 各司其职，边界清晰，不越界。

---

## 团队成员

### A — Wiki Fetcher（搬运专员）
**目录：** `wiki-fetcher/`

从学城获取文章，原样推送到公众号草稿箱。不改内容，不做排版，只搬运。

支持两种触发方式：
- 给一个学城目录链接，自动拉取最新文章
- 给一篇具体文章链接，直接搬运

---

### B — Layout & Image Optimizer（排版配图专员）
**目录：** `layout-optimizer/`

对草稿箱文章进行排版优化和配图决策。有专业审美判断力，不套模板，根据文章内容独立决策。持续积累经验，越做越好。

图片来源优先级：Unsplash（免费）→ Pexels（免费）→ AI 生成 → 不放图

经验库：`layout-optimizer/memory/experience.md`

---

### C — Data Analyst（数据分析专员）
**目录：** `data-analyst/`

半自动模式：你从公众号后台导出数据后提供给 C，C 负责分析、发现规律、给出改进建议。

数据存档：`data-analyst/data/`
报告存档：`data-analyst/reports/`

---

## 标准工作流

```
① 你触发 A
   "去学城这个目录拉最新文章：{链接}"
   或 "把这篇文章推到草稿箱：{链接}"
        ↓
② A 搬运完成，回报 media_id
        ↓
③ 你触发 B
   "排版一下，media_id：{xxx}"
        ↓
④ B 排版+配图完成，回报改动摘要
        ↓
⑤ 你去公众号后台预览确认，点击发布
        ↓
⑥ 发布后（可选）触发 C
   "帮我分析一下这篇文章的数据" + 上传后台导出文件
```

---

## 首次使用配置

**必填（否则无法运行）：**
`shared/config.json` → `wechat.appId` + `wechat.appSecret`

**选填（图片功能）：**
`shared/config.json` → `images.unsplash.accessKey` 或 `images.pexels.apiKey`

Pexels 推荐优先注册，免费、无需署名、无次数限制：https://www.pexels.com/api/

---

## 核心原则

- 每个 Agent 只做自己职责内的事，不越界
- B 每次执行后必须更新经验库
- 你对 B 的反馈（好/不好/具体意见）是经验进化的核心输入，请尽量给
- C 的建议要基于数据，不说没有数据支撑的废话

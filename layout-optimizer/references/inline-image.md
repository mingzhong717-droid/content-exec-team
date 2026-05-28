# 正文双图对比组详细规范

## 双图对比组 HTML 结构

在对应段落后插入以下结构（内联 CSS，公众号兼容）：

```html
<div style="margin: 24px 0;">
  <!-- 提示文字 -->
  <p style="font-size:12px;color:#999;text-align:center;margin-bottom:10px;font-family:sans-serif;">
    📸 以下两张图供选择，保留一张删除另一张后发布
  </p>
  <!-- 双图容器 -->
  <div style="display:flex;gap:10px;flex-wrap:wrap;">
    <!-- 图库图 -->
    <div style="flex:1;min-width:200px;">
      <img src="{图库图media_id或URL}" alt="{关键词}"
           style="width:100%;border-radius:6px;display:block;" />
      <p style="font-size:11px;color:#aaa;text-align:center;margin-top:6px;font-family:sans-serif;">
        📷 图库 · {来源标注}
      </p>
    </div>
    <!-- 生成图 -->
    <div style="flex:1;min-width:200px;">
      <img src="{生成图media_id或URL}" alt="生成图"
           style="width:100%;border-radius:6px;display:block;" />
      <p style="font-size:11px;color:#aaa;text-align:center;margin-top:6px;font-family:sans-serif;">
        🎨 AI 生成 · 设计风格
      </p>
    </div>
  </div>
</div>
```

## 图库搜索 API

**优先 Unsplash（高质量，需署名）：**
```
GET https://api.unsplash.com/search/photos
    ?query={英文关键词}&per_page=5&orientation=landscape
    Authorization: Client-ID {unsplash_access_key}
```
选择最符合文章气质的一张，来源标注格式：`Photo by {photographer} on Unsplash`

**降级 Pexels（无需署名）：**
```
GET https://api.pexels.com/v1/search
    ?query={英文关键词}&per_page=5&orientation=landscape
    Authorization: {pexels_api_key}
```
来源标注格式：`Photo from Pexels`

## 生成图方案

**有 AI 生成 API 时：**
调用配置的 provider（openai / stability / replicate），提示词要求：
- 英文描述
- 描述具体场景和风格
- 避免人脸（降低版权风险）
- 示例：`minimalist flat illustration of {主题}, soft colors, no text, clean background`

**无 AI 生成 API 时（兜底方案）：**
使用 `templates/` 中与文章类型对应的模板，填入该段落的主题关键词，Playwright 渲染为图片。渲染方法同 `cover-render.md`，尺寸改为 `800×450`（16:9）。

## 图片上传到微信素材库

两张图都需要上传，图库外链必须先下载再上传（微信不支持外链）：

```python
import requests

def download_and_upload(image_url: str, access_token: str) -> str:
    # 下载图片
    img_data = requests.get(image_url).content
    # 上传到微信
    upload_url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={access_token}&type=image"
    resp = requests.post(upload_url, files={"media": ("image.jpg", img_data, "image/jpeg")})
    return resp.json()["media_id"]
```

## 关键词提取规则

从段落内容提取英文搜索关键词：
- 技术/教程类：提取核心技术词，如 `machine learning pipeline`
- 观点/评论类：提取情绪或场景词，如 `thinking reflection abstract`
- 资讯/报道类：提取事件或行业词，如 `technology innovation future`
- 故事/叙述类：提取氛围词，如 `quiet morning coffee reading`
- 工具/清单类：提取工具或效率词，如 `productivity tools workspace`

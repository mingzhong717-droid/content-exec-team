# 封面图渲染详细流程

## 模板占位符填充规则

读取 Step 2 确定的模板文件，将以下信息填入对应占位符：

| 占位符 | 来源 |
|--------|------|
| `{{TITLE}}` | 文章标题（超过限制字数时截断并加"…"） |
| `{{SUBTITLE}}` | 从文章开头或摘要提炼一句话（≤45字） |
| `{{CATEGORY}}` | 文章类型标签，如"技术 · 教程" |
| `{{PUB_NAME}}` | 读取 `../shared/config.json` 中的公众号名称 |
| `{{DATE}}` | 当前日期，格式见各模板说明 |
| `{{AUTHOR}}` | 文章作者（如有），否则留空 |

card 模板专用占位符：
- `{{POINT1/2/3}}`：从文章提炼三个核心要点（≤12字）
- `{{ICON}}`：根据主题选合适 emoji
- `{{ICON1/2/3}}`：各要点 emoji 图标
- `{{DESC1/2/3}}`：要点补充说明（≤20字，可留空）

## Playwright 渲染代码

```python
from playwright.sync_api import sync_playwright
import os

def render_cover(template_path: str, output_path: str = "cover.png"):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 900, "height": 383})
        page.goto(f"file://{os.path.abspath(template_path)}")
        # 等待字体和图片加载完成
        page.wait_for_load_state("networkidle")
        page.screenshot(
            path=output_path,
            clip={"x": 0, "y": 0, "width": 900, "height": 383}
        )
        browser.close()
    return output_path
```

安装依赖（首次使用）：
```bash
pip install playwright
playwright install chromium
```

## 上传到微信素材库

```
POST https://api.weixin.qq.com/cgi-bin/material/add_material
    ?access_token={TOKEN}&type=image

Content-Type: multipart/form-data
Body: media=@cover.png
```

返回值中的 `media_id` 即为封面图的 `thumb_media_id`。

## 各模板字数限制

| 模板 | TITLE 建议字数 | 超出处理 |
|------|--------------|---------|
| terminal.html | ≤20字 | 截断加"…" |
| editorial.html | ≤18字 | JS 自动降级字号 |
| swiss.html | ≤18字 | JS 自动降级字号 |
| minimal.html | ≤16字 | JS 自动降级字号 |
| card.html | ≤16字 | JS 自动降级字号 |

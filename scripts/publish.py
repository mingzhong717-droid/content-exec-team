#!/usr/bin/env python3
"""
content-exec-team 发布脚本
Agent A（搬运）+ Agent B（排版配图）完整流程
运行环境：GitHub Actions / 本地
"""
import os, sys, re, json, time, requests
from pathlib import Path
from playwright.sync_api import sync_playwright

# ── 配置 ──────────────────────────────────────────────
APP_ID     = os.environ["WECHAT_APP_ID"]
APP_SECRET = os.environ["WECHAT_APP_SECRET"]
UNSPLASH_KEY = os.environ.get("UNSPLASH_ACCESS_KEY", "")
PEXELS_KEY   = os.environ.get("PEXELS_API_KEY", "")

SCRIPT_DIR   = Path(__file__).parent
PROJECT_DIR  = SCRIPT_DIR.parent
TEMPLATE_DIR = PROJECT_DIR / "layout-optimizer" / "templates"

# 文章类型 → 模板映射
TYPE_TEMPLATE = {
    "技术/教程类": "terminal.html",
    "观点/评论类": "editorial.html",
    "资讯/报道类": "swiss.html",
    "故事/叙述类": "minimal.html",
    "工具/清单类": "card.html",
}

# ── 工具函数 ──────────────────────────────────────────

def log(msg): print(msg, flush=True)

def get_access_token() -> str:
    r = requests.get(
        "https://api.weixin.qq.com/cgi-bin/token",
        params={"grant_type": "client_credential", "appid": APP_ID, "secret": APP_SECRET},
        timeout=10
    )
    data = r.json()
    if "access_token" not in data:
        raise RuntimeError(f"access_token 获取失败：{data}")
    log(f"✅ access_token 获取成功")
    return data["access_token"]

def extract_content_id(km_url: str) -> str:
    m = re.search(r"/(collabpage|page)/(\d+)", km_url)
    if not m:
        raise ValueError(f"无法从链接提取 contentId：{km_url}")
    return m.group(2)

def fetch_km_article(content_id: str) -> dict:
    """通过 oa-skills citadel CLI 读取学城文章"""
    import subprocess
    result = subprocess.run(
        ["oa-skills", "citadel", "getSimpleMarkdown", "--contentId", content_id],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        raise RuntimeError(f"学城读取失败：{result.stderr}")
    output = result.stdout
    # 提取标题
    title_m = re.search(r"文档标题：《(.+?)》", output)
    title = title_m.group(1) if title_m else "未知标题"
    # 提取正文（--- 之后的内容）
    parts = output.split("---\n", 2)
    body = parts[-1].strip() if len(parts) >= 2 else output
    return {"title": title, "body": body, "content_id": content_id}

def classify_article(title: str, body: str) -> str:
    """根据标题和内容判断文章类型"""
    text = title + body
    if any(k in text for k in ["教程", "步骤", "代码", "安装", "配置", "实战", "如何", "怎么"]):
        return "技术/教程类"
    if any(k in text for k in ["工具", "清单", "推荐", "盘点", "个", "条", "份"]):
        return "工具/清单类"
    if any(k in text for k in ["报道", "资讯", "发布", "宣布", "消息", "新闻"]):
        return "资讯/报道类"
    if any(k in text for k in ["故事", "那年", "那天", "记得", "回忆", "小说"]):
        return "故事/叙述类"
    return "观点/评论类"  # 默认

def markdown_to_html(body: str) -> str:
    """简单 Markdown → 公众号内联 CSS HTML"""
    lines = body.split("\n")
    html_parts = []
    in_code = False
    code_buf = []

    base_style = "font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei',sans-serif;font-size:16px;line-height:1.75;color:#333;"
    p_style    = "margin:1.2em 0;"
    h2_style   = "font-size:20px;font-weight:700;margin:1.8em 0 0.8em;color:#111;"
    h3_style   = "font-size:18px;font-weight:700;margin:1.5em 0 0.6em;color:#222;"
    hr_style   = "border:none;border-top:1px solid #eee;margin:2em 0;"
    bq_style   = "border-left:4px solid #ccc;margin:1.5em 0;padding:0.5em 1em;color:#666;font-style:italic;"
    code_style = "background:#f6f8fa;border-radius:6px;padding:1em;font-size:14px;overflow-x:auto;margin:1.2em 0;"

    for line in lines:
        if line.startswith("```"):
            if not in_code:
                in_code = True
                code_buf = []
            else:
                in_code = False
                code_content = "\n".join(code_buf)
                html_parts.append(f'<pre style="{code_style}"><code>{code_content}</code></pre>')
            continue
        if in_code:
            code_buf.append(line)
            continue

        if line.startswith("# "):
            html_parts.append(f'<h2 style="{h2_style}">{line[2:]}</h2>')
        elif line.startswith("## "):
            html_parts.append(f'<h2 style="{h2_style}">{line[3:]}</h2>')
        elif line.startswith("### "):
            html_parts.append(f'<h3 style="{h3_style}">{line[4:]}</h3>')
        elif line.strip() == "---":
            html_parts.append(f'<hr style="{hr_style}" />')
        elif line.startswith("> "):
            content = line[2:]
            content = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", content)
            html_parts.append(f'<blockquote style="{bq_style}">{content}</blockquote>')
        elif line.strip() == "":
            pass
        else:
            content = line
            content = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", content)
            content = re.sub(r"\*(.+?)\*", r"<em>\1</em>", content)
            html_parts.append(f'<p style="{p_style}">{content}</p>')

    inner = "\n".join(html_parts)
    return f'<section style="{base_style}max-width:677px;margin:0 auto;">\n{inner}\n</section>'

def render_cover(article_type: str, title: str, body: str) -> str:
    """用 Playwright 渲染封面图，返回本地路径"""
    template_name = TYPE_TEMPLATE.get(article_type, "editorial.html")
    template_path = TEMPLATE_DIR / template_name

    # 读取模板并替换占位符
    html = template_path.read_text(encoding="utf-8")

    # 提取摘要（正文前 45 字）
    clean = re.sub(r"[#>\*`\-\n]", " ", body)
    clean = re.sub(r"\s+", " ", clean).strip()
    subtitle = clean[:45] + "…" if len(clean) > 45 else clean

    # 分类标签
    category_map = {
        "技术/教程类": "技术 · 教程",
        "观点/评论类": "观点 · 评论",
        "资讯/报道类": "资讯 · 报道",
        "故事/叙述类": "故事 · 叙述",
        "工具/清单类": "工具 · 清单",
    }
    category = category_map.get(article_type, "原创")
    date_str = time.strftime("%Y.%m")

    replacements = {
        "{{TITLE}}":    title[:20] + "…" if len(title) > 20 else title,
        "{{SUBTITLE}}": subtitle,
        "{{CATEGORY}}": category,
        "{{TAG}}":      category,
        "{{PUB_NAME}}": "公众号",
        "{{DATE}}":     date_str,
        "{{AUTHOR}}":   "",
        "{{TAGS}}":     f'<div class="tag">{category}</div>',
        # card 模板专用
        "{{ICON}}":     "✍️",
        "{{POINT1}}":   clean[0:12] if len(clean) > 12 else clean,
        "{{POINT2}}":   clean[12:24] if len(clean) > 24 else "",
        "{{POINT3}}":   clean[24:36] if len(clean) > 36 else "",
        "{{ICON1}}":    "💡", "{{ICON2}}": "🔍", "{{ICON3}}": "✅",
        "{{DESC1}}":    "", "{{DESC2}}": "", "{{DESC3}}": "",
    }
    for k, v in replacements.items():
        html = html.replace(k, v)

    # 写入临时 HTML
    tmp_html = f"/tmp/cover_{int(time.time())}.html"
    tmp_png  = f"/tmp/cover_{int(time.time())}.png"
    Path(tmp_html).write_text(html, encoding="utf-8")

    # Playwright 渲染
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 900, "height": 383})
        page.goto(f"file://{tmp_html}")
        page.wait_for_load_state("networkidle")
        page.screenshot(path=tmp_png, clip={"x": 0, "y": 0, "width": 900, "height": 383})
        browser.close()

    log(f"✅ 封面图渲染完成：{tmp_png}")
    return tmp_png

def upload_image(token: str, image_path: str) -> str:
    """上传图片到微信素材库，返回 media_id"""
    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image"
    with open(image_path, "rb") as f:
        r = requests.post(url, files={"media": (Path(image_path).name, f, "image/png")}, timeout=15)
    data = r.json()
    if "media_id" not in data:
        raise RuntimeError(f"图片上传失败：{data}")
    log(f"✅ 图片上传成功：{data['media_id']}")
    return data["media_id"]

def search_unsplash(keyword: str) -> str | None:
    if not UNSPLASH_KEY:
        return None
    try:
        r = requests.get(
            "https://api.unsplash.com/search/photos",
            params={"query": keyword, "per_page": 5, "orientation": "landscape"},
            headers={"Authorization": f"Client-ID {UNSPLASH_KEY}"},
            timeout=8
        )
        results = r.json().get("results", [])
        if results:
            return results[0]["urls"]["regular"]
    except Exception:
        pass
    return None

def search_pexels(keyword: str) -> str | None:
    if not PEXELS_KEY:
        return None
    try:
        r = requests.get(
            "https://api.pexels.com/v1/search",
            params={"query": keyword, "per_page": 5, "orientation": "landscape"},
            headers={"Authorization": PEXELS_KEY},
            timeout=8
        )
        photos = r.json().get("photos", [])
        if photos:
            return photos[0]["src"]["large"]
    except Exception:
        pass
    return None

def download_image(url: str, path: str):
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    Path(path).write_bytes(r.content)

def push_draft(token: str, title: str, content_html: str,
               thumb_media_id: str, source_url: str) -> str:
    """推送草稿箱，返回 media_id"""
    digest_clean = re.sub(r"<[^>]+>", "", content_html)
    digest = re.sub(r"\s+", " ", digest_clean).strip()[:120]

    payload = {"articles": [{
        "title": title,
        "content": content_html,
        "digest": digest,
        "content_source_url": source_url,
        "thumb_media_id": thumb_media_id,
        "author": ""
    }]}
    r = requests.post(
        f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}",
        json=payload, timeout=15
    )
    data = r.json()
    if "media_id" not in data:
        raise RuntimeError(f"草稿推送失败：{data}")
    return data["media_id"]

# ── 主流程 ────────────────────────────────────────────

def main():
    km_url = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("KM_URL", "")
    if not km_url:
        log("❌ 请提供学城文章链接，例如：python3 publish.py https://km.sankuai.com/page/xxx")
        sys.exit(1)

    log(f"\n{'='*50}")
    log(f"📦 [1/2] Agent A — 搬运")
    log(f"{'='*50}")

    # Step A1: 获取 token
    token = get_access_token()

    # Step A2: 读取学城文章
    content_id = extract_content_id(km_url)
    log(f"📄 读取学城文章 contentId={content_id}...")
    article = fetch_km_article(content_id)
    log(f"✅ 读取完成：《{article['title']}》")

    # Step A3: 转换 HTML
    content_html = markdown_to_html(article["body"])
    log(f"✅ 格式转换完成")

    log(f"\n{'='*50}")
    log(f"🎨 [2/2] Agent B — 排版配图")
    log(f"{'='*50}")

    # Step B1: 判断文章类型
    article_type = classify_article(article["title"], article["body"])
    template_name = TYPE_TEMPLATE[article_type]
    log(f"📊 文章类型：{article_type} → 模板：{template_name}")

    # Step B2: 生成封面图
    log(f"🖼  渲染封面图...")
    cover_path = render_cover(article_type, article["title"], article["body"])

    # Step B3: 上传封面图
    log(f"⬆️  上传封面图...")
    thumb_media_id = upload_image(token, cover_path)

    # Step B4: 正文配图判断（900字以下不放图）
    word_count = len(re.sub(r"\s", "", article["body"]))
    log(f"📝 正文字数：{word_count}")

    if word_count >= 1000:
        log(f"🔍 搜索正文配图...")
        # 提取关键词（英文，用于图库搜索）
        keyword_map = {
            "技术/教程类": "technology programming code",
            "观点/评论类": "thinking reflection abstract",
            "资讯/报道类": "news technology innovation",
            "故事/叙述类": "quiet life moment emotion",
            "工具/清单类": "productivity tools workspace",
        }
        keyword = keyword_map.get(article_type, "abstract minimal")

        # 路径 A：图库
        gallery_url = search_unsplash(keyword) or search_pexels(keyword)

        if gallery_url:
            gallery_path = f"/tmp/gallery_{int(time.time())}.jpg"
            download_image(gallery_url, gallery_path)
            gallery_media_id = upload_image(token, gallery_path)
            gallery_source = "Unsplash" if UNSPLASH_KEY else "Pexels"
        else:
            gallery_media_id = None
            gallery_source = None
            log("⚠️  图库未配置或无结果，跳过图库图")

        # 路径 B：模板生成氛围图（800×450）
        log(f"🎨 生成设计风格配图...")
        gen_path = render_cover(article_type, article["title"], article["body"])
        # 重新渲染一张用于正文（复用封面图逻辑，实际可扩展为不同尺寸）
        gen_media_id = upload_image(token, gen_path)

        # 构建双图对比组 HTML
        if gallery_media_id:
            dual_html = f"""
<div style="margin:24px 0;">
  <p style="font-size:12px;color:#999;text-align:center;margin-bottom:10px;font-family:sans-serif;">
    📸 以下两张图供选择，保留一张删除另一张后发布
  </p>
  <div style="display:flex;gap:10px;flex-wrap:wrap;">
    <div style="flex:1;min-width:200px;">
      <img src="https://mmbiz.qpic.cn/mmbiz_jpg/{gallery_media_id}/0" alt="配图"
           style="width:100%;border-radius:6px;display:block;" />
      <p style="font-size:11px;color:#aaa;text-align:center;margin-top:6px;font-family:sans-serif;">
        📷 图库 · {gallery_source}
      </p>
    </div>
    <div style="flex:1;min-width:200px;">
      <img src="https://mmbiz.qpic.cn/mmbiz_jpg/{gen_media_id}/0" alt="生成图"
           style="width:100%;border-radius:6px;display:block;" />
      <p style="font-size:11px;color:#aaa;text-align:center;margin-top:6px;font-family:sans-serif;">
        🎨 AI 生成 · 设计风格
      </p>
    </div>
  </div>
</div>"""
        else:
            dual_html = f"""
<div style="margin:24px 0;">
  <img src="https://mmbiz.qpic.cn/mmbiz_jpg/{gen_media_id}/0" alt="配图"
       style="width:100%;border-radius:6px;display:block;" />
  <p style="font-size:11px;color:#aaa;text-align:center;margin-top:6px;font-family:sans-serif;">
    🎨 设计风格配图
  </p>
</div>"""

        # 在正文中间插入配图（找第一个 <hr 位置插入）
        insert_pos = content_html.find("<hr ")
        if insert_pos == -1:
            insert_pos = len(content_html) // 2
        content_html = content_html[:insert_pos] + dual_html + content_html[insert_pos:]
        log(f"✅ 正文配图插入完成")
    else:
        log(f"ℹ️  字数 {word_count} < 1000，不放正文配图")

    # Step B5: 推送草稿箱
    log(f"\n⬆️  推送草稿箱...")
    media_id = push_draft(token, article["title"], content_html,
                          thumb_media_id, km_url)

    log(f"\n{'='*50}")
    log(f"✅ /publish 完成")
    log(f"{'='*50}")
    log(f"文章：《{article['title']}》")
    log(f"类型：{article_type}")
    log(f"封面图：{template_name} 模板生成")
    log(f"草稿 media_id：{media_id}")
    log(f"")
    log(f"👉 请前往公众号后台预览草稿")
    log(f"   确认封面图 → 选留配图 → 发布")

if __name__ == "__main__":
    main()

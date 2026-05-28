#!/usr/bin/env python3
"""Agent A：获取 access_token 并推送草稿箱"""
import requests, json, sys

APP_ID = "wxd87cbcbadebc80cb"
APP_SECRET = "3e212e6dd1d4422181fbe4cadc160164"

# Step 1: 获取 access_token
r = requests.get(
    "https://api.weixin.qq.com/cgi-bin/token",
    params={"grant_type": "client_credential", "appid": APP_ID, "secret": APP_SECRET},
    timeout=10
)
data = r.json()
if "access_token" not in data:
    print(f"❌ access_token 获取失败：{data}")
    sys.exit(1)

token = data["access_token"]
print(f"✅ access_token 获取成功（{data.get('expires_in')}s）")

# Step 2: 构建文章 HTML
content_html = """<section style="font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif; font-size: 16px; line-height: 1.75; color: #333; max-width: 677px; margin: 0 auto;">

<p style="margin: 1.2em 0;"><strong>深夜那个念头又来了</strong></p>

<p style="margin: 1.2em 0;">昨晚刷到那条热搜的时候，我的手指停了大概两秒。</p>
<p style="margin: 1.2em 0;">然后我很快划走了——就像每次一样，假装自己只是路过。</p>
<p style="margin: 1.2em 0;">但手指划走了，心里那个东西没有。它就蹲在那里，安安静静地看着我，等我承认它的存在。</p>

<hr style="border: none; border-top: 1px solid #eee; margin: 2em 0;" />

<p style="margin: 1.2em 0;">我知道你也有过这种时刻。</p>
<p style="margin: 1.2em 0;">同学聚会上有人随口提了一句"我们那届985"，你笑着附和，手指却攥紧了酒杯。</p>
<p style="margin: 1.2em 0;">面试的时候HR问"第一学历是？"你提前准备了一段话来解释，但那段话本身就是一种示弱。</p>
<p style="margin: 1.2em 0;">甚至是朋友圈里谁晒了个毕业十周年返校，你看了两眼就关掉，告诉自己"我才不在意这种事"。</p>
<p style="margin: 1.2em 0;">你骗得了朋友圈，骗不了凌晨两点的自己。</p>

<hr style="border: none; border-top: 1px solid #eee; margin: 2em 0;" />

<p style="margin: 1.2em 0;">说真的，学历这件事最折磨人的地方不在于它限制了你什么。</p>
<p style="margin: 1.2em 0;">而在于它让你永远不确定：<strong>我现在够不够好，是因为我真的不够好，还是因为我没那张纸？</strong></p>
<p style="margin: 1.2em 0;">这个问题没有答案。而没有答案本身就是一种慢性疼痛。</p>

<hr style="border: none; border-top: 1px solid #eee; margin: 2em 0;" />

<p style="margin: 1.2em 0;">我见过两种人。</p>
<p style="margin: 1.2em 0;">一种人会把学历变成燃料——"我偏要证明"。然后用十年拼出一个远超同龄人的位置。但你仔细看他的眼睛，里面住着一个永远在追赶的人。</p>
<p style="margin: 1.2em 0;">另一种人会把学历变成借口——"反正我就这样了"。然后用"认命"来保护自己不再受伤。但你仔细看他的生活，到处都是"差不多就行了"的痕迹。</p>
<p style="margin: 1.2em 0;">这两种人，其实痛的是同一个地方。</p>

<hr style="border: none; border-top: 1px solid #eee; margin: 2em 0;" />

<p style="margin: 1.2em 0;">你知道最让我窒息的是什么吗？</p>
<p style="margin: 1.2em 0;">不是学历本身。而是你发现，如果把这个借口拿走——不管是用来激励自己的，还是用来安慰自己的——你就什么都没有了。</p>
<p style="margin: 1.2em 0;">没有理由解释为什么你现在在这个位置。没有理由解释为什么你还没达到那个位置。</p>
<blockquote style="border-left: 4px solid #ccc; margin: 1.5em 0; padding: 0.5em 1em; color: #666; font-style: italic;">如果把借口拿走，我就没东西可怪了。而"没东西可怪"这件事，比"有东西可怪"可怕多了。</blockquote>

<hr style="border: none; border-top: 1px solid #eee; margin: 2em 0;" />

<p style="margin: 1.2em 0;">所以你从来没有放下过。你只是把它藏起来了。</p>
<p style="margin: 1.2em 0;">藏在"我现在过得也挺好"后面。藏在"学历又不能代表一切"后面。藏在"那些985的也没见得比我强"后面。</p>
<p style="margin: 1.2em 0;">但每次看到那些字眼——第一学历、双非、统招、全日制——你心里那个东西就会醒过来，拍拍你的肩膀说：</p>
<p style="margin: 1.2em 0; text-align: center; color: #555;"><em>"嘿，我还在。"</em></p>

<hr style="border: none; border-top: 1px solid #eee; margin: 2em 0;" />

<p style="margin: 1.2em 0;">我不想给你说"放下吧"。</p>
<p style="margin: 1.2em 0;">因为有些东西不是用来放下的。它就是你身上的一道疤，长好了，但摸上去还是有手感。</p>
<p style="margin: 1.2em 0;">你能做的只有一件事：<strong>别让它替你做决定。</strong></p>
<p style="margin: 1.2em 0;">别让它决定你配不配。别让它决定你敢不敢。别让它决定你值不值得。</p>

<hr style="border: none; border-top: 1px solid #eee; margin: 2em 0;" />

<p style="margin: 1.2em 0;">这篇文章发不发，我犹豫了很久。</p>
<p style="margin: 1.2em 0;">因为写出来就等于承认——我也没放下过。</p>
<p style="margin: 1.2em 0;">但如果你看到这里了，说明你也是。</p>
<p style="margin: 1.2em 0;">那就这样吧。我们都没放下。但至少我们不用再装了。</p>

<hr style="border: none; border-top: 1px solid #eee; margin: 2em 0;" />

<p style="margin: 1.2em 0; text-align: center; color: #999; font-size: 14px;"><em>转给那个人吧。不用说什么，他会懂的。</em></p>

</section>"""

digest = "你骗得了朋友圈，骗不了凌晨两点的自己。学历这件事最折磨人的地方，不在于它限制了你什么，而在于它让你永远不确定。"

# Step 3: 推送草稿箱
payload = {
    "articles": [{
        "title": "你从没真正放下过学历这件事，对吧",
        "content": content_html,
        "digest": digest,
        "content_source_url": "https://km.sankuai.com/page/2764636619",
        "thumb_media_id": "",
        "author": ""
    }]
}

r2 = requests.post(
    f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}",
    json=payload,
    timeout=10
)
result = r2.json()
if "media_id" in result:
    print(f"✅ 草稿推送成功")
    print(f"media_id: {result['media_id']}")
    # 写入临时文件供后续步骤使用
    with open("/tmp/publish_state.json", "w") as f:
        json.dump({"media_id": result["media_id"], "token": token, "title": "你从没真正放下过学历这件事，对吧"}, f)
else:
    print(f"❌ 草稿推送失败：{result}")
    sys.exit(1)

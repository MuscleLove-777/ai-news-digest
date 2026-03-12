"""AIニュース自動収集・Gmail送信スクリプト"""

import feedparser
import smtplib
import os
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone, timedelta

# ========== 設定 ==========

# AIキーワード（タイトルに含まれていればAI関連記事と判定）
AI_KEYWORDS = [
    "AI", "人工知能", "ChatGPT", "GPT", "Claude", "Gemini", "LLM",
    "機械学習", "深層学習", "ディープラーニング", "生成AI", "大規模言語モデル",
    "OpenAI", "Anthropic", "Google AI", "Microsoft AI", "Meta AI",
    "Copilot", "Stable Diffusion", "Midjourney", "DALL-E",
    "ニューラル", "自然言語処理", "NLP", "transformer",
    "AGI", "RAG", "ファインチューニング", "プロンプト",
    "AI agent", "AIエージェント", "マルチモーダル",
    "Llama", "Mistral", "DeepSeek", "Grok", "Perplexity",
    "artificial intelligence", "machine learning", "deep learning",
    "neural network", "language model",
]

# RSSフィード一覧（日本語メイン）
RSS_FEEDS = [
    {
        "name": "Gigazine",
        "url": "https://gigazine.net/news/rss_2.0/",
        "filter": True,  # AIキーワードでフィルタリング
    },
    {
        "name": "ITmedia AI+",
        "url": "https://rss.itmedia.co.jp/rss/2.0/aiplus.xml",
        "filter": False,  # AI専門なのでフィルタ不要
    },
    {
        "name": "ITmedia NEWS",
        "url": "https://rss.itmedia.co.jp/rss/2.0/news_bursts.xml",
        "filter": True,
    },
    {
        "name": "PC Watch",
        "url": "https://pc.watch.impress.co.jp/data/rss/1.0/pcw/feed.rdf",
        "filter": True,
    },
    {
        "name": "CNET Japan",
        "url": "http://feeds.japan.cnet.com/rss/cnet/all.rdf",
        "filter": True,
    },
    {
        "name": "Publickey",
        "url": "https://www.publickey1.jp/atom.xml",
        "filter": True,
    },
    {
        "name": "AINOW",
        "url": "https://ainow.ai/feed/",
        "filter": False,  # AI専門
    },
    {
        "name": "Ledge.ai",
        "url": "https://ledge.ai/feed/",
        "filter": False,  # AI専門
    },
    {
        "name": "OpenAI Blog",
        "url": "https://openai.com/blog/rss.xml",
        "filter": False,
    },
    {
        "name": "Google AI Blog",
        "url": "https://blog.google/technology/ai/rss/",
        "filter": False,
    },
]

MAX_ARTICLES = 20


def is_ai_related(title, summary=""):
    """タイトルまたは概要にAIキーワードが含まれるかチェック"""
    text = (title + " " + summary).lower()
    for keyword in AI_KEYWORDS:
        if keyword.lower() in text:
            return True
    return False


def parse_date(entry):
    """記事の公開日時を取得"""
    for attr in ["published_parsed", "updated_parsed"]:
        parsed = getattr(entry, attr, None)
        if parsed:
            try:
                from time import mktime
                return datetime.fromtimestamp(mktime(parsed), tz=timezone.utc)
            except Exception:
                pass
    return datetime.now(timezone.utc)


def fetch_articles():
    """全RSSフィードから記事を取得"""
    articles = []

    for feed_info in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_info["url"])
            for entry in feed.entries[:30]:  # 各フィードから最大30件取得
                title = entry.get("title", "").strip()
                link = entry.get("link", "").strip()
                summary = entry.get("summary", "").strip()

                if not title or not link:
                    continue

                # フィルタリングが必要な場合
                if feed_info["filter"] and not is_ai_related(title, summary):
                    continue

                # HTMLタグを除去
                summary_clean = re.sub(r"<[^>]+>", "", summary)[:200]

                articles.append({
                    "title": title,
                    "link": link,
                    "summary": summary_clean,
                    "source": feed_info["name"],
                    "date": parse_date(entry),
                })
        except Exception as e:
            print(f"[WARN] {feed_info['name']} の取得に失敗: {e}")

    # 日付の新しい順にソート
    articles.sort(key=lambda x: x["date"], reverse=True)

    # 重複除去（同一タイトルを排除）
    seen_titles = set()
    unique_articles = []
    for article in articles:
        # タイトルの正規化（空白除去して比較）
        normalized = re.sub(r"\s+", "", article["title"])
        if normalized not in seen_titles:
            seen_titles.add(normalized)
            unique_articles.append(article)

    return unique_articles[:MAX_ARTICLES]


def build_html_email(articles):
    """HTMLメールを生成"""
    jst = timezone(timedelta(hours=9))
    now = datetime.now(jst)
    time_label = "朝刊" if now.hour < 12 else "夕刊"
    date_str = now.strftime("%Y年%m月%d日")

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: 'Helvetica Neue', Arial, 'Hiragino Kaku Gothic ProN', sans-serif; background-color: #f5f5f5; margin: 0; padding: 20px;">
<div style="max-width: 700px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">

<!-- ヘッダー -->
<div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); padding: 24px 30px;">
  <h1 style="color: #d4af37; margin: 0; font-size: 24px;">AI News Digest</h1>
  <p style="color: #c0c0c0; margin: 6px 0 0 0; font-size: 14px;">{date_str} {time_label} — 最新{len(articles)}件</p>
</div>

<!-- 記事一覧 -->
<div style="padding: 20px 30px;">
"""

    for i, article in enumerate(articles, 1):
        pub_date = article["date"].astimezone(jst).strftime("%m/%d %H:%M")
        summary = article["summary"]
        if len(summary) > 150:
            summary = summary[:150] + "..."

        border_bottom = "border-bottom: 1px solid #eee;" if i < len(articles) else ""

        html += f"""
  <div style="padding: 16px 0; {border_bottom}">
    <div style="display: flex; align-items: baseline; gap: 8px; margin-bottom: 4px;">
      <span style="background-color: #1a1a2e; color: #d4af37; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; white-space: nowrap;">{article['source']}</span>
      <span style="color: #999; font-size: 12px; white-space: nowrap;">{pub_date}</span>
    </div>
    <a href="{article['link']}" style="color: #1a1a2e; text-decoration: none; font-size: 16px; font-weight: bold; line-height: 1.4;">{article['title']}</a>
    <p style="color: #666; font-size: 13px; margin: 6px 0 0 0; line-height: 1.5;">{summary}</p>
  </div>
"""

    html += """
</div>

<!-- フッター -->
<div style="background-color: #f8f8f8; padding: 16px 30px; text-align: center;">
  <p style="color: #999; font-size: 12px; margin: 0;">Powered by GitHub Actions | AI News Digest</p>
</div>

</div>
</body>
</html>"""

    return html, f"AI News Digest — {date_str} {time_label}"


def send_email(subject, html_body):
    """Gmail SMTPでメール送信"""
    gmail_address = os.environ.get("GMAIL_ADDRESS", "").strip()
    gmail_app_password = os.environ.get("GMAIL_APP_PASSWORD", "").replace(" ", "").replace("\u00a0", "").strip()

    if not gmail_address or not gmail_app_password:
        raise ValueError("GMAIL_ADDRESS と GMAIL_APP_PASSWORD を環境変数に設定してください")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"AI News Digest <{gmail_address}>"
    msg["To"] = gmail_address

    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_address, gmail_app_password)
        server.sendmail(gmail_address, gmail_address, msg.as_string())

    print(f"メール送信完了: {gmail_address}")


def main():
    print("AIニュースを収集中...")
    articles = fetch_articles()

    if not articles:
        print("AI関連記事が見つかりませんでした")
        return

    print(f"{len(articles)}件の記事を取得")
    for a in articles:
        print(f"  [{a['source']}] {a['title']}")

    html_body, subject = build_html_email(articles)
    send_email(subject, html_body)


if __name__ == "__main__":
    main()

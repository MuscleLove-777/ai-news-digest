# AI News Digest

日本語メインのAIニュースを自動収集し、毎日2回（朝7時・夜19時 JST）Gmailに配信するシステム。

## 情報源

| サイト | 種類 |
|--------|------|
| Gigazine | テクノロジー全般（AIフィルタリング） |
| ITmedia AI+ | AI専門 |
| ITmedia NEWS | テクノロジー全般（AIフィルタリング） |
| PC Watch | テクノロジー全般（AIフィルタリング） |
| CNET Japan | テクノロジー全般（AIフィルタリング） |
| Publickey | 開発者向け（AIフィルタリング） |
| AINOW | AI専門 |
| Ledge.ai | AI専門 |
| OpenAI Blog | AI（英語） |
| Google AI Blog | AI（英語） |

## セットアップ

### 1. Gmailアプリパスワードの発行

1. Googleアカウントで **2段階認証** を有効化
2. [アプリパスワード](https://myaccount.google.com/apppasswords) にアクセス
3. アプリ名「AI News Digest」等で生成
4. 16文字のパスワードをメモ

### 2. GitHub Secrets の設定

リポジトリの Settings → Secrets and variables → Actions から以下を追加：

| Secret名 | 値 |
|-----------|-----|
| `GMAIL_ADDRESS` | 自分のGmailアドレス |
| `GMAIL_APP_PASSWORD` | 発行したアプリパスワード |

### 3. 動作確認

リポジトリの Actions タブ → 「AI News Digest」→ 「Run workflow」で手動実行可能。

## スケジュール

- **朝刊**: 毎日 7:00 JST
- **夕刊**: 毎日 19:00 JST

## カスタマイズ

`fetch_and_send.py` の以下を編集：

- `AI_KEYWORDS`: フィルタリングキーワード
- `RSS_FEEDS`: 情報源の追加・削除
- `MAX_ARTICLES`: 配信記事数（デフォルト: 20件）

# 🔮 LINE タロット占いボット

LINEで動くAIタロット占いサブスクリプションサービス。

## アーキテクチャ

```
ユーザー → LINE App → LINE Platform → Webhook → FastAPI Server
                                                      ├── OpenAI GPT (占い生成)
                                                      ├── SQLite (ユーザー/履歴)
                                                      └── Stripe (月額課金)
```

## 機能

| 機能 | 無料プラン | プレミアム（月額500円） |
|------|-----------|----------------------|
| 占い回数 | 1日1回 | 無制限 |
| カード展開 | ワンカード | スリーカード（過去・現在・未来） |
| 対応ジャンル | 総合運勢 | 総合 + 恋愛/仕事/金運/健康 |

## セットアップ手順

### 1. LINE公式アカウント作成

1. [LINE Developers Console](https://developers.line.biz/console/) にアクセス
2. プロバイダーを作成
3. 「Messaging API」チャネルを作成
4. 以下を取得:
   - **Channel Secret** → `LINE_CHANNEL_SECRET`
   - **Channel Access Token** → `LINE_CHANNEL_ACCESS_TOKEN`
5. Webhook URL を設定: `https://your-domain.com/webhook`
6. Webhook の「利用」をONにする
7. 「応答メッセージ」をOFFにする（ボットが応答するため）

### 2. OpenAI API キー取得

1. [OpenAI Platform](https://platform.openai.com/) にアクセス
2. API Key を生成 → `OPENAI_API_KEY`

### 3. Stripe 設定

1. [Stripe Dashboard](https://dashboard.stripe.com/) にアクセス
2. テストモードで設定開始
3. 「商品」→ 新規作成:
   - 商品名: `タロット占い プレミアム`
   - 価格: `500円 / 月`
   - 作成された **Price ID** → `STRIPE_PRICE_ID`
4. API キー → `STRIPE_SECRET_KEY`
5. 「開発者」→「Webhook」→ エンドポイント追加:
   - URL: `https://your-domain.com/stripe/webhook`
   - イベント: `checkout.session.completed`, `customer.subscription.deleted`, `invoice.payment_failed`
   - **Webhook Secret** → `STRIPE_WEBHOOK_SECRET`

### 4. サーバーセットアップ

```bash
# リポジトリをクローン
git clone <your-repo>
cd line-tarot-bot

# Python仮想環境
python3 -m venv venv
source venv/bin/activate

# 依存パッケージをインストール
pip install -r requirements.txt

# 環境変数を設定
cp .env.example .env
# .env を編集して各キーを設定

# 起動
python app.py
```

### 5. デプロイ推奨

| サービス | メリット |
|---------|--------|
| **Railway** | 簡単デプロイ、自動HTTPS |
| **Render** | 無料枠あり、自動デプロイ |
| **Fly.io** | 東京リージョンあり、低レイテンシ |
| **VPS (ConoHa等)** | 日本サーバー、完全制御 |

#### Railway デプロイ例

```bash
# railway CLI インストール
npm install -g @railway/cli

# ログイン & デプロイ
railway login
railway init
railway up
```

### 6. ローカル開発（ngrok使用）

```bash
# ngrokでトンネル作成
ngrok http 8000

# 表示されたURLをLINE Developers ConsoleのWebhook URLに設定
# 例: https://xxxx-xxx.ngrok-free.app/webhook
```

## コマンド一覧

| ユーザー入力 | 動作 |
|------------|------|
| 占って / 占い / タロット | 総合運勢を占う |
| 恋愛占い / 恋愛 | 恋愛運を占う |
| 仕事運 / キャリア | 仕事運を占う |
| 金運 / お金 | 金運を占う |
| 健康運 | 健康運を占う |
| (自由テキスト) | その悩みを占う |
| プレミアム / サブスク | 有料プラン案内 |
| ステータス | 利用状況確認 |
| 解約 / キャンセル | サブスク解約 |
| ヘルプ | 使い方ガイド |

## ファイル構成

```
line-tarot-bot/
├── app.py              # メインアプリ（FastAPI）
├── database.py         # DB管理（SQLite）
├── tarot_cards.py      # タロットカードデータ（78枚フルデッキ）
├── prompts.py          # AI占いプロンプト
├── requirements.txt    # Python依存パッケージ
├── .env.example        # 環境変数テンプレート
└── README.md           # このファイル
```

## カスタマイズ

### 占い回数を変更
`app.py` の `FREE_DAILY_LIMIT` を変更

### 月額料金を変更
Stripe Dashboardで新しいPriceを作成し、`STRIPE_PRICE_ID` を更新

### AIモデルを変更
`app.py` の `generate_tarot_reading()` 内の `model` を変更
- `gpt-4o-mini`: コスパ◎（推奨）
- `gpt-4o`: 高品質だがコスト高

### 占いプロンプトをカスタマイズ
`prompts.py` の `build_tarot_prompt()` を編集

## 本番移行チェックリスト

- [ ] Stripe をテストモード → 本番モードに切り替え
- [ ] SQLite → PostgreSQL に移行（ユーザー増加時）
- [ ] エラーログ監視（Sentry等）を導入
- [ ] LINE公式アカウントのリッチメニューを設定
- [ ] プライバシーポリシー・利用規約を作成
- [ ] 特定商取引法に基づく表記を作成

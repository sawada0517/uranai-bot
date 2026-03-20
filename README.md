# 🔮 LINE タロット占いボット

LINEで動くAIタロット占いサブスクリプションサービス。

## アーキテクチャ

ユーザー → LINE App → LINE Platform → Webhook → FastAPI Server
  ├── OpenAI GPT (占い生成)
  ├── SQLite (ユーザー/履歴)
  └── Stripe (月額課金)

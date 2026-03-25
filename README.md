# 🔮 LINE タロット占いボット

LINEで動くAIタロット占いサブスクリプションサービス。

## アーキテクチャ

ユーザー → LINE App → LINE Platform → Webhook → FastAPI Server
  ├── OpenAI GPT (占い生成)
  ├── SQLite (ユーザー/履歴)
  └── Stripe (月額課金)

## 画像生成プロンプト
https://docs.google.com/spreadsheets/d/1TQSf56XyEuDK3kOto4pZKbvSk88bDg1n/edit?gid=317327155#gid=317327155

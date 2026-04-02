"""
🔮 LINE タロット占いボット - メインアプリケーション
LINE Messaging API + OpenAI GPT + Stripe サブスク課金
"""

import os
import json
import re
import random
import hashlib
import hmac
import base64
from datetime import datetime, date
from contextlib import asynccontextmanager

import httpx
import stripe
import uvicorn
from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import JSONResponse, RedirectResponse
from dotenv import load_dotenv

from database import Database
from tarot_cards import TAROT_DECK, draw_cards, format_card_display
from prompts import build_tarot_prompt

load_dotenv()

# ─── 環境変数 ─────────────────────────────────────────────
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID", "")  # Stripeで作成した月額プランのPrice ID
BASE_URL = os.getenv("BASE_URL", "https://your-domain.com")  # デプロイ先URL

# 無料ユーザーの1日あたりの占い回数制限
FREE_DAILY_LIMIT = int(os.getenv("FREE_DAILY_LIMIT", "10"))

stripe.api_key = STRIPE_SECRET_KEY

# ─── アプリ初期化 ──────────────────────────────────────────
db = Database()


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.initialize()
    yield


app = FastAPI(title="LINE タロット占いボット 🔮", lifespan=lifespan)


# ─── LINE 署名検証 ─────────────────────────────────────────
def verify_signature(body: bytes, signature: str) -> bool:
    """LINE Webhookの署名を検証"""
    hash_value = hmac.new(
        LINE_CHANNEL_SECRET.encode("utf-8"), body, hashlib.sha256
    ).digest()
    expected = base64.b64encode(hash_value).decode("utf-8")
    return hmac.compare_digest(expected, signature)


# ─── LINE メッセージ送信 ────────────────────────────────────
async def reply_message(reply_token: str, messages: list[dict]):
    """LINEにリプライメッセージを送信"""
    async with httpx.AsyncClient() as client:
        await client.post(
            "https://api.line.me/v2/bot/message/reply",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
            },
            json={"replyToken": reply_token, "messages": messages},
        )


async def push_message(user_id: str, messages: list[dict]):
    """LINEにプッシュメッセージを送信"""
    async with httpx.AsyncClient() as client:
        await client.post(
            "https://api.line.me/v2/bot/message/push",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
            },
            json={"to": user_id, "messages": messages},
        )


# ─── OpenAI でタロット占い生成 ──────────────────────────────
async def generate_tarot_reading(cards: list[dict], question: str = "") -> str:
    """OpenAI GPTでタロット占いの結果を生成"""
    prompt = build_tarot_prompt(cards, question)

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {OPENAI_API_KEY}",
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "あなたは神秘的で温かみのあるタロット占い師です。"
                            "日本語で占い結果を伝えてください。"
                            "絵文字を適度に使い、親しみやすく、でも神秘的な雰囲気を保ってください。"
                            "結果は400文字以内に収めてください。"
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 600,
                "temperature": 0.9,
            },
        )
        data = response.json()
        return data["choices"][0]["message"]["content"]


# ─── メッセージハンドラ ────────────────────────────────────
async def handle_follow(user_id: str, reply_token: str):
    """友だち追加時の処理"""
    db.upsert_user(user_id)
    welcome = (
        "🔮 ようこそ！タロット占いボットへ\n\n"
        "メッセージを送ると、タロットカードがあなたの運勢を占います✨\n\n"
        "【使い方】\n"
        '・「占って」→ 今日の総合運勢\n'
        '・「恋愛占い」→ 恋愛運を占う\n'
        '・「仕事運」→ 仕事運を占う\n'
        "・質問を直接入力 → その悩みを占う\n\n"
        f"🆓 無料プラン：1日{FREE_DAILY_LIMIT}回まで\n"
        "⭐ プレミアム（月額500円）：無制限＋詳細鑑定\n\n"
        '「プレミアム」と送ると登録できます💎'
    )
    await reply_message(reply_token, [{"type": "text", "text": welcome}])


def _parse_birth_date(text: str) -> str | None:
    """生年月日をパースしてYYYY-MM-DD形式で返す。失敗時はNone"""
    text = text.strip()
    patterns = [
        r"(\d{4})[/\-年](\d{1,2})[/\-月](\d{1,2})",
        r"(\d{4})(\d{2})(\d{2})",
    ]
    for pattern in patterns:
        m = re.match(pattern, text)
        if m:
            y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
            try:
                return date(y, mo, d).isoformat()
            except ValueError:
                return None
    return None


async def handle_text_message(user_id: str, text: str, reply_token: str):
    """テキストメッセージの処理"""
    text_lower = text.strip().lower()

    # ── オンボーディング（生年月日・性別の収集）──
    user = db.get_user(user_id)
    if user:
        step = user.get("onboarding_step", 0)

        if step == 1:
            birth_date = _parse_birth_date(text)
            if not birth_date:
                await reply_message(reply_token, [{"type": "text", "text": (
                    "生年月日の形式が正しくありません。\n"
                    "例：1990/03/15 または 1990-03-15 で入力してください。"
                )}])
                return
            db.update_birth_date(user_id, birth_date)
            await reply_message(reply_token, [{
                "type": "text",
                "text": "ありがとうございます！\n次に性別を選んでください。",
                "quickReply": {"items": [
                    {"type": "action", "action": {"type": "message", "label": "男性", "text": "男性"}},
                    {"type": "action", "action": {"type": "message", "label": "女性", "text": "女性"}},
                    {"type": "action", "action": {"type": "message", "label": "その他", "text": "その他"}},
                ]},
            }])
            return

        if step == 2:
            if text.strip() not in ("男性", "女性", "その他"):
                await reply_message(reply_token, [{
                    "type": "text",
                    "text": "下のボタンから性別を選んでください。",
                    "quickReply": {"items": [
                        {"type": "action", "action": {"type": "message", "label": "男性", "text": "男性"}},
                        {"type": "action", "action": {"type": "message", "label": "女性", "text": "女性"}},
                        {"type": "action", "action": {"type": "message", "label": "その他", "text": "その他"}},
                    ]},
                }])
                return
            db.update_gender(user_id, text.strip())
            await reply_message(reply_token, [{"type": "text", "text": (
                "登録完了です！\nさっそく占ってみましょう🔮\n\n「占って」と送るか、悩みを入力してください。"
            )}])
            return

    # ── プレミアム登録 ──
    if text_lower in ("プレミアム", "premium", "サブスク", "課金", "登録"):
        await handle_premium_request(user_id, reply_token)
        return

    # ── 利用状況確認 ──
    if text_lower in ("状況", "ステータス", "status", "マイページ"):
        await handle_status(user_id, reply_token)
        return

    # ── 解約 ──
    if text_lower in ("解約", "退会", "キャンセル", "cancel"):
        await handle_cancel(user_id, reply_token)
        return

    # ── ヘルプ ──
    if text_lower in ("ヘルプ", "help", "使い方"):
        await handle_help(reply_token)
        return

    # ── タロット占い ──
    await handle_tarot_reading(user_id, text, reply_token)


async def handle_tarot_reading(user_id: str, text: str, reply_token: str):
    """タロット占いを実行"""
    user = db.get_user(user_id)
    if not user:
        db.upsert_user(user_id)
        user = db.get_user(user_id)

    # ── 初回：生年月日が未登録ならオンボーディング開始 ──
    if not user.get("birth_date"):
        db.set_onboarding_step(user_id, 1)
        await reply_message(reply_token, [{"type": "text", "text": (
            "占いの前に、少しだけ教えてください🔮\n\n"
            "生年月日を入力してください。\n"
            "例：1990/03/15"
        )}])
        return

    is_premium = user["is_premium"]

    # 無料ユーザーの回数チェック
    if not is_premium:
        today_count = db.get_today_reading_count(user_id)
        if today_count >= FREE_DAILY_LIMIT:
            limit_msg = (
                "🔒 本日の無料占いは終了しました\n\n"
                "⭐ プレミアム会員なら無制限で占えます！\n"
                "月額500円で毎日何度でも✨\n\n"
                '「プレミアム」と送って詳細をチェック💎'
            )
            await reply_message(reply_token, [{"type": "text", "text": limit_msg}])
            return

    # カードを引く（プレミアムは3枚展開、無料は1枚）
    num_cards = 3 if is_premium else 1
    cards = draw_cards(num_cards)

    # カード表示
    card_display = format_card_display(cards)

    # 質問の判別
    question = ""
    keywords_general = ["占って", "占い", "今日の運勢", "運勢", "タロット"]
    keywords_love = ["恋愛", "恋", "好きな人", "片思い", "復縁", "結婚"]
    keywords_work = ["仕事", "キャリア", "転職", "就職", "ビジネス"]
    keywords_money = ["金運", "お金", "収入", "投資", "財運"]
    keywords_health = ["健康", "体調", "ダイエット"]

    if any(k in text for k in keywords_love):
        question = "恋愛運について"
    elif any(k in text for k in keywords_work):
        question = "仕事運について"
    elif any(k in text for k in keywords_money):
        question = "金運について"
    elif any(k in text for k in keywords_health):
        question = "健康運について"
    elif not any(k in text for k in keywords_general):
        question = text  # ユーザーの質問をそのまま使う

    # AI占い結果を生成
    try:
        reading = await generate_tarot_reading(cards, question)
    except Exception as e:
        print(f"OpenAI API error: {e}")
        reading = "申し訳ありません、星の巡りが乱れているようです...もう一度お試しください🌟"

    # 結果を送信
    spread_type = "スリーカード・スプレッド" if is_premium else "ワンカード・リーディング"
    result_msg = f"🔮 {spread_type}\n\n{card_display}\n\n{'─' * 20}\n\n{reading}"

    if not is_premium:
        remaining = FREE_DAILY_LIMIT - db.get_today_reading_count(user_id) - 1
        result_msg += f"\n\n{'─' * 20}\n📊 本日の残り回数: {max(0, remaining)}回"

    await reply_message(reply_token, [{"type": "text", "text": result_msg}])

    # 履歴を保存
    db.save_reading(user_id, cards, question, reading)


async def handle_premium_request(user_id: str, reply_token: str):
    """プレミアム登録リクエスト"""
    user = db.get_user(user_id)

    if user and user["is_premium"]:
        await reply_message(
            reply_token,
            [{"type": "text", "text": "⭐ すでにプレミアム会員です！\n毎日無制限で占いをお楽しみください🔮✨"}],
        )
        return

    # Stripe Checkout セッションURL を生成
    checkout_url = f"{BASE_URL}/checkout?user_id={user_id}"

    msg = {
        "type": "template",
        "altText": "プレミアム会員のご案内",
        "template": {
            "type": "buttons",
            "title": "⭐ プレミアム会員",
            "text": (
                "月額500円で占い放題！\n\n"
                "✅ 1日の回数制限なし\n"
                "✅ 3枚展開で詳細鑑定\n"
                "✅ 恋愛/仕事/金運を深掘り"
            ),
            "actions": [
                {
                    "type": "uri",
                    "label": "💎 プレミアムに登録する",
                    "uri": checkout_url,
                }
            ],
        },
    }
    await reply_message(reply_token, [msg])


async def handle_status(user_id: str, reply_token: str):
    """ユーザーステータス表示"""
    user = db.get_user(user_id)
    if not user:
        db.upsert_user(user_id)
        user = db.get_user(user_id)

    total = db.get_total_reading_count(user_id)
    today = db.get_today_reading_count(user_id)

    if user["is_premium"]:
        plan = "⭐ プレミアム会員"
        limit_info = "回数制限なし ♾️"
    else:
        plan = "🆓 無料プラン"
        remaining = max(0, FREE_DAILY_LIMIT - today)
        limit_info = f"本日の残り: {remaining}/{FREE_DAILY_LIMIT}回"

    status_msg = (
        f"📊 あなたのステータス\n\n"
        f"プラン: {plan}\n"
        f"{limit_info}\n"
        f"累計占い回数: {total}回\n\n"
        f"{'「プレミアム」で会員登録 💎' if not user['is_premium'] else '毎日の占いをお楽しみください ✨'}"
    )
    await reply_message(reply_token, [{"type": "text", "text": status_msg}])


async def handle_cancel(user_id: str, reply_token: str):
    """サブスク解約"""
    user = db.get_user(user_id)

    if not user or not user["is_premium"]:
        await reply_message(
            reply_token,
            [{"type": "text", "text": "現在、有料プランには加入していません。"}],
        )
        return

    # Stripeサブスクリプションをキャンセル
    if user.get("stripe_subscription_id"):
        try:
            stripe.Subscription.modify(
                user["stripe_subscription_id"], cancel_at_period_end=True
            )
            msg = (
                "📋 解約手続きを受け付けました\n\n"
                "現在の請求期間の終了まで引き続きプレミアム機能をご利用いただけます。\n"
                "ご利用ありがとうございました 🙏"
            )
        except Exception as e:
            print(f"Stripe cancel error: {e}")
            msg = "解約処理中にエラーが発生しました。もう一度お試しください。"
    else:
        msg = "解約処理中にエラーが発生しました。サポートにお問い合わせください。"

    await reply_message(reply_token, [{"type": "text", "text": msg}])


async def handle_help(reply_token: str):
    """ヘルプメッセージ"""
    help_msg = (
        "📖 使い方ガイド\\n\\n"
        "【占いコマンド】\\n"
        "🔮「占って」→ 今日の総合運勢\\n"
        "💕「恋愛占い」→ 恋愛運\\n"
        "💼「仕事運」→ 仕事・キャリア運\\n"
        "💰「金運」→ 金運\\n"
        "🏥「健康運」→ 健康運\\n"
        "❓ 自由に質問を入力 → その悩みを占う\\n\\n"
        "【その他】\\n"
        "📊「ステータス」→ 利用状況\\n"
        "⭐「プレミアム」→ 有料プラン案内\\n"
        "❌「解約」→ サブスク解約\\n"
    )

    await reply_message(reply_token, [{"type": "text", "text": help_msg}])


# ─── LINE Webhook エンドポイント ─────────────────────────────
@app.post("/webhook")
async def webhook(request: Request, x_line_signature: str = Header(None)):
    """LINE Webhook受信"""
    body = await request.body()

    # 署名検証
    if x_line_signature and LINE_CHANNEL_SECRET:
        if not verify_signature(body, x_line_signature):
            raise HTTPException(status_code=400, detail="Invalid signature")

    data = json.loads(body)

    for event in data.get("events", []):
        user_id = event.get("source", {}).get("userId", "")
        reply_token = event.get("replyToken", "")

        if event["type"] == "follow":
            await handle_follow(user_id, reply_token)

        elif event["type"] == "message":
            msg = event.get("message", {})
            if msg.get("type") == "text":
                await handle_text_message(user_id, msg["text"], reply_token)

    return JSONResponse(content={"status": "ok"})


# ─── Stripe Checkout ─────────────────────────────────────────
@app.get("/checkout")
async def checkout(user_id: str):
    """Stripe Checkoutセッション作成 → リダイレクト"""
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{"price": STRIPE_PRICE_ID, "quantity": 1}],
            mode="subscription",
            success_url=f"{BASE_URL}/checkout/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{BASE_URL}/checkout/cancel",
            metadata={"line_user_id": user_id},
        )
        return RedirectResponse(url=session.url)
    except Exception as e:
        print(f"Stripe checkout error: {e}")
        return JSONResponse(
            content={"error": "決済ページの作成に失敗しました"}, status_code=500
        )


@app.get("/checkout/success")
async def checkout_success():
    """決済成功ページ"""
    return JSONResponse(
        content={
            "message": "✅ プレミアム登録が完了しました！LINEに戻って占いをお楽しみください 🔮✨"
        }
    )


@app.get("/checkout/cancel")
async def checkout_cancel():
    """決済キャンセルページ"""
    return JSONResponse(content={"message": "決済がキャンセルされました。LINEに戻ってお試しください。"})


# ─── Stripe Webhook ──────────────────────────────────────────
@app.post("/stripe/webhook")
async def stripe_webhook(request: Request):
    """Stripe Webhook受信 - 課金状態の更新"""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        raise HTTPException(status_code=400, detail="Invalid webhook")

    # チェックアウト完了
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        line_user_id = session.get("metadata", {}).get("line_user_id")
        subscription_id = session.get("subscription")
        customer_id = session.get("customer")

        if line_user_id:
            db.upgrade_to_premium(line_user_id, subscription_id, customer_id)
            await push_message(
                line_user_id,
                [
                    {
                        "type": "text",
                        "text": (
                            "🎉 プレミアム登録完了！\n\n"
                            "✅ 占い回数が無制限になりました\n"
                            "✅ 3枚展開の詳細鑑定が可能に\n\n"
                            "さっそく占ってみましょう🔮✨"
                        ),
                    }
                ],
            )

    # サブスクリプション削除（期間終了）
    elif event["type"] == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        subscription_id = subscription["id"]
        db.downgrade_from_premium(subscription_id)

    # 支払い失敗
    elif event["type"] == "invoice.payment_failed":
        invoice = event["data"]["object"]
        subscription_id = invoice.get("subscription")
        if subscription_id:
            user = db.get_user_by_subscription(subscription_id)
            if user:
                await push_message(
                    user["line_user_id"],
                    [
                        {
                            "type": "text",
                            "text": (
                                "⚠️ お支払いに失敗しました\n\n"
                                "カード情報をご確認ください。\n"
                                "お支払いが確認できない場合、プレミアム機能が停止されます。"
                            ),
                        }
                    ],
                )

    return JSONResponse(content={"status": "ok"})


# ─── ヘルスチェック ─────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok", "service": "LINE Tarot Bot 🔮"}


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8080, reload=True)

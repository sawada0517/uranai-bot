"""
🔮 LINE タロット占いボット - メインアプリケーション
LINE Messaging API + OpenAI GPT + Stripe サブスク課金
v2: カテゴリヘッダー、ローディングメッセージ、結果後Quick Reply追加
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
from prompts import build_tarot_prompt, build_system_prompt
from flex_messages import build_card_flex_message, build_spread_flex_message
from growth import (
    get_level_info, is_category_unlocked,
    build_reading_footer, build_status_message,
    build_levelup_message, build_lock_message,
    detect_category,
)

load_dotenv()

# ─── 環境変数 ─────────────────────────────────────────────
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID", "")
BASE_URL = os.getenv("BASE_URL", "https://your-domain.com")

FREE_DAILY_LIMIT = int(os.getenv("FREE_DAILY_LIMIT", "10"))

stripe.api_key = STRIPE_SECRET_KEY

# ─── アプリ初期化 ──────────────────────────────────────────
db = Database()


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.initialize()
    yield


app = FastAPI(title="LINE タロット占いボット 🔮", lifespan=lifespan)


# ─── カテゴリヘッダー定義 ──────────────────────────────────
CATEGORY_HEADERS = {
    "総合運": "🔮 今日の総合運鑑定",
    "恋愛運": "💕 恋愛運の鑑定",
    "仕事運": "💼 仕事運の鑑定",
    "金運": "💰 金運の鑑定",
    "健康運": "🌿 健康運の鑑定",
    "自由質問": "🌟 あなたの相談への鑑定",
}

# ─── ローディングメッセージのバリエーション ──────────────
LOADING_MESSAGES = [
    "アルカが星を読んでいるよ…✨\n少し待っててね🌙",
    "カードたちがざわめいてる…🔮\nあなたの運命が見えてくるよ✨",
    "星々があなたを照らし始めたよ🌟\nもうちょっと待ってね…",
    "うーん…見えてきた…！🔮\nアルカが解読中だよ✨",
    "宇宙からのメッセージが届いてる…🌙\nもう少しで読み解けるよ✨",
]


# ─── LINE 署名検証 ─────────────────────────────────────────
def verify_signature(body: bytes, signature: str) -> bool:
    hash_value = hmac.new(
        LINE_CHANNEL_SECRET.encode("utf-8"), body, hashlib.sha256
    ).digest()
    expected = base64.b64encode(hash_value).decode("utf-8")
    return hmac.compare_digest(expected, signature)


# ─── LINE メッセージ送信 ────────────────────────────────────
async def reply_message(reply_token: str, messages: list[dict]):
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
    async with httpx.AsyncClient() as client:
        await client.post(
            "https://api.line.me/v2/bot/message/push",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
            },
            json={"to": user_id, "messages": messages},
        )


# ─── 占い後のQuick Reply ────────────────────────────────────
def build_after_reading_quick_reply(level_info: dict, is_premium: bool) -> dict:
    """占い結果の後に表示するQuick Reply"""
    items = [
        {"type": "action", "action": {"type": "message", "label": "🔮 もう一度占う", "text": "占って"}},
    ]

    # アンロックされているカテゴリだけ表示
    level = level_info["level"]
    if level >= 2:
        items.append({"type": "action", "action": {"type": "message", "label": "💕 恋愛運", "text": "恋愛運"}})
    if level >= 3:
        items.append({"type": "action", "action": {"type": "message", "label": "💼 仕事運", "text": "仕事運"}})
    if level >= 4:
        items.append({"type": "action", "action": {"type": "message", "label": "💰 金運", "text": "金運"}})
    if level >= 5:
        items.append({"type": "action", "action": {"type": "message", "label": "🌿 健康運", "text": "健康運"}})

    items.append({"type": "action", "action": {"type": "message", "label": "📊 ステータス", "text": "ステータス"}})

    if not is_premium:
        items.append({"type": "action", "action": {"type": "message", "label": "⭐ Premium", "text": "プレミアム"}})

    return {"items": items[:13]}  # LINEの上限は13個


# ─── OpenAI でタロット占い生成 ──────────────────────────────
async def generate_tarot_reading(
    cards: list[dict],
    question: str = "",
    user_info: dict | None = None,
    level_info: dict | None = None,
    drill_down: dict | None = None,
    last_feedback: str | None = None,
    # TODO(engineer): drill_downはDBから取得した深掘り情報を渡してください
    # TODO(engineer): last_feedbackはDBから取得した前回フィードバック値を渡してください
    # 値は "good" / "maybe" / "miss" のいずれか
) -> str:
    prompt = build_tarot_prompt(cards, question, user_info, drill_down, last_feedback)
    system_prompt = build_system_prompt(level_info) if level_info else (
        "あなたは神秘的で温かみのあるタロット占い師です。"
        "日本語で具体的で行動可能な占い結果を伝えてください。"
    )

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
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 800,
                "temperature": 0.9,
            },
        )
        data = response.json()
        return data["choices"][0]["message"]["content"]


# ─── メッセージハンドラ ────────────────────────────────────
async def handle_follow(user_id: str, reply_token: str):
    db.upsert_user(user_id)

    arca_video = {
        "type": "video",
        "originalContentUrl": "https://sawada3.com/uranai-bot/onboarding.mp4",
        "previewImageUrl": "https://sawada3.com/uranai-bot/onboarding_thumb.jpg",
    }

    welcome = {
        "type": "text",
        "text": (
            "🔮 Arcanaへようこそ！\n\n"
            "わたしはアルカ、見習いタロット占い師です✨\n"
            "あなたと一緒に成長していきたいの！\n\n"
            "占えば占うほどアルカの力が目覚めて、\n"
            "鑑定の精度がどんどん上がっていくよ🌟\n\n"
            "まずは生年月日を教えてね！\n"
            "(例: 1990/04/28)\n\n"
            f"🆓 無料：1日{FREE_DAILY_LIMIT}回\n"
            "⭐ Premium(月額500円)：無制限＋育成加速\n"
        ),
    }

    await reply_message(reply_token, [arca_video, welcome])


async def handle_unfollow(user_id: str):
    db.delete_user(user_id)


def _parse_birth_date(text: str) -> str | None:
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
    text_lower = text.strip().lower()

    # ── オンボーディング ──
    user = db.get_user(user_id)
    if user:
        step = user.get("onboarding_step", 0)

        if step == 1:
            birth_date = _parse_birth_date(text)
            if not birth_date:
                await reply_message(reply_token, [{"type": "text", "text": (
                    "うーん、うまく読み取れなかった…💦\n"
                    "1990/03/15 みたいに入力してくれると嬉しいな🌟"
                )}])
                return
            db.update_birth_date(user_id, birth_date)
            await reply_message(reply_token, [{
                "type": "text",
                "text": "ありがとう✨ もうひとつだけ教えてね！\n性別を選んでくれる？",
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
                    "text": "下のボタンから選んでくれると嬉しいな🌟",
                    "quickReply": {"items": [
                        {"type": "action", "action": {"type": "message", "label": "男性", "text": "男性"}},
                        {"type": "action", "action": {"type": "message", "label": "女性", "text": "女性"}},
                        {"type": "action", "action": {"type": "message", "label": "その他", "text": "その他"}},
                    ]},
                }])
                return
            db.update_gender(user_id, text.strip())
            db.set_onboarding_step(user_id, 3)
            await reply_message(reply_token, [{
                "type": "text",
                "text": "ありがとう✨ もうひとつだけ！\nどのジャンルから占い始める？🌟\n\n占えば占うほどアルカの精度が上がっていくよ✨",
                "quickReply": {"items": [
                    {"type": "action", "action": {"type": "message", "label": "💕 恋愛運", "text": "恋愛運"}},
                    {"type": "action", "action": {"type": "message", "label": "💼 仕事運", "text": "仕事運"}},
                    {"type": "action", "action": {"type": "message", "label": "💰 金運", "text": "金運"}},
                    {"type": "action", "action": {"type": "message", "label": "🌿 健康運", "text": "健康運"}},
                    {"type": "action", "action": {"type": "message", "label": "🔮 総合運", "text": "占って"}},
                ]},
            }])
            return

        if step == 3:
            valid_categories = ("恋愛運", "仕事運", "金運", "健康運", "占って")
            if text.strip() not in valid_categories:
                await reply_message(reply_token, [{
                    "type": "text",
                    "text": "下のボタンから選んでくれると嬉しいな🌟",
                    "quickReply": {"items": [
                        {"type": "action", "action": {"type": "message", "label": "💕 恋愛運", "text": "恋愛運"}},
                        {"type": "action", "action": {"type": "message", "label": "💼 仕事運", "text": "仕事運"}},
                        {"type": "action", "action": {"type": "message", "label": "💰 金運", "text": "金運"}},
                        {"type": "action", "action": {"type": "message", "label": "🌿 健康運", "text": "健康運"}},
                        {"type": "action", "action": {"type": "message", "label": "🔮 総合運", "text": "占って"}},
                    ]},
                }])
                return
            db.set_onboarding_step(user_id, 0)
            await handle_tarot_reading(user_id, text.strip(), reply_token)
            return

    if text_lower in ("プレミアム", "premium", "サブスク", "課金", "登録"):
        await handle_premium_request(user_id, reply_token)
        return

    if text_lower in ("状況", "ステータス", "status", "マイページ"):
        await handle_status(user_id, reply_token)
        return

    if text_lower in ("解約", "退会", "キャンセル", "cancel"):
        await handle_cancel(user_id, reply_token)
        return

    if text_lower in ("ヘルプ", "help", "使い方"):
        await handle_help(reply_token)
        return

    if text_lower in ("通知オン", "通知on"):
        db.set_morning_notify(user_id, True)
        await reply_message(reply_token, [{"type": "text", "text": (
            "やったー！🌟\n"
            "毎朝7時にアルカから星座占いを\n"
            "お届けするね✨\n\n"
            "変更したいときは「通知オフ」と送ってね"
        )}])
        return

    if text_lower in ("通知オフ", "通知off"):
        db.set_morning_notify(user_id, False)
        await reply_message(reply_token, [{"type": "text", "text": (
            "わかった、お知らせしないようにするね🌙\n\n"
            "また受け取りたくなったら\n"
            "「通知オン」と送ってね✨"
        )}])
        return

    await handle_tarot_reading(user_id, text, reply_token)


async def handle_tarot_reading(user_id: str, text: str, reply_token: str):
    user = db.get_user(user_id)
    if not user:
        db.upsert_user(user_id)
        user = db.get_user(user_id)

    # ── フィードバック確認（次回占う前に前回の評価を聞く）──
    # TODO(engineer): db.get_pending_feedback(user_id) を実装してください
    # 戻り値: {"reading_id": str, "pending": bool} | None
    # pending=Trueの場合、以下のQuick Replyを表示してからreturnしてください
    #
    # await reply_message(reply_token, [{
    #     "type": "text",
    #     "text": "前回の占い、どうだった？🌙\nアルカ、気になってたんだ✨",
    #     "quickReply": {"items": [
    #         {"type": "action", "action": {"type": "message", "label": "✨ すごく当たってた", "text": "feedback_good"}},
    #         {"type": "action", "action": {"type": "message", "label": "🌙 なんとなく当たってた", "text": "feedback_maybe"}},
    #         {"type": "action", "action": {"type": "message", "label": "🌀 ちょっと違ったかも", "text": "feedback_miss"}},
    #     ]},
    # }])
    # return
    #
    # フィードバック受信時（text が "feedback_good/maybe/miss" の場合）:
    # db.save_feedback(user_id, reading_id, feedback_value) を実装してください
    # 保存後: last_feedback をgenerate_tarot_reading()に渡してください

    # ── 初回：オンボーディング ──
    if not user.get("birth_date"):
        db.set_onboarding_step(user_id, 1)
        await reply_message(reply_token, [{"type": "text", "text": (
            "占う前にちょっとだけ教えてほしいの🔮\n\n"
            "あなたの生年月日を教えてね！\n"
            "(例: 1990/03/15)"
        )}])
        return

    is_premium = user["is_premium"]
    total_before = db.get_total_reading_count(user_id)
    level_info = get_level_info(total_before)

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

    # カテゴリ判定
    category = detect_category(text)

    # カテゴリロックチェック
    if category != "自由質問" and not is_category_unlocked(total_before, category):
        lock_msg = build_lock_message(category, total_before, is_premium)
        await reply_message(reply_token, [{"type": "text", "text": lock_msg}])
        return

    # ✨ ローディングメッセージを先に送信（reply_messageで）
    loading_text = random.choice(LOADING_MESSAGES)
    await reply_message(reply_token, [{"type": "text", "text": loading_text}])

    # カードを引く
    num_cards = 3 if is_premium else 1
    cards = draw_cards(num_cards)

    # questionの設定
    from growth import CATEGORY_MAP
    if category == "自由質問":
        question = text
    elif category == "総合運":
        question = ""
    else:
        question = CATEGORY_MAP[category]["question"]

    # AI占い結果を生成
    try:
        reading = await generate_tarot_reading(cards, question, user_info=user, level_info=level_info)
    except Exception as e:
        print(f"OpenAI API error: {e}")
        reading = "申し訳ありません、星の巡りが乱れているようです...もう一度お試しください🌟"

    # 履歴を保存
    db.save_reading(user_id, cards, question, reading)
    total_after = db.get_total_reading_count(user_id)

    # ✨ カテゴリヘッダー + 鑑定結果
    header = CATEGORY_HEADERS.get(category, "🔮 鑑定結果")
    today_remaining = FREE_DAILY_LIMIT - db.get_today_reading_count(user_id) if not is_premium else 0
    footer = build_reading_footer(total_after, is_premium, today_remaining)
    reading_text = f"{header}\n\n{reading}\n\n{footer}"

    # Flex Message + テキスト送信（push_messageで）
    if num_cards == 1:
        flex_msg = build_card_flex_message(cards[0])
    else:
        flex_msg = build_spread_flex_message(cards)

    # ✨ Quick Reply付きの結果メッセージ
    text_msg = {
        "type": "text",
        "text": reading_text,
        "quickReply": build_after_reading_quick_reply(get_level_info(total_after), is_premium),
    }

    # ローディング後はpush_messageで送信
    await push_message(user_id, [flex_msg, text_msg])

    # レベルアップ通知
    levelup_msg = build_levelup_message(total_before, total_after)
    if levelup_msg:
        await push_message(user_id, [{"type": "text", "text": levelup_msg}])

    # ── 初回占い完了後：朝の星座通知オプトイン ──
    if total_after == 1:
        await push_message(user_id, [{
            "type": "text",
            "text": (
                "ねえねえ、ひとつ聞いてもいい？🌙\n\n"
                "毎朝7時に今日の星座占いを\n"
                "アルカからお届けすることができるんだけど…\n"
                "受け取る？✨"
            ),
            "quickReply": {"items": [
                {"type": "action", "action": {"type": "message", "label": "✅ 受け取る", "text": "通知オン"}},
                {"type": "action", "action": {"type": "message", "label": "🙅 いらない", "text": "通知オフ"}},
            ]},
        }])


async def handle_premium_request(user_id: str, reply_token: str):
    user = db.get_user(user_id)

    if user and user["is_premium"]:
        await reply_message(
            reply_token,
            [{"type": "text", "text": "⭐ すでにプレミアム会員です！\n毎日無制限で占いをお楽しみください🔮✨"}],
        )
        return

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
    user = db.get_user(user_id)
    if not user:
        db.upsert_user(user_id)
        user = db.get_user(user_id)

    total = db.get_total_reading_count(user_id)
    today = db.get_today_reading_count(user_id)
    today_remaining = max(0, FREE_DAILY_LIMIT - today) if not user["is_premium"] else 0

    status_msg = build_status_message(total, user["is_premium"], today_remaining)
    await reply_message(reply_token, [{"type": "text", "text": status_msg}])


async def handle_cancel(user_id: str, reply_token: str):
    user = db.get_user(user_id)

    if not user or not user["is_premium"]:
        await reply_message(
            reply_token,
            [{"type": "text", "text": "現在、有料プランには加入していません。"}],
        )
        return

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
    help_msg = (
        "📖 使い方ガイド\n\n"
        "【占いコマンド】\n"
        '🔮「占って」→ 今日の総合運勢\n'
        '💕「恋愛占い」→ 恋愛運\n'
        '💼「仕事運」→ 仕事・キャリア運\n'
        '💰「金運」→ 金運\n'
        '🏥「健康運」→ 健康運\n'
        "❓ 自由に質問を入力 → その悩みを占う\n\n"
        "【その他】\n"
        '📊「ステータス」→ 利用状況\n'
        '⭐「プレミアム」→ 有料プラン案内\n'
        '❌「解約」→ サブスク解約\n'
        '\n【通知設定】\n'
        '🌅「通知オン」→ 毎朝7時の星座占いを受け取る\n'
        '🔕「通知オフ」→ 朝の通知を止める\n'
    )
    await reply_message(reply_token, [{"type": "text", "text": help_msg}])


# ─── LINE Webhook エンドポイント ─────────────────────────────
@app.post("/webhook")
async def webhook(request: Request, x_line_signature: str = Header(None)):
    body = await request.body()

    if x_line_signature and LINE_CHANNEL_SECRET:
        if not verify_signature(body, x_line_signature):
            raise HTTPException(status_code=400, detail="Invalid signature")

    data = json.loads(body)

    for event in data.get("events", []):
        user_id = event.get("source", {}).get("userId", "")
        reply_token = event.get("replyToken", "")

        if event["type"] == "follow":
            await handle_follow(user_id, reply_token)

        elif event["type"] == "unfollow":
            await handle_unfollow(user_id)

        elif event["type"] == "message":
            msg = event.get("message", {})
            if msg.get("type") == "text":
                await handle_text_message(user_id, msg["text"], reply_token)

    return JSONResponse(content={"status": "ok"})


# ─── Stripe Checkout ─────────────────────────────────────────
@app.get("/checkout")
async def checkout(user_id: str):
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
    return JSONResponse(
        content={
            "message": "✅ プレミアム登録が完了しました！LINEに戻って占いをお楽しみください 🔮✨"
        }
    )


@app.get("/checkout/cancel")
async def checkout_cancel():
    return JSONResponse(content={"message": "決済がキャンセルされました。LINEに戻ってお試しください。"})


# ─── Stripe Webhook ──────────────────────────────────────────
@app.post("/stripe/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        raise HTTPException(status_code=400, detail="Invalid webhook")

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

    elif event["type"] == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        subscription_id = subscription["id"]
        db.downgrade_from_premium(subscription_id)

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
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

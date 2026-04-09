"""
🌅 朝の星座通知スクリプト

morning_notify=1 のユーザー全員に今日の総合運をLINE pushで送信する。
毎朝7時にcronで実行する想定。

使い方:
    python morning_notify.py

VPS crontab設定例:
    0 7 * * * cd /home/uranai-bot && /home/uranai-bot/venv/bin/python morning_notify.py >> /var/log/uranai-bot/morning_notify.log 2>&1
"""

import asyncio
import os

import httpx
from dotenv import load_dotenv

from database import Database
from growth import get_level_info, build_reading_footer
from prompts import build_tarot_prompt, build_system_prompt
from tarot_cards import draw_cards, format_card_display

load_dotenv()

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

db = Database()


async def generate_morning_reading(user: dict) -> str:
    cards = draw_cards(3)
    question = "今日の総合運"
    total_readings = db.get_total_reading_count(user["line_user_id"])
    level_info = get_level_info(total_readings)

    prompt = build_tarot_prompt(cards, question, user_info=user)
    system_prompt = build_system_prompt(level_info)

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
                "max_tokens": 600,
                "temperature": 0.9,
            },
        )
        data = response.json()
        reading_text = data["choices"][0]["message"]["content"]

    card_display = format_card_display(cards)
    total_readings_after = total_readings + 1
    footer = build_reading_footer(
        total_readings_after,
        is_premium=False,
        today_remaining=0,
    )

    db.save_reading(user["line_user_id"], cards, question, reading_text)

    return f"🌅 おはよう！今日の星を読んだよ✨\n\n{card_display}\n\n{reading_text}\n\n{footer}"


async def push_message(user_id: str, text: str):
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            "https://api.line.me/v2/bot/message/push",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
            },
            json={
                "to": user_id,
                "messages": [{"type": "text", "text": text}],
            },
        )
        if resp.status_code != 200:
            print(f"  ⚠️ push失敗 ({resp.status_code}): {resp.text}")


async def notify_user(user: dict):
    user_id = user["line_user_id"]
    try:
        message = await generate_morning_reading(user)
        await push_message(user_id, message)
        print(f"  ✅ 送信完了: {user_id}")
    except Exception as e:
        print(f"  ❌ 送信失敗: {user_id} - {e}")


async def main():
    users = db.get_morning_notify_users()
    print(f"🌅 朝の通知開始: {len(users)}人に送信")

    if not users:
        print("通知対象ユーザーなし")
        return

    # 同時送信数を制限（LINE APIのレート制限対策）
    semaphore = asyncio.Semaphore(5)

    async def notify_with_limit(user):
        async with semaphore:
            await notify_user(user)

    await asyncio.gather(*[notify_with_limit(u) for u in users])
    print(f"✅ 送信完了: {len(users)}人")


if __name__ == "__main__":
    asyncio.run(main())

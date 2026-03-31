# 育成システム組み込みガイド（エンジニア向け）

## 追加ファイル
- `growth.py` — 育成レベル・プログレスバー・メッセージ生成
- `prompts.py` — 既存を置き換え（build_system_prompt を追加）

## app.py への変更（最小限）

### 1. import追加（26行目付近）

```python
from growth import (
    get_level_info,
    is_category_unlocked,
    detect_category,
    build_reading_footer,
    build_status_message,
    build_levelup_message,
    build_lock_message,
    CATEGORY_MAP,
)
from prompts import build_tarot_prompt, build_system_prompt
```

### 2. generate_tarot_reading を変更（94行目付近）

```python
async def generate_tarot_reading(cards: list[dict], question: str = "", level_info: dict = None) -> str:
    """OpenAI GPTでタロット占いの結果を生成"""
    prompt = build_tarot_prompt(cards, question)
    system_prompt = build_system_prompt(level_info) if level_info else (
        "あなたは神秘的で温かみのあるタロット占い師です。"
        "日本語で占い結果を伝えてください。"
        "絵文字を適度に使い、親しみやすく、でも神秘的な雰囲気を保ってください。"
        "結果は400文字以内に収めてください。"
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
                "max_tokens": 600,
                "temperature": 0.9,
            },
        )
        data = response.json()
        return data["choices"][0]["message"]["content"]
```

### 3. handle_tarot_reading を変更（174行目付近）

```python
async def handle_tarot_reading(user_id: str, text: str, reply_token: str):
    """タロット占いを実行（育成システム対応）"""
    user = db.get_user(user_id)
    if not user:
        db.upsert_user(user_id)
        user = db.get_user(user_id)

    is_premium = user["is_premium"]
    total_readings = db.get_total_reading_count(user_id)
    level_info = get_level_info(total_readings)

    # ── カテゴリ判定 ──
    category = detect_category(text)

    # ── カテゴリロック判定 ──
    if category != "自由質問" and not is_category_unlocked(total_readings, category):
        lock_msg = build_lock_message(category, total_readings, is_premium)
        await reply_message(reply_token, [{"type": "text", "text": lock_msg}])
        return

    # ── 無料ユーザーの回数チェック ──
    if not is_premium:
        today_count = db.get_today_reading_count(user_id)
        if today_count >= FREE_DAILY_LIMIT:
            limit_msg = (
                "🔒 今日の無料占いは使い切っちゃった…\n\n"
                "⭐ Premiumなら毎日何度でも占えるよ！\n"
                "月額500円でアルカの育成も加速✨\n\n"
                "「プレミアム」と送って詳細をチェック💎"
            )
            await reply_message(reply_token, [{"type": "text", "text": limit_msg}])
            return

    # ── カードを引く ──
    num_cards = 3 if is_premium else 1
    cards = draw_cards(num_cards)

    # ── 質問テキスト ──
    if category == "自由質問":
        question = text
    elif category in CATEGORY_MAP:
        question = CATEGORY_MAP[category]["question"]
    else:
        question = ""

    # ── AI占い結果を生成（レベル情報を渡す）──
    try:
        reading = await generate_tarot_reading(cards, question, level_info)
    except Exception as e:
        print(f"OpenAI API error: {e}")
        reading = "ごめんなさい、星の巡りが乱れてうまく読めなかった…もう一度試してみて🌟"

    # ── 結果を送信（既存のFlex Message + テキスト）──
    if num_cards == 1:
        flex_msg = build_card_flex_message(cards[0])
    else:
        flex_msg = build_spread_flex_message(cards)

    # プログレスバー付きフッター
    today_remaining = 0
    if not is_premium:
        today_remaining = max(0, FREE_DAILY_LIMIT - db.get_today_reading_count(user_id) - 1)

    footer = build_reading_footer(total_readings + 1, is_premium, today_remaining)
    reading_text = f"🔮 鑑定結果\n\n{reading}\n\n{footer}"

    messages = [flex_msg, {"type": "text", "text": reading_text}]
    await reply_message(reply_token, messages)

    # ── 履歴を保存 ──
    before_count = total_readings
    db.save_reading(user_id, cards, question, reading)
    after_count = before_count + 1

    # ── レベルアップ通知 ──
    levelup_msg = build_levelup_message(before_count, after_count)
    if levelup_msg:
        await push_message(user_id, [{"type": "text", "text": levelup_msg}])
```

### 4. handle_status を変更（285行目付近）

```python
async def handle_status(user_id: str, reply_token: str):
    """ユーザーステータス表示（育成情報込み）"""
    user = db.get_user(user_id)
    if not user:
        db.upsert_user(user_id)
        user = db.get_user(user_id)

    total = db.get_total_reading_count(user_id)
    today = db.get_today_reading_count(user_id)
    is_premium = user["is_premium"]

    today_remaining = max(0, FREE_DAILY_LIMIT - today) if not is_premium else 0
    status_msg = build_status_message(total, is_premium, today_remaining)

    await reply_message(reply_token, [{"type": "text", "text": status_msg}])
```

### 5. handle_follow を変更（128行目付近）

```python
async def handle_follow(user_id: str, reply_token: str):
    """友だち追加時の処理"""
    db.upsert_user(user_id)
    welcome = (
        "🔮 Arcanaへようこそ！\n\n"
        "わたしはアルカ、見習いタロット占い師です✨\n"
        "あなたと一緒に成長していきたいの！\n\n"
        "今はまだ「総合運」しか占えないけど、\n"
        "たくさん占うほど、わたしの力が目覚めて\n"
        "恋愛運・仕事運・金運…と占えるようになるよ🌟\n\n"
        "下のメニューから「総合運」をタップして、\n"
        "さっそく始めましょう！\n\n"
        f"🆓 無料：1日{FREE_DAILY_LIMIT}回\n"
        "⭐ Premium（月額500円）：無制限＋育成加速\n"
    )
    await reply_message(reply_token, [{"type": "text", "text": welcome}])
```

## 注意事項
- database.py は変更不要（get_total_reading_count が既にある）
- flex_messages.py は変更不要（そのまま使える）
- tarot_cards.py は変更不要

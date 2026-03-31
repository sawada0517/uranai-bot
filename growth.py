"""
🌱 Arcana 育成システム - growth.py
レベル管理・プログレスバー・メッセージ生成

app.py からは以下のように使う:
  from growth import (
      get_level_info, is_category_unlocked,
      build_reading_footer, build_status_message,
      build_levelup_message, build_lock_message,
      detect_category, CATEGORY_MAP,
  )
"""

# ─── レベル定義 ───────────────────────────────────────────
LEVELS = [
    {
        "level": 1,
        "required_readings": 0,
        "unlocked_categories": ["総合運"],
        "title": "見習い占い師",
    },
    {
        "level": 2,
        "required_readings": 10,
        "unlocked_categories": ["総合運", "恋愛運"],
        "title": "恋の星読み",
    },
    {
        "level": 3,
        "required_readings": 30,
        "unlocked_categories": ["総合運", "恋愛運", "仕事運"],
        "title": "運命の導き手",
    },
    {
        "level": 4,
        "required_readings": 60,
        "unlocked_categories": ["総合運", "恋愛運", "仕事運", "金運"],
        "title": "星詠みの賢者",
    },
    {
        "level": 5,
        "required_readings": 100,
        "unlocked_categories": ["総合運", "恋愛運", "仕事運", "金運", "健康運"],
        "title": "大アルカナの使い手",
    },
    {
        "level": 6,
        "required_readings": 200,
        "unlocked_categories": ["総合運", "恋愛運", "仕事運", "金運", "健康運", "相性占い"],
        "title": "伝説のアルカニスト",
    },
]

# ─── カテゴリ定義 ──────────────────────────────────────────
CATEGORY_MAP = {
    "総合運": {
        "keywords": ["占って", "占い", "今日の運勢", "運勢", "タロット", "総合運"],
        "question": "",
        "emoji": "🔮",
    },
    "恋愛運": {
        "keywords": ["恋愛運", "恋愛", "恋", "好きな人", "片思い", "復縁", "結婚"],
        "question": "恋愛運について",
        "emoji": "💕",
    },
    "仕事運": {
        "keywords": ["仕事運", "仕事", "キャリア", "転職", "就職", "ビジネス"],
        "question": "仕事運について",
        "emoji": "💼",
    },
    "金運": {
        "keywords": ["金運", "お金", "収入", "投資", "財運"],
        "question": "金運について",
        "emoji": "💰",
    },
    "健康運": {
        "keywords": ["健康運", "健康", "体調", "ダイエット"],
        "question": "健康運について",
        "emoji": "🌿",
    },
    "相性占い": {
        "keywords": ["相性", "相性占い", "二人の相性"],
        "question": "二人の相性について",
        "emoji": "✨",
    },
}

# カテゴリの絵文字マッピング
CATEGORY_EMOJI = {cat: info["emoji"] for cat, info in CATEGORY_MAP.items()}

# 各カテゴリが解放されるレベル
CATEGORY_UNLOCK_LEVEL = {}
for _lv in LEVELS:
    for _cat in _lv["unlocked_categories"]:
        if _cat not in CATEGORY_UNLOCK_LEVEL:
            CATEGORY_UNLOCK_LEVEL[_cat] = _lv["level"]

# ─── プログレスバー設定 ────────────────────────────────────
BAR_FILLED = "▓"
BAR_EMPTY = "░"
BAR_LENGTH = 20


# ─── レベル判定関数 ────────────────────────────────────────
def get_level_info(total_readings: int) -> dict:
    """累計占い回数からレベル情報を取得"""
    current = LEVELS[0]
    for lv in LEVELS:
        if total_readings >= lv["required_readings"]:
            current = lv
        else:
            break
    return current


def get_next_level_info(total_readings: int) -> dict | None:
    """次のレベル情報を取得（MAXなら None）"""
    for lv in LEVELS:
        if total_readings < lv["required_readings"]:
            return lv
    return None


def is_category_unlocked(total_readings: int, category: str) -> bool:
    """指定カテゴリがアンロック済みか判定"""
    level_info = get_level_info(total_readings)
    return category in level_info["unlocked_categories"]


def get_readings_to_next_level(total_readings: int) -> int | None:
    """次のレベルまでの残り回数（MAXなら None）"""
    next_lv = get_next_level_info(total_readings)
    if next_lv is None:
        return None
    return next_lv["required_readings"] - total_readings


# ─── カテゴリ判定 ──────────────────────────────────────────
def detect_category(text: str) -> str:
    """テキストからカテゴリを判定。一致しなければ総合運"""
    for cat_name, cat_info in CATEGORY_MAP.items():
        if cat_name == "総合運":
            continue
        if any(k in text for k in cat_info["keywords"]):
            return cat_name
    if any(k in text for k in CATEGORY_MAP["総合運"]["keywords"]):
        return "総合運"
    return "自由質問"


# ─── プログレスバー生成 ────────────────────────────────────
def make_progress_bar(current: int, target: int) -> str:
    """テキストプログレスバーを生成"""
    if target <= 0:
        return BAR_FILLED * BAR_LENGTH
    ratio = min(current / target, 1.0)
    filled = round(ratio * BAR_LENGTH)
    empty = BAR_LENGTH - filled
    pct = round(ratio * 100)
    return f"{BAR_FILLED * filled}{BAR_EMPTY * empty} {pct}%"


def make_level_progress_bar(total_readings: int) -> str:
    """現在レベル内での進捗バーを生成"""
    level_info = get_level_info(total_readings)
    next_lv = get_next_level_info(total_readings)

    if next_lv is None:
        return f"{BAR_FILLED * BAR_LENGTH} MAX"

    current_base = level_info["required_readings"]
    next_target = next_lv["required_readings"]
    progress_in_level = total_readings - current_base
    level_range = next_target - current_base

    return make_progress_bar(progress_in_level, level_range)


# ─── メッセージ生成 ────────────────────────────────────────
def build_reading_footer(
    total_readings: int, is_premium: bool, today_remaining: int = 0
) -> str:
    """占い結果のフッターを生成"""
    level_info = get_level_info(total_readings)
    bar = make_level_progress_bar(total_readings)
    remaining = get_readings_to_next_level(total_readings)

    lines = [
        "──────────────────",
        f"👤 Lv.{level_info['level']}「{level_info['title']}」",
        f"🔮 累計: {total_readings}回",
        bar,
    ]

    if remaining is not None:
        lines.append(f"⬆️ Lv.{level_info['level'] + 1}まで あと{remaining}回")
    else:
        lines.append("⬆️ ✨ MAX LEVEL ✨")

    if not is_premium:
        lines.append(f"📊 本日の残り: {max(0, today_remaining)}回")

    lines.append("──────────────────")
    return "\n".join(lines)


def build_status_message(
    total_readings: int, is_premium: bool, today_remaining: int = 0
) -> str:
    """ステータス画面のメッセージを生成"""
    level_info = get_level_info(total_readings)
    bar = make_level_progress_bar(total_readings)
    remaining = get_readings_to_next_level(total_readings)

    # プラン情報
    if is_premium:
        plan_text = "⭐ Premium"
        limit_text = "回数制限なし ♾️"
    else:
        plan_text = "🆓 無料プラン"
        limit_text = f"本日の残り: {max(0, today_remaining)}/1回"

    # レベル進捗
    if remaining is not None:
        next_text = f"⬆️ 次のレベルまで: あと{remaining}回"
    else:
        next_text = "⬆️ ✨ MAX LEVEL ✨"

    # 解放/ロック カテゴリ一覧
    unlocked_lines = []
    locked_lines = []

    all_categories = []
    for lv in LEVELS:
        for cat in lv["unlocked_categories"]:
            if cat not in all_categories:
                all_categories.append(cat)

    for cat in all_categories:
        emoji = CATEGORY_EMOJI.get(cat, "")
        unlock_lv = CATEGORY_UNLOCK_LEVEL.get(cat, "?")
        if is_category_unlocked(total_readings, cat):
            unlocked_lines.append(f"  {emoji} {cat}")
        else:
            locked_lines.append(f"  🔒 {cat}（Lv.{unlock_lv}で解放）")

    unlocked_text = "\n".join(unlocked_lines) if unlocked_lines else "  なし"
    locked_text = "\n".join(locked_lines) if locked_lines else "  なし（全解放！🎉）"

    msg = (
        f"📊 あなたとアルカのステータス\n\n"
        f"👤 Lv.{level_info['level']}「{level_info['title']}」\n"
        f"🔮 累計占い: {total_readings}回\n"
        f"{bar}\n"
        f"{next_text}\n\n"
        f"📋 プラン: {plan_text}\n"
        f"{limit_text}\n\n"
        f"✅ 占えるカテゴリ:\n{unlocked_text}\n\n"
        f"🔒 未解放:\n{locked_text}"
    )

    if not is_premium:
        msg += "\n\n💡「プレミアム」で育成を加速💎"

    return msg


def build_levelup_message(before_count: int, after_count: int) -> str | None:
    """レベルアップ通知メッセージを生成（レベルアップなしならNone）"""
    before_level = get_level_info(before_count)
    after_level = get_level_info(after_count)

    if after_level["level"] <= before_level["level"]:
        return None

    bar = f"{BAR_FILLED * BAR_LENGTH} MAX"

    new_categories = set(after_level["unlocked_categories"]) - set(
        before_level["unlocked_categories"]
    )

    msg = (
        f"🎉 レベルアップ！\n\n"
        f"⬆️ Lv.{after_level['level']}「{after_level['title']}」に成長！\n"
        f"{bar}\n"
    )

    if new_categories:
        for cat in new_categories:
            emoji = CATEGORY_EMOJI.get(cat, "")
            msg += f"\n🆕 {emoji}「{cat}」が占えるようになったよ！"
        msg += "\n"

    # アルカのレベルアップセリフ
    levelup_quotes = {
        2: "恋の星が読めるようになったの…！\nあなたの恋、応援させてね💕",
        3: "見えてきたよ…！\nあなたのキャリアの星も読めるようになった✨",
        4: "だいぶ力がついてきた気がする…！\n金運の流れもわかるようになったよ💰",
        5: "ついに一人前の占い師になれた…！\nあなたのおかげだよ、ありがとう🌿",
        6: "あなたとの絆があるから、\nどんな星も読めるようになったわ✨\n伝説のアルカニスト…これからもよろしくね🔮",
    }

    quote = levelup_quotes.get(after_level["level"], "")
    if quote:
        msg += f"\nアルカ「{quote}」"

    msg += "\n\nこれからもたくさん占って、一緒に成長しよう✨"
    return msg


def build_lock_message(
    category: str, total_readings: int, is_premium: bool
) -> str:
    """カテゴリロック時のメッセージを生成"""
    level_info = get_level_info(total_readings)
    bar = make_level_progress_bar(total_readings)

    unlock_lv = CATEGORY_UNLOCK_LEVEL.get(category, "?")
    unlock_level_data = None
    for lv in LEVELS:
        if lv["level"] == unlock_lv:
            unlock_level_data = lv
            break

    unlock_at = unlock_level_data["required_readings"] if unlock_level_data else 0
    need_more = max(0, unlock_at - total_readings)

    emoji = CATEGORY_EMOJI.get(category, "")

    msg = (
        f"🔒 まだ「{category}」の力が目覚めていないの…\n\n"
        f"👤 Lv.{level_info['level']}「{level_info['title']}」\n"
        f"{bar}\n\n"
        f"{emoji} {category}はLv.{unlock_lv}で解放！\n"
        f"🔮 あと {need_more}回 占うと読めるようになるよ！\n\n"
        "まずは「総合運」で占ってみて！\n"
        "一緒にレベルアップしよう✨"
    )

    if not is_premium:
        msg += (
            "\n\n💡 Premiumなら無制限で占えるから\n"
            "育成がもっと早くなるよ💎"
        )

    return msg

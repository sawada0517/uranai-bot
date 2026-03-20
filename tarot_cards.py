"""
🃏 タロットカードデータ
大アルカナ22枚 + 小アルカナ56枚 = 78枚フルデッキ
"""

import random

# ─── 大アルカナ (Major Arcana) ─────────────────────────────
MAJOR_ARCANA = [
    {"id": 0, "name": "愚者", "name_en": "The Fool", "emoji": "🌟", "type": "major"},
    {"id": 1, "name": "魔術師", "name_en": "The Magician", "emoji": "🪄", "type": "major"},
    {"id": 2, "name": "女教皇", "name_en": "The High Priestess", "emoji": "🌙", "type": "major"},
    {"id": 3, "name": "女帝", "name_en": "The Empress", "emoji": "👑", "type": "major"},
    {"id": 4, "name": "皇帝", "name_en": "The Emperor", "emoji": "🏰", "type": "major"},
    {"id": 5, "name": "教皇", "name_en": "The Hierophant", "emoji": "📿", "type": "major"},
    {"id": 6, "name": "恋人", "name_en": "The Lovers", "emoji": "💕", "type": "major"},
    {"id": 7, "name": "戦車", "name_en": "The Chariot", "emoji": "⚔️", "type": "major"},
    {"id": 8, "name": "力", "name_en": "Strength", "emoji": "🦁", "type": "major"},
    {"id": 9, "name": "隠者", "name_en": "The Hermit", "emoji": "🏔️", "type": "major"},
    {"id": 10, "name": "運命の輪", "name_en": "Wheel of Fortune", "emoji": "🎡", "type": "major"},
    {"id": 11, "name": "正義", "name_en": "Justice", "emoji": "⚖️", "type": "major"},
    {"id": 12, "name": "吊された男", "name_en": "The Hanged Man", "emoji": "🔄", "type": "major"},
    {"id": 13, "name": "死神", "name_en": "Death", "emoji": "🦋", "type": "major"},
    {"id": 14, "name": "節制", "name_en": "Temperance", "emoji": "🌊", "type": "major"},
    {"id": 15, "name": "悪魔", "name_en": "The Devil", "emoji": "⛓️", "type": "major"},
    {"id": 16, "name": "塔", "name_en": "The Tower", "emoji": "⚡", "type": "major"},
    {"id": 17, "name": "星", "name_en": "The Star", "emoji": "⭐", "type": "major"},
    {"id": 18, "name": "月", "name_en": "The Moon", "emoji": "🌕", "type": "major"},
    {"id": 19, "name": "太陽", "name_en": "The Sun", "emoji": "☀️", "type": "major"},
    {"id": 20, "name": "審判", "name_en": "Judgement", "emoji": "📯", "type": "major"},
    {"id": 21, "name": "世界", "name_en": "The World", "emoji": "🌍", "type": "major"},
]

# ─── 小アルカナ (Minor Arcana) ─────────────────────────────
SUITS = {
    "wands": {"name": "ワンド", "emoji": "🪄", "element": "火"},
    "cups": {"name": "カップ", "emoji": "🏆", "element": "水"},
    "swords": {"name": "ソード", "emoji": "🗡️", "element": "風"},
    "pentacles": {"name": "ペンタクル", "emoji": "💰", "element": "地"},
}

COURT_CARDS = {
    "page": "ペイジ",
    "knight": "ナイト",
    "queen": "クイーン",
    "king": "キング",
}

MINOR_ARCANA = []
for suit_key, suit_info in SUITS.items():
    # 数札 (Ace〜10)
    for num in range(1, 11):
        name = f"{suit_info['name']}の{'エース' if num == 1 else str(num)}"
        MINOR_ARCANA.append(
            {
                "id": f"{suit_key}_{num}",
                "name": name,
                "name_en": f"{'Ace' if num == 1 else str(num)} of {suit_key.title()}",
                "emoji": suit_info["emoji"],
                "type": "minor",
                "suit": suit_key,
                "number": num,
            }
        )
    # コートカード
    for court_key, court_name in COURT_CARDS.items():
        name = f"{suit_info['name']}の{court_name}"
        MINOR_ARCANA.append(
            {
                "id": f"{suit_key}_{court_key}",
                "name": name,
                "name_en": f"{court_key.title()} of {suit_key.title()}",
                "emoji": suit_info["emoji"],
                "type": "minor",
                "suit": suit_key,
                "number": court_key,
            }
        )

# 完全なデッキ
TAROT_DECK = MAJOR_ARCANA + MINOR_ARCANA


def draw_cards(num: int = 1) -> list[dict]:
    """
    タロットカードをランダムに引く
    正位置/逆位置もランダムに決定
    """
    selected = random.sample(TAROT_DECK, num)
    result = []
    for card in selected:
        drawn = card.copy()
        drawn["reversed"] = random.choice([True, False])
        drawn["position"] = "逆位置" if drawn["reversed"] else "正位置"
        result.append(drawn)
    return result


def format_card_display(cards: list[dict]) -> str:
    """カードの表示用テキストを生成"""
    if len(cards) == 1:
        card = cards[0]
        position = "🔻 逆位置" if card["reversed"] else "🔺 正位置"
        return f"{card['emoji']} {card['name']}\n（{card['name_en']}）\n{position}"

    # 3枚展開 (過去・現在・未来)
    labels = ["🕐 過去", "🔮 現在", "🔭 未来"]
    lines = []
    for i, card in enumerate(cards):
        position = "逆位置" if card["reversed"] else "正位置"
        label = labels[i] if i < len(labels) else f"カード{i+1}"
        lines.append(f"{label}: {card['emoji']} {card['name']}（{position}）")

    return "\n".join(lines)

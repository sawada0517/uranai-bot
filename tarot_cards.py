"""
🃏 タロットカードデータ
大アルカナ22枚 + 小アルカナ56枚 = 78枚フルデッキ
龍神様タロット - 画像URL対応
"""

import os
import random

# カード画像のベースURL
CARD_IMAGE_BASE_URL = os.getenv(
    "CARD_IMAGE_BASE_URL", "https://sawada3.com/uranai-bot"
)

# ─── 大アルカナ (Major Arcana) ─────────────────────────────
MAJOR_ARCANA = [
    {"id": 0,  "name": "愚者",       "name_en": "The Fool",           "emoji": "🌟", "type": "major", "image_url": f"{CARD_IMAGE_BASE_URL}/001_0_TheFool.jpg"},
    {"id": 1,  "name": "魔術師",     "name_en": "The Magician",        "emoji": "🪄", "type": "major", "image_url": f"{CARD_IMAGE_BASE_URL}/002_1_TheMagician.jpg"},
    {"id": 2,  "name": "女教皇",     "name_en": "The High Priestess",  "emoji": "🌙", "type": "major", "image_url": f"{CARD_IMAGE_BASE_URL}/003_2_TheHighPriestess.jpg"},
    {"id": 3,  "name": "女帝",       "name_en": "The Empress",         "emoji": "👑", "type": "major", "image_url": f"{CARD_IMAGE_BASE_URL}/004_3_TheEmpress.jpg"},
    {"id": 4,  "name": "皇帝",       "name_en": "The Emperor",         "emoji": "🏰", "type": "major", "image_url": f"{CARD_IMAGE_BASE_URL}/005_4_TheEmperor.jpg"},
    {"id": 5,  "name": "教皇",       "name_en": "The Hierophant",      "emoji": "📿", "type": "major", "image_url": f"{CARD_IMAGE_BASE_URL}/006_5_TheHierophant.jpg"},
    {"id": 6,  "name": "恋人",       "name_en": "The Lovers",          "emoji": "💕", "type": "major", "image_url": f"{CARD_IMAGE_BASE_URL}/007_6_TheLovers.jpg"},
    {"id": 7,  "name": "戦車",       "name_en": "The Chariot",         "emoji": "⚔️", "type": "major", "image_url": f"{CARD_IMAGE_BASE_URL}/008_7_TheChariot.jpg"},
    {"id": 8,  "name": "力",         "name_en": "Strength",            "emoji": "🦁", "type": "major", "image_url": f"{CARD_IMAGE_BASE_URL}/009_8_Strength.jpg"},
    {"id": 9,  "name": "隠者",       "name_en": "The Hermit",          "emoji": "🏔️", "type": "major", "image_url": f"{CARD_IMAGE_BASE_URL}/010_9_TheHermit.jpg"},
    {"id": 10, "name": "運命の輪",   "name_en": "Wheel of Fortune",    "emoji": "🎡", "type": "major", "image_url": f"{CARD_IMAGE_BASE_URL}/011_10_WheelofFortune.jpg"},
    {"id": 11, "name": "正義",       "name_en": "Justice",             "emoji": "⚖️", "type": "major", "image_url": f"{CARD_IMAGE_BASE_URL}/012_11_Justice.jpg"},
    {"id": 12, "name": "吊された男", "name_en": "The Hanged Man",      "emoji": "🔄", "type": "major", "image_url": f"{CARD_IMAGE_BASE_URL}/013_12_TheHangedMan.jpg"},
    {"id": 13, "name": "死神",       "name_en": "Death",               "emoji": "🦋", "type": "major", "image_url": f"{CARD_IMAGE_BASE_URL}/014_13_Death.jpg"},
    {"id": 14, "name": "節制",       "name_en": "Temperance",          "emoji": "🌊", "type": "major", "image_url": f"{CARD_IMAGE_BASE_URL}/015_14_Temperance.jpg"},
    {"id": 15, "name": "悪魔",       "name_en": "The Devil",           "emoji": "⛓️", "type": "major", "image_url": f"{CARD_IMAGE_BASE_URL}/016_15_TheDevil.jpg"},
    {"id": 16, "name": "塔",         "name_en": "The Tower",           "emoji": "⚡", "type": "major", "image_url": f"{CARD_IMAGE_BASE_URL}/017_16_TheTower.jpg"},
    {"id": 17, "name": "星",         "name_en": "The Star",            "emoji": "⭐", "type": "major", "image_url": f"{CARD_IMAGE_BASE_URL}/018_17_TheStar.jpg"},
    {"id": 18, "name": "月",         "name_en": "The Moon",            "emoji": "🌕", "type": "major", "image_url": f"{CARD_IMAGE_BASE_URL}/019_18_TheMoon.jpg"},
    {"id": 19, "name": "太陽",       "name_en": "The Sun",             "emoji": "☀️", "type": "major", "image_url": f"{CARD_IMAGE_BASE_URL}/020_19_TheSun.jpg"},
    {"id": 20, "name": "審判",       "name_en": "Judgement",           "emoji": "📯", "type": "major", "image_url": f"{CARD_IMAGE_BASE_URL}/021_20_Judgement.jpg"},
    {"id": 21, "name": "世界",       "name_en": "The World",           "emoji": "🌍", "type": "major", "image_url": f"{CARD_IMAGE_BASE_URL}/022_21_TheWorld.jpg"},
]

# ─── 小アルカナ (Minor Arcana) ─────────────────────────────
SUITS = {
    "wands":    {"name": "ワンド",    "emoji": "🪄", "element": "火"},
    "cups":     {"name": "カップ",    "emoji": "🏆", "element": "水"},
    "swords":   {"name": "ソード",    "emoji": "🗡️", "element": "風"},
    "pentacles":{"name": "ペンタクル","emoji": "💰", "element": "地"},
}

COURT_CARDS = {
    "page":   "ペイジ",
    "knight": "ナイト",
    "queen":  "クイーン",
    "king":   "キング",
}

# ファイル名マッピング（実際のoutputフォルダのファイル名に対応）
_MINOR_IMAGE_MAP = {
    # Wands
    "wands_1":      "023_wands_1_AceofWands.jpg",
    "wands_2":      "024_wands_2_2ofWands.jpg",
    "wands_3":      "025_wands_3_3ofWands.jpg",
    "wands_4":      "026_wands_4_4ofWands.jpg",
    "wands_5":      "027_wands_5_5ofWands.jpg",
    "wands_6":      "028_wands_6_6ofWands.jpg",
    "wands_7":      "029_wands_7_7ofWands.jpg",
    "wands_8":      "030_wands_8_8ofWands.jpg",
    "wands_9":      "031_wands_9_9ofWands.jpg",
    "wands_10":     "032_wands_10_10ofWands.jpg",
    "wands_page":   "033_wands_page_PageofWands.jpg",
    "wands_knight": "034_wands_knight_KnightofWands.jpg",
    "wands_queen":  "035_wands_queen_QueenofWands.jpg",
    "wands_king":   "036_wands_king_KingofWands.jpg",
    # Cups
    "cups_1":       "037_cups_1_AceofCups.jpg",
    "cups_2":       "038_cups_2_2ofCups.jpg",
    "cups_3":       "039_cups_3_3ofCups.jpg",
    "cups_4":       "040_cups_4_4ofCups.jpg",
    "cups_5":       "041_cups_5_5ofCups.jpg",
    "cups_6":       "042_cups_6_6ofCups.jpg",
    "cups_7":       "043_cups_7_7ofCups.jpg",
    "cups_8":       "044_cups_8_8ofCups.jpg",
    "cups_9":       "045_cups_9_9ofCups.jpg",
    "cups_10":      "046_cups_10_10ofCups.jpg",
    "cups_page":    "047_cups_page_PageofCups.jpg",
    "cups_knight":  "048_cups_knight_KnightofCups.jpg",
    "cups_queen":   "049_cups_queen_QueenofCups.jpg",
    "cups_king":    "050_cups_king_KingofCups.jpg",
    # Swords
    "swords_1":       "051_swords_1_AceofSwords.jpg",
    "swords_2":       "052_swords_2_2ofSwords.jpg",
    "swords_3":       "053_swords_3_3ofSwords.jpg",
    "swords_4":       "054_swords_4_4ofSwords.jpg",
    "swords_5":       "055_swords_5_5ofSwords.jpg",
    "swords_6":       "056_swords_6_6ofSwords.jpg",
    "swords_7":       "057_swords_7_7ofSwords.jpg",
    "swords_8":       "058_swords_8_8ofSwords.jpg",
    "swords_9":       "059_swords_9_9ofSwords.jpg",
    "swords_10":      "060_swords_10_10ofSwords.jpg",
    "swords_page":    "061_swords_page_PageofSwords.jpg",
    "swords_knight":  "062_swords_knight_KnightofSwords.jpg",
    "swords_queen":   "063_swords_queen_QueenofSwords.jpg",
    "swords_king":    "064_swords_king_KingofSwords.jpg",
    # Pentacles
    "pentacles_1":       "065_pentacles_1_AceofPentacles.jpg",
    "pentacles_2":       "066_pentacles_2_2ofPentacles.jpg",
    "pentacles_3":       "067_pentacles_3_3ofPentacles.jpg",
    "pentacles_4":       "068_pentacles_4_4ofPentacles.jpg",
    "pentacles_5":       "069_pentacles_5_5ofPentacles.jpg",
    "pentacles_6":       "070_pentacles_6_6ofPentacles.jpg",
    "pentacles_7":       "071_pentacles_7_7ofPentacles.jpg",
    "pentacles_8":       "072_pentacles_8_8ofPentacles.jpg",
    "pentacles_9":       "073_pentacles_9_9ofPentacles.jpg",
    "pentacles_10":      "074_pentacles_10_10ofPentacles.jpg",
    "pentacles_page":    "075_pentacles_page_PageofPentacles.jpg",
    "pentacles_knight":  "076_pentacles_knight_KnightofPentacles.jpg",
    "pentacles_queen":   "077_pentacles_queen_QueenofPentacles.jpg",
    "pentacles_king":    "078_pentacles_king_KingofPentacles.jpg",
}

MINOR_ARCANA = []
for suit_key, suit_info in SUITS.items():
    # 数札 (Ace〜10)
    for num in range(1, 11):
        card_id   = f"{suit_key}_{num}"
        name      = f"{suit_info['name']}の{'エース' if num == 1 else str(num)}"
        name_en   = f"{'Ace' if num == 1 else str(num)} of {suit_key.title()}"
        filename  = _MINOR_IMAGE_MAP.get(card_id, f"{card_id}.jpg")
        MINOR_ARCANA.append({
            "id":        card_id,
            "name":      name,
            "name_en":   name_en,
            "emoji":     suit_info["emoji"],
            "type":      "minor",
            "suit":      suit_key,
            "number":    num,
            "image_url": f"{CARD_IMAGE_BASE_URL}/{filename}",
        })
    # コートカード
    for court_key, court_name in COURT_CARDS.items():
        card_id  = f"{suit_key}_{court_key}"
        name     = f"{suit_info['name']}の{court_name}"
        name_en  = f"{court_key.title()} of {suit_key.title()}"
        filename = _MINOR_IMAGE_MAP.get(card_id, f"{card_id}.jpg")
        MINOR_ARCANA.append({
            "id":        card_id,
            "name":      name,
            "name_en":   name_en,
            "emoji":     suit_info["emoji"],
            "type":      "minor",
            "suit":      suit_key,
            "number":    court_key,
            "image_url": f"{CARD_IMAGE_BASE_URL}/{filename}",
        })

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
        drawn           = card.copy()
        drawn["reversed"]  = random.choice([True, False])
        drawn["position"]  = "逆位置" if drawn["reversed"] else "正位置"
        result.append(drawn)
    return result


def format_card_display(cards: list[dict]) -> str:
    """カードの表示用テキストを生成"""
    if len(cards) == 1:
        card     = cards[0]
        position = "🔻 逆位置" if card["reversed"] else "🔺 正位置"
        return f"{card['emoji']} {card['name']}\n（{card['name_en']}）\n{position}"

    # 3枚展開 (過去・現在・未来)
    labels = ["🕐 過去", "🔮 現在", "🔭 未来"]
    lines  = []
    for i, card in enumerate(cards):
        position = "逆位置" if card["reversed"] else "正位置"
        label    = labels[i] if i < len(labels) else f"カード{i+1}"
        lines.append(f"{label}: {card['emoji']} {card['name']}（{position}）")
    return "\n".join(lines)

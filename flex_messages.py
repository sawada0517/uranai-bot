"""
🃏 LINE Flex Message Builder for Tarot Cards
龍神様占い - カード画像付きFlex Messageを構築
"""

# カード画像のベースURL（デプロイ後に環境変数から取得する想定）
import os

CARD_IMAGE_BASE_URL = os.getenv(
    "CARD_IMAGE_BASE_URL", "https://your-domain.com/static/cards"
)


def _get_card_image_url(card: dict) -> str:
    """カードの画像URLを取得"""
    if "image_url" in card and card["image_url"]:
        return card["image_url"]
    # フォールバック: IDベースのURL
    card_id = card.get("id", "unknown")
    return f"{CARD_IMAGE_BASE_URL}/{card_id}.png"


def build_card_flex_message(card: dict) -> dict:
    """
    ワンカード用 Flex Message
    カード画像 + カード名 + 正位置/逆位置を表示
    """
    image_url = _get_card_image_url(card)
    is_reversed = card.get("reversed", False)
    position_text = "🔻 逆位置" if is_reversed else "🔺 正位置"
    position_color = "#E74C3C" if is_reversed else "#2ECC71"

    flex_content = {
        "type": "bubble",
        "size": "kilo",
        "hero": {
            "type": "image",
            "url": image_url,
            "size": "full",
            "aspectRatio": "2:3",
            "aspectMode": "cover",
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": f"{card['emoji']} {card['name']}",
                    "weight": "bold",
                    "size": "lg",
                    "align": "center",
                    "color": "#2E1A47",
                },
                {
                    "type": "text",
                    "text": card.get("name_en", ""),
                    "size": "xs",
                    "color": "#888888",
                    "align": "center",
                    "margin": "xs",
                },
                {
                    "type": "text",
                    "text": position_text,
                    "size": "md",
                    "weight": "bold",
                    "align": "center",
                    "color": position_color,
                    "margin": "md",
                },
            ],
            "paddingAll": "12px",
            "backgroundColor": "#FFF8F0",
        },
        "styles": {
            "hero": {"separator": False},
            "body": {"separator": False},
        },
    }

    return {
        "type": "flex",
        "altText": f"🔮 {card['name']}（{'逆位置' if is_reversed else '正位置'}）",
        "contents": flex_content,
    }


def build_spread_flex_message(cards: list[dict]) -> dict:
    """
    スリーカード・スプレッド用 Flex Message (carousel)
    過去・現在・未来の3枚をカルーセルで表示
    """
    labels = ["🕐 過去", "🔮 現在", "🔭 未来"]
    label_colors = ["#3498DB", "#9B59B6", "#E67E22"]
    bubbles = []

    for i, card in enumerate(cards):
        image_url = _get_card_image_url(card)
        is_reversed = card.get("reversed", False)
        position_text = "🔻 逆位置" if is_reversed else "🔺 正位置"
        position_color = "#E74C3C" if is_reversed else "#2ECC71"
        label = labels[i] if i < len(labels) else f"カード{i+1}"
        label_color = label_colors[i] if i < len(label_colors) else "#888888"

        bubble = {
            "type": "bubble",
            "size": "micro",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": label,
                        "weight": "bold",
                        "size": "sm",
                        "align": "center",
                        "color": "#FFFFFF",
                    }
                ],
                "backgroundColor": label_color,
                "paddingAll": "8px",
            },
            "hero": {
                "type": "image",
                "url": image_url,
                "size": "full",
                "aspectRatio": "2:3",
                "aspectMode": "cover",
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": f"{card['emoji']} {card['name']}",
                        "weight": "bold",
                        "size": "sm",
                        "align": "center",
                        "color": "#2E1A47",
                        "wrap": True,
                    },
                    {
                        "type": "text",
                        "text": position_text,
                        "size": "xs",
                        "weight": "bold",
                        "align": "center",
                        "color": position_color,
                        "margin": "xs",
                    },
                ],
                "paddingAll": "8px",
                "backgroundColor": "#FFF8F0",
            },
        }
        bubbles.append(bubble)

    carousel = {"type": "carousel", "contents": bubbles}

    card_names = "・".join([c["name"] for c in cards])
    return {
        "type": "flex",
        "altText": f"🔮 スリーカード・スプレッド: {card_names}",
        "contents": carousel,
    }

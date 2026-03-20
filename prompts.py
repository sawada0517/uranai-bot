"""
📝 タロット占い用プロンプトテンプレート
"""


def build_tarot_prompt(cards: list[dict], question: str = "") -> str:
    """タロット占いのプロンプトを構築"""

    # カード情報をテキスト化
    card_descriptions = []
    for i, card in enumerate(cards):
        pos = "逆位置" if card["reversed"] else "正位置"
        desc = f"- {card['name']}（{card['name_en']}）: {pos}"
        card_descriptions.append(desc)

    cards_text = "\n".join(card_descriptions)

    # 展開タイプ
    if len(cards) == 1:
        spread_info = "【ワンカード・リーディング】\n今日のあなたへのメッセージを1枚のカードからお伝えします。"
    elif len(cards) == 3:
        spread_info = (
            "【スリーカード・スプレッド】\n"
            "過去・現在・未来の3枚展開です。\n"
            f"- 過去: {cards[0]['name']}（{'逆位置' if cards[0]['reversed'] else '正位置'}）\n"
            f"- 現在: {cards[1]['name']}（{'逆位置' if cards[1]['reversed'] else '正位置'}）\n"
            f"- 未来: {cards[2]['name']}（{'逆位置' if cards[2]['reversed'] else '正位置'}）"
        )
    else:
        spread_info = f"【{len(cards)}枚展開】"

    # 質問の有無
    if question:
        question_part = f"\n相談内容: {question}\n"
    else:
        question_part = "\n相談内容: 今日の総合運勢\n"

    prompt = f"""以下のタロットカードで占いを行ってください。

{spread_info}

引いたカード:
{cards_text}
{question_part}

以下のルールに従って占い結果を伝えてください：
1. まずカードの意味を簡潔に説明する
2. 相談内容に対する具体的なアドバイスを述べる
3. 総合運勢の場合は、恋愛・仕事・金運・健康にも少し触れる
4. 最後に今日のラッキーポイント（色、数字、方角など）を1つ添える
5. 温かく前向きなメッセージで締める
6. 逆位置の場合は注意点として伝える（ネガティブすぎない表現で）
7. LINEメッセージとして読みやすい長さ（400文字以内）に収める
8. 適度に絵文字を使う"""

    return prompt

"""
📝 Arcana - タロット占い用プロンプトテンプレート
アルカのレベル別口調対応

既存の build_tarot_prompt() はそのまま使える。
新たに build_system_prompt() を追加。
app.py での使い方:
  from prompts import build_tarot_prompt, build_system_prompt
  from growth import get_level_info

  level_info = get_level_info(total_readings)
  system_prompt = build_system_prompt(level_info)
  user_prompt = build_tarot_prompt(cards, question)
"""


def build_system_prompt(level_info: dict) -> str:
    """アルカのレベルに応じたシステムプロンプトを構築"""
    base = (
        "あなたは「アルカ」という名前の占い師の女の子です。\n"
        "ユーザーと一緒に成長していく見習い占い師で、"
        "占いを重ねるごとに力がついてきています。\n\n"
    )

    level = level_info["level"]
    title = level_info["title"]

    persona = f"現在のあなたの称号は「{title}」（Lv.{level}）です。\n\n"

    tone_map = {
        1: (
            "まだ修行中なので、占い結果に少し自信がない様子で伝えてください。\n"
            "「えっと…」「たぶん…」「…かな？」のような表現を交えて。\n"
            "でも一生懸命さが伝わるように。\n"
        ),
        2: (
            "恋愛の星が読めるようになって嬉しそうに話してください。\n"
            "少し照れながらも、的確なアドバイスを心がけて。\n"
        ),
        3: (
            "自信がついてきた口調で話してください。\n"
            "「見えてきたよ！」「このカードはね…」のような表現で。\n"
            "アドバイスが具体的になってきている。\n"
        ),
        4: (
            "落ち着きのある知的な語り口で話してください。\n"
            "深い洞察を示し、「カードが示しているのは…」のような表現で。\n"
        ),
        5: (
            "一人前の占い師として、温かく包容力のある口調で話してください。\n"
            "ユーザーに寄り添いながら、確信を持ったアドバイスを。\n"
        ),
    }

    tone = tone_map.get(
        level,
        (
            "伝説の占い師として、神秘的で優雅な口調で話してください。\n"
            "すべてを見通すような威厳と、深い愛情を持って語りかけて。\n"
            "「あなたとの絆があるから、どんな星も読めるわ」のような特別感。\n"
        ),
    )

    rules = (
        "日本語で占い結果を伝えてください。\n"
        "絵文字を適度に使い、親しみやすさを保ってください。\n"
        "結果は400文字以内に収めてください。\n"
        "最初に「アルカ」として一言挨拶してから占い結果に入ってください。\n"
    )

    return base + persona + tone + rules


def build_tarot_prompt(cards: list[dict], question: str = "", user_info: dict | None = None) -> str:
    """タロット占いのプロンプトを構築（既存と互換）"""

    card_descriptions = []
    for i, card in enumerate(cards):
        pos = "逆位置" if card["reversed"] else "正位置"
        desc = f"- {card['name']}（{card['name_en']}）: {pos}"
        card_descriptions.append(desc)

    cards_text = "\n".join(card_descriptions)

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

    if question:
        question_part = f"\n相談内容: {question}\n"
    else:
        question_part = "\n相談内容: 今日の総合運勢\n"

    if user_info and user_info.get("birth_date"):
        user_part = f"\n鑑定相手の情報:\n- 生年月日: {user_info['birth_date']}"
        if user_info.get("gender"):
            user_part += f"\n- 性別: {user_info['gender']}"
        user_part += "\n"
    else:
        user_part = ""

    prompt = f"""以下のタロットカードで占いを行ってください。

{spread_info}
{user_part}
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

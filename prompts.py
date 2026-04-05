"""
📝 Arcana - タロット占い用プロンプトテンプレート
アルカのレベル別口調 + 星座・数秘術・性別対応

app.py での使い方:
  from prompts import build_tarot_prompt, build_system_prompt
  from growth import get_level_info

  level_info = get_level_info(total_readings)
  system_prompt = build_system_prompt(level_info)
  user_prompt = build_tarot_prompt(cards, question, user_info)
"""

from datetime import datetime


# ─── 星座判定 ──────────────────────────────────────────
ZODIAC_SIGNS = [
    {"name": "山羊座", "en": "Capricorn", "start": (1, 1), "end": (1, 19),
     "traits": "責任感が強く、忍耐力がある。目標に向かって着実に歩む努力家"},
    {"name": "水瓶座", "en": "Aquarius", "start": (1, 20), "end": (2, 18),
     "traits": "独創的で自由を愛する。革新的なアイデアと博愛精神の持ち主"},
    {"name": "魚座", "en": "Pisces", "start": (2, 19), "end": (3, 20),
     "traits": "繊細で直感力に優れる。共感力が高く、芸術的な感性を持つ"},
    {"name": "牡羊座", "en": "Aries", "start": (3, 21), "end": (4, 19),
     "traits": "行動力があり、チャレンジ精神旺盛。リーダーシップを発揮する"},
    {"name": "牡牛座", "en": "Taurus", "start": (4, 20), "end": (5, 20),
     "traits": "安定志向で感覚的。美しいものを愛し、忍耐強く物事を進める"},
    {"name": "双子座", "en": "Gemini", "start": (5, 21), "end": (6, 21),
     "traits": "知的好奇心が旺盛で、コミュニケーション能力が高い。適応力抜群"},
    {"name": "蟹座", "en": "Cancer", "start": (6, 22), "end": (7, 22),
     "traits": "家族思いで愛情深い。直感力があり、大切な人を守る力が強い"},
    {"name": "獅子座", "en": "Leo", "start": (7, 23), "end": (8, 22),
     "traits": "華やかで存在感がある。自信に溢れ、周りを明るく照らすリーダー"},
    {"name": "乙女座", "en": "Virgo", "start": (8, 23), "end": (9, 22),
     "traits": "几帳面で分析力に優れる。細やかな気配りと奉仕の精神を持つ"},
    {"name": "天秤座", "en": "Libra", "start": (9, 23), "end": (10, 23),
     "traits": "調和とバランスを重んじる。美的感覚が鋭く、社交的で人を惹きつける"},
    {"name": "蠍座", "en": "Scorpio", "start": (10, 24), "end": (11, 22),
     "traits": "情熱的で洞察力が鋭い。深い絆を大切にし、一度決めたら貫く意志の強さ"},
    {"name": "射手座", "en": "Sagittarius", "start": (11, 23), "end": (12, 21),
     "traits": "楽観的で冒険心がある。知識への探究心と自由を求める旅人"},
    {"name": "山羊座", "en": "Capricorn", "start": (12, 22), "end": (12, 31),
     "traits": "責任感が強く、忍耐力がある。目標に向かって着実に歩む努力家"},
]


def get_zodiac(birth_date_str: str) -> dict | None:
    """生年月日文字列から星座を判定"""
    try:
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d"):
            try:
                dt = datetime.strptime(birth_date_str, fmt)
                break
            except ValueError:
                continue
        else:
            return None

        month, day = dt.month, dt.day
        for sign in ZODIAC_SIGNS:
            s_m, s_d = sign["start"]
            e_m, e_d = sign["end"]
            if (month == s_m and day >= s_d) or (month == e_m and day <= e_d):
                return sign
        return None
    except Exception:
        return None


# ─── 数秘術（運命数） ─────────────────────────────────────
DESTINY_NUMBERS = {
    1: {"name": "リーダー", "traits": "独立心が強く、開拓者精神を持つ。自分の道を切り開く力がある"},
    2: {"name": "調停者", "traits": "協調性があり、繊細な感受性を持つ。パートナーシップに恵まれやすい"},
    3: {"name": "表現者", "traits": "創造力と社交性に溢れる。言葉や芸術で人を魅了する才能がある"},
    4: {"name": "建設者", "traits": "堅実で努力家。安定した基盤を築く力があり、信頼される存在"},
    5: {"name": "冒険家", "traits": "自由を愛し、変化を恐れない。多才で好奇心旺盛な行動派"},
    6: {"name": "奉仕者", "traits": "愛情深く、責任感が強い。家庭や仲間を大切にする調和の人"},
    7: {"name": "探究者", "traits": "深い知性と直感力を持つ。内省的で、真理を追求する求道者"},
    8: {"name": "実現者", "traits": "野心と実行力がある。物質的な成功を引き寄せるパワーの持ち主"},
    9: {"name": "博愛者", "traits": "理想主義で人道的。広い視野と深い共感力で世界を良くしようとする"},
    11: {"name": "直感の人", "traits": "鋭い直感とスピリチュアルな感性を持つ。人々を導く使命がある"},
    22: {"name": "大建設者", "traits": "壮大なビジョンを現実にする力がある。マスタービルダーとしての使命"},
}


def calc_destiny_number(birth_date_str: str) -> int | None:
    """生年月日から運命数を算出"""
    try:
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d"):
            try:
                dt = datetime.strptime(birth_date_str, fmt)
                break
            except ValueError:
                continue
        else:
            return None

        digits = str(dt.year) + str(dt.month).zfill(2) + str(dt.day).zfill(2)
        total = sum(int(d) for d in digits)

        while total > 9 and total not in (11, 22):
            total = sum(int(d) for d in str(total))

        return total
    except Exception:
        return None


# ─── システムプロンプト ────────────────────────────────────
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
        "鑑定相手の星座や運命数の情報がある場合は、\n"
        "それらを自然に織り交ぜて占い結果を伝えてください。\n"
        "「あなたは○○座だから…」のように相手の特性に触れることで、\n"
        "パーソナライズされた特別な鑑定であることを演出してください。\n"
    )

    return base + persona + tone + rules


# ─── タロットプロンプト ────────────────────────────────────
def build_tarot_prompt(cards: list[dict], question: str = "", user_info: dict | None = None) -> str:
    """タロット占いのプロンプトを構築（星座・数秘術対応）"""

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

    # ── ユーザー情報（星座・数秘術・性別）──
    user_part = ""
    if user_info and user_info.get("birth_date"):
        birth_date = user_info["birth_date"]
        user_part = f"\n鑑定相手の情報:\n- 生年月日: {birth_date}"

        # 星座判定
        zodiac = get_zodiac(birth_date)
        if zodiac:
            user_part += f"\n- 星座: {zodiac['name']}（{zodiac['en']}）"
            user_part += f"\n- 星座の特性: {zodiac['traits']}"

        # 数秘術（運命数）
        destiny = calc_destiny_number(birth_date)
        if destiny and destiny in DESTINY_NUMBERS:
            dn = DESTINY_NUMBERS[destiny]
            user_part += f"\n- 運命数: {destiny}（{dn['name']}）"
            user_part += f"\n- 数秘術の特性: {dn['traits']}"

        # 性別
        if user_info.get("gender"):
            gender = user_info["gender"]
            user_part += f"\n- 性別: {gender}"

        user_part += "\n"
        user_part += "\n※ 星座と運命数の特性を踏まえて、カードの解釈をパーソナライズしてください。"
        user_part += "\n※ 性別に応じて恋愛運のアドバイスを自然に調整してください。\n"

    prompt = f"""以下のタロットカードで占いを行ってください。

{spread_info}
{user_part}
引いたカード:
{cards_text}
{question_part}

以下のルールに従って占い結果を伝えてください：
1. まずカードの意味を簡潔に説明する
2. 相談内容に対する具体的なアドバイスを述べる
3. 鑑定相手の星座や運命数の特性と、カードの意味を結びつけて解釈する
4. 総合運勢の場合は、恋愛・仕事・金運・健康にも少し触れる
5. 最後に今日のラッキーポイント（色、数字、方角など）を1つ添える
6. 温かく前向きなメッセージで締める
7. 逆位置の場合は注意点として伝える（ネガティブすぎない表現で）
8. LINEメッセージとして読みやすい長さ（400文字以内）に収める
9. 適度に絵文字を使う"""

    return prompt

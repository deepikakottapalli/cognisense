from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()

BURNOUT_KEYWORDS = [
    "tired", "exhausted", "overwhelmed", "hopeless", "burned out",
    "can't focus", "failing", "anxious", "stressed", "empty",
    "detached", "irritable", "no motivation", "giving up", "drained"
]

def calculate_bri(text: str) -> dict:
    if not text or not text.strip():
        return {
            "bri_score": 0,
            "risk_level": "Low",
            "tone_label": "Calm",
            "neg_score": 0.0,
            "keyword_hits": 0,
            "emotions": []
        }

    scores = analyzer.polarity_scores(text)
    neg_score = scores["neg"]  # 0.0 – 1.0

    text_lower = text.lower()
    hits = sum(1 for kw in BURNOUT_KEYWORDS if kw in text_lower)
    keyword_ratio = min(hits / 5, 1.0)  # max 5 hits = 1.0

    bri_raw = (neg_score * 70) + (keyword_ratio * 30)
    bri_score = int(max(0, min(100, round(bri_raw))))

    risk_level = get_risk_level(bri_score)
    tone_label = get_tone_label(bri_score)
    emotions = get_dominant_emotions(scores, text_lower)

    return {
        "bri_score": bri_score,
        "risk_level": risk_level,
        "tone_label": tone_label,
        "neg_score": round(neg_score, 3),
        "keyword_hits": hits,
        "emotions": emotions
    }


def get_risk_level(bri_score: int) -> str:
    if bri_score <= 40:
        return "Low"
    elif bri_score <= 74:
        return "Medium"
    else:
        return "High"


def get_tone_label(bri_score: int) -> str:
    if bri_score <= 30:
        return "Calm"
    elif bri_score <= 50:
        return "Neutral"
    elif bri_score <= 74:
        return "Tense"
    else:
        return "Burned Out"


def get_dominant_emotions(vader_scores: dict, text_lower: str) -> list:
    neg = vader_scores.get("neg", 0)
    compound = vader_scores.get("compound", 0)

    anxiety_score = 0
    exhaustion_score = 0
    detachment_score = 0
    irritability_score = 0
    hopelessness_score = 0

    # Keyword-based contribution
    anxiety_kw = ["anxious", "stressed", "scared", "worried", "panic", "fear", "nervous"]
    exhaustion_kw = ["tired", "exhausted", "drained", "no energy", "fatigue", "sleepy", "worn out"]
    detachment_kw = ["detached", "empty", "numb", "don't care", "disconnected", "hollow", "no motivation"]
    irritability_kw = ["irritable", "angry", "frustrated", "annoyed", "snap", "rage", "bitter"]
    hopelessness_kw = ["hopeless", "giving up", "worthless", "pointless", "useless", "failing", "can't go on"]

    def kw_score(keywords):
        return sum(1 for kw in keywords if kw in text_lower)

    anxiety_score = kw_score(anxiety_kw) * 15 + (neg * 30)
    exhaustion_score = kw_score(exhaustion_kw) * 15 + (neg * 25)
    detachment_score = kw_score(detachment_kw) * 15 + (max(0, -compound) * 20)
    irritability_score = kw_score(irritability_kw) * 15 + (neg * 15)
    hopelessness_score = kw_score(hopelessness_kw) * 15 + (max(0, -compound) * 25)

    emotions_raw = {
        "Anxiety": anxiety_score,
        "Exhaustion": exhaustion_score,
        "Detachment": detachment_score,
        "Irritability": irritability_score,
        "Hopelessness": hopelessness_score
    }

    # Normalize so max = 100
    max_val = max(emotions_raw.values()) if max(emotions_raw.values()) > 0 else 1
    emotions = [
        {"name": name, "percentage": int(min(100, round((val / max_val) * 100)))}
        for name, val in emotions_raw.items()
    ]

    # Sort descending
    emotions.sort(key=lambda x: x["percentage"], reverse=True)
    return emotions
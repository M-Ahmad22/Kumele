import re
import nltk
from nltk.corpus import stopwords
from transformers import pipeline
from app.services.feedback.classifier_model import get_classifier

nltk.download('stopwords')

STOP = set(stopwords.words("english"))

THEME_KEYWORDS = {
    "Bug": ["error", "crash", "bug", "lag", "problem", "issue"],
    "UX": ["ui", "design", "navigation", "interface", "experience"],
    "Feature": ["add", "feature", "new", "should have", "missing"],
    "Host": ["host", "behaviour", "rude", "organiser"],
    "Event": ["event", "location", "timing"],
}

def clean_text(text: str):
    text = text.lower()
    text = re.sub(r"[^a-zA-Z\s]", "", text)
    words = [w for w in text.split() if w not in STOP]
    return " ".join(words)

def extract_keywords(text: str):
    words = clean_text(text).split()
    return list(set([w for w in words if len(w) > 4]))[:5]

def detect_themes(text: str):
    themes = []
    for theme, keys in THEME_KEYWORDS.items():
        score = sum(k in text.lower() for k in keys)
        if score > 0:
            themes.append({"category": theme, "relevance": score})
    return themes

def analyze_feedback(text: str):
    clf = get_classifier()

    sentiment_out = clf(text)[0]
    sentiment = sentiment_out["label"].lower()
    confidence = float(sentiment_out["score"])

    keywords = extract_keywords(text)
    themes = detect_themes(text)

    return {
        "sentiment": sentiment,
        "confidence": confidence,
        "themes": themes,
        "keywords": keywords
    }

import os
from transformers import pipeline

MODEL_NAME = "distilbert-base-uncased-finetuned-sst-2-english"

_classifier = None

def get_classifier():
    global _classifier
    if _classifier is None:
        _classifier = pipeline("text-classification", model=MODEL_NAME)
    return _classifier

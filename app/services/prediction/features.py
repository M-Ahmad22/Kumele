# services/prediction/features.py

import pandas as pd

def build_features(df: pd.DataFrame):
    df = df.copy()

    # Duration in hours
    df["duration"] = (df["end_time"] - df["start_time"]).dt.total_seconds() / 3600

    # Start hour
    df["start_hour"] = df["start_time"].dt.hour

    # Categorical encodings
    df = pd.get_dummies(df, columns=["hobby_category", "location"], drop_first=True)

    # Drop columns not used by model
    return df.drop(columns=["title", "start_time", "end_time"])

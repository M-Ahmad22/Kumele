import numpy as np

def score_with_tfrs(user_vec, event_vecs):
    """
    Compute cosine similarity between user vector and a list of event vectors.
    """
    user_vec = np.array(user_vec).flatten()
    sims = []
    for evec in event_vecs:
        evec = np.array(evec).flatten()
        sim = np.dot(user_vec, evec) / (np.linalg.norm(user_vec) * np.linalg.norm(evec))
        sims.append(float(sim))
    return sims

# import numpy as np

# def score_with_tfrs(user_vec, event_vecs):
#     """
#     Compute cosine similarity between user vector and a list of event vectors.
#     """
#     user_vec = np.array(user_vec).flatten()
#     sims = []
#     for evec in event_vecs:
#         evec = np.array(evec).flatten()
#         sim = np.dot(user_vec, evec) / (np.linalg.norm(user_vec) * np.linalg.norm(evec))
#         sims.append(float(sim))
#     return sims

import numpy as np

def score_with_tfrs(user_vec, event_vecs):
    """
    Placeholder: cosine similarity for ML pipeline until TFRS model is integrated.
    """
    user = np.array(user_vec).flatten()
    scores = []

    for ev in event_vecs:
        ev = np.array(ev).flatten()
        sim = np.dot(user, ev) / (np.linalg.norm(user) * np.linalg.norm(ev))
        scores.append(float(sim))

    return scores

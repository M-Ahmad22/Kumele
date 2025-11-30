# import numpy as np

# def encode_status(level, gold_count):
#     mapping = {'none': 0.0, 'bronze': 0.25, 'silver': 0.5, 'gold': 1.0}
#     status_numeric = mapping.get(level, 0.0)
#     gold_norm = min(gold_count, 10) / 10.0
#     return status_numeric, gold_norm


# def final_score(relevance, user_status, host_status, dist_km,
#                 alpha_user=0.08, alpha_host=0.12, beta=0.03, max_dist=50):
#     trust_factor = 1 + alpha_user * user_status + alpha_host * host_status
#     trust_factor = min(trust_factor, 1.25)
#     dist_penalty = beta * (dist_km / max_dist)
#     return relevance * trust_factor - dist_penalty

import numpy as np

def cosine_similarity_basic(a, b):
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def combine_basic_score(sim, dist_km):
    # higher sim, lower distance → better
    return sim - (dist_km * 0.01)

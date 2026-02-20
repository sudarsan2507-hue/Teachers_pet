import pickle
from symbolic_engine import symbolic_score

model = pickle.load(open("model/ml_model.pkl", "rb"))
vectorizer = pickle.load(open("model/vectorizer.pkl", "rb"))

def evaluate_response(response, engagement_threshold=75):

    vec = vectorizer.transform([response])
    probs = model.predict_proba(vec)

    max_prob = max(probs[0])
    ml_score = max_prob * 70

    sym_score, reasons = symbolic_score(response)

    final_score = ml_score + sym_score

    if final_score >= engagement_threshold:
        status = "Engaged"
    elif final_score >= 50:
        status = "Partially Engaged"
    else:
        status = "Disengaged"

    return round(final_score, 2), status, reasons
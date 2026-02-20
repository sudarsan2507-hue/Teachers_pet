def symbolic_score(response):
    response = response.lower()
    score = 0
    reasons = []

    if "base case" in response:
        score += 20
        reasons.append("Contains key concept")

    if "because" in response:
        score += 10
        reasons.append("Logical explanation present")

    if "don't know" in response or "not sure" in response:
        score -= 20
        reasons.append("Contains uncertainty phrase")

    if len(response.strip()) == 0:
        score -= 30
        reasons.append("No response submitted")

    if len(response.split()) < 3:
        score -= 10
        reasons.append("Response too short")

    return score, reasons
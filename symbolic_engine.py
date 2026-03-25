"""
symbolic_engine.py — Rule-based concept coverage scoring engine.

Implements the K / C / L / P weighted formula:
    Score_rule = w1*K + w2*C + w3*L - w4*P
    (scaled to RULE_MAX points, default 30)

Where:
    K = keyword coverage ratio  (fraction of expected keywords present)
    C = concept cluster coverage (fraction of clusters with >= 1 keyword hit)
    L = normalized length factor (min(word_count / TARGET, 1.0))
    P = penalty scalar for off-topic / uncertainty phrases
"""

import config


def symbolic_score(response: str, topic: str = "") -> tuple[float, list[str], list[str]]:
    """
    Compute the rule-based understanding score for a student response.

    Args:
        response: Raw student response text.
        topic:    Session topic (e.g. "recursion"). Used for keyword lookup.

    Returns:
        (score, reasons, missing_keywords)
        - score:            float in [0, config.RULE_MAX]
        - reasons:          human-readable explanation strings
        - missing_keywords: concept keywords absent from the response
    """
    text    = response.lower().strip()
    reasons = []

    # ── K: Keyword coverage ratio ─────────────────────────────────────────────
    clusters = config.get_topic_clusters(topic)
    all_keywords = config.get_all_keywords(topic)

    if all_keywords:
        hit_keywords     = [kw for kw in all_keywords if kw in text]
        missing_keywords = [kw for kw in all_keywords if kw not in text]
        K = len(hit_keywords) / len(all_keywords)
    else:
        # Unknown topic — no keyword scoring possible
        hit_keywords     = []
        missing_keywords = []
        K = 0.0

    if K >= 0.75:
        reasons.append(f"Strong keyword coverage ({int(K*100)}% of expected terms)")
    elif K >= 0.40:
        reasons.append(f"Partial keyword coverage ({int(K*100)}% of expected terms)")
    elif all_keywords:
        reasons.append("Low keyword coverage — key concepts missing")

    # ── C: Concept cluster coverage ───────────────────────────────────────────
    if clusters:
        clusters_hit = sum(
            1 for _, kws in clusters
            if any(kw in text for kw in kws)
        )
        C = clusters_hit / len(clusters)
        if C >= 0.75:
            reasons.append(f"Covers {clusters_hit}/{len(clusters)} concept clusters")
        elif C >= 0.40:
            reasons.append(f"Partially covers concept clusters ({clusters_hit}/{len(clusters)})")
    else:
        C = 0.0

    # ── L: Normalized length factor ───────────────────────────────────────────
    word_count = len(text.split()) if text else 0
    L = min(word_count / config.TARGET_WORD_COUNT, 1.0)

    if word_count == 0:
        reasons.append("No response submitted")
    elif word_count < 5:
        reasons.append("Response too short")
    elif L >= 1.0:
        reasons.append("Response length adequate")

    # ── P: Penalty for off-topic / uncertainty indicators ─────────────────────
    penalty_hit = any(phrase in text for phrase in config.PENALTY_PHRASES)
    P = 1.0 if penalty_hit else 0.0
    if penalty_hit:
        reasons.append("Contains uncertainty phrase — concept gap likely")

    # ── Logical connective bonus (basic coherence indicator) ──────────────────
    # Small bonus added into K to reward causal reasoning
    if any(conn in text for conn in ["because", "therefore", "since", "which means"]):
        reasons.append("Logical explanation present")
        K = min(K + 0.10, 1.0)

    # ── Final weighted rule score ─────────────────────────────────────────────
    raw = (
        config.W1_KEYWORD * K
        + config.W2_CLUSTER * C
        + config.W3_LENGTH  * L
        - config.W4_PENALTY * P
    )
    raw   = max(raw, 0.0)           # floor at 0
    score = raw * config.RULE_MAX   # scale to [0, RULE_MAX]

    return round(score, 2), reasons, missing_keywords
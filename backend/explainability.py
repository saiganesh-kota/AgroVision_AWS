"""
explainability.py — XAI Score Generator (Patent Feature VII)
─────────────────────────────────────────────────────────────
Produces a human-readable explainability score and factor list
explaining WHY the AI made its recommendation.
"""

def explain_score(confidence: float, severity: float, risk: str) -> float:
    """
    Returns an overall explainability / confidence score 0-100.
    Higher = the model is more certain about its diagnosis.
    """
    # Normalize inputs
    conf_n = min(float(confidence), 100.0)
    sev_n  = min(float(severity),   100.0)

    risk_bonus = {"High": 15.0, "Medium": 8.0, "Low": 0.0}.get(str(risk).capitalize(), 0.0)

    # Weighted combination
    score = conf_n * 0.55 + sev_n * 0.30 + risk_bonus
    return round(min(score, 100.0), 2)


def explain_factors(confidence: float, severity: float, risk: str,
                    geo_risk: str = "Low", humidity: float = 60.0,
                    spread_velocity: float = 0.0) -> list[dict]:
    """
    Returns a list of factor dicts for the frontend XAI panel:
        [{ label, value (0-1), impact: 'positive'|'negative'|'neutral' }, ...]
    """
    factors = [
        {
            "label":  "Model Confidence",
            "value":  round(min(float(confidence), 100.0) / 100.0, 4),
            "impact": "positive" if confidence > 70 else "neutral",
        },
        {
            "label":  "Disease Severity",
            "value":  round(min(float(severity), 100.0) / 100.0, 4),
            "impact": "negative" if severity > 30 else "neutral",
        },
        {
            "label":  "Risk Level",
            "value":  {"High": 1.0, "Medium": 0.5, "Low": 0.1}.get(str(risk).capitalize(), 0.5),
            "impact": "negative" if risk == "High" else "neutral",
        },
        {
            "label":  "Geo Outbreak Risk",
            "value":  {"High": 0.9, "Medium": 0.5, "Low": 0.1}.get(str(geo_risk).capitalize(), 0.2),
            "impact": "negative" if geo_risk == "High" else "neutral",
        },
        {
            "label":  "Humidity Stress",
            "value":  round(min(abs(float(humidity) - 60.0) / 40.0, 1.0), 4),
            "impact": "negative" if abs(float(humidity) - 60.0) > 20 else "positive",
        },
        {
            "label":  "Spread Velocity",
            "value":  round(min(float(spread_velocity), 1.0), 4),
            "impact": "negative" if spread_velocity > 0.4 else "neutral",
        },
    ]
    return factors

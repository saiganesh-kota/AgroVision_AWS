def calibrate_confidence(confidence):
    """Normalize confidence to 0.0–1.0 range."""
    conf = float(confidence)
    if conf > 1.0:
        conf = conf / 100.0
    return max(0.0, min(1.0, conf))

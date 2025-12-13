import numpy as np

def compute_risk(sat_pos, deb_pos):
    min_dist = 9999
    for s in sat_pos:
        for d in deb_pos:
            dist = np.linalg.norm(s - d)
            min_dist = min(min_dist, dist)

    score = max(0, min(100, 100 - min_dist * 4))
    level = "HIGH" if score > 70 else "MEDIUM" if score > 40 else "LOW"

    return {
        "min_distance_km": round(min_dist, 2),
        "risk_score": score,
        "threat_level": level,
        "recommendation": "Raise orbit by 2 km" if level == "HIGH" else "No action needed"
    }

from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
import json
import os

from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DATA_FILE = Path(__file__).parent / "reviews.json"
_lock = Lock()


def _load_reviews():
    if not DATA_FILE.exists():
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_reviews(reviews):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(reviews, f, indent=2)


@app.route("/api/reviews", methods=["GET"])
def get_reviews():
    service = request.args.get("service")
    reviews = _load_reviews()
    if service:
        reviews = [r for r in reviews if r["service"].lower() == service.lower()]
    return jsonify(reviews)


@app.route("/api/reviews", methods=["POST"])
def create_review():
    data = request.get_json(force=True, silent=True) or {}
    patient_name = str(data.get("patient_name") or "").strip()
    service = str(data.get("service") or "").strip()
    comment = str(data.get("comment") or "").strip()
    rating = data.get("rating")

    if not patient_name or not service:
        return jsonify({"error": "patient_name and service are required"}), 400
    if not isinstance(rating, (int, float)) or isinstance(rating, bool) or not (1 <= rating <= 5):
        return jsonify({"error": "rating must be a number between 1 and 5"}), 400

    review = {
        "patient_name": patient_name,
        "service": service,
        "rating": rating,
        "comment": comment,
        "submitted_at": datetime.now(timezone.utc).isoformat(),
    }

    with _lock:
        reviews = _load_reviews()
        reviews.append(review)
        _save_reviews(reviews)

    return jsonify(review), 201


@app.route("/api/reviews/summary", methods=["GET"])
def reviews_summary():
    reviews = _load_reviews()
    if not reviews:
        return jsonify({"count": 0, "average_rating": None})
    average = sum(r["rating"] for r in reviews) / len(reviews)
    return jsonify({"count": len(reviews), "average_rating": round(average, 2)})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

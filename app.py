from flask import Flask, request, jsonify
from pymongo import MongoClient
from myscraper import get_music_recommendations

app = Flask(__name__)
client = MongoClient("mongodb://localhost:27017/")
db = client["musicApp"]
collection = db["user_searches"]

@app.route('/searches', methods=['POST'])
def get_user_searches():
    data = request.get_json()
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    doc = collection.find_one({"user_id": str(user_id)})

    if doc and 'searches' in doc:
        # Sort by timestamp descending and take the latest 5
        latest_searches = sorted(doc['searches'], key=lambda x: x['timestamp'], reverse=True)[:5]
        # Extract only the term values
        terms = [search['term'] for search in latest_searches]
        recommendations = get_music_recommendations(terms)

        return jsonify({
            "user_searches": terms,
            "recommendations": recommendations
        })


if __name__ == '__main__':
    app.run(debug=True)

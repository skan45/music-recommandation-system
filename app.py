from flask import Flask, request, jsonify
from pymongo import MongoClient
from chat import get_music_recommendations

app = Flask(__name__)
client = MongoClient("mongodb://localhost:27017/")
db = client["musicApp"]
fans_collection = db["fans"]  # Collection with artistPrefere and genreMusic

@app.route('/recommend', methods=['POST'])
def recommend_music():
    data = request.get_json()
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    fan_doc = fans_collection.find_one({"_id": str(user_id)})

    if not fan_doc:
        return jsonify({"error": "User not found"}), 404

    # Extract 2 artists and 2 genres
    artists = fan_doc.get("artistPrefere", [])[:2]
    genres = fan_doc.get("genreMusic", [])[:2]

    # Combine them into input for the model
    terms = artists + genres

    if not terms:
        return jsonify({"error": "No artist or genre preferences found"}), 400

    # Get recommendations using the model
    recommendations = get_music_recommendations(terms)

    return jsonify({
        "input_terms": terms,
        "recommendations": recommendations
    })

if __name__ == '__main__':
    app.run(debug=True)

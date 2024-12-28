from flask import Flask, request, jsonify
from firebase_admin import credentials, firestore, initialize_app
from fuzzywuzzy import fuzz
from flask_cors import CORS

app = Flask(__name__)

# Enable CORS
CORS(app)

# Firebase initialization
cred = credentials.Certificate(r"D:\music-5a8cc-firebase-adminsdk-pgurm-997875aacb.json")
initialize_app(cred)
db = firestore.client()

@app.route('/search', methods=['GET'])
def search_songs():
    query = request.args.get('query', '').lower()
    if not query:
        return jsonify({"error": "Query parameter is missing"}), 400

    # Fetch songs from Firestore
    songs_ref = db.collection('Songs')
    docs = songs_ref.get()

    results = []

    for doc in docs:
        song_data = doc.to_dict()
        song_title = song_data.get('Song Name', '').lower()
        artist_name = song_data.get('Song Artist', '').lower()

        # Calculate relevance score using fuzzy matching
        title_score = fuzz.partial_ratio(query, song_title)
        artist_score = fuzz.partial_ratio(query, artist_name)

        # Combine scores with weight (prioritize title over artist)
        total_score = 0.7 * title_score + 0.3 * artist_score  # 70% weight to title, 30% to artist

        # Add to results if score exceeds a threshold (e.g., 70)
        if total_score > 70:
            results.append({
                "id": doc.id,
                "title": song_data.get('Song Name', 'Unknown Title'),
                "artist": song_data.get('Song Artist', 'Unknown Artist'),
                "banner_url": song_data.get('Song Banner Url', ''),
                "audio_uri": song_data.get('Song Url', ''),
                "title_score": title_score,
                "artist_score": artist_score,
                "total_score": total_score  # Include the combined score for sorting
            })

    # Sort results first by title_score and then by artist_score in descending order
    results.sort(key=lambda x: (x['total_score'], x['title_score']), reverse=True)

    # Paginate results (e.g., 25 per page)
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 25))
    start = (page - 1) * page_size
    end = start + page_size

    paginated_results = results[start:end]

    return jsonify({"results": paginated_results}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

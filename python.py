import os
import json
from flask import Flask, request, jsonify
from firebase_admin import credentials, firestore, initialize_app
from fuzzywuzzy import fuzz
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Enable CORS
CORS(app)

# Firebase initialization using credentials from environment variable
firebase_credentials_json = os.getenv("FIREBASE_CREDENTIALS")

if not firebase_credentials_json:
    raise ValueError("Firebase credentials not found. Please set the FIREBASE_CREDENTIALS environment variable.")

try:
    firebase_credentials = json.loads(firebase_credentials_json)
except json.JSONDecodeError:
    raise ValueError("Invalid Firebase credentials format. Ensure it is a valid JSON string.")

cred = credentials.Certificate(firebase_credentials)
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

# # Run the Flask app
# if __name__ == "__main__":
#     app.run(debug=True)


# import os
# import requests
# from flask import Flask, request, jsonify
# from firebase_admin import credentials, firestore, initialize_app
# from fuzzywuzzy import fuzz
# from flask_cors import CORS
# from dotenv import load_dotenv

# # Load environment variables from .env file
# load_dotenv()

# app = Flask(__name__)

# # Enable CORS
# CORS(app)

# # URL to download the Firebase credentials from Google Drive
# FIREBASE_CREDENTIALS_URL = "https://drive.google.com/uc?export=download&id=YOUR_FILE_ID"

# # Download Firebase credentials file at runtime if not already downloaded
# def download_firebase_credentials():
#     # Check if credentials file exists
#     if not os.path.exists('firebase_credentials.json'):
#         print("Downloading Firebase credentials...")
        
#         # Make a GET request to download the file
#         response = requests.get(FIREBASE_CREDENTIALS_URL)
        
#         if response.status_code == 200:
#             with open('firebase_credentials.json', 'wb') as f:
#                 f.write(response.content)
#             print("Firebase credentials downloaded successfully.")
#         else:
#             raise Exception("Failed to download Firebase credentials.")
    
# # Download credentials
# download_firebase_credentials()

# # Firebase initialization
# cred_path = 'firebase_credentials.json'
# if not os.path.exists(cred_path):
#     raise FileNotFoundError("Firebase credentials file not found. Please check the download process.")

# cred = credentials.Certificate(cred_path)
# initialize_app(cred)
# db = firestore.client()

# @app.route('/search', methods=['GET'])
# def search_songs():
#     query = request.args.get('query', '').lower()
#     if not query:
#         return jsonify({"error": "Query parameter is missing"}), 400

#     # Fetch songs from Firestore
#     songs_ref = db.collection('Songs')
#     docs = songs_ref.get()

#     results = []

#     for doc in docs:
#         song_data = doc.to_dict()
#         song_title = song_data.get('Song Name', '').lower()
#         artist_name = song_data.get('Song Artist', '').lower()

#         # Calculate relevance score using fuzzy matching
#         title_score = fuzz.partial_ratio(query, song_title)
#         artist_score = fuzz.partial_ratio(query, artist_name)

#         # Combine scores with weight (prioritize title over artist)
#         total_score = 0.7 * title_score + 0.3 * artist_score  # 70% weight to title, 30% to artist

#         # Add to results if score exceeds a threshold (e.g., 70)
#         if total_score > 70:
#             results.append({
#                 "id": doc.id,
#                 "title": song_data.get('Song Name', 'Unknown Title'),
#                 "artist": song_data.get('Song Artist', 'Unknown Artist'),
#                 "banner_url": song_data.get('Song Banner Url', ''),
#                 "audio_uri": song_data.get('Song Url', ''),
#                 "title_score": title_score,
#                 "artist_score": artist_score,
#                 "total_score": total_score  # Include the combined score for sorting
#             })

#     # Sort results first by title_score and then by artist_score in descending order
#     results.sort(key=lambda x: (x['total_score'], x['title_score']), reverse=True)

#     # Paginate results (e.g., 25 per page)
#     page = int(request.args.get('page', 1))
#     page_size = int(request.args.get('page_size', 25))
#     start = (page - 1) * page_size
#     end = start + page_size

#     paginated_results = results[start:end]

#     return jsonify({"results": paginated_results}), 200

# # Run the Flask app
# if __name__ == "__main__":
#     app.run(debug=True)

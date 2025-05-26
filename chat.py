import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Get API keys from environment
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

# Configure Gemini
genai.configure(api_key=GOOGLE_API_KEY)

# Initialize Spotify client
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET
))

# Initialize Gemini model
gemini_model = genai.GenerativeModel("gemini-2.0-flash-001")


def get_artist_info(artist_name, market="TN"):
    try:
        result = sp.search(q=f"artist:{artist_name}", type="artist", limit=1, market=market)
        if result["artists"]["items"]:
            artist = result["artists"]["items"][0]
            return {
                "id": artist["id"],
                "url": f"https://open.spotify.com/artist/{artist['id']}"
            }
    except Exception as e:
        print(f"Error finding artist {artist_name}: {e}")
    return None


def get_top_track(artist_name, market="TN"):
    artist_info = get_artist_info(artist_name, market)
    if not artist_info:
        return None
    try:
        top_tracks = sp.artist_top_tracks(artist_info["id"], country=market)
        if not top_tracks["tracks"]:
            top_tracks = sp.artist_top_tracks(artist_info["id"])
        if top_tracks["tracks"]:
            track = top_tracks["tracks"][0]
            return {
                "name": track["name"],
                "url": f"https://open.spotify.com/track/{track['id']}"
            }
    except Exception as e:
        print(f"Error fetching top track for {artist_name}: {e}")
    return None


def get_music_recommendations(user_searches):
    # Create Gemini prompt
    prompt = f"""
    You are a music recommendation expert specializing in Tunisian rap and related genres. The user’s last five searches on a music platform are: {', '.join(user_searches)}. Based on these searches, recommend exactly three artists (excluding Balti, Sanfara, and Klay BBJ) that closely match the user’s preferences for Tunisian rap, drill, or chill rap tunisien. For each artist, provide a brief explanation of why they are relevant to the user's taste. Do not include song names, as they will be sourced from Spotify.

    Your response must be in plain text with **exactly three** recommendations, each on a new line, using the following format:
    Artist: [Artist Name] | Why: [Explanation]

    Do not include any additional text, comments, or formatting outside of the three lines.
    """

    recommended_artists = []

    try:
        response = gemini_model.generate_content(prompt)
        if response.text and response.text.strip():
            lines = response.text.strip().split("\n")
            for line in lines:
                line = line.strip()
                if ": | Why:" in line:
                    parts = line.split(": | Why:", 1)
                    if len(parts) == 2:
                        artist = parts[0].replace("Artist", "").strip(": ").strip()
                        why = parts[1].strip()
                        recommended_artists.append({"artist": artist, "why": why})
    except Exception as e:
        print(f"Error with Gemini API: {e}")
        return []

    # Enrich with Spotify data
    final_recommendations = []
    for rec in recommended_artists:
        artist = rec["artist"]
        artist_info = get_artist_info(artist)
        song_info = get_top_track(artist)
        final_recommendations.append({
            "artist": artist,
            "why": rec["why"],
            "artist_url": artist_info["url"] if artist_info else "Not found",
            "top_song": song_info["name"] if song_info else "Not found",
            "song_url": song_info["url"] if song_info else "Not found"
        })

    return final_recommendations

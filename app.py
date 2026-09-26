import os
import requests

from flask import Flask, render_template, redirect, request, session
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth


load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")
LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")


def create_spotify_oauth():
    return SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope="user-top-read user-library-read playlist-modify-private"
    )

def get_liked_tracks(spotify):
    liked_tracks = []
    results = spotify.current_user_saved_tracks(limit=50)

    while results:
        for item in results["items"]:
            liked_tracks.append(item["track"])

        if results["next"]:
            results = spotify.next(results)
        else:
            break

    return liked_tracks

def get_discography_candidates(spotify, artist_id, known_track_ids):
    candidates = []

    albums = spotify.artist_albums(
        artist_id,
        album_type="album",
        limit=10
    )

    for album_rank, album in enumerate(albums["items"], start=1):
        tracks = spotify.album_tracks(album["id"], limit=50)

        for track in tracks["items"]:

            if not track["artists"]:
                continue

            primary_artist_id = track["artists"][0]["id"]

            if primary_artist_id != artist_id:
                continue

            if track["id"] not in known_track_ids:
                candidates.append({
                    "id": track["id"],
                    "name": track["name"],
                    "album_name": album["name"],
                    "album_id": album["id"],
                    "album_rank": album_rank
                })

    return candidates

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/login")
def login():
    spotify_oauth = create_spotify_oauth()
    authorization_url = spotify_oauth.get_authorize_url()

    return redirect(authorization_url)

@app.route("/callback")
def callback():
    spotify_oauth = create_spotify_oauth()

    code = request.args.get("code")

    token_info = spotify_oauth.get_access_token(code, as_dict=True)

    session["token_info"] = token_info

    return redirect("/profile")

@app.route("/profile")
def profile():
    token_info = session.get("token_info")

    if not token_info:
        return redirect("/login")

    spotify = spotipy.Spotify(auth=token_info["access_token"])

    user = spotify.current_user()

    top_artists = spotify.current_user_top_artists(
        limit=10,
        time_range="medium_term"
    )
    # i think this is all testing??
    first_artist = top_artists["items"][0]

    artist_profile = build_artist_profile(
        spotify,
        first_artist
    )

    top_tracks = spotify.current_user_top_tracks(
        limit=10,
        time_range="medium_term"
    )
    """ commenting this out bc it's slow
    liked_tracks = get_liked_tracks(spotify)

    known_track_ids = set()

    for track in liked_tracks:
        known_track_ids.add(track["id"])

    for track in top_tracks["items"]:
        known_track_ids.add(track["id"])

    print("Liked tracks:", len(liked_tracks))
    print("Known tracks:", len(known_track_ids))

    """


    return render_template(
        "profile.html",
        user=user,
        top_artists=top_artists["items"],
        top_tracks=top_tracks["items"]
    )

@app.route("/artist/<artist_id>")
def artist_page(artist_id):
    token_info = session.get("token_info")

    if not token_info:
        return redirect("/login")

    spotify = spotipy.Spotify(auth=token_info["access_token"])

    artist = spotify.artist(artist_id)

    similar_artists = get_similar_spotify_artists(
        spotify,
        artist["name"],
        limit=10
    )

    albums = spotify.artist_albums(
        artist_id,
        album_type="album",
        limit=10
    )

    top_tracks = spotify.current_user_top_tracks(
        limit=50,
        time_range="medium_term"
    )

    known_track_ids = {
        track["id"] for track in top_tracks["items"]
    }

    candidates = get_discography_candidates(
        spotify,
        artist_id,
        known_track_ids
    )

    return render_template(
        "artist.html",
        artist=artist,
        albums=albums["items"],
        candidates=candidates,
        similar_artists=similar_artists
    )

@app.route("/album/<album_id>")
def album_page(album_id):
    token_info = session.get("token_info")

    if not token_info:
        return redirect("/login")

    spotify = spotipy.Spotify(auth=token_info["access_token"])

    album = spotify.album(album_id)

    tracks = spotify.album_tracks(
        album_id,
        limit=50
    )

    return render_template(
        "album.html",
        album=album,
        tracks=tracks["items"]
    )

@app.route("/recommendations")
def recommendations():
    token_info = session.get("token_info")

    if not token_info:
        return redirect("/login")

    spotify = spotipy.Spotify(
        auth=token_info["access_token"]
    )

    top_artists = spotify.current_user_top_artists(
        limit=5,
        time_range="medium_term"
    )["items"]

    similar_artist_pool = build_similar_artist_pool(
        spotify,
        top_artists,
        similar_per_artist=5
    )

    for artist in similar_artist_pool:
        artist["score"] = score_similar_artist(artist)

    similar_artist_pool.sort(
        key=lambda artist: artist["score"],
        reverse=True
    )

    top_tracks = spotify.current_user_top_tracks(
        limit=50,
        time_range="medium_term"
    )["items"]

    favorite_album_ids = set()

    for track in top_tracks:
        favorite_album_ids.add(track["album"]["id"])

    known_track_ids = {
        track["id"] for track in top_tracks
    }

    candidates = build_favorite_artist_candidates(
        spotify,
        top_artists,
        known_track_ids,
        favorite_album_ids
    )

    similar_candidates = build_similar_artist_candidates(
        spotify,
        similar_artist_pool,
        known_track_ids,
        artist_limit=5
    )

    candidates.extend(similar_candidates)

    unique_candidates = {}

    for track in candidates:
        key = (
            track["artist"].lower(),
            track["name"].lower()
        )

        if key not in unique_candidates:
            unique_candidates[key] = track

        elif track["score"] > unique_candidates[key]["score"]:
            unique_candidates[key] = track

    candidates = list(unique_candidates.values())

    candidates.sort(
        key=lambda track: track["score"],
        reverse=True
    )

    selected_tracks = select_balanced_tracks(
        candidates,
        playlist_size=30,
        max_per_artist=5,
        max_per_album=3
    )

    return render_template(
        "recommendations.html",
        candidates=candidates,
        selected_tracks=selected_tracks
    )

def build_artist_profile(spotify, artist):
    albums = spotify.artist_albums(
        artist["id"],
        album_type="album",
        limit=10
    )

    album_data = []

    for album in albums["items"]:
        album_data.append({
            "id": album["id"],
            "name": album["name"],
            "release_date": album["release_date"]
        })

    return {
        "id": artist["id"],
        "name": artist["name"],
        "albums": album_data
    }

def get_similar_artists(artist_name, limit=10):
    url = "https://ws.audioscrobbler.com/2.0/"

    params = {
        "method": "artist.getsimilar",
        "artist": artist_name,
        "api_key": LASTFM_API_KEY,
        "format": "json",
        "limit": limit
    }

    response = requests.get(url, params=params)
    response.raise_for_status()

    data = response.json()

    similar_artists = []

    for artist in data["similarartists"]["artist"]:
        similar_artists.append({
            "name": artist["name"],
            "match": float(artist["match"])
        })

    return similar_artists

def find_spotify_artist(spotify, artist_name):
    results = spotify.search(
        q=f"artist:{artist_name}",
        type="artist",
        limit=1
    )

    artists = results["artists"]["items"]

    if not artists:
        return None

    return artists[0]
def get_similar_spotify_artists(spotify, artist_name, limit=10):
    lastfm_artists = get_similar_artists(artist_name, limit)

    similar_artists = []

    for lastfm_artist in lastfm_artists:
        spotify_artist = find_spotify_artist(
            spotify,
            lastfm_artist["name"]
        )

        if spotify_artist is None:
            continue

        similar_artists.append({
            "id": spotify_artist["id"],
            "name": spotify_artist["name"],
            "lastfm_name": lastfm_artist["name"],
            "match": lastfm_artist["match"]
        })

    return similar_artists

def score_candidate(
    source_artist_rank,
    same_favorite_album=False,
    similarity=1.0,
    same_artist=True
):
    artist_affinity = 1 / source_artist_rank

    album_score = 1.0 if same_favorite_album else 0.0

    if same_artist:
        source_score = 1.0
    else:
        source_score = similarity

    score = (
        0.45 * artist_affinity + # how important is this artist to the user?
        0.35 * album_score + # is this from an album containing a favorite song?
        0.20 * source_score # what type/strength of artist connection produced it?
    )

    return score

def build_favorite_artist_candidates(
    spotify,
    top_artists,
    known_track_ids,
    favorite_album_ids
):
    candidates = []

    for rank, artist in enumerate(top_artists, start=1):

        tracks = get_discography_candidates(
            spotify,
            artist["id"],
            known_track_ids
        )

        for track in tracks:

            same_favorite_album = track["album_id"] in favorite_album_ids

            score = score_candidate(
                source_artist_rank=rank,
                same_favorite_album=same_favorite_album,
                same_artist=True
            )

            candidates.append({
                "id": track["id"],
                "name": track["name"],
                "artist": artist["name"],
                "album": track["album_name"],
                "source_artist": artist["name"],
                "reason": "favorite_artist_discography",
                "same_favorite_album": same_favorite_album,
                "score": score
            })

    return candidates

def select_balanced_tracks(
    candidates,
    playlist_size=30,
    max_per_artist=5,
    max_per_album=3
):
    selected = []

    artist_counts = {}
    album_counts = {}

    for track in candidates:
        artist = track["artist"]
        album = track["album"]

        artist_count = artist_counts.get(artist, 0)
        album_count = album_counts.get(album, 0)

        if artist_count >= max_per_artist:
            continue

        if album_count >= max_per_album:
            continue

        selected.append(track)

        artist_counts[artist] = artist_count + 1
        album_counts[album] = album_count + 1

        if len(selected) >= playlist_size:
            break

    return selected

def normalize_artist_name(name):
    return (
        name.lower()
        .replace("$", "s")
        .replace(".", "")
        .replace("-", " ")
        .strip()
    )

def build_similar_artist_pool(spotify, top_artists, similar_per_artist=5):
    top_artist_ids = {
        artist["id"] for artist in top_artists
    }

    top_artist_names = {
        normalize_artist_name(artist["name"])
        for artist in top_artists
    }

    similar_artist_pool = {}

    for rank, source_artist in enumerate(top_artists, start=1):

        similar_artists = get_similar_spotify_artists(
            spotify,
            source_artist["name"],
            limit=similar_per_artist
        )

        for similar in similar_artists:

            if (
                similar["id"] in top_artist_ids
                or normalize_artist_name(similar["name"]) in top_artist_names
            ):
                continue

            artist_id = similar["id"]

            connection = {
                "source_artist": source_artist["name"],
                "source_artist_rank": rank,
                "similarity": similar["match"]
            }

            if artist_id not in similar_artist_pool:
                similar_artist_pool[artist_id] = {
                    "id": artist_id,
                    "name": similar["name"],
                    "connections": []
                }

            similar_artist_pool[artist_id]["connections"].append(
                connection
            )

    return list(similar_artist_pool.values())

def score_similar_artist(artist):
    connection_scores = []

    for connection in artist["connections"]:
        artist_affinity = 1 / connection["source_artist_rank"]
        similarity = connection["similarity"]

        connection_score = (
            0.5 * artist_affinity +
            0.5 * similarity
        )

        connection_scores.append(connection_score)

    best_connection = max(connection_scores)

    extra_connections = len(connection_scores) - 1
    connection_bonus = min(extra_connections * 0.05, 0.15)

    return min(best_connection + connection_bonus, 1.0)

def build_similar_artist_candidates(
    spotify,
    similar_artist_pool,
    known_track_ids,
    artist_limit=5
):
    candidates = []

    selected_artists = similar_artist_pool[:artist_limit]

    for artist in selected_artists:

        tracks = get_discography_candidates(
            spotify,
            artist["id"],
            known_track_ids
        )

        best_connection = get_best_artist_connection(artist)

        for track in tracks:
            candidates.append({
                "id": track["id"],
                "name": track["name"],
                "artist": artist["name"],
                "album": track["album_name"],

                # This tells us WHY this track was recommended.
                "source_artist": best_connection["source_artist"],
                "reason": "similar_artist_discovery",

                "similar_artist_score": artist["score"],
                "score": artist["score"]
            })

    return candidates

def get_best_artist_connection(artist):
    return max(
        artist["connections"],
        key=lambda connection: (
            0.5 * (1 / connection["source_artist_rank"])
            + 0.5 * connection["similarity"]
        )
    )

if __name__ == "__main__":
    app.run(debug=True, port=5000)
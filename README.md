# Spotify Music Discover and Playlist Generator

A Flask web application that analyzes a user's Spotify listening preferences to generate personalized music discovery playlists.

Rather than relying solely on recommendations returned by Spotify, the application builds its own recommendation pipeline using listening affinity, artist discographies, cross-platform artist similarity, candidate scoring, duplicate filtering, and playlist diversity constraints.

Generated playlists can be reviewed in the web application and created directly in the user's Spotify account.

## Features

- Spotify OAuth authentication
- Analysis of a user's top artists and tracks
- Artist and album discography exploration
- Discovery of tracks outside the user's current top songs
- Similar-artist discovery using the Last.fm API
- Cross-platform artist matching between Last.fm and Spotify
- Artist alias filtering to reduce duplicate artist recommendations
- Custom recommendation scoring based on:
  - user affinity for source artists
  - Last.fm artist similarity
  - connections through multiple favorite artists
  - album relationships
- Filtering of duplicate and invalid recommendation candidates
- Playlist diversity constraints across artists and albums
- Generation of a balanced 30-track discovery playlist
- Automatic creation of the generated playlist in the user's Spotify account

## Recommendation Pipeline

The recommendation engine combines multiple data sources and ranking signals instead of simply displaying recommendations from an external API.

```text
Spotify listening data
        |
        v
User's top artists and tracks
        |
        +--------------------------+
        |                          |
        v                          v
Favorite artist             Last.fm artist
discographies                 similarity
        |                          |
        |                          v
        |                  Spotify artist matching
        |                          |
        |                          v
        |                  Similar artist pool
        |                          |
        |                          v
        |                  Custom artist scoring
        |                          |
        +------------+-------------+
                     |
                     v
             Track candidates
                     |
                     v
        Primary-artist filtering
                     |
                     v
              Deduplication
                     |
                     v
             Candidate ranking
                     |
                     v
       Artist/album diversity rules
                     |
                     v
          Generated playlist
                     |
                     v
             Spotify playlist
```

### Similar Artist Scoring

Similar artists are scored using a combination of:

- the user's affinity for the favorite artist that produced the connection
- the similarity value returned by Last.fm
- additional evidence when a discovered artist is connected to multiple favorite artists

This allows the application to use external similarity data as one signal while performing its own ranking and selection.

## Tech Stack

**Backend**
- Python
- Flask

**APIs**
- Spotify Web API
- Last.fm API

**Libraries**
- Spotipy
- Requests
- python-dotenv

**Frontend**
- HTML
- Jinja templates

**Development**
- Git
- GitHub

## Running Locally

### 1. Clone the repository

```bash
git clone https://github.com/annakerns/spotify-playlist-generator.git
cd spotify-playlist-generator
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create a `.env` file

Create a `.env` file in the project root containing:

```text
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:5000/callback
FLASK_SECRET_KEY=your_flask_secret_key
LASTFM_API_KEY=your_lastfm_api_key
```

API credentials are intentionally excluded from version control.

### 5. Run the application

```bash
python app.py
```

Then open:

```text
http://127.0.0.1:5000
```

## Current Status

The application currently supports an end-to-end music discovery workflow:

1. Authenticate with Spotify
2. Analyze the user's top artists and tracks
3. Explore favorite-artist discographies
4. Discover related artists through Last.fm
5. Generate and rank recommendation candidates
6. Apply artist and album diversity constraints
7. Preview a generated discovery playlist
8. Create the playlist directly in the user's Spotify account

## Planned Improvements

- User-selectable playlist length
- Adjustable familiarity vs. discovery level
- Improved track-level recommendation scoring
- Familiar-song anchors within discovery playlists
- More robust cross-platform artist matching
- Recommendation explanations in the interface
- Performance improvements and API-response caching
- Improved frontend design and playlist visualization
# Spotify Playlist Generator

A music discovery web application designed to help users explore the discographies of their favorite artists and discover related artists.

Rather than generating playlists solely from a user's existing favorite songs, the application uses listening history as a starting point to recommend tracks from relevant albums, deeper portions of artists' catalogs, and similar artists.

## Current Features

- Spotify OAuth authentication
- Retrieval of a user's top artists and tracks
- Artist and album discography exploration
- Discography-based recommendation candidate generation
- Artist similarity data using the Last.fm API
- Cross-API mapping between Last.fm artists and Spotify artists
- Custom recommendation scoring based on artist affinity and album relevance
- Duplicate-track filtering

## Recommendation Approach

The application builds its own recommendation layer on top of music data retrieved from Spotify and Last.fm.

Current recommendation scoring considers:

- the user's affinity for an artist based on their top-artist ranking
- whether a candidate track belongs to an album containing one of the user's top tracks
- the source of the recommendation
- artist similarity information from Last.fm

The recommendation system is being developed iteratively, with future versions incorporating playlist diversity, familiarity modeling, and deeper similar-artist exploration.

## Tech Stack

- Python
- Flask
- Spotify Web API
- Last.fm API
- Spotipy
- HTML
- Git / GitHub

## Project Status

This project is currently under active development.

Current focus: converting the ranked recommendation candidate pool into balanced playlists containing both favorite-artist discography discoveries and similar-artist discoveries.

## Running Locally

1. Clone the repository.
2. Create and activate a Python virtual environment.
3. Install dependencies:

```bash
pip install -r requirements.txt
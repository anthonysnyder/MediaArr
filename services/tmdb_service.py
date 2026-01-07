"""
TMDb API service for fetching movie/TV metadata and artwork
"""

import requests
import os


class TMDbService:
    """Handles all interactions with The Movie Database API"""

    BASE_URL = "https://api.themoviedb.org/3"
    IMAGE_BASE_URL = "https://image.tmdb.org/t/p/original"

    def __init__(self, api_key: str):
        """
        Initialize TMDb service with API key.

        Args:
            api_key: TMDb API key
        """
        self.api_key = api_key

    def search_movies(self, query: str) -> list:
        """
        Search for movies by title.

        Args:
            query: Movie title to search for

        Returns:
            List of movie results from TMDb
        """
        try:
            response = requests.get(
                f"{self.BASE_URL}/search/movie",
                params={"api_key": self.api_key, "query": query}
            )
            response.raise_for_status()
            return response.json().get('results', [])
        except Exception as e:
            print(f"Error searching movies: {e}")
            return []

    def search_tv(self, query: str) -> list:
        """
        Search for TV shows by title.

        Args:
            query: TV show title to search for

        Returns:
            List of TV show results from TMDb
        """
        try:
            response = requests.get(
                f"{self.BASE_URL}/search/tv",
                params={
                    "api_key": self.api_key,
                    "query": query,
                    "include_adult": False,
                    "language": "en-US",
                    "page": 1
                }
            )
            response.raise_for_status()
            return response.json().get('results', [])
        except Exception as e:
            print(f"Error searching TV shows: {e}")
            return []

    def get_movie_details(self, movie_id: int) -> dict:
        """
        Get detailed information about a movie.

        Args:
            movie_id: TMDb movie ID

        Returns:
            Movie details dictionary
        """
        try:
            response = requests.get(
                f"{self.BASE_URL}/movie/{movie_id}",
                params={"api_key": self.api_key}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error getting movie details: {e}")
            return {}

    def get_tv_details(self, tv_id: int) -> dict:
        """
        Get detailed information about a TV show.

        Args:
            tv_id: TMDb TV show ID

        Returns:
            TV show details dictionary
        """
        try:
            response = requests.get(
                f"{self.BASE_URL}/tv/{tv_id}",
                params={"api_key": self.api_key}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error getting TV details: {e}")
            return {}

    def get_backdrops(self, tmdb_id: int, media_type: str) -> list:
        """
        Get available backdrops for a movie or TV show.

        Args:
            tmdb_id: TMDb ID
            media_type: 'movie' or 'tv'

        Returns:
            List of backdrop dictionaries sorted by resolution (highest first)
        """
        try:
            endpoint = f"{self.BASE_URL}/{media_type}/{tmdb_id}/images"
            response = requests.get(endpoint, params={"api_key": self.api_key})
            response.raise_for_status()

            backdrops = response.json().get('backdrops', [])

            # Sort by resolution (highest first)
            backdrops_sorted = sorted(
                backdrops,
                key=lambda b: b['width'] * b['height'],
                reverse=True
            )

            # Format for display
            return [{
                'url': f"{self.IMAGE_BASE_URL}{backdrop['file_path']}",
                'size': f"{backdrop['width']}x{backdrop['height']}",
                'language': backdrop.get('iso_639_1', 'N/A')
            } for backdrop in backdrops_sorted]

        except Exception as e:
            print(f"Error getting backdrops: {e}")
            return []

    def get_logos(self, tmdb_id: int, media_type: str) -> list:
        """
        Get available logos for a movie or TV show.

        Args:
            tmdb_id: TMDb ID
            media_type: 'movie' or 'tv'

        Returns:
            List of logo dictionaries (English only, sorted by resolution)
        """
        try:
            endpoint = f"{self.BASE_URL}/{media_type}/{tmdb_id}/images"
            response = requests.get(endpoint, params={"api_key": self.api_key})
            response.raise_for_status()

            logos = response.json().get('logos', [])

            # Filter to English only
            logos = [logo for logo in logos if logo.get('iso_639_1') == 'en']

            # Sort by resolution (highest first)
            logos_sorted = sorted(
                logos,
                key=lambda l: l['width'] * l['height'],
                reverse=True
            )

            # Format for display
            return [{
                'url': f"{self.IMAGE_BASE_URL}{logo['file_path']}",
                'size': f"{logo['width']}x{logo['height']}",
                'language': logo.get('iso_639_1', 'N/A')
            } for logo in logos_sorted]

        except Exception as e:
            print(f"Error getting logos: {e}")
            return []

    def get_posters(self, tmdb_id: int, media_type: str) -> list:
        """
        Get available posters for a movie or TV show.

        Args:
            tmdb_id: TMDb ID
            media_type: 'movie' or 'tv'

        Returns:
            List of poster dictionaries (English only, sorted by resolution)
        """
        try:
            endpoint = f"{self.BASE_URL}/{media_type}/{tmdb_id}/images"
            response = requests.get(endpoint, params={"api_key": self.api_key})
            response.raise_for_status()

            posters = response.json().get('posters', [])

            # Filter to English only
            posters = [poster for poster in posters if poster.get('iso_639_1') == 'en']

            # Sort by resolution (highest first)
            posters_sorted = sorted(
                posters,
                key=lambda p: p['width'] * p['height'],
                reverse=True
            )

            # Format for display
            return [{
                'url': f"{self.IMAGE_BASE_URL}{poster['file_path']}",
                'size': f"{poster['width']}x{poster['height']}",
                'language': poster.get('iso_639_1', 'N/A')
            } for poster in posters_sorted]

        except Exception as e:
            print(f"Error getting posters: {e}")
            return []

import os
import json
import nltk
import numpy as np
import requests
import time
import re
from flask import Flask, request, jsonify, render_template
from flask import send_from_directory
from flask_cors import CORS
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime
import random
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor

# Set custom download directory
NLTK_DIR = "/tmp/nltk_data"
nltk.data.path.append(NLTK_DIR)

# Download required models if not already present
nltk.download("punkt", download_dir=NLTK_DIR, quiet=True)
nltk.download("wordnet", download_dir=NLTK_DIR, quiet=True)
nltk.download("stopwords", download_dir=NLTK_DIR, quiet=True)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Constants
DATA_FILE = "movie_data.json"
API_KEY_FILE = "tmdb_api_key.txt"
TMDB_BASE_URL = "https://api.themoviedb.org/3"

# Updated target counts - focusing only on Hollywood and Bollywood
HOLLYWOOD_COUNT = 8000  # Increased count
BOLLYWOOD_COUNT = 2000  # Increased count

# Total target count
TARGET_MOVIE_COUNT = HOLLYWOOD_COUNT + BOLLYWOOD_COUNT

# Constants for optimized fetching
MAX_THREADS = 5
CACHE_SIZE = 1000
BATCH_SIZE = 20  # Process movies in batches


class MovieRecommender:
    def __init__(self):
        self.movies = []
        self.tfidf_matrix = None
        self.vectorizer = None
        self.api_key = self._load_api_key()
        self.unique_movie_ids = set()  # To track unique movies

        # Load existing data or fetch new data
        if os.path.exists(DATA_FILE):
            self._load_data()
            # If loaded data is less than target, fetch more
            if len(self.movies) < TARGET_MOVIE_COUNT:
                print(
                    f"Only {len(self.movies)} movies in dataset, fetching more to reach {TARGET_MOVIE_COUNT}..."
                )
                self._fetch_additional_data()
        else:
            self._fetch_and_process_data()

        self._prepare_tfidf()

    def _load_api_key(self):
        """Load TMDB API key from a mounted file (Render Secret File)"""
        api_key_path = "/etc/secrets/tmdb_api_key"
        try:
            with open(api_key_path, "r") as f:
                return f.read().strip()
        except FileNotFoundError:
            raise ValueError(f"API key file not found at {api_key_path}")

    def _load_data(self):
        """Load movie data from JSON file"""
        print("Loading existing movie data...")
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                self.movies = json.load(f)
            # Populate the unique IDs set
            self.unique_movie_ids = set(movie["id"] for movie in self.movies)
            print(f"Loaded {len(self.movies)} movies")
        except json.JSONDecodeError:
            print("Error parsing JSON file. Starting with empty dataset.")
            self.movies = []
            self.unique_movie_ids = set()

    def _fetch_and_process_data(self):
        """Fetch a large dataset of movies from TMDB API using multiple methods"""
        print(f"Fetching {TARGET_MOVIE_COUNT} movies from TMDB API...")
        self.movies = []
        self.unique_movie_ids = set()

        # Track progress
        start_time = time.time()

        # Track movie counts by category
        hollywood_count = 0
        bollywood_count = 0

        # 1. Fetch Hollywood movies first (popular movies)
        print(f"Phase 1: Fetching Hollywood movies (target: {HOLLYWOOD_COUNT})...")

        # 1.1 Fetch popular movies
        self._fetch_from_endpoint("movie/popular", pages=50)
        hollywood_count = len(self.unique_movie_ids)
        self._save_progress("Popular Movies")

        # 1.2 Fetch top-rated movies
        self._fetch_from_endpoint("movie/top_rated", pages=50)
        hollywood_count = len(self.unique_movie_ids)
        self._save_progress("Top Rated Movies")

        # 1.3 Fetch movies by year (recent years first)
        current_year = datetime.now().year
        years_to_fetch = list(
            range(current_year, current_year - 50, -1)
        )  # 50 years back

        # Fetch in batches with threads
        with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            futures = {
                executor.submit(self._fetch_by_year, year, 5, True): year
                for year in years_to_fetch
            }
            for future in futures:
                future.result()  # Wait for completion
                hollywood_count = len(self.unique_movie_ids)
                self._save_progress(f"Year {futures[future]}")

                if hollywood_count >= HOLLYWOOD_COUNT:
                    break

        # 1.4 Fetch movies by genre
        genres = self._get_genres()

        # Fetch in batches with threads
        if hollywood_count < HOLLYWOOD_COUNT:
            with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
                futures = {
                    executor.submit(
                        self._fetch_by_genre, genre["id"], genre["name"], 10
                    ): genre["name"]
                    for genre in genres
                }
                for future in futures:
                    future.result()  # Wait for completion
                    hollywood_count = len(self.unique_movie_ids)
                    self._save_progress(f"Genre {futures[future]}")

                    if hollywood_count >= HOLLYWOOD_COUNT:
                        break

        # 1.5 Fetch by top studios if still needed
        if hollywood_count < HOLLYWOOD_COUNT:
            top_studios = [
                420,  # Marvel Studios
                2,  # Disney
                33,  # Universal Pictures
                4,  # Paramount
                174,  # Warner Bros. Pictures
                7505,  # Sony Pictures
                25,  # 20th Century Fox
                4171,  # Pixar
                41,  # Dreamworks
            ]

            with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
                futures = {
                    executor.submit(self._fetch_by_company, studio_id, 10): studio_id
                    for studio_id in top_studios
                }
                for future in futures:
                    future.result()  # Wait for completion
                    hollywood_count = len(self.unique_movie_ids)
                    self._save_progress(f"Studio {futures[future]}")

                    if hollywood_count >= HOLLYWOOD_COUNT:
                        break

        # 2. Fetch Bollywood movies (Hindi cinema)
        print(f"Phase 2: Fetching Bollywood movies (target: {BOLLYWOOD_COUNT})...")
        bollywood_start_count = len(self.unique_movie_ids)
        bollywood_fetched = 0

        # 2.1 Using discover endpoint with Hindi language parameter
        max_pages = 100  # Increase pages to get more Bollywood content
        page = 1
        while bollywood_fetched < BOLLYWOOD_COUNT and page <= max_pages:
            url = f"{TMDB_BASE_URL}/discover/movie?api_key={self.api_key}&with_original_language=hi&page={page}&sort_by=popularity.desc"
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])
                    if not results:
                        break

                    before_count = len(self.unique_movie_ids)
                    self._process_movie_results(results, is_bollywood=True)
                    after_count = len(self.unique_movie_ids)
                    bollywood_fetched += after_count - before_count

                    self._save_progress(f"Bollywood movies (page {page})")
                    page += 1
                    time.sleep(0.3)  # Slightly reduced sleep time

                    # Break if we've reached end of results
                    if page > data.get("total_pages", 1):
                        break
                else:
                    print(
                        f"Error {response.status_code} when fetching Bollywood movies"
                    )
                    time.sleep(1)
            except Exception as e:
                print(f"Exception while fetching Bollywood movies: {e}")
                time.sleep(1)

        print(f"Fetched {bollywood_fetched} Bollywood movies")

        # 2.2 Fetch by popular Bollywood studios/production companies (optimized with parallel fetching)
        if bollywood_fetched < BOLLYWOOD_COUNT:
            bollywood_studios = [
                1569,  # Yash Raj Films
                2515,  # Dharma Productions
                1913,  # Excel Entertainment
                5626,  # Red Chillies Entertainment
                1884,  # UTV Motion Pictures
                3538,  # T-Series
                7294,  # Viacom18 Studios
                128250,  # Aamir Khan Productions
                156782,  # Sanjay Leela Bhansali Productions
                2043,  # Balaji Motion Pictures
                10039,  # Nadiadwala Grandson Entertainment
                12299,  # Reliance Entertainment
                133990,  # Maddock Films
                56369,  # Phantom Films
                138377,  # Colour Yellow Productions
            ]

            with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
                futures = {
                    executor.submit(
                        self._fetch_bollywood_by_studio, studio_id
                    ): studio_id
                    for studio_id in bollywood_studios
                }
                for future in futures:
                    future.result()  # Wait for completion
                    current_bollywood = len(self.unique_movie_ids) - hollywood_count
                    self._save_progress(f"Bollywood studio {futures[future]}")

                    if current_bollywood >= BOLLYWOOD_COUNT:
                        break

        # Final save
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.movies, f, ensure_ascii=False, indent=2)

        elapsed_time = (time.time() - start_time) / 60

        # Print summary
        print("\n=== FINAL SUMMARY ===")
        print(f"Total movies in dataset: {len(self.movies)}")
        print(f"- Hollywood: {hollywood_count}")
        print(f"- Bollywood: {len(self.unique_movie_ids) - hollywood_count}")
        print(f"Fetched and saved in {elapsed_time:.2f} minutes")

    def _fetch_bollywood_by_studio(self, studio_id, max_pages=10):
        """Fetch Bollywood movies from a specific studio"""
        url = f"{TMDB_BASE_URL}/discover/movie?api_key={self.api_key}&with_companies={studio_id}&with_original_language=hi&page=1&sort_by=popularity.desc"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                total_pages = min(data.get("total_pages", 1), max_pages)

                # Process first page results
                self._process_movie_results(data.get("results", []), is_bollywood=True)

                # Process remaining pages in parallel
                if total_pages > 1:
                    with ThreadPoolExecutor(
                        max_workers=3
                    ) as executor:  # Use fewer threads for nested operations
                        for page in range(2, total_pages + 1):
                            url = f"{TMDB_BASE_URL}/discover/movie?api_key={self.api_key}&with_companies={studio_id}&with_original_language=hi&page={page}&sort_by=popularity.desc"
                            try:
                                resp = requests.get(url)
                                if resp.status_code == 200:
                                    page_data = resp.json()
                                    self._process_movie_results(
                                        page_data.get("results", []), is_bollywood=True
                                    )
                                    time.sleep(0.3)
                            except Exception as e:
                                print(
                                    f"Error on page {page} for studio {studio_id}: {e}"
                                )
        except Exception as e:
            print(f"Error fetching from Bollywood studio {studio_id}: {e}")

    def _fetch_additional_data(self):
        """Fetch additional movies to reach the target count"""
        current_count = len(self.movies)
        if current_count >= TARGET_MOVIE_COUNT:
            return

        # How many more movies we need
        needed = TARGET_MOVIE_COUNT - current_count

        # Count movies by category in current dataset
        hollywood_count = 0
        bollywood_count = 0

        for movie in self.movies:
            language = movie.get("language", "unknown")

            if language == "hi":
                bollywood_count += 1
            else:
                hollywood_count += 1

        print(f"\nCurrent counts:")
        print(f"- Hollywood: {hollywood_count}")
        print(f"- Bollywood: {bollywood_count}")

        # Calculate how many more of each category we need
        need_hollywood = max(0, HOLLYWOOD_COUNT - hollywood_count)
        need_bollywood = max(0, BOLLYWOOD_COUNT - bollywood_count)

        print(f"\nNeed to fetch:")
        print(f"- Hollywood: {need_hollywood}")
        print(f"- Bollywood: {need_bollywood}")

        # First try to fetch more Bollywood movies if needed (typically harder to find)
        if need_bollywood > 0:
            print(f"Fetching {need_bollywood} more Bollywood movies...")

            # 1. Using Hindi language filter - more pages
            pages_to_fetch = min(100, need_bollywood // 20 + 5)
            self._fetch_by_language("hi", max_pages=pages_to_fetch)

            # 2. Try actor-specific searches for popular Bollywood actors
            bollywood_actors = [
                "Shah Rukh Khan",
                "Amitabh Bachchan",
                "Aamir Khan",
                "Salman Khan",
                "Hrithik Roshan",
                "Ranbir Kapoor",
                "Ranveer Singh",
                "Akshay Kumar",
                "Deepika Padukone",
                "Priyanka Chopra",
                "Alia Bhatt",
                "Katrina Kaif",
            ]

            # Use the search endpoint to find movies by these actors
            for actor in bollywood_actors:
                if bollywood_count >= BOLLYWOOD_COUNT:
                    break

                self._fetch_by_person(actor, is_bollywood=True)

                # Update count
                bollywood_count = 0
                for movie in self.movies:
                    if movie.get("language") == "hi":
                        bollywood_count += 1

        # Then fetch more Hollywood movies if needed
        if need_hollywood > 0:
            print(f"Fetching {need_hollywood} more Hollywood movies...")

            # Try to fetch by years we might not have covered yet
            years_to_try = list(range(1980, datetime.now().year))
            random.shuffle(years_to_try)  # Randomize to get variety

            # Use parallel fetching for efficiency
            with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
                futures = {}
                for year in years_to_try[
                    :20
                ]:  # Limit to 20 years to prevent overloading
                    futures[executor.submit(self._fetch_by_year, year, 3, True)] = year

                for future in futures:
                    future.result()  # Wait for completion

                    # Update Hollywood count
                    hollywood_count = 0
                    for movie in self.movies:
                        if movie.get("language") != "hi":
                            hollywood_count += 1

                    if hollywood_count >= HOLLYWOOD_COUNT:
                        break

            # If still need more, try popular English language directors
            if hollywood_count < HOLLYWOOD_COUNT:
                directors = [
                    "Steven Spielberg",
                    "Christopher Nolan",
                    "Martin Scorsese",
                    "Quentin Tarantino",
                    "James Cameron",
                    "Ridley Scott",
                    "David Fincher",
                    "Denis Villeneuve",
                    "Wes Anderson",
                ]

                for director in directors:
                    if hollywood_count >= HOLLYWOOD_COUNT:
                        break

                    self._fetch_by_person(director)

                    # Update count
                    hollywood_count = 0
                    for movie in self.movies:
                        if movie.get("language") != "hi":
                            hollywood_count += 1

        # Save final dataset
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.movies, f, ensure_ascii=False, indent=2)

        print(f"Dataset updated to {len(self.movies)} movies")

    def _fetch_by_person(self, person_name, is_bollywood=False):
        """Fetch movies by a specific person (actor, director)"""
        # First search for the person
        search_url = (
            f"{TMDB_BASE_URL}/search/person?api_key={self.api_key}&query={person_name}"
        )
        try:
            response = requests.get(search_url)
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])

                if results:
                    person_id = results[0]["id"]

                    # Now get movies associated with this person
                    credits_url = f"{TMDB_BASE_URL}/person/{person_id}/movie_credits?api_key={self.api_key}"
                    credits_response = requests.get(credits_url)

                    if credits_response.status_code == 200:
                        credits_data = credits_response.json()
                        movies = credits_data.get("cast", []) + credits_data.get(
                            "crew", []
                        )

                        # If looking for Bollywood specifically, filter by language
                        if is_bollywood:
                            movie_ids = [movie["id"] for movie in movies]
                            filtered_movies = []

                            # Process in batches to avoid too many requests
                            for i in range(0, len(movie_ids), BATCH_SIZE):
                                batch = movie_ids[i : i + BATCH_SIZE]
                                for movie_id in batch:
                                    details = self._get_movie_details(movie_id)
                                    if details and details.get("language") == "hi":
                                        filtered_movies.append(details)
                                        if details["id"] not in self.unique_movie_ids:
                                            self.movies.append(details)
                                            self.unique_movie_ids.add(details["id"])
                        else:
                            # For Hollywood, process all movies
                            for movie in movies:
                                if movie["id"] not in self.unique_movie_ids:
                                    details = self._get_movie_details(movie["id"])
                                    if (
                                        details and details.get("language") != "hi"
                                    ):  # Ensure it's not Hindi
                                        self.movies.append(details)
                                        self.unique_movie_ids.add(details["id"])

                        print(f"Processed movies for {person_name}")
        except Exception as e:
            print(f"Error fetching movies for {person_name}: {e}")

    def _get_genres(self):
        """Get list of all available movie genres from TMDB"""
        url = f"{TMDB_BASE_URL}/genre/movie/list?api_key={self.api_key}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.json().get("genres", [])
            else:
                print(f"Error {response.status_code} when fetching genres")
                return []
        except Exception as e:
            print(f"Exception while fetching genres: {e}")
            return []

    def _fetch_from_endpoint(self, endpoint, pages=10):
        """Fetch movies from a specific TMDB endpoint using parallel requests"""
        # Create page ranges to fetch in parallel
        page_batches = [
            list(range(i, min(i + MAX_THREADS, pages + 1)))
            for i in range(1, pages + 1, MAX_THREADS)
        ]

        for batch in page_batches:
            with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
                futures = {
                    executor.submit(self._fetch_single_page, endpoint, page): page
                    for page in batch
                }
                for future in futures:
                    future.result()  # Wait for completion

    def _fetch_single_page(self, endpoint, page):
        """Fetch a single page from an endpoint"""
        url = f"{TMDB_BASE_URL}/{endpoint}?api_key={self.api_key}&page={page}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                self._process_movie_results(data.get("results", []))
                print(f"Fetched {endpoint} page {page}")
                time.sleep(0.3)  # Reduced sleep time
            else:
                print(
                    f"Error {response.status_code} when fetching {endpoint} page {page}"
                )
                time.sleep(1)
        except Exception as e:
            print(f"Exception while fetching {endpoint} page {page}: {e}")
            time.sleep(1)

    def _fetch_by_year(self, year, max_pages=5, strict_year=False):
        """Fetch movies released in a specific year"""
        for page in range(1, max_pages + 1):
            # For strict year matching, use both primary_release_year and year parameters
            if strict_year:
                url = f"{TMDB_BASE_URL}/discover/movie?api_key={self.api_key}&primary_release_year={year}&year={year}&page={page}&sort_by=popularity.desc"
            else:
                url = f"{TMDB_BASE_URL}/discover/movie?api_key={self.api_key}&primary_release_year={year}&page={page}&sort_by=popularity.desc"

            try:
                response = requests.get(url)
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])

                    # Additional verification for strict year matching
                    if strict_year:
                        filtered_results = []
                        for movie in results:
                            release_date = movie.get("release_date", "")
                            if release_date and release_date.startswith(str(year)):
                                filtered_results.append(movie)
                        results = filtered_results

                    self._process_movie_results(results)
                    print(f"Fetched year {year} page {page}/{max_pages}")
                    time.sleep(0.3)
                else:
                    print(
                        f"Error {response.status_code} when fetching year {year} page {page}"
                    )
                    time.sleep(1)
            except Exception as e:
                print(f"Exception while fetching year {year} page {page}: {e}")
                time.sleep(1)

    def _fetch_by_genre(self, genre_id, genre_name, max_pages=5):
        """Fetch movies by genre"""
        for page in range(1, max_pages + 1):
            url = f"{TMDB_BASE_URL}/discover/movie?api_key={self.api_key}&with_genres={genre_id}&page={page}&sort_by=popularity.desc"
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])

                    # Add genre tag for easier searching
                    for movie in results:
                        movie["genre_tag"] = genre_name.lower()

                    self._process_movie_results(results)
                    print(f"Fetched genre {genre_name} page {page}/{max_pages}")
                    time.sleep(0.3)
                else:
                    print(
                        f"Error {response.status_code} when fetching genre {genre_name} page {page}"
                    )
                    time.sleep(1)
            except Exception as e:
                print(f"Exception while fetching genre {genre_name} page {page}: {e}")
                time.sleep(1)

    def _fetch_by_language(self, language_code, max_pages=10):
        """Fetch movies by original language"""
        # Create page ranges to fetch in parallel for efficiency
        page_batches = [
            list(range(i, min(i + MAX_THREADS, max_pages + 1)))
            for i in range(1, max_pages + 1, MAX_THREADS)
        ]

        for batch in page_batches:
            with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
                futures = {
                    executor.submit(
                        self._fetch_language_page, language_code, page
                    ): page
                    for page in batch
                }
                for future in futures:
                    future.result()  # Wait for completion

    def _fetch_language_page(self, language_code, page):
        """Fetch a single page of language-specific results"""
        url = f"{TMDB_BASE_URL}/discover/movie?api_key={self.api_key}&with_original_language={language_code}&page={page}&sort_by=popularity.desc"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                self._process_movie_results(
                    data.get("results", []), is_bollywood=(language_code == "hi")
                )
                print(f"Fetched language {language_code} page {page}")
                time.sleep(0.3)
            else:
                print(
                    f"Error {response.status_code} when fetching language {language_code} page {page}"
                )
                time.sleep(1)
        except Exception as e:
            print(f"Exception while fetching language {language_code} page {page}: {e}")
            time.sleep(1)

    def _fetch_by_company(self, company_id, max_pages=5):
        """Fetch movies by production company"""
        for page in range(1, max_pages + 1):
            url = f"{TMDB_BASE_URL}/discover/movie?api_key={self.api_key}&with_companies={company_id}&page={page}&sort_by=popularity.desc"
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    data = response.json()
                    self._process_movie_results(data.get("results", []))
                    print(f"Fetched company {company_id} page {page}/{max_pages}")
                    time.sleep(0.3)
                else:
                    print(
                        f"Error {response.status_code} when fetching company {company_id} page {page}"
                    )
                    time.sleep(1)
            except Exception as e:
                print(f"Exception while fetching company {company_id} page {page}: {e}")
                time.sleep(1)

    def _process_movie_results(self, results, is_bollywood=False):
        """Process movie results and add to dataset if not already present"""
        count = 0

        # Process movies in batches for better efficiency
        movie_batches = [
            results[i : i + BATCH_SIZE] for i in range(0, len(results), BATCH_SIZE)
        ]

        for batch in movie_batches:
            # Process each batch with parallel requests
            movie_details_list = []
            with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
                movie_ids = [
                    movie["id"]
                    for movie in batch
                    if movie.get("id") and movie["id"] not in self.unique_movie_ids
                ]
                futures = {
                    executor.submit(
                        self._get_movie_details, movie_id, is_bollywood
                    ): movie_id
                    for movie_id in movie_ids
                }

                for future in futures:
                    movie_details = future.result()
                    if movie_details:
                        movie_details_list.append(movie_details)

            # Add valid movies to our dataset
            for movie_details in movie_details_list:
                # Add specific tags based on movie type
                if is_bollywood:
                    movie_details["document"] += " bollywood hindi indian"

                self.movies.append(movie_details)
                self.unique_movie_ids.add(movie_details["id"])
                count += 1

        if count > 0:
            print(f"Added {count} new movies from batch")

    @lru_cache(maxsize=CACHE_SIZE)
    def _get_movie_details(self, movie_id, prefer_hindi=False):
        """Get detailed information about a specific movie with caching"""
        url = f"{TMDB_BASE_URL}/movie/{movie_id}?api_key={self.api_key}&append_to_response=credits,keywords"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()

                # Basic movie information
                title = data.get("title", "")
                original_title = data.get("original_title", "")
                overview = data.get("overview", "")
                release_date = data.get("release_date", "")

                # Language handling - for Bollywood preferences
                original_language = data.get("original_language", "")
                if prefer_hindi and original_language != "hi":
                    return None

                # For our dataset, we only want English (Hollywood) or Hindi (Bollywood) movies
                if original_language not in ["en", "hi"]:
                    return None

                # Get genres, cast, crew
                genres = [genre["name"] for genre in data.get("genres", [])]

                # Get director and top cast
                director = ""
                cast = []

                credits = data.get("credits", {})
                crew = credits.get("crew", [])
                actors = credits.get("cast", [])

                for person in crew:
                    if person.get("job") == "Director":
                        director = person.get("name", "")
                        break

                for actor in actors[:10]:  # Get top 10 cast
                    if actor.get("name"):
                        cast.append(actor.get("name"))

                # Get keywords/tags
                keywords = []
                if "keywords" in data and "keywords" in data["keywords"]:
                    keywords = [kw["name"] for kw in data["keywords"]["keywords"]]

                # Create a comprehensive document for text search
                document = f"{title} {original_title} {overview} {' '.join(genres)} {director} {' '.join(cast)} {' '.join(keywords)}"

                # Prepare and return the structured movie data
                movie_info = {
                    "id": movie_id,
                    "title": title,
                    "original_title": original_title,
                    "overview": overview,
                    "release_date": release_date,
                    "genres": genres,
                    "director": director,
                    "cast": cast,
                    "keywords": keywords,
                    "language": original_language,
                    "document": document,
                    "poster_path": data.get("poster_path", None),

                }

                return movie_info
            else:
                print(f"Error {response.status_code} when fetching movie {movie_id}")
                return None
        except Exception as e:
            print(f"Exception while fetching movie {movie_id}: {e}")
            return None

    def _save_progress(self, phase_name):
        """Save intermediate progress to the data file"""
        if len(self.movies) % 100 == 0:  # Save every 100 movies
            print(
                f"Progress update ({phase_name}): {len(self.movies)} movies in dataset"
            )
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.movies, f, ensure_ascii=False, indent=2)

    def _prepare_tfidf(self):
        """Prepare the TF-IDF matrix for recommendation"""
        print("Preparing TF-IDF vectorizer...")
        stop_words = set(stopwords.words("english"))
        lemmatizer = WordNetLemmatizer()

        # Preprocess the documents for more effective recommendations
        preprocessed_docs = []
        for movie in self.movies:
            doc = movie.get("document", "")

            # Tokenize and preprocess
            tokens = word_tokenize(doc.lower())
            tokens = [
                lemmatizer.lemmatize(token)
                for token in tokens
                if token.isalpha() and token not in stop_words
            ]

            preprocessed_docs.append(" ".join(tokens))

        # Create TF-IDF matrix
        self.vectorizer = TfidfVectorizer(
            max_features=5000
        )  # Limit features for memory efficiency
        self.tfidf_matrix = self.vectorizer.fit_transform(preprocessed_docs)
        print(f"TF-IDF matrix shape: {self.tfidf_matrix.shape}")

    def search_movies(self, query, limit=10, language=None):
        """Search movies based on text query with optional language filter"""
        if not query:
            return self._get_random_recommendations(limit, language)

        # Preprocess the query
        stop_words = set(stopwords.words("english"))
        lemmatizer = WordNetLemmatizer()

        # Clean and tokenize the query
        query = re.sub(r"[^\w\s]", "", query.lower())
        tokens = word_tokenize(query)
        processed_tokens = [
            lemmatizer.lemmatize(token)
            for token in tokens
            if token.isalpha() and token not in stop_words
        ]
        processed_query = " ".join(processed_tokens)

        # Transform query to the same vector space
        query_vector = self.vectorizer.transform([processed_query])

        # Calculate similarity with all movies
        sim_scores = cosine_similarity(query_vector, self.tfidf_matrix).flatten()

        # Get movie indices with highest similarity
        movie_indices = sim_scores.argsort()[::-1]

        # Apply language filter if specified
        results = []
        count = 0

        for idx in movie_indices:
            movie = self.movies[idx]
            # Apply language filter if specified
            if language and movie.get("language") != language:
                continue

            # Add similarity score to movie data
            movie_with_score = movie.copy()
            movie_with_score["similarity"] = float(sim_scores[idx])

            results.append(movie_with_score)
            count += 1

            if count >= limit:
                break

        return results

    def get_movie_recommendations(self, movie_id, limit=10, language=None):
        """Get movie recommendations based on a specific movie"""
        # Find the movie in our dataset
        movie_idx = None
        for idx, movie in enumerate(self.movies):
            if str(movie["id"]) == str(movie_id):
                movie_idx = idx
                break

        if movie_idx is None:
            return {"error": "Movie not found in the database"}

        # Calculate similarity with all other movies
        movie_vector = self.tfidf_matrix[movie_idx]
        sim_scores = cosine_similarity(movie_vector, self.tfidf_matrix).flatten()

        # Get movie indices with highest similarity (excluding the movie itself)
        indices = list(range(len(sim_scores)))
        indices.sort(key=lambda x: sim_scores[x], reverse=True)
        indices = [
            idx for idx in indices if idx != movie_idx
        ]  # Exclude the movie itself

        # Apply language filter if specified
        recommendations = []
        count = 0

        for idx in indices:
            movie = self.movies[idx]
            # Apply language filter if specified
            if language and movie.get("language") != language:
                continue

            # Add similarity score to movie data
            movie_with_score = movie.copy()
            movie_with_score["similarity"] = float(sim_scores[idx])

            recommendations.append(movie_with_score)
            count += 1

            if count >= limit:
                break

        return recommendations

    def _get_random_recommendations(self, limit=10, language=None):
        """Get random movie recommendations with optional language filter"""
        filtered_movies = self.movies

        # Apply language filter if specified
        if language:
            filtered_movies = [
                movie for movie in self.movies if movie.get("language") == language
            ]

        # Shuffle and return limited number
        random_selection = random.sample(
            filtered_movies, min(limit, len(filtered_movies))
        )

        # Add a placeholder similarity score
        for movie in random_selection:
            movie_with_score = movie.copy()
            movie_with_score["similarity"] = (
                0.0  # Zero similarity for random recommendations
            )

        return random_selection


# Initialize recommender system
recommender = MovieRecommender()


@app.route('/')
def serve_frontend():
    return send_from_directory('../frontend', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('../frontend', path)

@app.route("/api/trailer/<int:movie_id>", methods=["GET"])
def get_trailer(movie_id):
    url = f"{TMDB_BASE_URL}/movie/{movie_id}/videos?api_key={recommender.api_key}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            videos = response.json().get("results", [])
            for video in videos:
                if video["site"] == "YouTube" and video["type"] == "Trailer":
                    return jsonify({"key": video["key"]})
            return jsonify({"error": "Trailer not found"}), 404
        else:
            return jsonify({"error": f"TMDB error {response.status_code}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/search", methods=["GET"])
def search():
    """API endpoint for searching movies"""
    query = request.args.get("query", "")
    limit = int(request.args.get("limit", 10))
    language = request.args.get("language", None)

    results = recommender.search_movies(query, limit, language)
    return jsonify(results)


@app.route("/api/recommend", methods=["GET"])
def recommend():
    """API endpoint for getting movie recommendations"""
    movie_id = request.args.get("movie_id")
    limit = int(request.args.get("limit", 10))
    language = request.args.get("language", None)

    if not movie_id:
        return jsonify({"error": "Movie ID is required"}), 400

    recommendations = recommender.get_movie_recommendations(movie_id, limit, language)
    return jsonify(recommendations)


@app.route("/api/movie/<int:movie_id>", methods=["GET"])
def get_movie(movie_id):
    """API endpoint for getting details of a specific movie"""
    for movie in recommender.movies:
        if movie["id"] == movie_id:
            return jsonify(movie)

    return jsonify({"error": "Movie not found"}), 404


@app.route("/api/random", methods=["GET"])
def random_movies():
    """API endpoint for getting random movies"""
    limit = int(request.args.get("limit", 10))
    language = request.args.get("language", None)

    random_selections = recommender._get_random_recommendations(limit, language)
    return jsonify(random_selections)


@app.route("/api/languages", methods=["GET"])
def get_languages():
    """API endpoint for getting available languages"""
    languages = {"en": "English (Hollywood)", "hi": "Hindi (Bollywood)"}
    return jsonify(languages)


if __name__ == "__main__":
    app.run(debug=True, port=5500)

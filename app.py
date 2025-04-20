from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import random
import json
import os
from sentence_transformers import util
from optimized_movie_recommender import MovieRecommender

app = Flask(__name__)
CORS(app)

recommender = MovieRecommender()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/random')
def api_random():
    limit = int(request.args.get('limit', 10))
    lang = request.args.get('language', None)
    movies = [movie for movie in recommender.movies if not lang or movie.get("language") == lang]
    return jsonify(random.sample(movies, min(limit, len(movies))))

@app.route("/api/search")
def search_movies():
    """API endpoint for searching movies with advanced NLP"""
    query = request.args.get("query", "").strip()
    limit = int(request.args.get("limit", 10))
    language = request.args.get("language", None)
    
    if not query:
        return jsonify(recommender._get_random_recommendations(limit, language))
    
    try:
        # Use search_movies_enhanced instead of trying to parse the query separately
        results = recommender.search_movies_enhanced(query, limit, language)
        return jsonify(results)
    except Exception as e:
        print(f"Error during search: {str(e)}")
        return jsonify({"error": f"Search failed: {str(e)}"}), 500

    # ✅ Use the actual recommender instance
    query_info = recommender._parse_query(query)
    print("[DEBUG] Parsed Query Info:", query_info)

    clean_query = query_info.get("clean_query") or query
    print("[DEBUG] Semantic query used:", clean_query)

    try:
        query_embedding = recommender.model.encode(clean_query, convert_to_tensor=True)
        cos_scores = util.pytorch_cos_sim(query_embedding, recommender.embeddings["full"])[0]
    except Exception as e:
        print("[ERROR] NLP embedding/search failed:", e)
        return jsonify([])

    top_indices = cos_scores.argsort(descending=True)

    results = []
    for idx in top_indices:
        movie = recommender.movies[idx]
        if language and movie.get("language") != language:
            continue
        results.append(movie)
        if len(results) >= limit:
            break

    print(f"[DEBUG] Found {len(results)} semantic matches for: {query}")
    return jsonify(results)

@app.route('/api/movie/<int:movie_id>')
def api_movie_detail(movie_id):
    movie = next((m for m in recommender.movies if m['id'] == movie_id), None)
    if movie:
        return jsonify(movie)
    else:
        return jsonify({'error': 'Movie not found'}), 404

@app.route('/api/recommend')
def api_recommend():
    movie_id = int(request.args.get('movie_id'))
    limit = int(request.args.get('limit', 5))
    lang = request.args.get('language', None)

    movie = next((m for m in recommender.movies if m['id'] == movie_id), None)
    if not movie:
        return jsonify({'error': 'Movie not found'}), 404

    same_lang = [m for m in recommender.movies if m.get('language') == movie.get('language') and m['id'] != movie_id]
    return jsonify(random.sample(same_lang, min(limit, len(same_lang))))

if __name__ == '__main__':
    app.run(debug=True)

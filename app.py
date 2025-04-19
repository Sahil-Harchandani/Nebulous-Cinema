from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import random
import json
import os
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

@app.route('/api/search')
def api_search():
    query = request.args.get('query', '')
    limit = int(request.args.get('limit', 10))
    lang = request.args.get('language', None)

    results = []
    for movie in recommender.movies:
        if lang and movie.get('language') != lang:
            continue
        if query.lower() in movie.get('title', '').lower():
            results.append(movie)
        if len(results) >= limit:
            break
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

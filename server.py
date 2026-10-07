import sqlite3
from flask import Flask, jsonify, request, Response
import requests
from flask_cors import CORS

app = Flask(__name__)

@app.route('/')
def home():
    return {"status": "Cynexis Backend is Live and Running!"}

CORS(app) # Browser ko local connect karne ki permission deta hai

import os

# Cloud aur local dono ke liye absolute path set karein
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "all_world_movies.db")

# Database Initialization (Table create karega agar nahi hai toh)
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY,
            title TEXT,
            poster TEXT,
            streamUrl TEXT,
            year TEXT,
            rating REAL
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# 1. Home page ke liye popular/latest 50 movies
@app.route('/api/movies')
def get_movies():
    conn = get_db_connection()
    # SELECT * karne se id, title, poster sab frontend ko jayega
    movies = conn.execute('SELECT * FROM movies ORDER BY id DESC').fetchall()
    conn.close()
    return jsonify([dict(row) for row in movies])

@app.route('/api/search')
def search_movies():
    query = request.args.get('q', '')
    if not query:
        return jsonify([])

    # 1. TMDB API se live search karein
    url = f"https://api.themoviedb.org/3/search/movie?query={query}&include_adult=false&language=en-US&page=1&api_key=16f62d38fec24f4e6c2adc9388da20ce"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        tmdb_results = data.get("results", [])
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        search_results = []
        
        for m in tmdb_results:
            tmdb_id = m.get("id")
            title = m.get("title")
            
            poster_path = m.get("poster_path")
            poster = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else ""
            
            release_date = m.get("release_date", "")
            year = release_date.split("-")[0] if release_date else ""
            
            rating = round(m.get("vote_average", 0), 1)
            
            # Check karein agar movie pehle se database me hai
            existing = cursor.execute("SELECT * FROM movies WHERE id=?", (tmdb_id,)).fetchone()
            
            if not existing:
                # Agar nahi hai toh DB me nayi movie save karein
                cursor.execute("""
                    INSERT INTO movies (id, title, poster, streamUrl, year, rating) 
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (tmdb_id, title, poster, "", year, rating))
                search_results.append({
                    "id": tmdb_id, "title": title, "poster": poster, 
                    "streamUrl": "", "year": year, "rating": rating
                })
            else:
                # Agar pehle se hai toh directly list me daal dein
                search_results.append(dict(existing))
                
        conn.commit()
        conn.close()
        
        return jsonify(search_results)
        
    except Exception as e:
        # Agar net band ho toh purane database me search kare
        conn = get_db_connection()
        movies = conn.execute('SELECT * FROM movies WHERE title LIKE ? ORDER BY id DESC', ('%' + query + '%',)).fetchall()
        conn.close()
        return jsonify([dict(row) for row in movies])

@app.route("/stream/proxy")
def stream_proxy():
    target_url = request.args.get("url")
    if not target_url:
        return "Missing URL", 400

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://hubstream.art/"
    }

    try:
        req = requests.get(target_url, headers=headers, stream=True, timeout=15)
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers_to_send = [(name, value) for (name, value) in req.raw.headers.items() if name.lower() not in excluded_headers]
        headers_to_send.append(('Access-Control-Allow-Origin', '*'))

        return Response(req.iter_content(chunk_size=1024 * 64), headers=headers_to_send, status=req.status_code)
    except Exception as e:
        return str(e), 500

@app.route("/api/sync")
def sync_gaiaflix_movies():
    try:
        conn = get_db_connection()
        added_count = 0
        total_fetched = 0
        
        # Hum 1 se lekar 5 pages tak loop chalayenge (5 pages x 20 = 100 movies)
        # Agar aapko aur zyada chahiye, toh (1, 6) ko (1, 11) kar dein (10 pages ke liye)
        for page_num in range(1, 6):
            url = f"https://api.themoviedb.org/3/discover/movie?language=en-US&page={page_num}&sort_by=popularity.desc&include_adult=false&without_genres=16&api_key=16f62d38fec24f4e6c2adc9388da20ce"
            
            response = requests.get(url, timeout=10)
            data = response.json()
            movies_list = data.get("results", [])
            total_fetched += len(movies_list)
            
            for m in movies_list:
                tmdb_id = m.get("id")
                title = m.get("title")
                
                poster_path = m.get("poster_path")
                poster = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else ""
                
                release_date = m.get("release_date", "")
                year = release_date.split("-")[0] if release_date else ""
                
                rating = round(m.get("vote_average", 0), 1)
                
                existing = conn.execute("SELECT id FROM movies WHERE id=?", (tmdb_id,)).fetchone()
                if not existing:
                    conn.execute("""
                        INSERT INTO movies (id, title, poster, streamUrl, year, rating) 
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (tmdb_id, title, poster, "", year, rating))
                    added_count += 1
                    
        conn.commit()
        conn.close()
        
        return jsonify({
            "status": "Success", 
            "message": f"{added_count} new movies synced! (Total fetched from TMDB: {total_fetched})"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

import os

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
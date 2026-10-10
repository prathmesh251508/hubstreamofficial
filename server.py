import sqlite3
from flask import Flask, jsonify, request, Response, render_template_string
import requests
from flask_cors import CORS

app = Flask(__name__)

@app.route('/')
def home():
    return {"status": "Cynexis Backend is Live and Running!"}

CORS(app)

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "all_world_movies.db")

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

@app.route('/api/movies')
def get_movies():
    conn = get_db_connection()
    try:
        working_movies = conn.execute("SELECT * FROM movies WHERE streamUrl IS NOT NULL AND streamUrl != '' ORDER BY id DESC").fetchall()
        if working_movies:
            movies_list = [dict(row) for row in working_movies]
        else:
            all_movies = conn.execute('SELECT * FROM movies ORDER BY id DESC LIMIT 50').fetchall()
            movies_list = [dict(row) for row in all_movies]
        conn.close()
        return jsonify(movies_list)
    except Exception as e:
        conn.close()
        return jsonify([])

# 🛠️ ADMIN DASHBOARD ROUTE
@app.route('/admin')
def admin_panel():
    admin_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>HubStream Admin Panel</title>
        <style>
            body { background: #050508; color: #fff; font-family: sans-serif; padding: 20px; }
            h1 { color: #e11d48; margin-bottom: 20px; }
            .btn { background: #e11d48; color: #fff; border: none; padding: 10px 18px; border-radius: 6px; cursor: pointer; font-weight: bold; margin-bottom: 20px; }
            .btn-danger { background: #ef4444; padding: 6px 12px; font-size: 12px; }
            table { width: 100%; border-collapse: collapse; background: #0f172a; border-radius: 8px; overflow: hidden; }
            th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #1e293b; font-size: 14px; }
            th { background: #1e293b; }
            img { width: 40px; height: 60px; object-fit: cover; border-radius: 4px; }
            .no-link { color: #f87171; font-weight: bold; }
            .has-link { color: #34d399; font-weight: bold; }
        </style>
    </head>
    <body>
        <h1>HubStream Cinema - Admin Manager</h1>
        <button class="btn" onclick="clearEmpty()">🗑️ Delete All Movies Without Links</button>
        <div id="status" style="margin-bottom: 15px; color: #38bdf8;"></div>
        <table>
            <thead>
                <tr>
                    <th>Poster</th>
                    <th>Title</th>
                    <th>Year</th>
                    <th>Stream Status</th>
                    <th>Action</th>
                </tr>
            </thead>
            <tbody id="movieTable">
                <tr><td colspan="5" style="text-align:center;">Loading movies...</td></tr>
            </tbody>
        </table>

        <script>
            async function fetchAdminMovies() {
                const res = await fetch('/api/admin/movies');
                const movies = await res.json();
                const tbody = document.getElementById('movieTable');
                tbody.innerHTML = '';

                if(movies.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;">No movies found in database.</td></tr>';
                    return;
                }

                movies.forEach(m => {
                    const tr = document.createElement('tr');
                    const hasStream = m.streamUrl && m.streamUrl.trim() !== "";
                    tr.innerHTML = `
                        <td><img src="${m.poster || 'https://images.unsplash.com/photo-1485846234645-a62644f84728?w=100&q=80'}" /></td>
                        <td><b>${m.title}</b><br><small style="color:#94a3b8">ID: ${m.id}</small></td>
                        <td>${m.year || 'N/A'}</td>
                        <td>${hasStream ? '<span class="has-link">Working Link</span>' : '<span class="no-link">No Link</span>'}</td>
                        <td><button class="btn btn-danger" onclick="deleteMovie(${m.id})">Delete</button></td>
                    `;
                    tbody.appendChild(tr);
                });
            }

            async function deleteMovie(id) {
                if(!confirm("Kya aap is movie ko delete karna chahte hain?")) return;
                const res = await fetch(`/api/movies/${id}`, { method: 'DELETE' });
                const data = await res.json();
                document.getElementById('status').innerText = data.message;
                fetchAdminMovies();
            }

            async function clearEmpty() {
                if(!confirm("Kya aap saari bina link wali movies ek sath delete karna chahte hain?")) return;
                const res = await fetch('/api/admin/clear-empty', { method: 'POST' });
                const data = await res.json();
                document.getElementById('status').innerText = data.message;
                fetchAdminMovies();
            }

            fetchAdminMovies();
        </script>
    </body>
    </html>
    """
    return render_template_string(admin_html)

# API to fetch all movies for admin table
@app.route('/api/admin/movies')
def admin_get_all_movies():
    conn = get_db_connection()
    movies = conn.execute('SELECT * FROM movies ORDER BY id DESC').fetchall()
    conn.close()
    return jsonify([dict(row) for row in movies])

# API to delete single movie
@app.route('/api/movies/<int:movie_id>', methods=['DELETE'])
def delete_movie(movie_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM movies WHERE id = ?', (movie_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "Success", "message": f"Movie ID {movie_id} successfully deleted!"})

# API to delete all movies with empty streamUrl
@app.route('/api/admin/clear-empty', methods=['POST'])
def clear_empty_movies():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM movies WHERE streamUrl IS NULL OR streamUrl = ''")
    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()
    return jsonify({"status": "Success", "message": f"Total {deleted_count} empty-link movies cleared successfully!"})

@app.route('/api/search')
def search_movies():
    query = request.args.get('q', '')
    if not query:
        return jsonify([])

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
            
            existing = cursor.execute("SELECT * FROM movies WHERE id=?", (tmdb_id,)).fetchone()
            
            if not existing:
                cursor.execute("""
                    INSERT INTO movies (id, title, poster, streamUrl, year, rating) 
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (tmdb_id, title, poster, "", year, rating))
                search_results.append({
                    "id": tmdb_id, "title": title, "poster": poster, 
                    "streamUrl": "", "year": year, "rating": rating
                })
            else:
                search_results.append(dict(existing))
                
        conn.commit()
        conn.close()
        return jsonify(search_results)
        
    except Exception as e:
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
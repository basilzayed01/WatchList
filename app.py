from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import psycopg2
from psycopg2 import Error, sql
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from dotenv import load_dotenv

# Load environment variables from .env file (optional for local)
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')

# Database configuration - uses environment variable on Render, falls back to SQLite locally
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///watchlist.db')

def get_db_connection():
    """Create a connection to the PostgreSQL database"""
    try:
        # Parse the DATABASE_URL for Render's PostgreSQL
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Error as e:
        print(f"Error connecting to PostgreSQL: {e}")
        return None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first!', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, username, password_hash FROM \"User\" WHERE username = %s", (username,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if user and check_password_hash(user[2], password):
                session['user_id'] = user[0]
                session['username'] = user[1]
                flash('Login successful!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        password_hash = generate_password_hash(password)
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO \"User\" (username, email, password_hash) VALUES (%s, %s, %s)",
                    (username, email, password_hash)
                )
                conn.commit()
                flash('Registration successful! Please login.', 'success')
                return redirect(url_for('login'))
            except Error as e:
                flash(f'Error: {e}', 'danger')
            finally:
                cursor.close()
                conn.close()
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'info')
    return redirect(url_for('index'))

@app.route('/movies')
def movies():
    conn = get_db_connection()
    movies_list = []
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT movie_id, title, release_year, genre, director, description FROM \"Movie\" ORDER BY release_year DESC")
        movies_list = cursor.fetchall()
        cursor.close()
        conn.close()
    return render_template('movies.html', movies=movies_list)

@app.route('/add_movie', methods=['GET', 'POST'])
@login_required
def add_movie():
    if request.method == 'POST':
        title = request.form['title']
        release_year = request.form['release_year']
        genre = request.form['genre']
        director = request.form['director']
        description = request.form['description']
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO \"Movie\" (title, release_year, genre, director, description) VALUES (%s, %s, %s, %s, %s)",
                (title, release_year, genre, director, description)
            )
            conn.commit()
            cursor.close()
            conn.close()
            flash('Movie added successfully!', 'success')
            return redirect(url_for('movies'))
    
    return render_template('add_movie.html')

@app.route('/edit_movie/<int:movie_id>', methods=['GET', 'POST'])
@login_required
def edit_movie(movie_id):
    conn = get_db_connection()
    if request.method == 'POST':
        title = request.form['title']
        release_year = request.form['release_year']
        genre = request.form['genre']
        director = request.form['director']
        description = request.form['description']
        
        if conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE \"Movie\" SET title=%s, release_year=%s, genre=%s, director=%s, description=%s WHERE movie_id=%s",
                (title, release_year, genre, director, description, movie_id)
            )
            conn.commit()
            cursor.close()
            conn.close()
            flash('Movie updated successfully!', 'success')
            return redirect(url_for('movies'))
    
    movie = None
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT movie_id, title, release_year, genre, director, description FROM \"Movie\" WHERE movie_id = %s", (movie_id,))
        movie = cursor.fetchone()
        cursor.close()
        conn.close()
    
    return render_template('edit_movie.html', movie=movie)

@app.route('/delete_movie/<int:movie_id>')
@login_required
def delete_movie(movie_id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM \"Movie\" WHERE movie_id = %s", (movie_id,))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Movie deleted successfully!', 'success')
    return redirect(url_for('movies'))

@app.route('/watchlist')
@login_required
def watchlist():
    conn = get_db_connection()
    watchlist_items = []
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT w.watchlist_id, w.status, m.movie_id, m.title, m.release_year, m.genre
            FROM \"Watchlist\" w
            JOIN \"Movie\" m ON w.movie_id = m.movie_id
            WHERE w.user_id = %s
            ORDER BY 
                CASE w.status 
                    WHEN 'Favorite' THEN 1 
                    WHEN 'Watched' THEN 2 
                    WHEN 'Want to Watch' THEN 3 
                END
        """, (session['user_id'],))
        watchlist_items = cursor.fetchall()
        cursor.close()
        conn.close()
    return render_template('watchlist.html', watchlist=watchlist_items)

@app.route('/add_to_watchlist/<int:movie_id>', methods=['POST'])
@login_required
def add_to_watchlist(movie_id):
    status = request.form.get('status', 'Want to Watch')
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO \"Watchlist\" (user_id, movie_id, status) VALUES (%s, %s, %s)",
                (session['user_id'], movie_id, status)
            )
            conn.commit()
            flash('Added to watchlist!', 'success')
        except Error:
            flash('Movie already in watchlist!', 'warning')
        finally:
            cursor.close()
            conn.close()
    return redirect(url_for('movies'))

@app.route('/update_watchlist_status/<int:watchlist_id>', methods=['POST'])
@login_required
def update_watchlist_status(watchlist_id):
    new_status = request.form['status']
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE \"Watchlist\" SET status = %s WHERE watchlist_id = %s AND user_id = %s",
            (new_status, watchlist_id, session['user_id'])
        )
        conn.commit()
        cursor.close()
        conn.close()
        flash('Watchlist updated!', 'success')
    return redirect(url_for('watchlist'))

@app.route('/remove_from_watchlist/<int:watchlist_id>')
@login_required
def remove_from_watchlist(watchlist_id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM \"Watchlist\" WHERE watchlist_id = %s AND user_id = %s",
            (watchlist_id, session['user_id'])
        )
        conn.commit()
        cursor.close()
        conn.close()
        flash('Removed from watchlist!', 'success')
    return redirect(url_for('watchlist'))

@app.route('/reviews')
def reviews():
    conn = get_db_connection()
    reviews_list = []
    all_movies = []
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.review_id, r.rating, r.review_text, r.review_date,
                   u.username, m.title, m.movie_id
            FROM \"Review\" r
            JOIN \"User\" u ON r.user_id = u.user_id
            JOIN \"Movie\" m ON r.movie_id = m.movie_id
            ORDER BY r.review_date DESC
        """)
        reviews_list = cursor.fetchall()
        
        cursor.execute("SELECT movie_id, title, release_year FROM \"Movie\" ORDER BY title")
        all_movies = cursor.fetchall()
        cursor.close()
        conn.close()
    return render_template('reviews.html', reviews=reviews_list, all_movies=all_movies)

@app.route('/add_review', methods=['POST'])
@login_required
def add_review():
    movie_id = request.form['movie_id']
    rating = request.form['rating']
    review_text = request.form['review_text']
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO \"Review\" (user_id, movie_id, rating, review_text) VALUES (%s, %s, %s, %s)",
            (session['user_id'], movie_id, rating, review_text)
        )
        conn.commit()
        cursor.close()
        conn.close()
        flash('Review added successfully!', 'success')
    return redirect(url_for('reviews'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
from flask import Flask, render_template, url_for, redirect, request, flash, session, jsonify
from flask_bcrypt import Bcrypt
import pandas as pd
import numpy as np
import sqlite3
import requests 
from recommender import hybrid_recommender, load_matrix
from datetime import datetime 
from surprise import Dataset, Reader

app = Flask(__name__)
app.secret_key = "ibrahimssecretkey" # used for session cookies
bcrypt = Bcrypt(app) # used for hashing passwords 

ratings = load_matrix()

API_KEY = "80af0fb6b0282be640962102d44e8ebd"

@app.route('/')
def home():
    return render_template('website.html')

@app.route('/student-login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row  
        cursor = conn.cursor()
        row = cursor.execute("SELECT * FROM StudentLogin WHERE Username=?", (username,)).fetchone()
        conn.close()

        print (bcrypt.check_password_hash(row["PasswordHash"], password))

        # if username exists and hashed password in the same row equals the original password:
        if row and bcrypt.check_password_hash(row["PasswordHash"], password):

            # if login successful, create session
            session.clear()
            session['user_id'] = row['StudentID']
            session['username'] = row['Username']

            if row['FirstTime'] == 1:
                return redirect(url_for('choosefaves'))
            else:
                return redirect(url_for('homepage'))
        else:
            # if login fail, flash message
            flash("Wrong username or password. Try again.")
            return redirect(url_for('student_login'))

    return render_template('student-login.html')

@app.route('/teacher-login')
def teacherlogin():
    return render_template('teacher-login.html')

@app.route('/choose-faves')
def choosefaves():
    return render_template('choose-faves.html')

@app.route('/homepage', methods=['GET', 'POST'])
def homepage():

    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    # check if recommendations are not in user's session
    if 'recommendations' not in session:
        ratings = load_matrix()
        movie_ids = hybrid_recommender(user_id, ratings)  # call recommender
        movie_ids = [int(id) for id in movie_ids]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        placeholders = ",".join("?" * len(movie_ids))  # placeholders (?, ?, ?)
        cursor.execute(f"SELECT id, title, release_year, poster_path FROM Movies WHERE id IN ({placeholders})", movie_ids)
        rows = cursor.fetchall()
        conn.close()

        base_url = "https://image.tmdb.org/t/p/w500"

        movies = []
        for id, title, year, poster in rows:
            movies.append({
                "id": id,
                "title": title,
                "release_year": year,
                "poster_path": base_url + poster
            })

        # save to session to avoid having to generate recommendaitons every time
        session['recommendations'] = movies

    else:
        # Use cached recommendations
        movies = session['recommendations']

    return render_template('homepage.html', movies=movies)

@app.route('/logout')
def logout():
    session.clear()  
    return redirect(url_for('home'))  

@app.route('/profile')
def profile():

    user_id = session.get('user_id')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("""
                   SELECT Movies.id, Movies.Title, Movies.release_year, Movies.poster_path
                   FROM Movies
                   INNER JOIN Favourites 
                   ON Movies.id = Favourites.MovieID
                   WHERE Favourites.StudentID = ? """, (user_id,))

    rows = cursor.fetchall()

    cursor.execute(""" 
                    SELECT Movies.id, Movies.Title, Movies.release_year, Movies.poster_path, 
                    Reviews.Rating, Reviews.Date, Reviews.ReviewText
                    FROM Reviews
                    INNER JOIN Movies 
                    ON Reviews.MovieID = Movies.id
                    WHERE Reviews.StudentID = ?
                    ORDER BY Reviews.Date DESC 
                    LIMIT 3 """, (user_id,))
    
    rows2 = cursor.fetchall()

    cursor.execute("""
                    SELECT COUNT (*)
                    FROM Reviews
                    WHERE StudentID = ?
                    """, (user_id,))
    
    review_count = cursor.fetchone()[0] # fetch first element as tuple is returned

    conn.close()

    base_url = "https://image.tmdb.org/t/p/w500"

    favourites = []
    for id, title, year, poster in rows:
        favourites.append({
                "id": id,
                "title": title,
                "release_year": year,
                "poster_path": base_url + poster
        })

    recent_reviews = []
    for id, title, year, poster, rating, date, review in rows2:
        recent_reviews.append({
                "id": id,
                "title": title,
                "release_year": year,
                "poster_path": base_url + poster,
                "rating": rating,
                "date": date,
                "review": review
        })

    return render_template('profile/profile.html', favourites=favourites, recent_reviews=recent_reviews, review_count=review_count)

@app.route('/activity')
def activity():

    user_id = session.get('user_id')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute(""" 
                    SELECT Movies.id, Movies.Title, Movies.release_year, Movies.poster_path, 
                    Reviews.Rating, Reviews.Date, Reviews.ReviewText
                    FROM Reviews
                    INNER JOIN Movies 
                    ON Reviews.MovieID = Movies.id
                    WHERE Reviews.StudentID = ?
                    ORDER BY Reviews.Date DESC 
                    """, (user_id,))
    
    rows = cursor.fetchall()
    conn.close()

    base_url = "https://image.tmdb.org/t/p/w500"

    reviews = []
    for id, title, year, poster, rating, date, review in rows:
        reviews.append({
                "id": id,
                "title": title,
                "release_year": year,
                "poster_path": base_url + poster,
                "rating": rating,
                "date": date,
                "review": review
        })

    return render_template('profile/activity.html', reviews=reviews)

@app.route('/scores')
def scores():
    return render_template('profile/scores.html')

@app.route('/reviews')
def reviews():

    user_id = session.get('user_id')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute(""" 
                    SELECT Movies.id, Movies.Title, Movies.release_year, Movies.poster_path, 
                    Reviews.Rating, Reviews.Date, Reviews.ReviewText
                    FROM Reviews
                    INNER JOIN Movies 
                    ON Reviews.MovieID = Movies.id
                    WHERE Reviews.StudentID = ?
                    ORDER BY Reviews.Date DESC 
                    """, (user_id,))
    
    rows = cursor.fetchall()
    conn.close()

    base_url = "https://image.tmdb.org/t/p/w500"

    reviews = []
    for id, title, year, poster, rating, date, review in rows:
        reviews.append({
                "id": id,
                "title": title,
                "release_year": year,
                "poster_path": base_url + poster,
                "rating": rating,
                "date": date,
                "review": review
        })

    return render_template('profile/reviews.html', reviews=reviews)

@app.route('/details')
def details():

    user_id = session.get('user_id')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute(""" SELECT Students.FullName,
                            Teachers.Name,
                            Class.ClassName
                    FROM Students
                    INNER JOIN Class ON Students.ClassID = Class.ClassID
                    INNER JOIN Teachers ON Class.TeacherID = Teachers.TeacherID
                    WHERE Students.StudentID = ?
                    """, (user_id,))
    
    details = cursor.fetchone()
    conn.close()

    return render_template('profile/details.html', details=details)

@app.route('/classpage')
def classpage():

    user_id = session.get('user_id')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute(
            "SELECT ClassID FROM Students WHERE StudentID = ?",
            (user_id,)
        )
 
    class_id = cursor.fetchone()[0]

    cursor.execute (
            "SELECT ClassName FROM Class WHERE ClassID = ?",
            (class_id,)
    )

    class_name = cursor.fetchone()[0]

    cursor.execute(
            "SELECT FullName FROM Students WHERE ClassID = ?",
            (class_id,)
        )

    students = cursor.fetchall()

    cursor.execute(""" 
                    SELECT Movies.id, Movies.Title, Movies.release_year, Movies.poster_path, 
                    Reviews.Rating, Reviews.Date, Reviews.ReviewText, 
                    Students.FullName
                    FROM Reviews
                    INNER JOIN Movies 
                    ON Reviews.MovieID = Movies.id
                    INNER JOIN Students 
                    ON Reviews.StudentID = Students.StudentID
                    WHERE Students.ClassID = ?
                    ORDER BY Reviews.Date DESC 
                    """, (class_id,))
    
    rows = cursor.fetchall()
    conn.close()

    base_url = "https://image.tmdb.org/t/p/w500"

    reviews = []
    for id, title, year, poster, rating, date, review, student in rows:
        reviews.append({
                "id": id,
                "title": title,
                "release_year": year,
                "poster_path": base_url + poster,
                "rating": rating,
                "date": date,
                "review": review,
                "student": student
        })

    print (reviews)

    return render_template('classpage.html', students=students, class_name=class_name, reviews=reviews)

@app.route('/watchlist')
def watchlist():

    user_id = session.get('user_id')
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute(""" 
                    SELECT Movies.Title, Movies.release_year, Movies.poster_path, 
                    Watchlist.MovieID, Watchlist.Date
                    FROM Watchlist
                    INNER JOIN Movies 
                    ON Watchlist.MovieID = Movies.id
                    WHERE Watchlist.StudentID = ?
                    ORDER BY Watchlist.Date DESC 
                    """, (user_id,))
    
    rows = cursor.fetchall()
    conn.close()

    base_url = "https://image.tmdb.org/t/p/w500"

    watchlist = []
    for title, year, poster, id, date in rows:
        watchlist.append({
                "title": title,
                "release_year": year,
                "poster_path": base_url + poster,
                "id": id,
                "date": date
        })

    return render_template('watchlist.html', watchlist=watchlist)

@app.route('/search')
def search():
    return render_template('search.html')

@app.route('/moviepage/<int:movie_id>')
def moviepage(movie_id):

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, title, overview, genres, release_year, poster_path
        FROM Movies 
        WHERE id = ?
    """, (movie_id,)) 
    
    movie = cursor.fetchone()
    
    base_url = "https://image.tmdb.org/t/p/w500" 

    moviedata = {
        "id": movie[0],
        "title": movie[1],
        "overview": movie[2],
        "genres": movie[3],
        "release_year": movie[4],
        "poster_path": base_url + movie[5]
     }
    
    conn.close()

    url = f"https://api.themoviedb.org/3/movie/{movie_id}/credits?api_key={API_KEY}"

    response = requests.get(url)
    credits = response.json()

    cast = credits.get("cast", [])[:10]   # limit to 10 cast members
    crew = credits.get("crew", [])

    # find director(s)
    director = [person["name"] for person in crew if person["job"] == "Director"]

    return render_template(
        "moviepage.html",
        movie=moviedata,
        cast=cast,
        director=director
    )
    
@app.route('/quiz')
def quiz():
    return render_template('quiz.html')

@app.route("/test")
def test():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM movies LIMIT 10;")
    rows = cursor.fetchall()  # list of tuples

    # send rows into template
    return render_template("test.html", movies=rows)

@app.route("/autocomplete", methods=["GET"])
def autocomplete():

    # search input query 
    search_query = request.args.get("q", "")
    search_query = search_query.lower() # removes case sensitivity 

    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT id, title, release_year, poster_path FROM Movies WHERE Title LIKE ? LIMIT 10", ('%' + search_query + '%',))

    results = cursor.fetchall()
    conn.close()

    # convert rows to json
    movies = [{"id": row["id"], "title": row["title"], "year": row["release_year"], "poster_path": row["poster_path"]} for row in results]
    return jsonify(movies)

@app.route('/save-favourites', methods=['POST'])
def save_favourites():
   
    data = request.get_json()
    film_ids = data.get("films", [])
    user_id = session['user_id']

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    for film_id in film_ids:

        cursor.execute(
            "SELECT MatrixID FROM Movies WHERE id = ?",
            (film_id,)
        )
        
        matrix_id = cursor.fetchone()[0]

        cursor.execute(
            "INSERT INTO Favourites (StudentID, MovieID) VALUES (?, ?)",
            (user_id, film_id)
        )

        # default rating of 5 in utility matrix
        cursor.execute(
            "INSERT INTO Ratings (StudentID, MovieID, MatrixID, Rating) VALUES (?, ?, ?, ?)",
            (user_id, film_id, matrix_id, 5)
        )

    # update user status so that they aren't new anymore 
    cursor.execute(
        "UPDATE StudentLogin SET FirstTime = 0 WHERE StudentID = ?",
        (user_id,)
    )

    # save changes and close connection
    conn.commit()
    conn.close()

    conn = sqlite3.connect('database.db')

    # load utility matrix
    ratings = pd.read_sql_query("SELECT StudentID, MatrixID, MovieID, Rating FROM Ratings", conn)
    conn.close()

    ratings = ratings.pivot(index="StudentID", columns="MatrixID", values="Rating")
    ratings = ratings.reindex(columns=range(1, 5001), fill_value=np.nan)
    print (ratings)

    return jsonify({
        "films_added": film_ids
    })

@app.route('/submit_review', methods=['POST'])
def submit_review():

    data = request.get_json()
    student_id = session.get('user_id')
    movie_id = data.get('movie_id')
    review_text = data.get('review')
    rating = data.get('rating')

    print (student_id)

    review_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print("student_id:", student_id)
    print("movie_id:", movie_id)
    print("rating:", rating)
    print("review_text:", review_text)
    
    # save to database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # check if the user already reviewed this movie
    existing_review = cursor.execute(
        'SELECT * FROM Reviews WHERE StudentID = ? AND MovieID = ?',
        (student_id, movie_id)
    ).fetchone()

    if existing_review:
        return jsonify({'message': 'You have already rated and reviewed this movie!'}), 400

    cursor.execute(
            "SELECT MatrixID FROM Movies WHERE id = ?",
            (movie_id,))
    
    matrix_id = cursor.fetchone()[0]

    cursor.execute('''
        INSERT INTO Reviews (StudentID, MovieID, Rating, ReviewText, Date) VALUES (?, ?, ?, ?, ?)''', 
        (student_id, movie_id, rating, review_text, review_date))
    
    cursor.execute('''
        INSERT INTO Ratings (StudentID, MovieID, MatrixID, Rating) VALUES (?,?,?,?)''',
        (student_id, movie_id, matrix_id, rating))

    conn.commit()
    conn.close()

    ratings = load_matrix()
    movie_ids = hybrid_recommender(student_id, ratings)  # call recommender
    movie_ids = [int(id) for id in movie_ids]

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    placeholders = ",".join("?" * len(movie_ids))  # placeholders (?, ?, ?)
    cursor.execute(f"SELECT id, title, release_year, poster_path FROM Movies WHERE id IN ({placeholders})", movie_ids)
    rows = cursor.fetchall()
    conn.close()

    base_url = "https://image.tmdb.org/t/p/w500"

    movies = []
    for id, title, year, poster in rows:
        movies.append({
                "id": id,
                "title": title,
                "release_year": year,
                "poster_path": base_url + poster
            })

    # save to session to avoid having to generate recommendaitons every time
    session['recommendations'] = movies

    return jsonify({'success': True})

@app.route('/addto_watchlist', methods=['POST'])
def addto_watchlist():

    data = request.get_json()
    student_id = session.get('user_id')
    movie_id = data.get('movie_id')
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # save to database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # check if the user already reviewed this movie
    existing_film = cursor.execute(
        'SELECT * FROM Watchlist WHERE StudentID = ? AND MovieID = ?',
        (student_id, movie_id)
    ).fetchone()

    if existing_film:
        return jsonify({'message': 'You have already added this film to your watchlist!'}), 400
    
    cursor.execute('''
        INSERT INTO Watchlist (StudentID, MovieID, Date) VALUES (?, ?, ?)''', 
        (student_id, movie_id, date))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/removefrom_watchlist', methods=['POST'])
def removefrom_watchlist():

    data = request.get_json()
    user_id = session.get("user_id")
    movie_id = data.get("movie_id")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM Watchlist
        WHERE StudentID = ? AND MovieID = ?
    """, (user_id, movie_id))

    conn.commit()
    conn.close()

    return jsonify({"success": True})

@app.route("/recommendations")
def recommendations():

    user_id = session.get('user_id')
    print ('userid is', user_id)

    if not user_id:
        return jsonify({"error": "User not logged in"}), 401

    movie_ids = hybrid_recommender(user_id, ratings) # call recommender 
    print (movie_ids)

    movie_ids = [int(id) for id in movie_ids]

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    placeholders = ",".join("?" * len(movie_ids)) # placeholders (?, ?, ?)
    print (placeholders)

    cursor.execute(f"SELECT id, title, release_year, poster_path FROM Movies WHERE id IN ({placeholders})", movie_ids)

    movies = cursor.fetchall()
    print (movies)

    base_url = "https://image.tmdb.org/t/p/w500" 
    for movie in movies:
        movie['poster_path'] = base_url + movie['poster_path']

    conn.close()

    return jsonify([ {"id": movie[0], "title": movie[1], "release_year": movie[2], "poster_path": movie[3]} for movie in movies])

if __name__ == '__main__':
    app.run(debug=True)
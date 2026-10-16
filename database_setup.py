import pandas as pd
import sqlite3
from flask_bcrypt import Bcrypt
import random

bcrypt = Bcrypt()

conn = sqlite3.connect("database.db") # establish connection

# loading movie CSV 
usecols = ['id', 'title', 'release_date', 'revenue', 'runtime', 'original_language', 
           'original_title', 'production_companies', 'production_countries', 'overview', 
           'popularity', 'poster_path', 'tagline', 'genres', 'spoken_languages', 'keywords']
            # specifying the necessary columns of the dataset to use
            
moviedf = pd.read_csv("datasets/TMDB_movie_dataset_v11.csv", 
                      usecols = usecols, index_col = "id", nrows = 1000) 
# read the CSV, index is the movie id, and 5000 movies read (can be adjusted)

# pre-processing data 

criticalcols = ['title', 'poster_path', 'release_date', 'overview', 'genres']
# columns that are essential to have and mustn't contain any null values 

moviedf = moviedf.dropna(subset = criticalcols) # drops null values in critical columns
moviedf['release_year'] = moviedf['release_date'].str[:4] # new column of releaseyear

# save dataframe as sql table 
moviedf['MatrixID'] = range(len(moviedf))
moviedf.to_sql("Movies", conn, if_exists="replace", index='id')

cursor = conn.cursor()

# teachers
cursor.execute("""
CREATE TABLE IF NOT EXISTS Teachers(
    TeacherID INTEGER PRIMARY KEY AUTOINCREMENT,
    Name TEXT NOT NULL,
    Username TEXT UNIQUE,
    PasswordHash TEXT );
""")

# class
cursor.execute("""
CREATE TABLE IF NOT EXISTS Class (
    ClassID INTEGER PRIMARY KEY,
    ClassName TEXT NOT NULL,
    TeacherID INTEGER NOT NULL,
    FOREIGN KEY (TeacherID) REFERENCES Teachers(TeacherID) );
""")

# students
cursor.execute("""
CREATE TABLE IF NOT EXISTS Students (
    StudentID INTEGER PRIMARY KEY AUTOINCREMENT,
    FullName TEXT UNIQUE NOT NULL,
    ClassID INTEGER NOT NULL,
    TargetGrade TEXT,
    FOREIGN KEY (ClassID) REFERENCES Class(ClassID) );
""")

#login db
cursor.execute("""
CREATE TABLE IF NOT EXISTS StudentLogin (
    StudentID INTEGER PRIMARY KEY AUTOINCREMENT,
    Username TEXT UNIQUE NOT NULL,
    PasswordHash TEXT NOT NULL, 
    FirstTime INTEGER DEFAULT 1 NOT NULL,
    FOREIGN KEY (StudentID) REFERENCES Students(StudentID) );
""")

# placeholder information
cursor.execute(
    "INSERT INTO Students (FullName, ClassID, TargetGrade) VALUES ('Ibrahim Hussain', 1, 'A*')"
)

username = "Ibrahim"
password = 'Password123'
hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

cursor.execute(
    "INSERT INTO StudentLogin (Username, PasswordHash) VALUES (?, ?)", (username, hashed_password)
)

username = "John"
password = 'Password'
hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

cursor.execute(
    "INSERT INTO StudentLogin (Username, PasswordHash) VALUES (?, ?)", (username, hashed_password)
)

# placeholder information
cursor.execute(
    "INSERT INTO Students (FullName, ClassID, TargetGrade) VALUES ('John Doe', 1, 'A*')"
)

username = "Nadeem"
password = 'Password'
hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

cursor.execute(
    "INSERT INTO StudentLogin (Username, PasswordHash) VALUES (?, ?)", (username, hashed_password)
)

# placeholder information
cursor.execute(
    "INSERT INTO Students (FullName, ClassID, TargetGrade) VALUES ('Nad Chow', 1, 'D')"
)

cursor.execute (
    "INSERT INTO Class (ClassID, ClassName, TeacherID) VALUES (1, 'ClassA', 1)"
)

cursor.execute (
    "INSERT INTO Teachers (TeacherID, Name, Username, PasswordHash) VALUES (1, 'Charlene Page', 'Charlene', 'Password123')"
)

# reviews 
cursor.execute("""
CREATE TABLE IF NOT EXISTS Reviews (
    WatchID INTEGER PRIMARY KEY AUTOINCREMENT,
    StudentID INTEGER NOT NULL,
    MovieID INTEGER NOT NULL,
    Rating REAL NOT NULL,
    Date TEXT NOT NULL,
    ReviewText TEXT NOT NULL, 
    UNIQUE (StudentID, MovieID)
    FOREIGN KEY (StudentID) REFERENCES Students(StudentID),
    FOREIGN KEY (MovieID) REFERENCES Movies(id)  );
""")

# academic details
cursor.execute("""
CREATE TABLE IF NOT EXISTS AcademicDetails (
    DetailID INTEGER PRIMARY KEY AUTOINCREMENT,
    StudentID INTEGER NOT NULL,
    MovieID INTEGER NOT NULL,
    QuizScore REAL,
    Analysis Grade TEXT,
    Watched INTEGER, 
    FOREIGN KEY (StudentID) REFERENCES Students(StudentID),
    FOREIGN KEY (MovieID) REFERENCES Movies(id)  );
""")

# favourite films 
cursor.execute("""
CREATE TABLE IF NOT EXISTS Favourites (
    StudentID INTEGER NOT NULL,
    MovieID INTEGER NOT NULL,
    UNIQUE (StudentID, MovieID),
    FOREIGN KEY (StudentID) REFERENCES Students(StudentID),
    FOREIGN KEY (MovieID) REFERENCES Movies(id)  );
""")

# ratings table 
cursor.execute("""
CREATE TABLE IF NOT EXISTS Ratings (
    StudentID INTEGER NOT NULL,
    MovieID INTEGER NOT NULL,
    MatrixID INTEGER NOT NULL,
    Rating REAL NOT NULL, 
    UNIQUE (StudentID, MovieID, MatrixID),
    FOREIGN KEY (StudentID) REFERENCES Students(StudentID),
    FOREIGN KEY (MovieID) REFERENCES Movies(id)  
    FOREIGN KEY (MatrixID) REFERENCES Movies(MatrixID)  );
""")

# watchlist table
cursor.execute("""
CREATE TABLE IF NOT EXISTS Watchlist (
    StudentID INTEGER NOT NULL,
    MovieID INTEGER NOT NULL,
    Date TEXT NOT NULL,
    UNIQUE (StudentID, MovieID)
    FOREIGN KEY (StudentID) REFERENCES Students(StudentID),
    FOREIGN KEY (MovieID) REFERENCES Movies(id)  );
""")


conn.commit()
conn.close()



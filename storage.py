# synthetic test users 
synthetic_users = [('TestUser1',),('TestUser2',),('TestUser3',),('TestUser4',),('TestUser5',)]

synthetic_students = []

for user in synthetic_users:
    synthetic_students.append((user[0], 1, 'A*'))

cursor.executemany(
    "INSERT INTO Students (FullName, ClassID, TargetGrade) VALUES (?, ?, ?)", synthetic_students
)

synthetic_logins = []

for user in synthetic_users:
    synthetic_logins.append((user[0], hashed_password))

cursor.executemany(
    "INSERT INTO StudentLogin (Username, PasswordHash) VALUES (?, ?)", synthetic_logins
)

# test users preferences



for user, preferred_genres in user_preferences.items():
    cursor.execute (
        "SELECT StudentID FROM Students WHERE FullName = ?", (user,)
    )

    user_id = cursor.fetchone()[0]

    for id, genres in movies:

        # decide whether to rate
        if random.random() > 0.2:
            continue   # skip this movie

        if any(genre in genres for genre in preferred_genres):
            rating = random.randint(4,5)
        else: 
            rating = random.randint(2,3)

        cursor.execute(
            "SELECT MatrixID FROM Movies WHERE id = ?",
            (id,)
        )

        matrix_id = cursor.fetchone()[0]

        synthetic_ratings.append(
            ((user_id, id, matrix_id, rating))
        )

    print (synthetic_ratings)

cursor.executemany(
    "INSERT INTO Ratings (StudentID, MovieID, MatrixID, Rating) VALUES (?, ?, ?, ?)",
    synthetic_ratings
)
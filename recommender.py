import pandas as pd 
import re 
import numpy as np 
import requests
from collections import defaultdict
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer 
from sklearn.metrics.pairwise import cosine_similarity 
import sqlite3

def load_matrix():
    
    # loading movies table to a pandas DF
    conn = sqlite3.connect('database.db')
    global moviedf 
    moviedf = pd.read_sql_query("SELECT id, title, overview, poster_path, tagline, genres, keywords, release_year FROM Movies", conn)

    # load utility matrix
    ratings = pd.read_sql_query("SELECT StudentID, MatrixID, MovieID, Rating FROM Ratings", conn)
    conn.close()

    ratings = ratings.pivot(index="StudentID", columns="MatrixID", values="Rating")
    ratings = ratings.reindex(columns=range(1, 1001), fill_value=np.nan)
    print (ratings)

    return ratings

def clean_text (text):

    stops = stopwords.words('english') # set to avoid duplicates
    text = text.lower() # converts to lowercase
    text = re.sub(r'[^a-z\s]', '', text) # removes special characters
    text = text.split() # tokenises string
    text = [word for word in text if word not in stops] # removes stopwords
    
    return ' '.join(text) # join back to string for TF-IDF

def TF_IDF (tokens, target_user):

    tfidf = TfidfVectorizer(ngram_range=(1, 2), max_features=5000, min_df = 3)
    tfidf_matrix = tfidf.fit_transform(tokens) # transforms into a matrix
    cosine_matrix = cosine_similarity(tfidf_matrix, tfidf_matrix)
    
    conn = sqlite3.connect('database.db')

    user_ratings = pd.read_sql_query(
    f"SELECT MatrixID, Rating FROM Ratings WHERE StudentID = {target_user}", conn
    )
    conn.close()

    # sort by rating and get 20 films 
    top_faves = user_ratings.sort_values(by="Rating", ascending=False).head(20)
    faves = top_faves['MatrixID'].tolist()

    id_to_index = {movie_id: matrix_id for matrix_id, movie_id in enumerate(moviedf.index)}
    # we need to map the movie id to a matrix id 

    fave_indices = [id_to_index[faveid] for faveid in faves]
    # finds cosine matrix index for favourite films

    similarities = [cosine_matrix[faveidx] for faveidx in fave_indices]
    # for each fave index, find row in cosine matrix

    average_sim = sum(similarities) / 3
    scores = list(enumerate(average_sim))

    scores = [score for score in scores if score[0] not in fave_indices]
    # excludes favourite films from being recommended 

    scores = sorted(scores, key=lambda x: x[1], reverse = True)
    # sorts in descending order and retrieves score for each film

    most_similar = scores[0:14] # obtains 14 most similar films

    for index, score in most_similar:
       print (f"{moviedf.iloc[index]['title']} - similarity score: {score:.3f}")

    cbf_score = ([(index, round(score, 3)) for index, score in most_similar])
    return cbf_score

def contentbased_filtering(target_user):
    
    genre_weighting = (moviedf['genres'] + ' ') * 2

    moviedf['combined'] = moviedf['overview'] + ' ' + genre_weighting +  ' ' + moviedf['keywords'] + ' ' + moviedf['tagline']
    moviedf['combined'] = moviedf['combined'].fillna(' ') # handles null values

    moviedf['tokens'] = moviedf['combined'].apply(clean_text)
    cbf_score = TF_IDF(moviedf['tokens'], target_user)

    return cbf_score

def synthetic_data(num_users, num_movies):

    np.random.seed(12345)

    userids = [id for id in range(1, num_users + 1)]
    movieids = [id for id in range (1, num_movies + 1)]

    mask = np.random.rand(num_users, num_movies) < 0.2

    ratings = np.random.choice([0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0], size=(num_users, num_movies),
                               p = [0.01, 0.02, 0.03, 0.05, 0.19, 0.24, 0.25, 0.15, 0.05, 0.01])
    
    ratings = np.where(mask, ratings, np.nan)
    utility_matrix = pd.DataFrame(ratings, index = userids, columns = movieids)

    return utility_matrix 

def map_syntheticid_to_movieid(ratings, moviedf):

    synthetic_movieids = ratings.columns.tolist() # put synthetic ids in list
    moviedf_ids = moviedf.index.tolist() # put movie ids in a list 

    mapping = dict(zip(synthetic_movieids, moviedf_ids)) # takes pairs for each index and converts to dict 

    return mapping

def create_similaritymatrix(ratings):

    ratings = ratings.fillna(0).values # fill NaN values to compute similarity 

    similarity_matrix = cosine_similarity(ratings) 
    np.fill_diagonal(similarity_matrix, 0) # fill diagonal values with 0 

    return similarity_matrix

def findK_neighbours(target_user, ratings):

    similarity_matrix = create_similaritymatrix(ratings)

     # ratings.index = [1,2,3,...]  # DB IDs
    user_id_to_index = {uid: i for i, uid in enumerate(ratings.index)}
    target_idx = user_id_to_index[target_user]

    print ('mapping:', user_id_to_index)
    print ('target user', target_user)
    print ('target index:', target_idx)

    target_similarity = similarity_matrix[target_idx] # obtain the target user's row
    top_k_neighbours = np.argsort(target_similarity)[-10:] # top 10 neighbours with highest scores 

    top_k_neighbours = top_k_neighbours[::-1] # reverse to get list in descending order 
    
    return top_k_neighbours

def find_potentialfilms(target_user, ratings):
    top_k_neighbours = findK_neighbours(target_user, ratings)

    targetuser_rated = ratings.loc[target_user] > 0 
    # returns boolean matrix (True - has watched, False - hasn't watched)

    filtered_ratings = ratings.iloc[top_k_neighbours].copy() # ratings for the neighbours 
    filtered_ratings.loc[:, targetuser_rated] = 0 
    # sets the True (movies watched by target user) to 0 

    rows, columns = np.where(filtered_ratings.values > 0)
    # returns (neighbour, movie) for where ratings exist 

    potential_films = defaultdict(list) # so we don't have to check if key already exists 
    movieid_mapping = map_syntheticid_to_movieid(ratings, moviedf)

    for neighbour, movie in zip(rows, columns): 
        neighbourid = filtered_ratings.index[neighbour]  # gets neighbourid
        movieid = filtered_ratings.columns[movie]
        rating = ratings.loc[neighbourid, movieid] # gets rating for a movie neighbour has watched
        potential_films[int(movieid)].append((int(neighbourid), float(rating)))

        movieid2 = movieid_mapping.get(movieid, "Unknown ID")
        # print (f"{moviedf.loc[movieid2]['title']}: neighbour= {neighbourid}, rating= {rating}")
        
    return potential_films

def CBF_filmrecs(target_user, ratings):

    potential_films = find_potentialfilms(target_user, ratings) 
    
    # initialise dictionaries 
    weighted_ratings  = {}
    sum_similarities = {}

    similarity_matrix = create_similaritymatrix(ratings) # call subroutines again 

    print ('target user is', target_user)

    # ratings.index = [1,2,3,...]  # DB IDs
    user_id_to_index = {uid: i for i, uid in enumerate(ratings.index)}
    target_idx = user_id_to_index[target_user]

    for movie, neighbour_rating in potential_films.items(): # iterate through each film 
            
            neighbours = np.array([entry[0] for entry in neighbour_rating]) # gets neighbours for each dict entry
            ratings_array = np.array([entry[1] for entry in neighbour_rating]) # gets ratings for each dict entry 

            neighbour_indices = [user_id_to_index[n] for n in neighbours]
            neighbour_similarities = similarity_matrix[target_idx][neighbour_indices] # finds neighbour similarities

            weighted_rating = np.dot(ratings_array, neighbour_similarities) # finds dot product 
            sum_similarity = np.sum(neighbour_similarities) # adds up similarities to normalise later

            weighted_ratings[movie] = weighted_rating # stores results for each film 
            sum_similarities[movie] = sum_similarity

    weighted_series = pd.Series(weighted_ratings) # converting dict to series for easy division
    sum_series = pd.Series(sum_similarities)

    predicted_ratings = (weighted_series / sum_series) # normalising 

    # sort by predicting rating, in descending order 
    top_recommendations = sorted(predicted_ratings.items(), key=lambda x: x[1], reverse=True)

    recs = top_recommendations[:14]

    movieid_mapping = map_syntheticid_to_movieid(ratings, moviedf)

    knn_scores = []

    for movie, score in recs:
        movieid = movieid_mapping.get(movie, "Unknown ID")
        print (f"{moviedf.loc[movieid]['title']}: predicted rating = {score:.10f}")
    
        knn_scores.append((movieid, score))
    
    return knn_scores 

def collaborative_filtering(target_user, ratings): 

    CBF_filmrecs(target_user, ratings) # generate film recommendations 

def matrix_factorisation(target_user, ratings):

    # import relevant modules
    import os
    import random
    import operator 
    import requests
    import numpy as np
    import pandas as pd
    from scipy import sparse
    import sys
    from surprise import Dataset, Reader
    from surprise import KNNBasic, SVD
    from surprise.model_selection import train_test_split
    from surprise import accuracy
    from surprise.dataset import DatasetAutoFolds

    long_format = ratings.stack().reset_index() # put data into long format
    long_format.columns = ['userid', 'itemid', 'rating']

    reader = Reader(rating_scale=(0.5, 5.0)) # rating scale range
    data = Dataset.load_from_df(long_format, reader)

    # split data into training and testing sets 
    trainset, testset = train_test_split(data, test_size=0.25)
    
    model = SVD()
    model.fit(trainset)

    predictions = model.test(testset)
    accuracy.rmse(predictions) # calculates RMSE 
    accuracy.mae(predictions)

    items = trainset.build_anti_testset() # user-item pairs not in training set 

    user_items = list(filter(lambda x: x[0] == target_user, items))

    # generate recommendation
    recommendations = model.test(user_items) 
    recommendations.sort(key=operator.itemgetter(3), reverse=True) # sorts by rating 

    movieid_mapping = map_syntheticid_to_movieid(ratings, moviedf) # mapping subroutine


    mf_scores = []
    for rec in recommendations[0:14]:
        movie_id = rec[1] 
        movieid = movieid_mapping.get(movie_id, "Unknown ID") # map synthetic id to movie id
        predicted_rating = round(rec[3], 3) 

        mf_scores.append((movie_id, predicted_rating))
        print(f" movie: {moviedf.loc[movieid]['title']}, predicted rating: {predicted_rating}")
        
    return mf_scores

def matrix_sparsity(ratings):

    rows, columns = ratings.shape # gets number of rows and columns
    print (f"shape is {ratings.shape}")
    total_ratings = (rows * columns) # multiply to get total ratings

    actual_ratings = ratings.notnull().sum().sum() # find sum of non-null values 
    sparsity = 1 - (actual_ratings / total_ratings) # calculate sparsity 
    
    return sparsity 

def algorithm_selection(target_user, ratings, sparsity, user_ratings):

    print ('matrix sparsity is', sparsity)
    print (f'user {target_user} has {user_ratings} ratings')

    # if matrix is too sparse or insufficient user data, use CBF
    if user_ratings <= 10:
        print ('use CBF completely')
        return 'use CBF completely'

    if sparsity >= 0.95:
        print ('use CBF completely')
        return 'use CBF completely'

    elif sparsity >= 0.9:
        print ('use blend of CBF and MF')
        return 'use blend of CBF and MF'

    elif sparsity >= 0.8:
        print ('use blend of MF and KNN')
        return 'use blend of MF and KNN'

    else: # if matrix is dense enough and user has > 10 ratings
        print ('use KNN completely')
        return 'use KNN completely'

def compute_mu(target_user, ratings, sparsity, user_ratings):

    # decide which algorithm or blend we want 
    algorithm = algorithm_selection(target_user, ratings, sparsity, user_ratings)

    if algorithm == 'use CBF completely':
        sparsity_mu = 0

    elif algorithm == 'use KNN completely':
        sparsity_mu = 1

    elif algorithm == 'use blend of CBF and MF':
        sparsity_mu = (0.95 - sparsity) / (0.95 - 0.85)
        # normalises sparsity mu to a float between [0,1]

    elif algorithm == 'use blend of MF and KNN':
        sparsity_mu = (0.85 - sparsity) / (0.85 - 0.75)
        # normalises sparsity mu to a float between [0,1]
    
    user_mu = np.clip((user_ratings - 10) / 20, 0, 1)
    # normalises user mu to a float between [0,1]

    print ('sparsity mu:', sparsity_mu)
    print ('user_mu', user_mu)
    
    print ('mu is', sparsity_mu * user_mu)
    return sparsity_mu * user_mu 

def blend_scores(cbf_scores, mf_scores, mu):

    films_union = set(cbf_scores) | set(mf_scores) # finds the union of both sets 
    weighted_scores = {movie_id: mu * mf_scores.get(movie_id, 0) + (1 - mu) * cbf_scores.get(movie_id, 0) for movie_id in films_union}
    # important line: forms a dictionary of movieid, score
    # score is calculated with the mu formula, so the scores are now weighted 

    return weighted_scores

def hybrid_recommender(target_user, ratings):

    watched_byuser = ratings.loc[target_user] > 0 # boolean mask
    user_ratings = ratings.loc[target_user][watched_byuser].count() # count Trues to get user ratings

    sparsity = matrix_sparsity(ratings)
    mu = compute_mu(target_user, ratings, sparsity, user_ratings) # calculate the value of mu 

    algorithm = algorithm_selection(target_user, ratings, sparsity, user_ratings)

    if algorithm == 'use CBF completely' or algorithm == 'use blend of CBF and MF':

        cbf_output = contentbased_filtering(target_user) # scores from content-based filtering in (movieid, score)
        cbf_scores = {movie_id: score for movie_id, score in cbf_output}

        mf_output = matrix_factorisation(target_user, ratings) # scores from collaborative filtering in (movieid, spredicted)
        mf_scores = {movie_id: predicted for movie_id, predicted in mf_output} # convert to dictionary for look-up
        mf_scores = {movie_id: (predicted - 0.5) / 4.5 for movie_id, predicted in mf_scores.items()} # normalise 

        scores = blend_scores(cbf_scores, mf_scores, mu) # call subroutine to blend scores


        top_recs = sorted(scores.items(), key=lambda x: x[1], reverse=True)


    if algorithm == 'use KNN completely' or algorithm == 'use blend of MF and KNN':

        mf_output = matrix_factorisation(target_user, ratings) # scores from collaborative filtering in (movieid, spredicted)
        mf_scores = {movie_id: predicted for movie_id, predicted in mf_output} # convert to dictionary for look-up
        mf_scores = {movie_id: (predicted - 0.5) / 4.5 for movie_id, predicted in mf_scores.items()} # normalise 


        knn_output = CBF_filmrecs(target_user, ratings) # scores from content-based filtering in (movieid, score)
        knn_scores = {movie_id: score for movie_id, score in knn_output}


        scores = blend_scores(mf_scores, knn_scores, mu) # call subroutine to blend scores

        top_recs = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    recommendations = []

    for matrixid, score in top_recs:

        actual_id = moviedf.iloc[matrixid]['id']   # SQL MovieID
        title = moviedf.iloc[matrixid]['title']
        recommendations.append((actual_id, title, score))
    
    print (recommendations)

    recommendation_ids = [film[0] for film in recommendations]
    return (recommendation_ids[0:14])

def evaluate_precision(target_user, ratings):
    user_ratings = ratings.loc[target_user]
    relevant_films = user_ratings[user_ratings >= 4.0].dropna().index.tolist()

    print (relevant_films)

    for i in relevant_films:
        mapping = map_syntheticid_to_movieid(ratings, moviedf)
        movieid = mapping.get(i, 'unknown ID')
        print (moviedf.loc[movieid]['title'])

load_matrix()
ratings = synthetic_data(50, 1000)
CBF_filmrecs(1, ratings)
evaluate_precision(1, ratings)



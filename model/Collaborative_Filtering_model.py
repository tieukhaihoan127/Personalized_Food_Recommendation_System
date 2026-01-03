import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import csr_matrix
import json
import os


def load_user_ratings():
    ratings_data = []

    if os.path.exists("./data/restaurant_comments.json"):
        try:
            with open("./data/restaurant_comments.json", 'r', encoding='utf-8') as f:
                reviews = json.load(f)

            for review in reviews:
                ratings_data.append({
                    'user_id': review.get('user_id', 'anonymous'),
                    'restaurant_id': review.get('res_id', 0),
                    'rating': review.get('rating', 5),
                    'source': 'foody'
                })
        except:
            pass

    if os.path.exists("./data/user_preferences.json"):
        try:
            with open("./data/user_preferences.json", 'r', encoding='utf-8') as f:
                prefs = json.load(f)

            for res_id in prefs.get('liked_restaurants', []):
                ratings_data.append({
                    'user_id': 'current_user',
                    'restaurant_id': res_id,
                    'rating': 9,
                    'source': 'preference'
                })

            for res_id in prefs.get('viewed_restaurants', [])[-10:]:
                if res_id not in prefs.get('liked_restaurants', []):
                    ratings_data.append({
                        'user_id': 'current_user',
                        'restaurant_id': res_id,
                        'rating': 6,
                        'source': 'preference'
                    })
        except:
            pass

    if not ratings_data:
        return pd.DataFrame(columns=['user_id', 'restaurant_id', 'rating'])

    df = pd.DataFrame(ratings_data)
    df['rating'] = df['rating'].clip(1, 10)

    return df


def build_user_item_matrix(ratings_df):
    if ratings_df.empty:
        return None, None, None

    user_item_matrix = ratings_df.pivot_table(
        index='user_id',
        columns='restaurant_id',
        values='rating',
        fill_value=0
    )

    sparse_matrix = csr_matrix(user_item_matrix.values)

    return user_item_matrix, sparse_matrix, user_item_matrix.index, user_item_matrix.columns

def calculate_user_similarity(user_item_matrix):
    if user_item_matrix is None:
        return None

    user_similarity = cosine_similarity(user_item_matrix.values)

    return pd.DataFrame(
        user_similarity,
        index=user_item_matrix.index,
        columns=user_item_matrix.index
    )

def calculate_item_similarity(user_item_matrix):
    if user_item_matrix is None:
        return None

    item_similarity = cosine_similarity(user_item_matrix.T.values)

    return pd.DataFrame(
        item_similarity,
        index=user_item_matrix.columns,
        columns=user_item_matrix.columns
    )

def get_cf_recommendations(user_id, user_item_matrix, item_similarity_df, n=10):
    if user_item_matrix is None or item_similarity_df is None:
        return []

    if user_id not in user_item_matrix.index:
        return get_popular_recommendations(user_item_matrix, n)
    
    user_ratings = user_item_matrix.loc[user_id]
    unrated_items = user_ratings[user_ratings == 0].index.tolist()

    if not unrated_items:
        return []

    predictions = []

    for item_id in unrated_items:
        if item_id not in item_similarity_df.index:
            continue

        rated_items = user_ratings[user_ratings > 0].index

        if len(rated_items) == 0:
            continue

        similarities = item_similarity_df.loc[item_id, rated_items]

        if similarities.sum() > 0:
            predicted_rating = (similarities * user_ratings[rated_items]).sum() / similarities.sum()
            predictions.append((item_id, predicted_rating))

    predictions.sort(key=lambda x: x[1], reverse=True)

    return predictions[:n]


def get_popular_recommendations(user_item_matrix, n=10):
    if user_item_matrix is None:
        return []

    avg_ratings = user_item_matrix.mean(axis=0)

    top_items = avg_ratings.nlargest(n)

    return [(item_id, score) for item_id, score in top_items.items()]

class CollaborativeFilteringModel:
    def __init__(self):
        self.ratings_df = None
        self.user_item_matrix = None
        self.user_similarity_df = None
        self.item_similarity_df = None
        self.is_trained = False

    def train(self):
        self.ratings_df = load_user_ratings()

        if self.ratings_df.empty:
            print("No ratings data found!")
            self.is_trained = False
            return False

        print(f"Loaded {len(self.ratings_df)} ratings")
        print(f"Users: {self.ratings_df['user_id'].nunique()}")
        print(f"Restaurants: {self.ratings_df['restaurant_id'].nunique()}")

        print("Building user-item matrix")
        self.user_item_matrix, _, _, _ = build_user_item_matrix(self.ratings_df)

        if self.user_item_matrix is None:
            self.is_trained = False
            return False

        print("Calculating item similarity")
        self.item_similarity_df = calculate_item_similarity(self.user_item_matrix)

        print("CF Model trained successfully!")
        self.is_trained = True
        return True

    def get_recommendations(self, user_id='current_user', n=10):
        if not self.is_trained:
            return []

        return get_cf_recommendations(
            user_id,
            self.user_item_matrix,
            self.item_similarity_df,
            n
        )

def load_cf_model():
    model = CollaborativeFilteringModel()
    model.train()
    return model


if __name__ == "__main__":
    print("Testing Collaborative Filtering Model")

    model = load_cf_model()

    if model.is_trained:
        recommendations = model.get_recommendations('current_user', n=10)
        for i, (res_id, score) in enumerate(recommendations, 1):
            print(f"{i}. Restaurant ID: {res_id}, Score: {score:.3f}")
    else:
        print("Model training failed - not enough data")
import itertools
import pandas as pd
import numpy as np
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import MinMaxScaler

def load_and_prepare_data(json_path="./data/restaurants.json"):
    data = pd.read_json(json_path)
    features = [
        'id', 'name', 'address', 'district', 'city', 'category',
        'food_categories', 'main_opening_hour', 'main_closing_hour',
        'style', 'appropriate', 'suitable_time',
        'average_price_min', 'avarage_price_max', 'average_rating',
        'quality_rating', 'service_rating', 'price_rating',
        'location_rating', 'space_rating'
    ]

    existing_features = [f for f in features if f in data.columns]
    X = data[existing_features].copy()

    for col in X.columns:
        if X[col].dtype == 'object':
            X[col] = X[col].fillna('')
        else:
            X[col] = X[col].fillna(0)
        'style', 'appropriate', 'suitable_time',
        'average_price_min', 'avarage_price_max', 'average_rating',
        'quality_rating', 'service_rating', 'price_rating',
        'location_rating', 'space_rating'

    for col in X.columns:
        if X[col].dtype == 'object':
            X[col] = X[col].fillna('')
        else:
            X[col] = X[col].fillna(0)

    return X

def build_feature_matrix(X):
    all_food_cats = list(set(itertools.chain.from_iterable(X['food_categories'])))
    food_matrix = np.zeros((len(X), len(all_food_cats)))

    for i, row in X.iterrows():
        for j, cat in enumerate(all_food_cats):
            if cat in row['food_categories']:
                food_matrix[i, j] = 1

    all_styles = list(set(itertools.chain.from_iterable(X['style'])))
    style_matrix = np.zeros((len(X), len(all_styles)))

    for i, row in X.iterrows():
        for j, style in enumerate(all_styles):
            if style in row['style']:
                style_matrix[i, j] = 1

    all_appropriate = list(set(itertools.chain.from_iterable(X['appropriate'])))
    appropriate_matrix = np.zeros((len(X), len(all_appropriate)))

    for i, row in X.iterrows():
        for j, app in enumerate(all_appropriate):
            if app in row['appropriate']:
                appropriate_matrix[i, j] = 1

    if 'suitable_time' in X.columns:
        all_times = list(set(itertools.chain.from_iterable(X['suitable_time'])))
        time_matrix = np.zeros((len(X), len(all_times)))

        for i, row in X.iterrows():
            for j, time in enumerate(all_times):
                if time in row['suitable_time']:
                    time_matrix[i, j] = 1
    else:
        time_matrix = np.zeros((len(X), 1))

    districts = X['district'].unique()
    district_matrix = np.zeros((len(X), len(districts)))
    district_dict = {d: i for i, d in enumerate(districts)}

    for i, row in X.iterrows():
        if row['district'] in district_dict:
            district_matrix[i, district_dict[row['district']]] = 1

    scaler = MinMaxScaler()
    price_matrix = scaler.fit_transform(
        X[['average_price_min', 'avarage_price_max']].values
    )

    if 'average_rating' in X.columns:
        rating_matrix = scaler.fit_transform(
            X[['average_rating']].values
        )
    else:
        rating_matrix = np.zeros((len(X), 1))

    combined_matrix = np.hstack([
        food_matrix * 3, 
        style_matrix * 2,  
        appropriate_matrix * 2, 
        time_matrix * 1.5, 
        district_matrix * 1.5,  
        price_matrix * 1, 
        rating_matrix * 1 
    ])

    return combined_matrix

def build_similarity_model(X):
    feature_matrix = build_feature_matrix(X)
    cosine_sim = cosine_similarity(feature_matrix, feature_matrix)
    return cosine_sim

def recommend_restaurants(restaurant_id, X, cosine_sim, n=10):
    try:
        idx = X[X['id'] == restaurant_id].index[0]

        sim_scores = list(enumerate(cosine_sim[idx]))

        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)

        sim_scores = sim_scores[1:n + 1]

        restaurant_indices = [i[0] for i in sim_scores]

        return X.iloc[restaurant_indices]['id'].tolist()

    except IndexError:
        return []


def get_recommendations(name, X, cosine_sim, top_n=5):
    matches = X[X['name'].str.lower() == name.lower()]

    if len(matches) == 0:
        return pd.DataFrame()

    idx = matches.index[0]
    restaurant_id = X.loc[idx, 'id']

    recommended_ids = recommend_restaurants(restaurant_id, X, cosine_sim, top_n)

    recommendations = X[X['id'].isin(recommended_ids)].copy()

    for i, rec_id in enumerate(recommended_ids):
        rec_idx = X[X['id'] == rec_id].index[0]
        recommendations.loc[recommendations['id'] == rec_id, 'similarity'] = cosine_sim[idx][rec_idx]
    idx = matches.index[0]
    restaurant_id = X.loc[idx, 'id']

    recommendations = recommendations.sort_values('similarity', ascending=False)

    return recommendations[['name', 'district', 'address', 'category', 'food_categories', 'similarity']]


def get_recommendations_by_preferences(food_cats, districts, X, cosine_sim, top_n=10):
    filtered = X.copy()

    if food_cats:
        filtered = filtered[
            filtered['food_categories'].apply(
                lambda cats: any(cat in food_cats for cat in cats)
            )
        ]

    if districts:
        filtered = filtered[filtered['district'].isin(districts)]

    filtered = filtered.sort_values('average_rating', ascending=False)

    return filtered.head(top_n)['id'].tolist()

def load_data(json_path="./data/restaurants.json"):
    X = load_and_prepare_data(json_path)
    cosine_sim = build_similarity_model(X)
    return X, cosine_sim

if __name__ == "__main__":
    X, cosine_sim = load_data()
    print(f"Loaded {len(X)} restaurants")
    print(f"Similarity matrix shape: {cosine_sim.shape}")

    if len(X) > 0:
        test_id = X.iloc[0]['id']
        test_name = X.iloc[0]['name']

        recs = recommend_restaurants(test_id, X, cosine_sim, n=5)
        print(f"Recommended IDs: {recs}")

        recs_df = get_recommendations(test_name, X, cosine_sim, top_n=5)
        print("Recommendations:")
        print(recs_df[['name', 'district', 'similarity']])
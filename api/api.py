from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Resource, Api, reqparse, fields, marshal_with, marshal, abort
from datetime import datetime
import json
import os

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "database.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
api = Api(app)

class RestaurantModel(db.Model):
    __tablename__ = 'restaurants'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.String(200))
    district = db.Column(db.String(100))
    city = db.Column(db.String(100))
    main_opening_hour = db.Column(db.String(10))
    main_closing_hour = db.Column(db.String(10))
    sub_opening_hour = db.Column(db.String(10))
    sub_closing_hour = db.Column(db.String(10))
    category = db.Column(db.String(100))
    food_categories = db.Column(db.Text)  
    suitable_time = db.Column(db.Text)
    style = db.Column(db.Text) 
    appropriate = db.Column(db.Text) 
    average_price_min = db.Column(db.Float)
    avarage_price_max = db.Column(db.Float)
    average_rating = db.Column(db.Float)
    quality_rating = db.Column(db.Float)
    location_rating = db.Column(db.Float)
    price_rating = db.Column(db.Float)
    service_rating = db.Column(db.Float)
    space_rating = db.Column(db.Float)
    comment_quantity = db.Column(db.Integer)
    marvelous_comment = db.Column(db.Integer)
    good_comment = db.Column(db.Integer)
    ok_comment = db.Column(db.Integer)
    awful_comment = db.Column(db.Integer)
    image = db.Column(db.String(500))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

    
    reviews = db.relationship('ReviewModel', backref='restaurant', lazy=True, cascade='all, delete-orphan')

class ReviewModel(db.Model):
    __tablename__ = 'reviews'
    
    review_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100))
    username = db.Column(db.String(200))
    profile_url = db.Column(db.Text)
    review_text = db.Column(db.Text) 
    rating = db.Column(db.Float)
    timestamp = db.Column(db.String(50))
    res_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False)

class UserPreferenceModel(db.Model):
    __tablename__ = 'user_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), nullable=False, unique=True)
    preferred_categories = db.Column(db.Text) 
    preferred_districts = db.Column(db.Text) 
    price_range_min = db.Column(db.Float)
    price_range_max = db.Column(db.Float)
    avg_rating_given = db.Column(db.Float) 
    total_reviews = db.Column(db.Integer, default=0)

restaurant_args = reqparse.RequestParser()
restaurant_args.add_argument('name', type=str, required=True)
restaurant_args.add_argument('address', type=str)
restaurant_args.add_argument('district', type=str)
restaurant_args.add_argument('city', type=str)

review_args = reqparse.RequestParser()
review_args.add_argument('user_id', type=str, required=True)
review_args.add_argument('username', type=str, required=True)
review_args.add_argument('review_text', type=str, required=True)
review_args.add_argument('rating', type=float, required=True)
review_args.add_argument('res_id', type=int, required=True)

def extract_features_from_review(review_text):
    features = {
        'keywords': [],
        'aspects': {
            'food_quality': [],
            'service': [],
            'space': [],
            'price': [],
            'location': []
        },
        'sentiment': 'neutral',
        'sentiment_score': 0.5
    }
    
    if not review_text:
        return features
    
    text_lower = review_text.lower()

    positive_keywords = ['ngon', 'tốt', 'đẹp', 'sạch', 'rộng', 'tuyệt', 
                        'hợp lý', 'nhanh', 'nhiệt tình', 'tươi']
 
    negative_keywords = ['dở', 'tệ', 'chậm', 'bẩn', 'đắt', 'kém']
    
    found_positive = sum(1 for kw in positive_keywords if kw in text_lower)
    found_negative = sum(1 for kw in negative_keywords if kw in text_lower)

    if found_positive > found_negative:
        features['sentiment'] = 'positive'
        features['sentiment_score'] = min(0.5 + (found_positive * 0.1), 1.0)
    elif found_negative > found_positive:
        features['sentiment'] = 'negative'
        features['sentiment_score'] = max(0.5 - (found_negative * 0.1), 0.0)

    for kw in positive_keywords + negative_keywords:
        if kw in text_lower:
            features['keywords'].append(kw)

    food_words = ['ngon', 'tươi', 'tốt', 'dở', 'món']
    service_words = ['nhiệt tình', 'nhanh', 'chậm', 'phục vụ']
    space_words = ['rộng', 'đẹp', 'sạch', 'bẩn', 'không gian']
    price_words = ['rẻ', 'đắt', 'hợp lý', 'giá']
    
    for word in food_words:
        if word in text_lower:
            features['aspects']['food_quality'].append(word)
    
    for word in service_words:
        if word in text_lower:
            features['aspects']['service'].append(word)
    
    for word in space_words:
        if word in text_lower:
            features['aspects']['space'].append(word)
    
    for word in price_words:
        if word in text_lower:
            features['aspects']['price'].append(word)
    
    return features


def get_user_feature_profile(user_id):
    reviews = ReviewModel.query.filter_by(user_id=user_id).all()
    
    if not reviews:
        return {
            'total_reviews': 0,
            'avg_rating': 0,
            'preferred_aspects': {},
            'keywords': []
        }
    
    all_keywords = []
    aspect_counts = {
        'food_quality': {},
        'service': {},
        'space': {},
        'price': {},
        'location': {}
    }
    
    for review in reviews:
        if review.rating >= 4.0:
            features = extract_features_from_review(review.review_text)

            all_keywords.extend(features['keywords'])
   
            for aspect, words in features['aspects'].items():
                for word in words:
                    aspect_counts[aspect][word] = aspect_counts[aspect].get(word, 0) + 1

    from collections import Counter
    keyword_counter = Counter(all_keywords)
    top_keywords = [kw for kw, count in keyword_counter.most_common(10)]

    preferred_aspects = {}
    for aspect, words_dict in aspect_counts.items():
        if words_dict:
            top_words = sorted(words_dict.items(), key=lambda x: x[1], reverse=True)[:3]
            preferred_aspects[aspect] = [word for word, count in top_words]
    
    avg_rating = sum(r.rating for r in reviews) / len(reviews)
    
    return {
        'total_reviews': len(reviews),
        'avg_rating': avg_rating,
        'preferred_aspects': preferred_aspects,
        'keywords': top_keywords
    }


def calculate_feature_similarity(features1, features2):
    keywords1 = set(features1.get('keywords', []))
    keywords2 = set(features2.get('keywords', []))
    
    if not keywords1 or not keywords2:
        return 0.0
    
    intersection = len(keywords1 & keywords2)
    union = len(keywords1 | keywords2)
    
    keyword_sim = intersection / union if union > 0 else 0

    aspects1 = features1.get('preferred_aspects', {})
    aspects2 = features2.get('aspects', {})
    
    aspect_scores = []
    for aspect in ['food_quality', 'service', 'space', 'price']:
        words1 = set(aspects1.get(aspect, []))
        words2 = set(aspects2.get(aspect, []))
        
        if words1 or words2:
            intersection = len(words1 & words2)
            union = len(words1 | words2)
            aspect_scores.append(intersection / union if union > 0 else 0)
    
    aspect_sim = sum(aspect_scores) / len(aspect_scores) if aspect_scores else 0

    similarity = 0.6 * keyword_sim + 0.4 * aspect_sim
    
    return similarity

restaurantFields = {
    'id': fields.Integer,
    'name': fields.String,
    'address': fields.String,
    'district': fields.String,
    'city': fields.String,
    'main_opening_hour': fields.String,
    'main_closing_hour': fields.String,
    'category': fields.String,
    'food_categories': fields.String,
    'average_price_min': fields.Float,
    'avarage_price_max': fields.Float,
    'average_rating': fields.Float,
    'quality_rating': fields.Float,
    'location_rating': fields.Float,
    'price_rating': fields.Float,
    'service_rating': fields.Float,
    'space_rating': fields.Float,
    'image': fields.String,
    'latitude': fields.Float,
    'longtitude': fields.Float,
}

reviewFields = {
    'review_id': fields.Integer,
    'user_id': fields.String,
    'username': fields.String,
    'profile_url': fields.String,
    'review_text': fields.String,
    'rating': fields.Float,
    'timestamp': fields.String,
    'res_id': fields.Integer
}

userPreferenceFields = {
    'id': fields.Integer,
    'user_id': fields.String,
    'preferred_categories': fields.String,
    'preferred_districts': fields.String,
    'price_range_min': fields.Float,
    'price_range_max': fields.Float,
    'avg_rating_given': fields.Float,
    'total_reviews': fields.Integer
}

class Restaurants(Resource):
    def get(self):
        district = request.args.get('district')
        query = RestaurantModel.query
        
        if district:
            query = query.filter(RestaurantModel.district.ilike(f'%{district}%'))
        
        restaurants = query.all()
        return [marshal(r, restaurantFields) for r in restaurants]
    
    def post(self):
        data = request.get_json()

        if data and 'food_categories' in data and not data.get('name'):
            food_categories = data.get('food_categories', [])
            district = data.get('district')
            
            query = RestaurantModel.query
            
            if district:
                query = query.filter(RestaurantModel.district.ilike(f'%{district}%'))
            
            if food_categories:
                for category in food_categories:
                    query = query.filter(RestaurantModel.food_categories.like(f'%{category}%'))
            
            restaurants = query.all()
            return [marshal(r, restaurantFields) for r in restaurants]

        args = restaurant_args.parse_args()
        restaurant = RestaurantModel(**args)
        db.session.add(restaurant)
        db.session.commit()
        return marshal(restaurant, restaurantFields), 201

class Restaurant(Resource):
    @marshal_with(restaurantFields)
    def get(self, id):
        restaurant = RestaurantModel.query.filter_by(id=id).first()
        if not restaurant:
            abort(404, message="Restaurant not found")
        return restaurant
    
    def patch(self, id):
        restaurant = RestaurantModel.query.filter_by(id=id).first()
        if not restaurant:
            abort(404, message="Restaurant not found")
        
        data = request.get_json()
        for key, value in data.items():
            if hasattr(restaurant, key):
                setattr(restaurant, key, value)
        
        db.session.commit()
        return marshal(restaurant, restaurantFields)
    
    def delete(self, id):
        restaurant = RestaurantModel.query.filter_by(id=id).first()
        if not restaurant:
            abort(404, message="Restaurant not found")
        db.session.delete(restaurant)
        db.session.commit()
        return '', 204

class Reviews(Resource):
    def get(self):
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        user_id = request.args.get('user_id')
        
        query = ReviewModel.query

        if user_id:
            query = query.filter_by(user_id=user_id)
        
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return {
            'reviews': [marshal(review, reviewFields) for review in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'per_page': per_page,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    
    def post(self):
        args = review_args.parse_args()
        review = ReviewModel(**args)
        db.session.add(review)
        db.session.commit()

        self._update_user_preferences(args['user_id'], args['rating'], args['res_id'])
        
        return marshal(review, reviewFields), 201
    
    def _update_user_preferences(self, user_id, rating, res_id):
        pref = UserPreferenceModel.query.filter_by(user_id=user_id).first()
        
        if not pref:
            pref = UserPreferenceModel(user_id=user_id, total_reviews=0, avg_rating_given=0)
            db.session.add(pref)

        total = pref.total_reviews
        pref.avg_rating_given = ((pref.avg_rating_given * total) + rating) / (total + 1)
        pref.total_reviews += 1

        restaurant = RestaurantModel.query.get(res_id)
        if restaurant and rating >= 4.0: 
            if restaurant.food_categories:
                existing = json.loads(pref.preferred_categories) if pref.preferred_categories else []
                restaurant_cats = json.loads(restaurant.food_categories)
                for cat in restaurant_cats:
                    if cat not in existing:
                        existing.append(cat)
                pref.preferred_categories = json.dumps(existing, ensure_ascii=False)

            if restaurant.district:
                existing_districts = json.loads(pref.preferred_districts) if pref.preferred_districts else []
                if restaurant.district not in existing_districts:
                    existing_districts.append(restaurant.district)
                pref.preferred_districts = json.dumps(existing_districts, ensure_ascii=False)
        
        db.session.commit()

class Review(Resource):
    @marshal_with(reviewFields)
    def get(self, review_id):
        review = ReviewModel.query.filter_by(review_id=review_id).first()
        if not review:
            abort(404, message="Review not found")
        return review
    
    def patch(self, review_id):
        review = ReviewModel.query.filter_by(review_id=review_id).first()
        if not review:
            abort(404, message="Review not found")
        
        data = request.get_json()
        for key, value in data.items():
            if hasattr(review, key):
                setattr(review, key, value)
        
        db.session.commit()
        return marshal(review, reviewFields)
    
    def delete(self, review_id):
        review = ReviewModel.query.filter_by(review_id=review_id).first()
        if not review:
            abort(404, message="Review not found")
        db.session.delete(review)
        db.session.commit()
        return '', 204

class RestaurantReviews(Resource):
    def get(self, res_id):
        reviews = ReviewModel.query.filter_by(res_id=res_id).all()
        if not reviews:
            return {'reviews': [], 'message': 'No reviews found'}
        return {'reviews': [marshal(r, reviewFields) for r in reviews]}

class UserPreferences(Resource):
    @marshal_with(userPreferenceFields)
    def get(self, user_id):
        pref = UserPreferenceModel.query.filter_by(user_id=user_id).first()
        if not pref:
            abort(404, message="User preferences not found")
        return pref

class RecommendContentBased(Resource):
    """Content-Based Filtering: dựa trên features từ reviews"""
    def post(self):
        data = request.get_json()
        user_id = data.get('user_id')
        top_k = data.get('top_k', 10)
        
        if not user_id:
            abort(400, message="user_id is required")

        user_profile = get_user_feature_profile(user_id)
        
        if user_profile['total_reviews'] == 0:
            return {
                'user_id': user_id,
                'recommendations': [],
                'method': 'content_based',
                'message': 'User has no reviews yet. Try popular recommendations.'
            }

        user_reviewed_restaurants = set(
            r.res_id for r in ReviewModel.query.filter_by(user_id=user_id).all()
        )

        restaurant_scores = []
        all_restaurants = RestaurantModel.query.all()
        
        for restaurant in all_restaurants:
            if restaurant.id in user_reviewed_restaurants:
                continue

            restaurant_reviews = ReviewModel.query.filter_by(res_id=restaurant.id).all()
            
            if not restaurant_reviews:
                continue

            restaurant_features = {
                'keywords': [],
                'aspects': {
                    'food_quality': [],
                    'service': [],
                    'space': [],
                    'price': [],
                    'location': []
                }
            }
            
            for review in restaurant_reviews:
                if review.rating >= 4.0:  
                    features = extract_features_from_review(review.review_text)
                    restaurant_features['keywords'].extend(features['keywords'])
                    for aspect, words in features['aspects'].items():
                        restaurant_features['aspects'][aspect].extend(words)

            similarity = calculate_feature_similarity(user_profile, restaurant_features)
            
            restaurant_scores.append({
                'restaurant': marshal(restaurant, restaurantFields),
                'score': similarity,
                'similarity': similarity,
                'explanation': self._generate_explanation(user_profile, restaurant_features)
            })

        restaurant_scores.sort(key=lambda x: x['score'], reverse=True)
        top_recommendations = restaurant_scores[:top_k]
        
        return {
            'user_id': user_id,
            'recommendations': top_recommendations,
            'method': 'content_based',
            'user_profile': user_profile
        }
    
    def _generate_explanation(self, user_profile, restaurant_features):
        common_keywords = set(user_profile['keywords']) & set(restaurant_features['keywords'])
        
        if common_keywords:
            return f"Phù hợp với sở thích của bạn: {', '.join(list(common_keywords)[:3])}"
        
        return "Được gợi ý dựa trên lịch sử đánh giá của bạn"

class RecommendCollaborativeFiltering(Resource):
    def post(self):
        data = request.get_json()
        user_id = data.get('user_id')
        top_k = data.get('top_k', 10)
        
        if not user_id:
            abort(400, message="user_id is required")

        return {
            'user_id': user_id,
            'recommendations': [],
            'method': 'collaborative_filtering',
            'message': 'Implementation pending - build user-item matrix'
        }

class RecommendHybrid(Resource):
    def post(self):
        data = request.get_json()
        user_id = data.get('user_id')
        top_k = data.get('top_k', 10)
        time_context = data.get('time_context') 
        
        if not user_id:
            abort(400, message="user_id is required")
        
        return {
            'user_id': user_id,
            'recommendations': [],
            'method': 'hybrid',
            'context': {
                'time': time_context
            },
            'message': 'Implementation pending - combine all methods'
        }

class ExtractReviewFeatures(Resource):
    def post(self):
        data = request.get_json()
        review_text = data.get('review_text')
        
        if not review_text:
            abort(400, message="review_text is required")
        
        features = extract_features_from_review(review_text)
        
        return {
            'review_text': review_text,
            'extracted_features': features
        }

class GetUserFeatureProfile(Resource):
    def get(self, user_id):
        profile = get_user_feature_profile(user_id)
        
        return {
            'user_id': user_id,
            'profile': profile
        }

class PopularRestaurants(Resource):
    def get(self):
        top_k = int(request.args.get('top_k', 10))
        district = request.args.get('district')
        
        query = RestaurantModel.query
        
        if district:
            query = query.filter(RestaurantModel.district.ilike(f'%{district}%'))
        
        restaurants = query.order_by(
            RestaurantModel.average_rating.desc(),
            RestaurantModel.comment_quantity.desc()
        ).limit(top_k).all()
        
        return {
            'recommendations': [marshal(r, restaurantFields) for r in restaurants],
            'method': 'popularity',
            'count': len(restaurants)
        }

api.add_resource(Restaurants, '/api/restaurants/')
api.add_resource(Restaurant, '/api/restaurants/<int:id>')
api.add_resource(Reviews, '/api/reviews/')
api.add_resource(Review, '/api/reviews/<int:review_id>')
api.add_resource(RestaurantReviews, '/api/restaurants/<int:res_id>/reviews')
api.add_resource(UserPreferences, '/api/users/<string:user_id>/preferences')

api.add_resource(RecommendContentBased, '/api/recommend/content-based')
api.add_resource(RecommendCollaborativeFiltering, '/api/recommend/collaborative')
api.add_resource(RecommendHybrid, '/api/recommend/hybrid')
api.add_resource(PopularRestaurants, '/api/recommend/popular')

api.add_resource(ExtractReviewFeatures, '/api/features/extract')
api.add_resource(GetUserFeatureProfile, '/api/features/user-profile/<string:user_id>')

@app.route('/')
def home():
    return jsonify({
        'message': 'Restaurant Recommendation System API',
        'endpoints': {
            'restaurants': '/api/restaurants/',
            'reviews': '/api/reviews/',
            'user_preferences': '/api/users/<user_id>/preferences',
            'recommendations': {
                'content_based': '/api/recommend/content-based',
                'collaborative': '/api/recommend/collaborative',
                'hybrid': '/api/recommend/hybrid',
                'popular': '/api/recommend/popular'
            }
        }
    })

@app.route('/api/reset-user', methods=['POST'])
def reset_user():
    data = request.get_json()
    user_id = data.get('user_id', 'default_user')
    
    with app.app_context():
        ReviewModel.query.filter_by(user_id=user_id).delete()
  
        UserPreferenceModel.query.filter_by(user_id=user_id).delete()
        
        db.session.commit()
    
    return jsonify({
        'message': f'User {user_id} has been reset successfully',
        'user_id': user_id
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        DEFAULT_USER_ID = 'default_user'
        ReviewModel.query.filter_by(user_id=DEFAULT_USER_ID).delete()
        UserPreferenceModel.query.filter_by(user_id=DEFAULT_USER_ID).delete()
        db.session.commit()
        
        print(f"\nDefault user '{DEFAULT_USER_ID}' has been reset!")
        print("You can use this user_id for all operations.\n")
    
    app.run(debug=True)
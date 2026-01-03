# from flask import Flask, jsonify, request
# from flask_sqlalchemy import SQLAlchemy
# from flask_restful import Resource, Api, reqparse, fields, marshal_with, marshal, abort
# from datetime import datetime
# import json
# import os

# app = Flask(__name__)
# basedir = os.path.abspath(os.path.dirname(__file__))
# app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "database.db")}'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# db = SQLAlchemy(app)
# api = Api(app)

# class RestaurantModel(db.Model):
#     __tablename__ = 'restaurants'
    
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(200), nullable=False)
#     address = db.Column(db.String(200))
#     district = db.Column(db.String(100))
#     city = db.Column(db.String(100))
#     main_opening_hour = db.Column(db.String(10))
#     main_closing_hour = db.Column(db.String(10))
#     sub_opening_hour = db.Column(db.String(10))
#     sub_closing_hour = db.Column(db.String(10))
#     category = db.Column(db.String(100))
#     food_categories = db.Column(db.Text)  
#     suitable_time = db.Column(db.Text)
#     style = db.Column(db.Text) 
#     appropriate = db.Column(db.Text) 
#     average_price_min = db.Column(db.Float)
#     avarage_price_max = db.Column(db.Float)
#     average_rating = db.Column(db.Float)
#     quality_rating = db.Column(db.Float)
#     location_rating = db.Column(db.Float)
#     price_rating = db.Column(db.Float)
#     service_rating = db.Column(db.Float)
#     space_rating = db.Column(db.Float)
#     comment_quantity = db.Column(db.Integer)
#     marvelous_comment = db.Column(db.Integer)
#     good_comment = db.Column(db.Integer)
#     ok_comment = db.Column(db.Integer)
#     awful_comment = db.Column(db.Integer)
#     image = db.Column(db.String(500))
#     latitude = db.Column(db.Float)
#     longitude = db.Column(db.Float)

    
#     reviews = db.relationship('ReviewModel', backref='restaurant', lazy=True, cascade='all, delete-orphan')

# class ReviewModel(db.Model):
#     __tablename__ = 'reviews'
    
#     review_id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.String(100))
#     username = db.Column(db.String(200))
#     profile_url = db.Column(db.Text)
#     review_text = db.Column(db.Text) 
#     rating = db.Column(db.Float)
#     timestamp = db.Column(db.String(50))
#     res_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False)

# class UserPreferenceModel(db.Model):
#     __tablename__ = 'user_preferences'
    
#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.String(100), nullable=False, unique=True)
#     preferred_categories = db.Column(db.Text) 
#     preferred_districts = db.Column(db.Text) 
#     price_range_min = db.Column(db.Float)
#     price_range_max = db.Column(db.Float)
#     avg_rating_given = db.Column(db.Float) 
#     total_reviews = db.Column(db.Integer, default=0)

# restaurant_args = reqparse.RequestParser()
# restaurant_args.add_argument('name', type=str, required=True)
# restaurant_args.add_argument('address', type=str)
# restaurant_args.add_argument('district', type=str)
# restaurant_args.add_argument('city', type=str)

# review_args = reqparse.RequestParser()
# review_args.add_argument('user_id', type=str, required=True)
# review_args.add_argument('username', type=str, required=True)
# review_args.add_argument('review_text', type=str, required=True)
# review_args.add_argument('rating', type=float, required=True)
# review_args.add_argument('res_id', type=int, required=True)

# def extract_features_from_review(review_text):
#     features = {
#         'keywords': [],
#         'aspects': {
#             'food_quality': [],
#             'service': [],
#             'space': [],
#             'price': [],
#             'location': []
#         },
#         'sentiment': 'neutral',
#         'sentiment_score': 0.5
#     }
    
#     if not review_text:
#         return features
    
#     text_lower = review_text.lower()

#     positive_keywords = ['ngon', 'tốt', 'đẹp', 'sạch', 'rộng', 'tuyệt', 
#                         'hợp lý', 'nhanh', 'nhiệt tình', 'tươi']
 
#     negative_keywords = ['dở', 'tệ', 'chậm', 'bẩn', 'đắt', 'kém']
    
#     found_positive = sum(1 for kw in positive_keywords if kw in text_lower)
#     found_negative = sum(1 for kw in negative_keywords if kw in text_lower)

#     if found_positive > found_negative:
#         features['sentiment'] = 'positive'
#         features['sentiment_score'] = min(0.5 + (found_positive * 0.1), 1.0)
#     elif found_negative > found_positive:
#         features['sentiment'] = 'negative'
#         features['sentiment_score'] = max(0.5 - (found_negative * 0.1), 0.0)

#     for kw in positive_keywords + negative_keywords:
#         if kw in text_lower:
#             features['keywords'].append(kw)

#     food_words = ['ngon', 'tươi', 'tốt', 'dở', 'món']
#     service_words = ['nhiệt tình', 'nhanh', 'chậm', 'phục vụ']
#     space_words = ['rộng', 'đẹp', 'sạch', 'bẩn', 'không gian']
#     price_words = ['rẻ', 'đắt', 'hợp lý', 'giá']
    
#     for word in food_words:
#         if word in text_lower:
#             features['aspects']['food_quality'].append(word)
    
#     for word in service_words:
#         if word in text_lower:
#             features['aspects']['service'].append(word)
    
#     for word in space_words:
#         if word in text_lower:
#             features['aspects']['space'].append(word)
    
#     for word in price_words:
#         if word in text_lower:
#             features['aspects']['price'].append(word)
    
#     return features


# def get_user_feature_profile(user_id):
#     reviews = ReviewModel.query.filter_by(user_id=user_id).all()
    
#     if not reviews:
#         return {
#             'total_reviews': 0,
#             'avg_rating': 0,
#             'preferred_aspects': {},
#             'keywords': []
#         }
    
#     all_keywords = []
#     aspect_counts = {
#         'food_quality': {},
#         'service': {},
#         'space': {},
#         'price': {},
#         'location': {}
#     }
    
#     for review in reviews:
#         if review.rating >= 4.0:
#             features = extract_features_from_review(review.review_text)

#             all_keywords.extend(features['keywords'])
   
#             for aspect, words in features['aspects'].items():
#                 for word in words:
#                     aspect_counts[aspect][word] = aspect_counts[aspect].get(word, 0) + 1

#     from collections import Counter
#     keyword_counter = Counter(all_keywords)
#     top_keywords = [kw for kw, count in keyword_counter.most_common(10)]

#     preferred_aspects = {}
#     for aspect, words_dict in aspect_counts.items():
#         if words_dict:
#             top_words = sorted(words_dict.items(), key=lambda x: x[1], reverse=True)[:3]
#             preferred_aspects[aspect] = [word for word, count in top_words]
    
#     avg_rating = sum(r.rating for r in reviews) / len(reviews)
    
#     return {
#         'total_reviews': len(reviews),
#         'avg_rating': avg_rating,
#         'preferred_aspects': preferred_aspects,
#         'keywords': top_keywords
#     }


# def calculate_feature_similarity(features1, features2):
#     keywords1 = set(features1.get('keywords', []))
#     keywords2 = set(features2.get('keywords', []))
    
#     if not keywords1 or not keywords2:
#         return 0.0
    
#     intersection = len(keywords1 & keywords2)
#     union = len(keywords1 | keywords2)
    
#     keyword_sim = intersection / union if union > 0 else 0

#     aspects1 = features1.get('preferred_aspects', {})
#     aspects2 = features2.get('aspects', {})
    
#     aspect_scores = []
#     for aspect in ['food_quality', 'service', 'space', 'price']:
#         words1 = set(aspects1.get(aspect, []))
#         words2 = set(aspects2.get(aspect, []))
        
#         if words1 or words2:
#             intersection = len(words1 & words2)
#             union = len(words1 | words2)
#             aspect_scores.append(intersection / union if union > 0 else 0)
    
#     aspect_sim = sum(aspect_scores) / len(aspect_scores) if aspect_scores else 0

#     similarity = 0.6 * keyword_sim + 0.4 * aspect_sim
    
#     return similarity

# restaurantFields = {
#     'id': fields.Integer,
#     'name': fields.String,
#     'address': fields.String,
#     'district': fields.String,
#     'city': fields.String,
#     'main_opening_hour': fields.String,
#     'main_closing_hour': fields.String,
#     'category': fields.String,
#     'food_categories': fields.String,
#     'average_price_min': fields.Float,
#     'avarage_price_max': fields.Float,
#     'average_rating': fields.Float,
#     'quality_rating': fields.Float,
#     'location_rating': fields.Float,
#     'price_rating': fields.Float,
#     'service_rating': fields.Float,
#     'space_rating': fields.Float,
#     'image': fields.String,
#     'latitude': fields.Float,
#     'longtitude': fields.Float,
# }

# reviewFields = {
#     'review_id': fields.Integer,
#     'user_id': fields.String,
#     'username': fields.String,
#     'profile_url': fields.String,
#     'review_text': fields.String,
#     'rating': fields.Float,
#     'timestamp': fields.String,
#     'res_id': fields.Integer
# }

# userPreferenceFields = {
#     'id': fields.Integer,
#     'user_id': fields.String,
#     'preferred_categories': fields.String,
#     'preferred_districts': fields.String,
#     'price_range_min': fields.Float,
#     'price_range_max': fields.Float,
#     'avg_rating_given': fields.Float,
#     'total_reviews': fields.Integer
# }

# class Restaurants(Resource):
#     def get(self):
#         district = request.args.get('district')
#         query = RestaurantModel.query
        
#         if district:
#             query = query.filter(RestaurantModel.district.ilike(f'%{district}%'))
        
#         restaurants = query.all()
#         return [marshal(r, restaurantFields) for r in restaurants]
    
#     def post(self):
#         data = request.get_json()

#         if data and 'food_categories' in data and not data.get('name'):
#             food_categories = data.get('food_categories', [])
#             district = data.get('district')
            
#             query = RestaurantModel.query
            
#             if district:
#                 query = query.filter(RestaurantModel.district.ilike(f'%{district}%'))
            
#             if food_categories:
#                 for category in food_categories:
#                     query = query.filter(RestaurantModel.food_categories.like(f'%{category}%'))
            
#             restaurants = query.all()
#             return [marshal(r, restaurantFields) for r in restaurants]

#         args = restaurant_args.parse_args()
#         restaurant = RestaurantModel(**args)
#         db.session.add(restaurant)
#         db.session.commit()
#         return marshal(restaurant, restaurantFields), 201

# class Restaurant(Resource):
#     @marshal_with(restaurantFields)
#     def get(self, id):
#         restaurant = RestaurantModel.query.filter_by(id=id).first()
#         if not restaurant:
#             abort(404, message="Restaurant not found")
#         return restaurant
    
#     def patch(self, id):
#         restaurant = RestaurantModel.query.filter_by(id=id).first()
#         if not restaurant:
#             abort(404, message="Restaurant not found")
        
#         data = request.get_json()
#         for key, value in data.items():
#             if hasattr(restaurant, key):
#                 setattr(restaurant, key, value)
        
#         db.session.commit()
#         return marshal(restaurant, restaurantFields)
    
#     def delete(self, id):
#         restaurant = RestaurantModel.query.filter_by(id=id).first()
#         if not restaurant:
#             abort(404, message="Restaurant not found")
#         db.session.delete(restaurant)
#         db.session.commit()
#         return '', 204

# class Reviews(Resource):
#     def get(self):
#         page = int(request.args.get('page', 1))
#         per_page = int(request.args.get('per_page', 50))
#         user_id = request.args.get('user_id')
        
#         query = ReviewModel.query

#         if user_id:
#             query = query.filter_by(user_id=user_id)
        
#         pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
#         return {
#             'reviews': [marshal(review, reviewFields) for review in pagination.items],
#             'total': pagination.total,
#             'pages': pagination.pages,
#             'current_page': page,
#             'per_page': per_page,
#             'has_next': pagination.has_next,
#             'has_prev': pagination.has_prev
#         }
    
#     def post(self):
#         args = review_args.parse_args()
#         review = ReviewModel(**args)
#         db.session.add(review)
#         db.session.commit()

#         self._update_user_preferences(args['user_id'], args['rating'], args['res_id'])
        
#         return marshal(review, reviewFields), 201
    
#     def _update_user_preferences(self, user_id, rating, res_id):
#         pref = UserPreferenceModel.query.filter_by(user_id=user_id).first()
        
#         if not pref:
#             pref = UserPreferenceModel(user_id=user_id, total_reviews=0, avg_rating_given=0)
#             db.session.add(pref)

#         total = pref.total_reviews
#         pref.avg_rating_given = ((pref.avg_rating_given * total) + rating) / (total + 1)
#         pref.total_reviews += 1

#         restaurant = RestaurantModel.query.get(res_id)
#         if restaurant and rating >= 4.0: 
#             if restaurant.food_categories:
#                 existing = json.loads(pref.preferred_categories) if pref.preferred_categories else []
#                 restaurant_cats = json.loads(restaurant.food_categories)
#                 for cat in restaurant_cats:
#                     if cat not in existing:
#                         existing.append(cat)
#                 pref.preferred_categories = json.dumps(existing, ensure_ascii=False)

#             if restaurant.district:
#                 existing_districts = json.loads(pref.preferred_districts) if pref.preferred_districts else []
#                 if restaurant.district not in existing_districts:
#                     existing_districts.append(restaurant.district)
#                 pref.preferred_districts = json.dumps(existing_districts, ensure_ascii=False)
        
#         db.session.commit()

# class Review(Resource):
#     @marshal_with(reviewFields)
#     def get(self, review_id):
#         review = ReviewModel.query.filter_by(review_id=review_id).first()
#         if not review:
#             abort(404, message="Review not found")
#         return review
    
#     def patch(self, review_id):
#         review = ReviewModel.query.filter_by(review_id=review_id).first()
#         if not review:
#             abort(404, message="Review not found")
        
#         data = request.get_json()
#         for key, value in data.items():
#             if hasattr(review, key):
#                 setattr(review, key, value)
        
#         db.session.commit()
#         return marshal(review, reviewFields)
    
#     def delete(self, review_id):
#         review = ReviewModel.query.filter_by(review_id=review_id).first()
#         if not review:
#             abort(404, message="Review not found")
#         db.session.delete(review)
#         db.session.commit()
#         return '', 204

# class RestaurantReviews(Resource):
#     def get(self, res_id):
#         reviews = ReviewModel.query.filter_by(res_id=res_id).all()
#         if not reviews:
#             return {'reviews': [], 'message': 'No reviews found'}
#         return {'reviews': [marshal(r, reviewFields) for r in reviews]}

# class UserPreferences(Resource):
#     @marshal_with(userPreferenceFields)
#     def get(self, user_id):
#         pref = UserPreferenceModel.query.filter_by(user_id=user_id).first()
#         if not pref:
#             abort(404, message="User preferences not found")
#         return pref

# class RecommendContentBased(Resource):
#     """Content-Based Filtering: dựa trên features từ reviews"""
#     def post(self):
#         data = request.get_json()
#         user_id = data.get('user_id')
#         top_k = data.get('top_k', 10)
        
#         if not user_id:
#             abort(400, message="user_id is required")

#         user_profile = get_user_feature_profile(user_id)
        
#         if user_profile['total_reviews'] == 0:
#             return {
#                 'user_id': user_id,
#                 'recommendations': [],
#                 'method': 'content_based',
#                 'message': 'User has no reviews yet. Try popular recommendations.'
#             }

#         user_reviewed_restaurants = set(
#             r.res_id for r in ReviewModel.query.filter_by(user_id=user_id).all()
#         )

#         restaurant_scores = []
#         all_restaurants = RestaurantModel.query.all()
        
#         for restaurant in all_restaurants:
#             if restaurant.id in user_reviewed_restaurants:
#                 continue

#             restaurant_reviews = ReviewModel.query.filter_by(res_id=restaurant.id).all()
            
#             if not restaurant_reviews:
#                 continue

#             restaurant_features = {
#                 'keywords': [],
#                 'aspects': {
#                     'food_quality': [],
#                     'service': [],
#                     'space': [],
#                     'price': [],
#                     'location': []
#                 }
#             }
            
#             for review in restaurant_reviews:
#                 if review.rating >= 4.0:  
#                     features = extract_features_from_review(review.review_text)
#                     restaurant_features['keywords'].extend(features['keywords'])
#                     for aspect, words in features['aspects'].items():
#                         restaurant_features['aspects'][aspect].extend(words)

#             similarity = calculate_feature_similarity(user_profile, restaurant_features)
            
#             restaurant_scores.append({
#                 'restaurant': marshal(restaurant, restaurantFields),
#                 'score': similarity,
#                 'similarity': similarity,
#                 'explanation': self._generate_explanation(user_profile, restaurant_features)
#             })

#         restaurant_scores.sort(key=lambda x: x['score'], reverse=True)
#         top_recommendations = restaurant_scores[:top_k]
        
#         return {
#             'user_id': user_id,
#             'recommendations': top_recommendations,
#             'method': 'content_based',
#             'user_profile': user_profile
#         }
    
#     def _generate_explanation(self, user_profile, restaurant_features):
#         common_keywords = set(user_profile['keywords']) & set(restaurant_features['keywords'])
        
#         if common_keywords:
#             return f"Phù hợp với sở thích của bạn: {', '.join(list(common_keywords)[:3])}"
        
#         return "Được gợi ý dựa trên lịch sử đánh giá của bạn"

# class RecommendCollaborativeFiltering(Resource):
#     def post(self):
#         data = request.get_json()
#         user_id = data.get('user_id')
#         top_k = data.get('top_k', 10)
        
#         if not user_id:
#             abort(400, message="user_id is required")

#         return {
#             'user_id': user_id,
#             'recommendations': [],
#             'method': 'collaborative_filtering',
#             'message': 'Implementation pending - build user-item matrix'
#         }

# class RecommendHybrid(Resource):
#     def post(self):
#         data = request.get_json()
#         user_id = data.get('user_id')
#         top_k = data.get('top_k', 10)
#         time_context = data.get('time_context') 
        
#         if not user_id:
#             abort(400, message="user_id is required")
        
#         return {
#             'user_id': user_id,
#             'recommendations': [],
#             'method': 'hybrid',
#             'context': {
#                 'time': time_context
#             },
#             'message': 'Implementation pending - combine all methods'
#         }

# class ExtractReviewFeatures(Resource):
#     def post(self):
#         data = request.get_json()
#         review_text = data.get('review_text')
        
#         if not review_text:
#             abort(400, message="review_text is required")
        
#         features = extract_features_from_review(review_text)
        
#         return {
#             'review_text': review_text,
#             'extracted_features': features
#         }

# class GetUserFeatureProfile(Resource):
#     def get(self, user_id):
#         profile = get_user_feature_profile(user_id)
        
#         return {
#             'user_id': user_id,
#             'profile': profile
#         }

# class PopularRestaurants(Resource):
#     def get(self):
#         top_k = int(request.args.get('top_k', 10))
#         district = request.args.get('district')
        
#         query = RestaurantModel.query
        
#         if district:
#             query = query.filter(RestaurantModel.district.ilike(f'%{district}%'))
        
#         restaurants = query.order_by(
#             RestaurantModel.average_rating.desc(),
#             RestaurantModel.comment_quantity.desc()
#         ).limit(top_k).all()
        
#         return {
#             'recommendations': [marshal(r, restaurantFields) for r in restaurants],
#             'method': 'popularity',
#             'count': len(restaurants)
#         }

# api.add_resource(Restaurants, '/api/restaurants/')
# api.add_resource(Restaurant, '/api/restaurants/<int:id>')
# api.add_resource(Reviews, '/api/reviews/')
# api.add_resource(Review, '/api/reviews/<int:review_id>')
# api.add_resource(RestaurantReviews, '/api/restaurants/<int:res_id>/reviews')
# api.add_resource(UserPreferences, '/api/users/<string:user_id>/preferences')

# api.add_resource(RecommendContentBased, '/api/recommend/content-based')
# api.add_resource(RecommendCollaborativeFiltering, '/api/recommend/collaborative')
# api.add_resource(RecommendHybrid, '/api/recommend/hybrid')
# api.add_resource(PopularRestaurants, '/api/recommend/popular')

# api.add_resource(ExtractReviewFeatures, '/api/features/extract')
# api.add_resource(GetUserFeatureProfile, '/api/features/user-profile/<string:user_id>')

# @app.route('/')
# def home():
#     return jsonify({
#         'message': 'Restaurant Recommendation System API',
#         'endpoints': {
#             'restaurants': '/api/restaurants/',
#             'reviews': '/api/reviews/',
#             'user_preferences': '/api/users/<user_id>/preferences',
#             'recommendations': {
#                 'content_based': '/api/recommend/content-based',
#                 'collaborative': '/api/recommend/collaborative',
#                 'hybrid': '/api/recommend/hybrid',
#                 'popular': '/api/recommend/popular'
#             }
#         }
#     })

# @app.route('/api/reset-user', methods=['POST'])
# def reset_user():
#     data = request.get_json()
#     user_id = data.get('user_id', 'default_user')
    
#     with app.app_context():
#         ReviewModel.query.filter_by(user_id=user_id).delete()
  
#         UserPreferenceModel.query.filter_by(user_id=user_id).delete()
        
#         db.session.commit()
    
#     return jsonify({
#         'message': f'User {user_id} has been reset successfully',
#         'user_id': user_id
#     })

# if __name__ == '__main__':
#     with app.app_context():
#         db.create_all()
        
#         DEFAULT_USER_ID = 'default_user'
#         ReviewModel.query.filter_by(user_id=DEFAULT_USER_ID).delete()
#         UserPreferenceModel.query.filter_by(user_id=DEFAULT_USER_ID).delete()
#         db.session.commit()
        
#         print(f"\nDefault user '{DEFAULT_USER_ID}' has been reset!")
#         print("You can use this user_id for all operations.\n")
    
#     app.run(debug=True)

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Resource, Api, fields, marshal, abort
from flask_cors import CORS
from datetime import datetime
import json
import os
from collections import defaultdict, Counter

# ==================== FLASK APP SETUP ====================
app = Flask(__name__)
CORS(app)

# Configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "database.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'

db = SQLAlchemy(app)
api = Api(app)

# ==================== MODELS ====================
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
    source = db.Column(db.String(20), default='user')

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
    liked_restaurants = db.Column(db.Text)
    viewed_restaurants = db.Column(db.Text)

# ==================== UTILITIES ====================
FOOD_KEYWORDS = {
    "bún": ["Bún"], "bun": ["Bún"],
    "cơm": ["Cơm"], "com": ["Cơm"],
    "phở": ["Phở"], "pho": ["Phở"],
    "bánh": ["Bánh mì", "Bánh"], "banh": ["Bánh mì", "Bánh"],
    "nướng": ["Đồ nướng"], "nuong": ["Đồ nướng"], "bbq": ["Đồ nướng"],
    "lẩu": ["Lẩu"], "lau": ["Lẩu"],
    "hải sản": ["Hải sản"], "hai san": ["Hải sản"],
    "gà": ["Gà"], "ga": ["Gà"], "chicken": ["Gà"],
    "bò": ["Bò"], "bo": ["Bò"],
    "pizza": ["Pizza"], "burger": ["Burger"],
    "mì": ["Mì"], "mi": ["Mì"],
}

DISTRICT_KEYWORDS = {
    "quận 1": "Quận 1", "quan 1": "Quận 1", "q1": "Quận 1",
    "quận 3": "Quận 3", "quan 3": "Quận 3", "q3": "Quận 3",
    "quận 5": "Quận 5", "quan 5": "Quận 5", "q5": "Quận 5",
    "bình thạnh": "Quận Bình Thạnh", "binh thanh": "Quận Bình Thạnh",
    "tân bình": "Quận Tân Bình", "tan binh": "Quận Tân Bình",
    "gò vấp": "Quận Gò Vấp", "go vap": "Quận Gò Vấp",
}

def parse_json_field(field_value):
    """Parse JSON field safely"""
    if not field_value:
        return []
    try:
        if isinstance(field_value, str):
            return json.loads(field_value)
        return field_value
    except:
        return []

def extract_keywords_from_comment(comment_text, restaurant_categories=None):
    """Extract food categories and districts from comment"""
    if not comment_text:
        return [], []
    
    comment_lower = comment_text.lower()
    detected_categories = set()
    detected_districts = set()
    
    # Ensure restaurant_categories is a list
    if restaurant_categories is None:
        restaurant_categories = []
    elif not isinstance(restaurant_categories, list):
        restaurant_categories = []
    
    # Detect food categories
    for keyword, potential_categories in FOOD_KEYWORDS.items():
        if keyword in comment_lower:
            if restaurant_categories:
                # Match với categories của restaurant
                for cat in potential_categories:
                    for rest_cat in restaurant_categories:
                        try:
                            if cat.lower() in rest_cat.lower() or rest_cat.lower() in cat.lower():
                                detected_categories.add(rest_cat)
                        except (AttributeError, TypeError):
                            continue
            else:
                # Không có restaurant categories → thêm trực tiếp
                detected_categories.update(potential_categories)
    
    # Detect districts
    for keyword, district in DISTRICT_KEYWORDS.items():
        if keyword in comment_lower:
            detected_districts.add(district)
    
    return list(detected_categories), list(detected_districts)

def calculate_cosine_similarity(vec1, vec2):
    """Calculate cosine similarity"""
    if len(vec1) == 0 or len(vec2) == 0:
        return 0.0
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = sum(a * a for a in vec1) ** 0.5
    magnitude2 = sum(b * b for b in vec2) ** 0.5
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
    return dot_product / (magnitude1 * magnitude2)

# ==================== RECOMMENDATION ALGORITHMS ====================
def get_user_restaurant_matrix():
    """Build user-restaurant rating matrix"""
    reviews = ReviewModel.query.all()
    user_ratings = defaultdict(dict)
    for review in reviews:
        user_ratings[review.user_id][review.res_id] = review.rating
    return user_ratings

def get_similar_users(target_user_id, user_ratings, top_n=5):
    """Find similar users"""
    if target_user_id not in user_ratings:
        return []
    
    target_ratings = user_ratings[target_user_id]
    similarities = []
    
    for user_id, ratings in user_ratings.items():
        if user_id == target_user_id:
            continue
        
        common_restaurants = set(target_ratings.keys()) & set(ratings.keys())
        if len(common_restaurants) < 2:
            continue
        
        vec1 = [target_ratings[r] for r in common_restaurants]
        vec2 = [ratings[r] for r in common_restaurants]
        
        similarity = calculate_cosine_similarity(vec1, vec2)
        if similarity > 0:
            similarities.append((user_id, similarity))
    
    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities[:top_n]

def get_collaborative_recommendations(user_id, n=10):
    """Collaborative Filtering"""
    user_ratings = get_user_restaurant_matrix()
    
    if user_id not in user_ratings:
        return []
    
    similar_users = get_similar_users(user_id, user_ratings)
    if not similar_users:
        return []
    
    target_user_restaurants = set(user_ratings[user_id].keys())
    recommendations = defaultdict(float)
    
    for similar_user_id, similarity in similar_users:
        for res_id, rating in user_ratings[similar_user_id].items():
            if res_id not in target_user_restaurants and rating >= 7:
                recommendations[res_id] += similarity * (rating / 10.0)
    
    if recommendations:
        max_score = max(recommendations.values())
        if max_score > 0:
            recommendations = {k: v/max_score for k, v in recommendations.items()}
    
    sorted_recs = sorted(recommendations.items(), key=lambda x: x[1], reverse=True)
    return [(res_id, score) for res_id, score in sorted_recs[:n]]

def get_content_based_recommendations(user_pref, n=10):
    """Content-Based Filtering"""
    preferred_categories = parse_json_field(user_pref.preferred_categories)
    preferred_districts = parse_json_field(user_pref.preferred_districts)
    liked_restaurants = parse_json_field(user_pref.liked_restaurants)
    viewed_restaurants = parse_json_field(user_pref.viewed_restaurants)
    
    all_restaurants = RestaurantModel.query.all()
    scored_restaurants = []
    
    for restaurant in all_restaurants:
        if restaurant.id in viewed_restaurants:
            continue
        
        score = 0.0
        rest_categories = parse_json_field(restaurant.food_categories)
        
        category_matches = len(set(preferred_categories) & set(rest_categories))
        if category_matches > 0:
            score += 0.6 * (category_matches / max(len(preferred_categories), 1))
        
        if restaurant.district in preferred_districts:
            score += 0.3
        
        if restaurant.average_rating:
            score += 0.1 * (restaurant.average_rating / 10.0)
        
        if score > 0:
            scored_restaurants.append((restaurant.id, score))
    
    scored_restaurants.sort(key=lambda x: x[1], reverse=True)
    return scored_restaurants[:n]

def get_hybrid_recommendations(user_id, n=12, cf_weight=0.4, cb_weight=0.6):
    """Hybrid Recommendation"""
    user_pref = UserPreferenceModel.query.filter_by(user_id=user_id).first()
    
    cf_recs = get_collaborative_recommendations(user_id, n=n*2)
    cf_dict = {res_id: score * cf_weight for res_id, score in cf_recs}
    
    if user_pref:
        cb_recs = get_content_based_recommendations(user_pref, n=n*2)
        cb_dict = {res_id: score * cb_weight for res_id, score in cb_recs}
    else:
        cb_dict = {}
    
    all_restaurant_ids = set(cf_dict.keys()) | set(cb_dict.keys())
    hybrid_scores = []
    
    for res_id in all_restaurant_ids:
        total_score = cf_dict.get(res_id, 0) + cb_dict.get(res_id, 0)
        
        if user_pref:
            restaurant = RestaurantModel.query.get(res_id)
            preferred_districts = parse_json_field(user_pref.preferred_districts)
            if restaurant and restaurant.district in preferred_districts:
                total_score += 0.1
        
        hybrid_scores.append({
            'res_id': res_id,
            'score': total_score,
            'cf_score': cf_dict.get(res_id, 0),
            'cb_score': cb_dict.get(res_id, 0)
        })
    
    hybrid_scores.sort(key=lambda x: x['score'], reverse=True)
    return hybrid_scores[:n]

# ==================== FIELD DEFINITIONS ====================
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
    'suitable_time': fields.String,
    'style': fields.String,
    'appropriate': fields.String,
    'average_price_min': fields.Float,
    'avarage_price_max': fields.Float,
    'average_rating': fields.Float,
    'quality_rating': fields.Float,
    'location_rating': fields.Float,
    'price_rating': fields.Float,
    'service_rating': fields.Float,
    'space_rating': fields.Float,
    'comment_quantity': fields.Integer,
    'image': fields.String,
    'latitude': fields.Float,
    'longitude': fields.Float,
}

reviewFields = {
    'review_id': fields.Integer,
    'user_id': fields.String,
    'username': fields.String,
    'profile_url': fields.String,
    'review_text': fields.String,
    'rating': fields.Float,
    'timestamp': fields.String,
    'res_id': fields.Integer,
    'source': fields.String
}

# ==================== API RESOURCES ====================
class Restaurants(Resource):
    def get(self):
        district = request.args.get('district')
        category = request.args.get('category')
        query = RestaurantModel.query
        
        if district:
            query = query.filter(RestaurantModel.district.ilike(f'%{district}%'))
        if category:
            query = query.filter(RestaurantModel.food_categories.like(f'%{category}%'))
        
        restaurants = query.all()
        return [marshal(r, restaurantFields) for r in restaurants]

class Restaurant(Resource):
    def get(self, id):
        restaurant = RestaurantModel.query.filter_by(id=id).first()
        if not restaurant:
            abort(404, message="Restaurant not found")
        return marshal(restaurant, restaurantFields)

class Reviews(Resource):
    def get(self):
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        res_id = request.args.get('res_id')
        
        query = ReviewModel.query
        if res_id:
            query = query.filter_by(res_id=int(res_id))
        
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return {
            'reviews': [marshal(review, reviewFields) for review in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page
        }
    
    def post(self):
        data = request.get_json()
        required_fields = ['user_id', 'username', 'review_text', 'rating', 'res_id']
        
        for field in required_fields:
            if field not in data:
                abort(400, message=f"Missing required field: {field}")
        
        try:
            review = ReviewModel(
                user_id=data['user_id'],
                username=data['username'],
                review_text=data['review_text'],
                rating=data['rating'],
                res_id=data['res_id'],
                timestamp=datetime.now().strftime("%d/%m/%Y %H:%M"),
                source='user'
            )
            
            db.session.add(review)
            db.session.commit()
            
            # Update preferences - wrap in try/except
            try:
                update_user_preferences(
                    data['user_id'], 
                    data['rating'], 
                    data['res_id'], 
                    data['review_text']
                )
            except Exception as pref_error:
                print(f"Warning: Error updating preferences: {pref_error}")
                # Review đã được lưu, chỉ log warning
            
            return marshal(review, reviewFields), 201
            
        except Exception as e:
            db.session.rollback()
            print(f"Error creating review: {e}")
            abort(500, message=f"Error creating review: {str(e)}")

def update_user_preferences(user_id, rating, res_id, review_text):
    """Update user preferences based on review"""
    print(f"\n=== UPDATE PREFERENCES DEBUG ===")
    print(f"User ID: {user_id}")
    print(f"Rating: {rating}")
    print(f"Restaurant ID: {res_id}")
    print(f"Review text: {review_text[:50]}...")
    
    pref = UserPreferenceModel.query.filter_by(user_id=user_id).first()
    
    if not pref:
        print("Creating new preference record")
        pref = UserPreferenceModel(
            user_id=user_id,
            total_reviews=0,
            avg_rating_given=0,
            preferred_categories='[]',
            preferred_districts='[]',
            liked_restaurants='[]',
            viewed_restaurants='[]'
        )
        db.session.add(pref)
    
    # Update average rating
    total = pref.total_reviews
    pref.avg_rating_given = ((pref.avg_rating_given * total) + rating) / (total + 1)
    pref.total_reviews += 1
    
    print(f"Total reviews: {pref.total_reviews}")
    print(f"Avg rating: {pref.avg_rating_given}")
    
    restaurant = RestaurantModel.query.get(res_id)
    if restaurant:
        rest_categories = parse_json_field(restaurant.food_categories)
        print(f"Restaurant categories: {rest_categories}")
        
        detected_categories, detected_districts = extract_keywords_from_comment(
            review_text, 
            rest_categories
        )
        print(f"Detected categories: {detected_categories}")
        print(f"Detected districts: {detected_districts}")
        
        # Update preferred_categories
        existing_cats = parse_json_field(pref.preferred_categories)
        print(f"Existing categories: {existing_cats}")
        
        if rating >= 7:
            print(f"Rating >= 7, adding restaurant categories")
            for cat in rest_categories:
                if cat not in existing_cats:
                    existing_cats.append(cat)
                    print(f"  Added: {cat}")
        
        for cat in detected_categories:
            if cat not in existing_cats:
                existing_cats.append(cat)
                print(f"  Added detected: {cat}")
        
        pref.preferred_categories = json.dumps(existing_cats, ensure_ascii=False)
        print(f"Final categories: {existing_cats}")
        
        # Update preferred_districts
        existing_districts = parse_json_field(pref.preferred_districts)
        print(f"Existing districts: {existing_districts}")
        
        if rating >= 8 and restaurant.district:
            print(f"Rating >= 8, adding restaurant district: {restaurant.district}")
            if restaurant.district not in existing_districts:
                existing_districts.append(restaurant.district)
        
        for district in detected_districts:
            if district not in existing_districts:
                existing_districts.append(district)
                print(f"  Added detected: {district}")
        
        pref.preferred_districts = json.dumps(existing_districts, ensure_ascii=False)
        print(f"Final districts: {existing_districts}")
        
        # Add to liked_restaurants
        if rating >= 8:
            print(f"Rating >= 8, adding to liked")
            liked = parse_json_field(pref.liked_restaurants)
            if res_id not in liked:
                liked.append(res_id)
                print(f"  Added restaurant {res_id} to liked")
            pref.liked_restaurants = json.dumps(liked)
    
    try:
        db.session.commit()
        print("✅ Preferences updated successfully")
    except Exception as e:
        print(f"❌ Error committing: {e}")
        db.session.rollback()
        raise
    
    print("=== END DEBUG ===\n")

class RestaurantReviews(Resource):
    def get(self, res_id):
        reviews = ReviewModel.query.filter_by(res_id=res_id).order_by(
            ReviewModel.review_id.desc()
        ).all()
        return {
            'reviews': [marshal(r, reviewFields) for r in reviews],
            'count': len(reviews)
        }

class UserPreferences(Resource):
    def get(self, user_id):
        pref = UserPreferenceModel.query.filter_by(user_id=user_id).first()
        if not pref:
            return {
                'user_id': user_id,
                'favorite_categories': [],
                'favorite_districts': [],
                'price_range': [0, 500000],
                'liked_restaurants': [],
                'viewed_restaurants': [],
                'total_reviews': 0
            }
        
        return {
            'user_id': user_id,
            'favorite_categories': parse_json_field(pref.preferred_categories),
            'favorite_districts': parse_json_field(pref.preferred_districts),
            'price_range': [pref.price_range_min or 0, pref.price_range_max or 500000],
            'liked_restaurants': parse_json_field(pref.liked_restaurants),
            'viewed_restaurants': parse_json_field(pref.viewed_restaurants),
            'total_reviews': pref.total_reviews
        }
    
    def put(self, user_id):
        data = request.get_json()
        pref = UserPreferenceModel.query.filter_by(user_id=user_id).first()
        
        if not pref:
            pref = UserPreferenceModel(user_id=user_id)
            db.session.add(pref)
        
        if 'favorite_categories' in data:
            pref.preferred_categories = json.dumps(data['favorite_categories'], ensure_ascii=False)
        if 'favorite_districts' in data:
            pref.preferred_districts = json.dumps(data['favorite_districts'], ensure_ascii=False)
        if 'price_range' in data:
            pref.price_range_min = data['price_range'][0]
            pref.price_range_max = data['price_range'][1]
        if 'liked_restaurants' in data:
            pref.liked_restaurants = json.dumps(data['liked_restaurants'])
        if 'viewed_restaurants' in data:
            pref.viewed_restaurants = json.dumps(data['viewed_restaurants'])
        
        db.session.commit()
        return {'message': 'Preferences updated successfully'}

class RecommendHybrid(Resource):
    def post(self):
        data = request.get_json()
        user_id = data.get('user_id')
        top_k = data.get('top_k', 12)
        
        if not user_id:
            abort(400, message="user_id is required")
        
        recommendations = get_hybrid_recommendations(user_id, n=top_k)
        
        result = []
        for rec in recommendations:
            restaurant = RestaurantModel.query.get(rec['res_id'])
            if restaurant:
                rest_data = marshal(restaurant, restaurantFields)
                rest_data['recommendation_score'] = rec['score']
                rest_data['cf_score'] = rec['cf_score']
                rest_data['cb_score'] = rec['cb_score']
                result.append(rest_data)
        
        return {
            'user_id': user_id,
            'recommendations': result,
            'method': 'hybrid',
            'count': len(result)
        }

class AddToHistory(Resource):
    def post(self):
        data = request.get_json()
        user_id = data.get('user_id')
        res_id = data.get('res_id')
        action = data.get('action', 'viewed')
        
        if not user_id or not res_id:
            abort(400, message="user_id and res_id are required")
        
        pref = UserPreferenceModel.query.filter_by(user_id=user_id).first()
        if not pref:
            pref = UserPreferenceModel(
                user_id=user_id,
                preferred_categories='[]',
                preferred_districts='[]',
                liked_restaurants='[]',
                viewed_restaurants='[]'
            )
            db.session.add(pref)
        
        if action == 'viewed':
            viewed = parse_json_field(pref.viewed_restaurants)
            if res_id not in viewed:
                viewed.append(res_id)
                viewed = viewed[-50:]
            pref.viewed_restaurants = json.dumps(viewed)
        elif action == 'liked':
            liked = parse_json_field(pref.liked_restaurants)
            if res_id not in liked:
                liked.append(res_id)
            pref.liked_restaurants = json.dumps(liked)
            
            viewed = parse_json_field(pref.viewed_restaurants)
            if res_id in viewed:
                viewed.remove(res_id)
            pref.viewed_restaurants = json.dumps(viewed)
        
        db.session.commit()
        return {'message': f'Added to {action}', 'user_id': user_id, 'res_id': res_id}

# ==================== REGISTER ROUTES ====================
api.add_resource(Restaurants, '/api/restaurants/')
api.add_resource(Restaurant, '/api/restaurants/<int:id>')
api.add_resource(Reviews, '/api/reviews/')
api.add_resource(RestaurantReviews, '/api/restaurants/<int:res_id>/reviews')
api.add_resource(UserPreferences, '/api/users/<string:user_id>/preferences')
api.add_resource(RecommendHybrid, '/api/recommend/hybrid')
api.add_resource(AddToHistory, '/api/users/history')

@app.route('/')
def home():
    return jsonify({
        'message': 'TasteMatch Restaurant Recommendation API',
        'version': '2.0',
        'endpoints': {
            'restaurants': '/api/restaurants/',
            'restaurant_detail': '/api/restaurants/<id>',
            'reviews': '/api/reviews/',
            'restaurant_reviews': '/api/restaurants/<id>/reviews',
            'user_preferences': '/api/users/<user_id>/preferences',
            'recommendations': '/api/recommend/hybrid',
            'add_to_history': '/api/users/history'
        }
    })

# ==================== MAIN ====================
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("\n✅ Database tables verified/created!")
        print("🚀 API Server starting on http://localhost:5000\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
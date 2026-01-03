# import json
# from api import app, db, RestaurantModel, ReviewModel

# def load_data():
#     with app.app_context():
#         db.drop_all()
#         db.create_all()

#         try:
#             with open('./data/restaurants.json', 'r', encoding='utf-8') as f:
#                 restaurants_data = json.load(f)

#             if isinstance(restaurants_data, dict):
#                 restaurants_data = [restaurants_data]
            
#             for rest_data in restaurants_data:
#                 if 'food_categories' in rest_data and isinstance(rest_data['food_categories'], list):
#                     rest_data['food_categories'] = json.dumps(rest_data['food_categories'], ensure_ascii=False)
#                 if 'suitable_time' in rest_data and isinstance(rest_data['suitable_time'], list):
#                     rest_data['suitable_time'] = json.dumps(rest_data['suitable_time'], ensure_ascii=False)
#                 if 'style' in rest_data and isinstance(rest_data['style'], list):
#                     rest_data['style'] = json.dumps(rest_data['style'], ensure_ascii=False)
#                 if 'appropriate' in rest_data and isinstance(rest_data['appropriate'], list):
#                     rest_data['appropriate'] = json.dumps(rest_data['appropriate'], ensure_ascii=False)
                
#                 restaurant = RestaurantModel(**rest_data)
#                 db.session.add(restaurant)
            
#             print(f"Prepared {len(restaurants_data)} restaurants")
#         except FileNotFoundError:
#             print("restaurants.json not found")
#         except Exception as e:
#             print(f"Error loading restaurants: {e}")
#             db.session.rollback()

#         try:
#             with open('./data/reviews.json', 'r', encoding='utf-8') as f:
#                 reviews_data = json.load(f)
                
#             if isinstance(reviews_data, dict):
#                 reviews_data = [reviews_data]
            
#             for review_data in reviews_data:
#                 review = ReviewModel(**review_data)
#                 db.session.add(review)
            
#             print(f"✓ Prepared {len(reviews_data)} reviews")
#         except FileNotFoundError:
#             print("reviews.json not found")
#         except Exception as e:
#             print(f"Error loading reviews: {e}")
#             db.session.rollback()

#         try:
#             db.session.commit()
#             print("All data loaded successfully!")
#             print("You can now run: python api.py")
#         except Exception as e:
#             print(f"Error committing to database: {e}")
#             db.session.rollback()

# def check_database():
#     with app.app_context():
#         restaurants = RestaurantModel.query.all()
#         print(f"\nRestaurants: {len(restaurants)} records")
#         for r in restaurants[:3]:
#             print(f"  - ID: {r.id}, Name: {r.name}")

#         reviews = ReviewModel.query.all()
#         print(f"\nReviews: {len(reviews)} records")
#         for r in reviews[:3]:  
#             print(f"  - ID: {r.review_id}, User: {r.username}, Rating: {r.rating}")
        
#         if len(restaurants) == 0 and len(reviews) == 0:
#             print("DATABASE IS EMPTY! Run 'python load_data.py' to load sample data")
#         else:
#             print("Database has data!")

# if __name__ == '__main__':
#     import sys
#     if len(sys.argv) > 1 and sys.argv[1] == 'check':
#         check_database()
#     else:
#         load_data()

import json
import os
import sys

# Import from app.py
from api import app, db, RestaurantModel, ReviewModel

def load_data():
    """Load data from JSON files into database"""
    with app.app_context():
        # Drop and recreate all tables
        print("🗑️  Dropping existing tables...")
        db.drop_all()
        
        print("🔨 Creating tables...")
        db.create_all()
        print("✅ Database tables created\n")

        # Load restaurants
        restaurants_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'restaurants.json')
        try:
            print(f"📥 Loading restaurants from {restaurants_file}...")
            with open(restaurants_file, 'r', encoding='utf-8') as f:
                restaurants_data = json.load(f)

            if isinstance(restaurants_data, dict):
                restaurants_data = [restaurants_data]
            
            for rest_data in restaurants_data:
                # Convert lists to JSON strings
                if 'food_categories' in rest_data and isinstance(rest_data['food_categories'], list):
                    rest_data['food_categories'] = json.dumps(rest_data['food_categories'], ensure_ascii=False)
                if 'suitable_time' in rest_data and isinstance(rest_data['suitable_time'], list):
                    rest_data['suitable_time'] = json.dumps(rest_data['suitable_time'], ensure_ascii=False)
                if 'style' in rest_data and isinstance(rest_data['style'], list):
                    rest_data['style'] = json.dumps(rest_data['style'], ensure_ascii=False)
                if 'appropriate' in rest_data and isinstance(rest_data['appropriate'], list):
                    rest_data['appropriate'] = json.dumps(rest_data['appropriate'], ensure_ascii=False)
                
                restaurant = RestaurantModel(**rest_data)
                db.session.add(restaurant)
            
            print(f"✅ Loaded {len(restaurants_data)} restaurants")
        except FileNotFoundError:
            print(f"⚠️  File not found: {restaurants_file}")
        except Exception as e:
            print(f"❌ Error loading restaurants: {e}")
            db.session.rollback()
            return

        # Load reviews from reviews.json (Foody reviews)
        reviews_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'reviews.json')
        foody_count = 0
        try:
            print(f"📥 Loading Foody reviews from {reviews_file}...")
            with open(reviews_file, 'r', encoding='utf-8') as f:
                reviews_data = json.load(f)
                
            if isinstance(reviews_data, dict):
                reviews_data = [reviews_data]
            
            for review_data in reviews_data:
                review_data['source'] = 'foody'
                review = ReviewModel(**review_data)
                db.session.add(review)
                foody_count += 1
            
            print(f"✅ Loaded {foody_count} Foody reviews")
        except FileNotFoundError:
            print(f"⚠️  File not found: {reviews_file}")
        except Exception as e:
            print(f"❌ Error loading reviews: {e}")

        # Load user comments from restaurant_comments.json
        comments_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'restaurant_comments.json')
        user_count = 0
        try:
            print(f"📥 Loading user comments from {comments_file}...")
            with open(comments_file, 'r', encoding='utf-8') as f:
                comments_data = json.load(f)
            
            for res_id_str, comments in comments_data.items():
                res_id = int(res_id_str)
                
                for comment in comments:
                    review = ReviewModel(
                        user_id=comment.get('user', 'anonymous'),
                        username=comment.get('user', 'Anonymous'),
                        profile_url='',
                        review_text=comment.get('comment', ''),
                        rating=comment.get('rating', 0),
                        timestamp=comment.get('timestamp', ''),
                        res_id=res_id,
                        source='user'
                    )
                    db.session.add(review)
                    user_count += 1
            
            print(f"✅ Loaded {user_count} user comments")
        except FileNotFoundError:
            print(f"⚠️  File not found: {comments_file}")
        except Exception as e:
            print(f"❌ Error loading comments: {e}")

        # Commit all changes
        try:
            print("\n💾 Saving to database...")
            db.session.commit()
            
            print("\n" + "="*60)
            print("✅ ALL DATA LOADED SUCCESSFULLY!")
            print("="*60)
            print(f"📊 Total restaurants: {RestaurantModel.query.count()}")
            print(f"📊 Total reviews: {ReviewModel.query.count()}")
            print(f"   - Foody reviews: {foody_count}")
            print(f"   - User comments: {user_count}")
            print("="*60)
            print("\n🚀 You can now run: python app.py")
        except Exception as e:
            print(f"\n❌ Error committing to database: {e}")
            db.session.rollback()

def check_database():
    """Check database contents"""
    with app.app_context():
        restaurants = RestaurantModel.query.all()
        reviews = ReviewModel.query.all()
        foody_reviews = ReviewModel.query.filter_by(source='foody').all()
        user_reviews = ReviewModel.query.filter_by(source='user').all()
        
        print("\n" + "="*60)
        print("DATABASE STATUS")
        print("="*60)
        print(f"📊 Restaurants: {len(restaurants)} records")
        for r in restaurants[:3]:
            print(f"   - ID: {r.id}, Name: {r.name}")
        
        print(f"\n📊 Reviews: {len(reviews)} total")
        print(f"   - Foody: {len(foody_reviews)}")
        print(f"   - Users: {len(user_reviews)}")
        
        for r in reviews[:3]:
            print(f"   - [{r.source}] {r.username}: {r.rating}/10")
        
        print("="*60)
        
        if len(restaurants) == 0:
            print("\n⚠️  DATABASE IS EMPTY!")
            print("Run: python load_data.py")
        else:
            print("\n✅ Database is ready!")

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'check':
        check_database()
    else:
        load_data()
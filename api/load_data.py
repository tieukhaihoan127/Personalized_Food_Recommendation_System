import json
import os
import sys

from api import app, db, RestaurantModel, ReviewModel

def load_data():
    with app.app_context():
        print("Dropping existing tables")
        db.drop_all()
        
        print("Creating tables")
        db.create_all()
        print("Database tables created")

        restaurants_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'restaurants.json')
        try:
            with open(restaurants_file, 'r', encoding='utf-8') as f:
                restaurants_data = json.load(f)

            if isinstance(restaurants_data, dict):
                restaurants_data = [restaurants_data]
            
            for rest_data in restaurants_data:
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
            
            print(f"Loaded {len(restaurants_data)} restaurants")
        except FileNotFoundError:
            print(f"File not found: {restaurants_file}")
        except Exception as e:
            print(f"Error loading restaurants: {e}")
            db.session.rollback()
            return

        reviews_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'reviews.json')
        foody_count = 0
        try:
            with open(reviews_file, 'r', encoding='utf-8') as f:
                reviews_data = json.load(f)
                
            if isinstance(reviews_data, dict):
                reviews_data = [reviews_data]
            
            for review_data in reviews_data:
                review_data['source'] = 'foody'
                review = ReviewModel(**review_data)
                db.session.add(review)
                foody_count += 1
            
            print(f"Loaded {foody_count} Foody reviews")
        except FileNotFoundError:
            print(f"File not found: {reviews_file}")
        except Exception as e:
            print(f"Error loading reviews: {e}")

        comments_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'restaurant_comments.json')
        user_count = 0
        try:
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
            
            print(f"Loaded {user_count} user comments")
        except FileNotFoundError:
            print(f"File not found: {comments_file}")
        except Exception as e:
            print(f"Error loading comments: {e}")

        try:
            print("\n💾 Saving to database...")
            db.session.commit()
            
            print(f"Total restaurants: {RestaurantModel.query.count()}")
            print(f"Total reviews: {ReviewModel.query.count()}")
            print(f"Foody reviews: {foody_count}")
            print(f"User comments: {user_count}")
        except Exception as e:
            print(f"Error committing to database: {e}")
            db.session.rollback()

def check_database():
    with app.app_context():
        restaurants = RestaurantModel.query.all()
        reviews = ReviewModel.query.all()
        foody_reviews = ReviewModel.query.filter_by(source='foody').all()
        user_reviews = ReviewModel.query.filter_by(source='user').all()

        print("DATABASE STATUS")
        print(f"Restaurants: {len(restaurants)} records")
        for r in restaurants[:3]:
            print(f"   - ID: {r.id}, Name: {r.name}")
        
        print(f"Reviews: {len(reviews)} total")
        print(f"Foody: {len(foody_reviews)}")
        print(f"Users: {len(user_reviews)}")
        
        for r in reviews[:3]:
            print(f"   - [{r.source}] {r.username}: {r.rating}/10")
        
        if len(restaurants) == 0:
            print("DATABASE IS EMPTY!")
        else:
            print("Database is ready!")

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'check':
        check_database()
    else:
        load_data()
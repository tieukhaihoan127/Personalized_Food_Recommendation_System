import json
from api import app, db, RestaurantModel, ReviewModel

def load_data():
    with app.app_context():
        db.drop_all()
        db.create_all()

        try:
            with open('./data/restaurants.json', 'r', encoding='utf-8') as f:
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
            
            print(f"Prepared {len(restaurants_data)} restaurants")
        except FileNotFoundError:
            print("restaurants.json not found")
        except Exception as e:
            print(f"Error loading restaurants: {e}")
            db.session.rollback()

        try:
            with open('./data/reviews.json', 'r', encoding='utf-8') as f:
                reviews_data = json.load(f)
                
            if isinstance(reviews_data, dict):
                reviews_data = [reviews_data]
            
            for review_data in reviews_data:
                review = ReviewModel(**review_data)
                db.session.add(review)
            
            print(f"✓ Prepared {len(reviews_data)} reviews")
        except FileNotFoundError:
            print("reviews.json not found")
        except Exception as e:
            print(f"Error loading reviews: {e}")
            db.session.rollback()

        try:
            db.session.commit()
            print("All data loaded successfully!")
            print("You can now run: python api.py")
        except Exception as e:
            print(f"Error committing to database: {e}")
            db.session.rollback()

def check_database():
    with app.app_context():
        restaurants = RestaurantModel.query.all()
        print(f"\nRestaurants: {len(restaurants)} records")
        for r in restaurants[:3]:
            print(f"  - ID: {r.id}, Name: {r.name}")

        reviews = ReviewModel.query.all()
        print(f"\nReviews: {len(reviews)} records")
        for r in reviews[:3]:  
            print(f"  - ID: {r.review_id}, User: {r.username}, Rating: {r.rating}")
        
        if len(restaurants) == 0 and len(reviews) == 0:
            print("DATABASE IS EMPTY! Run 'python load_data.py' to load sample data")
        else:
            print("Database has data!")

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'check':
        check_database()
    else:
        load_data()
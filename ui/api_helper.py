import requests
from typing import List, Dict, Optional

API_BASE_URL = "http://localhost:5000/api"

class APIHelper:    
    @staticmethod
    def get_all_restaurants(district: Optional[str] = None, category: Optional[str] = None) -> List[Dict]:
        try:
            params = {}
            if district:
                params['district'] = district
            if category:
                params['category'] = category
            
            response = requests.get(f"{API_BASE_URL}/restaurants/", params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching restaurants: {e}")
            return []
    
    @staticmethod
    def get_restaurant_by_id(restaurant_id: int) -> Optional[Dict]:
        try:
            response = requests.get(f"{API_BASE_URL}/restaurants/{restaurant_id}", timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching restaurant {restaurant_id}: {e}")
            return None
    
    @staticmethod
    def get_restaurant_reviews(restaurant_id: int) -> List[Dict]:
        try:
            response = requests.get(f"{API_BASE_URL}/restaurants/{restaurant_id}/reviews", timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get('reviews', [])
        except Exception as e:
            print(f"Error fetching reviews for restaurant {restaurant_id}: {e}")
            return []
    
    @staticmethod
    def add_review(user_id: str, username: str, review_text: str, rating: float, res_id: int) -> bool:
        try:
            data = {
                'user_id': user_id,
                'username': username,
                'review_text': review_text,
                'rating': rating,
                'res_id': res_id
            }
            
            response = requests.post(f"{API_BASE_URL}/reviews/", json=data, timeout=10)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Error adding review: {e}")
            return False
    
    @staticmethod
    def get_user_preferences(user_id: str) -> Dict:
        try:
            response = requests.get(f"{API_BASE_URL}/users/{user_id}/preferences", timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching user preferences: {e}")
            return {
                'user_id': user_id,
                'favorite_categories': [],
                'favorite_districts': [],
                'price_range': [0, 500000],
                'liked_restaurants': [],
                'viewed_restaurants': [],
                'total_reviews': 0
            }
    
    @staticmethod
    def update_user_preferences(user_id: str, preferences: Dict) -> bool:
        try:
            response = requests.put(
                f"{API_BASE_URL}/users/{user_id}/preferences",
                json=preferences,
                timeout=10
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Error updating user preferences: {e}")
            return False
    
    @staticmethod
    def get_hybrid_recommendations(user_id: str, top_k: int = 12) -> List[Dict]:
        try:
            data = {
                'user_id': user_id,
                'top_k': top_k
            }
            
            response = requests.post(
                f"{API_BASE_URL}/recommend/hybrid",
                json=data,
                timeout=15
            )
            response.raise_for_status()
            result = response.json()
            return result.get('recommendations', [])
        except Exception as e:
            print(f"Error getting recommendations: {e}")
            return []
    
    @staticmethod
    def add_to_history(user_id: str, res_id: int, action: str = 'viewed') -> bool:
        try:
            data = {
                'user_id': user_id,
                'res_id': res_id,
                'action': action
            }
            
            response = requests.post(
                f"{API_BASE_URL}/users/history",
                json=data,
                timeout=10
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Error adding to history: {e}")
            return False

def get_restaurants(**kwargs):
    return APIHelper.get_all_restaurants(**kwargs)

def get_restaurant(restaurant_id):
    return APIHelper.get_restaurant_by_id(restaurant_id)

def get_reviews(restaurant_id):
    return APIHelper.get_restaurant_reviews(restaurant_id)

def add_review(**kwargs):
    return APIHelper.add_review(**kwargs)

def get_user_prefs(user_id):
    return APIHelper.get_user_preferences(user_id)

def update_user_prefs(user_id, preferences):
    return APIHelper.update_user_preferences(user_id, preferences)

def get_recommendations(user_id, top_k=12):
    return APIHelper.get_hybrid_recommendations(user_id, top_k)

def add_to_history(user_id, res_id, action='viewed'):
    return APIHelper.add_to_history(user_id, res_id, action)
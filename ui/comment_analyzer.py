# comment_analyzer.py
import json
import os
import re
from collections import defaultdict

# =======================
# KEYWORD DICTIONARIES
# =======================

# Mapping từ keywords → food categories
FOOD_KEYWORDS = {
    # Bún
    "bún": ["Bún"],
    "bun": ["Bún"],

    # Cơm
    "cơm": ["Cơm"],
    "com": ["Cơm"],
    "cơm chiên": ["Cơm Chiên"],
    "com chien": ["Cơm Chiên"],

    # Phở
    "phở": ["Phở"],
    "pho": ["Phở"],

    # Bánh
    "bánh": ["Bánh mì", "Bánh"],
    "banh": ["Bánh mì", "Bánh"],
    "bánh mì": ["Bánh mì"],
    "banh mi": ["Bánh mì"],
    "bánh xèo": ["Bánh xèo"],

    # Nướng
    "nướng": ["Đồ nướng"],
    "nuong": ["Đồ nướng"],
    "bbq": ["Đồ nướng"],
    "xiên nướng": ["Xiên nướng"],

    # Lẩu
    "lẩu": ["Lẩu"],
    "lau": ["Lẩu"],

    # Hải sản
    "hải sản": ["Hải sản"],
    "hai san": ["Hải sản"],
    "cua": ["Cua - Ghẹ", "Hải sản"],
    "ghẹ": ["Cua - Ghẹ", "Hải sản"],
    "tôm": ["Hải sản"],
    "tom": ["Hải sản"],
    "cá": ["Hải sản"],
    "ca": ["Hải sản"],
    "ốc": ["Ốc", "Hải sản"],
    "oc": ["Ốc", "Hải sản"],

    # Gà
    "gà": ["Gà"],
    "ga": ["Gà"],
    "gà rán": ["Gà rán"],
    "ga ran": ["Gà rán"],
    "chicken": ["Gà"],

    # Bò
    "bò": ["Bò"],
    "bo": ["Bò"],
    "bít tết": ["Bò", "Đồ nướng"],
    "beefsteak": ["Bò", "Đồ nướng"],

    # Heo/Lợn
    "heo": ["Heo", "Đồ nướng"],
    "lợn": ["Heo", "Đồ nướng"],
    "lon": ["Heo", "Đồ nướng"],
    "ba chỉ": ["Heo", "Đồ nướng"],

    # Món chay
    "chay": ["Món chay"],

    # Đồ ăn vặt
    "ăn vặt": ["Đồ ăn vặt"],
    "an vat": ["Đồ ăn vặt"],
    "snack": ["Đồ ăn vặt"],

    # Món Trung
    "dimsum": ["Món Trung Hoa"],
    "dim sum": ["Món Trung Hoa"],
    "há cảo": ["Món Trung Hoa"],
    "ha cao": ["Món Trung Hoa"],

    # Món Nhật
    "sushi": ["Món Nhật"],
    "ramen": ["Món Nhật"],
    "mì nhật": ["Món Nhật"],

    # Món Hàn
    "kim chi": ["Món Hàn Quốc"],
    "kimchi": ["Món Hàn Quốc"],
    "gimbap": ["Món Hàn Quốc"],
    "tokbokki": ["Món Hàn Quốc"],

    # Pizza/Burger
    "pizza": ["Pizza"],
    "burger": ["Burger"],
    "hamburger": ["Burger"],

    # Mì/Miến
    "mì": ["Mì"],
    "mi": ["Mì"],
    "miến": ["Miến"],
    "mien": ["Miến"],

    # Xôi
    "xôi": ["Xôi"],
    "xoi": ["Xôi"],
}

# Mapping từ keywords → districts
DISTRICT_KEYWORDS = {
    "quận 1": "Quận 1",
    "quan 1": "Quận 1",
    "q1": "Quận 1",
    "quận 2": "Quận 2",
    "quan 2": "Quận 2",
    "q2": "Quận 2",
    "quận 3": "Quận 3",
    "quan 3": "Quận 3",
    "q3": "Quận 3",
    "quận 4": "Quận 4",
    "quan 4": "Quận 4",
    "q4": "Quận 4",
    "quận 5": "Quận 5",
    "quan 5": "Quận 5",
    "q5": "Quận 5",
    "quận 6": "Quận 6",
    "quan 6": "Quận 6",
    "q6": "Quận 6",
    "quận 7": "Quận 7",
    "quan 7": "Quận 7",
    "q7": "Quận 7",
    "quận 8": "Quận 8",
    "quan 8": "Quận 8",
    "q8": "Quận 8",
    "quận 9": "Quận 9",
    "quan 9": "Quận 9",
    "q9": "Quận 9",
    "quận 10": "Quận 10",
    "quan 10": "Quận 10",
    "q10": "Quận 10",
    "quận 11": "Quận 11",
    "quan 11": "Quận 11",
    "q11": "Quận 11",
    "quận 12": "Quận 12",
    "quan 12": "Quận 12",
    "q12": "Quận 12",
    "thủ đức": "Thành phố Thủ Đức",
    "thu duc": "Thành phố Thủ Đức",
    "bình thạnh": "Quận Bình Thạnh",
    "binh thanh": "Quận Bình Thạnh",
    "tân bình": "Quận Tân Bình",
    "tan binh": "Quận Tân Bình",
    "tân phú": "Quận Tân Phú",
    "tan phu": "Quận Tân Phú",
    "phú nhuận": "Quận Phú Nhuận",
    "phu nhuan": "Quận Phú Nhuận",
    "gò vấp": "Quận Gò Vấp",
    "go vap": "Quận Gò Vấp",
}


# =======================
# ANALYSIS FUNCTIONS
# =======================

def extract_keywords_from_comment(comment_text, restaurant_categories=None):
    """
    Phân tích comment và extract keywords về món ăn và địa điểm
    Chỉ trả về categories có trong restaurant nếu được cung cấp

    Args:
        comment_text: Nội dung comment
        restaurant_categories: List các categories của quán (optional)

    Returns:
        detected_categories: List categories phù hợp
        detected_districts: List districts được nhắc đến
    """
    comment_lower = comment_text.lower()

    detected_categories = set()
    detected_districts = set()

    # Tìm food keywords
    for keyword, potential_categories in FOOD_KEYWORDS.items():
        if keyword in comment_lower:
            # Nếu có restaurant_categories, chỉ add categories có trong quán
            if restaurant_categories:
                for cat in potential_categories:
                    # Kiểm tra xem category có trong quán không (partial match)
                    for rest_cat in restaurant_categories:
                        if cat.lower() in rest_cat.lower() or rest_cat.lower() in cat.lower():
                            detected_categories.add(rest_cat)
            else:
                # Không có info quán → add tất cả potential categories
                detected_categories.update(potential_categories)

    # Tìm district keywords
    for keyword, district in DISTRICT_KEYWORDS.items():
        if keyword in comment_lower:
            detected_districts.add(district)

    return list(detected_categories), list(detected_districts)


def analyze_user_comments(comments_file="./data/restaurant_comments.json",
                          restaurants_file="./data/restaurants.json"):
    """
    Phân tích tất cả comments và tạo user preferences

    Returns:
        dict: {
            'user_name': {
                'favorite_categories': [...],
                'favorite_districts': [...],
                'liked_restaurants': [...],
                'comment_count': X
            }
        }
    """
    # Load comments
    if not os.path.exists(comments_file):
        return {}

    with open(comments_file, 'r', encoding='utf-8') as f:
        all_comments = json.load(f)

    # Load restaurants để lấy thông tin quán
    if os.path.exists(restaurants_file):
        with open(restaurants_file, 'r', encoding='utf-8') as f:
            restaurants = json.load(f)
        restaurants_dict = {r['id']: r for r in restaurants}
    else:
        restaurants_dict = {}

    # Phân tích theo user
    user_preferences = defaultdict(lambda: {
        'favorite_categories': set(),
        'favorite_districts': set(),
        'liked_restaurants': [],
        'comment_count': 0
    })

    for restaurant_id, comments_list in all_comments.items():
        restaurant_id = int(restaurant_id)

        # Lấy thông tin quán
        restaurant = restaurants_dict.get(restaurant_id, {})
        restaurant_district = restaurant.get('district', '')
        restaurant_categories = restaurant.get('food_categories', [])

        for comment in comments_list:
            user_name = comment.get('user', 'anonymous')
            comment_text = comment.get('comment', '')
            rating = comment.get('rating', 0)

            # Extract keywords từ comment với restaurant context
            detected_categories, detected_districts = extract_keywords_from_comment(
                comment_text,
                restaurant_categories=restaurant_categories  # Pass restaurant categories
            )

            # Cập nhật preferences
            prefs = user_preferences[user_name]

            # Thêm categories từ comment (đã được filter theo quán)
            prefs['favorite_categories'].update(detected_categories)

            # Thêm categories từ quán (nếu rating >= 7)
            if rating >= 7:
                prefs['favorite_categories'].update(restaurant_categories)

            # Thêm districts từ comment
            prefs['favorite_districts'].update(detected_districts)

            # Thêm district của quán (nếu rating >= 8)
            if rating >= 8 and restaurant_district:
                prefs['favorite_districts'].add(restaurant_district)

            # Thêm vào liked restaurants (nếu rating >= 8)
            if rating >= 8 and restaurant_id not in prefs['liked_restaurants']:
                prefs['liked_restaurants'].append(restaurant_id)

            prefs['comment_count'] += 1

    # Convert sets to lists
    result = {}
    for user_name, prefs in user_preferences.items():
        result[user_name] = {
            'favorite_categories': list(prefs['favorite_categories']),
            'favorite_districts': list(prefs['favorite_districts']),
            'liked_restaurants': prefs['liked_restaurants'],
            'comment_count': prefs['comment_count'],
            'price_range': [0, 500000]  # Default
        }

    return result


def update_user_preferences(target_user='current_user',
                            comments_file="./data/restaurant_comments.json",
                            restaurants_file="./data/restaurant.json",
                            prefs_file="./data/user_preferences.json",
                            silent=False):
    """
    Phân tích comments và cập nhật preferences cho target_user

    Args:
        silent: Nếu True, không print output (dùng cho auto-run)
    """
    if not silent:
        print("Analyzing comments...")

    # Analyze all comments
    all_user_prefs = analyze_user_comments(comments_file, restaurants_file)

    # Load existing preferences
    if os.path.exists(prefs_file):
        with open(prefs_file, 'r', encoding='utf-8') as f:
            current_prefs = json.load(f)
    else:
        current_prefs = {
            'favorite_categories': [],
            'favorite_districts': [],
            'liked_restaurants': [],
            'viewed_restaurants': [],
            'price_range': [0, 500000]
        }

    # Merge preferences từ comments
    new_categories = set(current_prefs.get('favorite_categories', []))
    new_districts = set(current_prefs.get('favorite_districts', []))
    new_liked = list(current_prefs.get('liked_restaurants', []))

    # Aggregate preferences từ tất cả users
    for user_name, prefs in all_user_prefs.items():
        new_categories.update(prefs['favorite_categories'])
        new_districts.update(prefs['favorite_districts'])

        # Thêm liked restaurants (không duplicate)
        for rest_id in prefs['liked_restaurants']:
            if rest_id not in new_liked:
                new_liked.append(rest_id)

    # Update current preferences
    current_prefs['favorite_categories'] = list(new_categories)
    current_prefs['favorite_districts'] = list(new_districts)
    current_prefs['liked_restaurants'] = new_liked

    # Save
    with open(prefs_file, 'w', encoding='utf-8') as f:
        json.dump(current_prefs, f, ensure_ascii=False, indent=2)

    if not silent:
        print("✅ Updated user preferences successfully!")

    return current_prefs, all_user_prefs


def get_analysis_summary(all_user_prefs):
    """
    Tạo summary report
    """
    total_users = len(all_user_prefs)
    total_comments = sum(p['comment_count'] for p in all_user_prefs.values())

    # Top categories
    all_categories = defaultdict(int)
    for prefs in all_user_prefs.values():
        for cat in prefs['favorite_categories']:
            all_categories[cat] += 1

    top_categories = sorted(all_categories.items(), key=lambda x: x[1], reverse=True)[:10]

    # Top districts
    all_districts = defaultdict(int)
    for prefs in all_user_prefs.values():
        for dist in prefs['favorite_districts']:
            all_districts[dist] += 1

    top_districts = sorted(all_districts.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        'total_users': total_users,
        'total_comments': total_comments,
        'top_categories': top_categories,
        'top_districts': top_districts
    }


# =======================
# MAIN EXECUTION
# =======================

if __name__ == "__main__":
    print("=" * 60)
    print("COMMENT ANALYZER - Tự động phân tích preferences")
    print("=" * 60)

    # Analyze và update
    print("\n📊 Đang phân tích comments...")
    updated_prefs, all_user_prefs = update_user_preferences()

    # Summary
    summary = get_analysis_summary(all_user_prefs)

    print(f"\n✅ Phân tích hoàn tất!")
    print(f"   - Tổng users: {summary['total_users']}")
    print(f"   - Tổng comments: {summary['total_comments']}")

    print(f"\n📈 Top 10 món ăn được nhắc đến:")
    for i, (cat, count) in enumerate(summary['top_categories'], 1):
        print(f"   {i}. {cat}: {count} lần")

    print(f"\n📍 Top 5 khu vực được nhắc đến:")
    for i, (dist, count) in enumerate(summary['top_districts'], 1):
        print(f"   {i}. {dist}: {count} lần")

    print(f"\n💾 Đã cập nhật user_preferences.json")
    print(f"   - Categories: {len(updated_prefs['favorite_categories'])}")
    print(f"   - Districts: {len(updated_prefs['favorite_districts'])}")
    print(f"   - Liked restaurants: {len(updated_prefs['liked_restaurants'])}")

    print("\n" + "=" * 60)
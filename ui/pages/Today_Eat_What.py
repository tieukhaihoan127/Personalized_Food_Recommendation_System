import streamlit as st
import pandas as pd
import json
import os
import time
import re
from datetime import datetime
import sys
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(ROOT_DIR)

from model.Content_based_Filtering_model import (
    load_and_prepare_data,
    build_similarity_model,
    recommend_restaurants
)
from model.Collaborative_Filtering_model import load_cf_model
from comment_analyzer import update_user_preferences, get_analysis_summary

st.set_page_config(
    page_title="Hôm nay ăn gì?",
    page_icon="🍽️",
    layout="wide"
)


# ----------------------
# LOAD DATA & MODEL
# ----------------------
@st.cache_data
def load_data():
    X = load_and_prepare_data("./data/restaurants.json")
    cosine_sim = build_similarity_model(X)
    return X, cosine_sim


@st.cache_resource
def load_cf():
    """Load Collaborative Filtering model"""
    cf_model = load_cf_model()
    return cf_model


@st.cache_data
def load_full_data():
    """Load file JSON gốc để có đầy đủ thông tin"""
    with open("./data/restaurants.json", 'r', encoding='utf-8') as f:
        data = json.load(f)
    return pd.DataFrame(data)


X, cosine_sim = load_data()
cf_model = load_cf()
full_df = load_full_data()

def district_sort_key(name):
    if name.startswith("Quận"):
        match = re.search(r"\d+", name)
        if match:
            return (0, int(match.group()))
        else:
            return (0, 999)
    return (1, name)

# ----------------------
# USER PREFERENCE FUNCTIONS
# ----------------------
USER_PREFS_FILE = "./data/user_preferences.json"

# Initialize session state for preferences
if 'user_preferences' not in st.session_state:
    st.session_state.user_preferences = None


def load_user_preferences():
    """Load preferences từ file hoặc session state"""

    # Ưu tiên session state (trong memory)
    if st.session_state.user_preferences is not None:
        return st.session_state.user_preferences

    # Nếu không có, load từ file
    if not os.path.exists(USER_PREFS_FILE):
        default_prefs = {
            "favorite_categories": [],
            "favorite_districts": [],
            "price_range": [0, 500000],
            "viewed_restaurants": [],
            "liked_restaurants": []
        }
        st.session_state.user_preferences = default_prefs
        return default_prefs

    try:
        with open(USER_PREFS_FILE, 'r', encoding='utf-8') as f:
            prefs = json.load(f)
            st.session_state.user_preferences = prefs
            return prefs
    except:
        default_prefs = {
            "favorite_categories": [],
            "favorite_districts": [],
            "price_range": [0, 500000],
            "viewed_restaurants": [],
            "liked_restaurants": []
        }
        st.session_state.user_preferences = default_prefs
        return default_prefs


def save_user_preferences(prefs):
    """Lưu preferences với dual storage: session state + file"""

    # Convert tất cả int64 sang int trước khi lưu
    def convert_to_native_types(obj):
        """Convert numpy/pandas types sang native Python types"""
        if isinstance(obj, dict):
            return {k: convert_to_native_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_to_native_types(item) for item in obj]
        elif hasattr(obj, 'item'):  # numpy types
            return obj.item()
        else:
            return obj

    prefs = convert_to_native_types(prefs)

    # 1. Lưu vào session state (LUÔN THÀNH CÔNG)
    st.session_state.user_preferences = prefs

    # 2. Thử lưu vào file (không bắt buộc)
    try:
        # Kiểm tra thư mục tồn tại
        directory = os.path.dirname(USER_PREFS_FILE) or '.'
        if not os.path.exists(directory):
            os.makedirs(directory)

        # Thử ghi file
        with open(USER_PREFS_FILE, 'w', encoding='utf-8') as f:
            json.dump(prefs, f, ensure_ascii=False, indent=2)

        return True

    except Exception as e:
        # Silent fail - session state vẫn work
        return True


def add_to_history(restaurant_id, action="viewed"):
    """Thêm quán vào lịch sử"""
    prefs = load_user_preferences()

    # Convert sang int chuẩn (tránh int64 từ pandas)
    restaurant_id = int(restaurant_id)

    if action == "viewed":
        if restaurant_id not in prefs["viewed_restaurants"]:
            prefs["viewed_restaurants"].append(restaurant_id)
            # Giữ tối đa 50 quán gần nhất
            prefs["viewed_restaurants"] = prefs["viewed_restaurants"][-50:]

    elif action == "liked":
        if restaurant_id not in prefs["liked_restaurants"]:
            prefs["liked_restaurants"].append(restaurant_id)
            # Đồng thời xóa khỏi viewed nếu có
            if restaurant_id in prefs["viewed_restaurants"]:
                prefs["viewed_restaurants"].remove(restaurant_id)

    return save_user_preferences(prefs)


# ----------------------
# HYBRID RECOMMENDATION ENGINE
# ----------------------
def get_hybrid_recommendations(user_prefs, X, full_df, cosine_sim, cf_model, n=12, cf_weight=0.4, cb_weight=0.6):
    """
    Hybrid Recommendation: 40% CF + 60% CB
    Ưu tiên quán ở các quận trong favorite_districts
    """
    hybrid_scores = {}

    # ==================
    # 1. GET CF RECOMMENDATIONS (40%)
    # ==================
    if cf_model.is_trained:
        cf_recs = cf_model.get_recommendations('current_user', n=n * 2)

        # Normalize CF scores to 0-1
        if cf_recs:
            max_cf_score = max([score for _, score in cf_recs])
            min_cf_score = min([score for _, score in cf_recs])

            if max_cf_score > min_cf_score:
                for res_id, score in cf_recs:
                    normalized_score = (score - min_cf_score) / (max_cf_score - min_cf_score)
                    hybrid_scores[res_id] = {
                        'cf_score': normalized_score * cf_weight,
                        'cb_score': 0,
                        'reason_cf': 'Dựa trên sở thích người dùng tương tự',
                        'type': 'cf'
                    }

    # ==================
    # 2. GET CB RECOMMENDATIONS (60%)
    # ==================
    cb_candidates = []

    # Strategy A: Content-Based từ quán đã thích
    if user_prefs["liked_restaurants"]:
        for rest_id in user_prefs["liked_restaurants"][-3:]:
            if rest_id in X.index:
                similar = recommend_restaurants(rest_id, X, cosine_sim, n=10)
                for idx in similar:
                    if idx not in user_prefs["viewed_restaurants"]:
                        cb_candidates.append({
                            'id': idx,
                            'score': 0.95,
                            'reason': f"Tương tự quán bạn đã thích"
                        })

    # Strategy B: Filter theo sở thích + ƯU TIÊN QUẬN
    if user_prefs["favorite_categories"]:
        filtered_df = full_df[
            full_df['food_categories'].apply(
                lambda cats: any(cat in user_prefs["favorite_categories"] for cat in cats)
            )
        ]

        # Ưu tiên quán ở favorite_districts trước
        if user_prefs["favorite_districts"]:
            # Quán ở quận yêu thích
            priority_df = filtered_df[filtered_df['district'].isin(user_prefs["favorite_districts"])]

            for idx, row in priority_df.head(15).iterrows():
                if idx not in user_prefs["viewed_restaurants"]:
                    matched_cats = [cat for cat in row['food_categories']
                                    if cat in user_prefs["favorite_categories"]]
                    cb_candidates.append({
                        'id': idx,
                        'score': 0.90,  # Score cao hơn vì ở quận yêu thích
                        'reason': f"Phù hợp: {', '.join(matched_cats[:2])} tại {row['district']}"
                    })

            # Quán ở quận khác (điểm thấp hơn)
            other_df = filtered_df[~filtered_df['district'].isin(user_prefs["favorite_districts"])]
            for idx, row in other_df.head(10).iterrows():
                if idx not in user_prefs["viewed_restaurants"]:
                    matched_cats = [cat for cat in row['food_categories']
                                    if cat in user_prefs["favorite_categories"]]
                    cb_candidates.append({
                        'id': idx,
                        'score': 0.75,  # Score thấp hơn
                        'reason': f"Phù hợp: {', '.join(matched_cats[:2])}"
                    })
        else:
            # Không có district preference → xử lý bình thường
            for idx, row in filtered_df.head(15).iterrows():
                if idx not in user_prefs["viewed_restaurants"]:
                    matched_cats = [cat for cat in row['food_categories']
                                    if cat in user_prefs["favorite_categories"]]
                    cb_candidates.append({
                        'id': idx,
                        'score': 0.85,
                        'reason': f"Phù hợp với sở thích: {', '.join(matched_cats[:2])}"
                    })

    # Strategy C: Filter theo QUẬN trước (nếu có)
    if user_prefs["favorite_districts"]:
        district_df = full_df[full_df['district'].isin(user_prefs["favorite_districts"])]

        # Lấy top rated ở quận yêu thích
        top_in_district = district_df.nlargest(10, 'average_rating')
        for idx, row in top_in_district.iterrows():
            if idx not in user_prefs["viewed_restaurants"]:
                cb_candidates.append({
                    'id': idx,
                    'score': 0.80,  # Score cao vì ở quận yêu thích
                    'reason': f"Đánh giá cao tại {row['district']} ({row['average_rating']}/10)"
                })

    # Strategy D: Top rated (điểm thấp nhất)
    top_rated = full_df.nlargest(15, 'average_rating')
    for idx, row in top_rated.iterrows():
        if idx not in user_prefs["viewed_restaurants"]:
            cb_candidates.append({
                'id': idx,
                'score': 0.70,
                'reason': f"Đánh giá cao ({row['average_rating']}/10)"
            })

    # Normalize CB scores
    for candidate in cb_candidates:
        res_id = candidate['id']
        if res_id in hybrid_scores:
            # Cộng điểm CB vào
            hybrid_scores[res_id]['cb_score'] = candidate['score'] * cb_weight
            hybrid_scores[res_id]['reason_cb'] = candidate['reason']
            hybrid_scores[res_id]['type'] = 'hybrid'
        else:
            # Chỉ có CB
            hybrid_scores[res_id] = {
                'cf_score': 0,
                'cb_score': candidate['score'] * cb_weight,
                'reason_cb': candidate['reason'],
                'type': 'cb'
            }

    # ==================
    # 3. CALCULATE HYBRID SCORES
    # ==================
    recommendations = []

    for res_id, scores in hybrid_scores.items():
        if res_id not in full_df.index:
            continue

        restaurant = full_df.loc[res_id]

        # Tính tổng điểm
        total_score = scores['cf_score'] + scores['cb_score']

        # BONUS: Thêm điểm nếu quán ở favorite_districts
        if user_prefs["favorite_districts"] and restaurant['district'] in user_prefs["favorite_districts"]:
            total_score += 0.1  # Bonus 10%

        # Tạo reason message
        if scores['type'] == 'hybrid':
            reason = f"🤖 Hybrid: {scores.get('reason_cb', '')} & {scores.get('reason_cf', '')}"
        elif scores['type'] == 'cf':
            reason = f"👥 CF: {scores.get('reason_cf', '')}"
        else:
            reason = f"🎯 CB: {scores.get('reason_cb', '')}"

        recommendations.append({
            'restaurant': restaurant,
            'reason': reason,
            'score': total_score,
            'cf_score': scores['cf_score'],
            'cb_score': scores['cb_score'],
            'type': scores['type']
        })

    # Sort theo hybrid score (bao gồm bonus)
    recommendations.sort(key=lambda x: x['score'], reverse=True)

    return recommendations[:n]


# ----------------------
# MAIN UI
# ----------------------
st.title("🍽️ Hôm nay ăn gì?")
st.caption("Khám phá những gợi ý cá nhân hóa dành riêng cho bạn")

# Load user preferences
user_prefs = load_user_preferences()

# ----------------------
# SIDEBAR - User Preferences
# ----------------------
st.sidebar.header("⚙️ Tùy chọn của bạn")

# Categories preference
all_categories = list(set([cat for cats in X['food_categories'] for cat in cats]))
selected_categories = st.sidebar.multiselect(
    "🍜 Món ăn yêu thích",
    options=sorted(all_categories),
    default=user_prefs["favorite_categories"],
    help="Chọn các loại món bạn thích"
)

# Districts preference
all_districts = sorted(X['district'].unique().tolist(), key=district_sort_key)
selected_districts = st.sidebar.multiselect(
    "📍 Khu vực quan tâm",
    options=all_districts,
    default=user_prefs["favorite_districts"],
    help="Chọn các quận bạn muốn tìm quán"
)

# Price range
price_range = st.sidebar.slider(
    "💰 Khoảng giá mong muốn (VNĐ)",
    min_value=0,
    max_value=500000,
    value=(user_prefs["price_range"][0], user_prefs["price_range"][1]),
    step=10000,
    format="%d đ"
)

# Save preferences button
if st.sidebar.button("💾 Lưu sở thích", type="primary", use_container_width=True):
    user_prefs["favorite_categories"] = selected_categories
    user_prefs["favorite_districts"] = selected_districts
    user_prefs["price_range"] = list(price_range)

    if save_user_preferences(user_prefs):
        st.sidebar.success("✅ Đã lưu sở thích!")
        st.rerun()

# # Auto-analyze comments button
# st.sidebar.write("---")
# if st.sidebar.button("🤖 Phân tích Comments tự động", use_container_width=True):
#     with st.sidebar.spinner("Đang phân tích..."):
#         try:
#             updated_prefs, all_user_prefs = update_user_preferences()
#
#             st.sidebar.success("✅ Phân tích thành công!")
#
#             # Show summary
#             with st.sidebar.expander("📊 Kết quả phân tích"):
#                 st.write(f"**Categories mới:** {len(updated_prefs['favorite_categories'])}")
#                 st.write(f"**Districts mới:** {len(updated_prefs['favorite_districts'])}")
#                 st.write(f"**Liked restaurants:** {len(updated_prefs['liked_restaurants'])}")
#
#             # Clear cache và reload
#             st.cache_data.clear()
#             st.cache_resource.clear()
#             time.sleep(1)
#             st.rerun()
#
#         except Exception as e:
#             st.sidebar.error(f"❌ Lỗi: {str(e)}")
#
# # Debug info ở sidebar (có thể ẩn khi production)
# if st.sidebar.checkbox("🔧 Hiển thị thông tin kỹ thuật", value=False):
#     with st.sidebar.expander("Debug Info"):
#         st.write("**File paths:**")
#         st.code(f"USER_PREFS_FILE: {os.path.abspath(USER_PREFS_FILE)}")
#         st.write(f"File exists: {os.path.exists(USER_PREFS_FILE)}")
#
#         if os.path.exists(USER_PREFS_FILE):
#             st.write(f"File size: {os.path.getsize(USER_PREFS_FILE)} bytes")
#
#         st.write(f"Current dir: {os.getcwd()}")

# Stats
st.sidebar.write("---")
st.sidebar.write("📊 **Thống kê của bạn:**")

# Reload prefs để hiển thị realtime
current_prefs = load_user_preferences()
st.sidebar.metric("Quán đã xem", len(current_prefs.get("viewed_restaurants", [])))
st.sidebar.metric("Quán yêu thích", len(current_prefs.get("liked_restaurants", [])))

# Debug button
if st.sidebar.button("🔄 Refresh Stats"):
    st.cache_data.clear()
    st.cache_resource.clear()
    st.rerun()

# Show liked restaurants
if current_prefs.get("liked_restaurants"):
    with st.sidebar.expander("❤️ Quán đã thích"):
        for res_id in current_prefs["liked_restaurants"]:
            try:
                matching = full_df[full_df['id'] == res_id]
                if not matching.empty:
                    restaurant_name = matching.iloc[0]['name']
                    st.write(f"• {restaurant_name}")
            except:
                pass

# ----------------------
# GET RECOMMENDATIONS
# ----------------------
with st.spinner("🔍 Đang tìm kiếm gợi ý cho bạn..."):
    recommendations = get_hybrid_recommendations(
        user_prefs, X, full_df, cosine_sim, cf_model, n=12
    )

# ----------------------
# DISPLAY RECOMMENDATIONS
# ----------------------
if not recommendations:
    st.info("""
    👋 Chào mừng bạn đến với TasteMatch!

    Để nhận được gợi ý cá nhân hóa, hãy:
    1. Chọn **món ăn yêu thích** ở sidebar
    2. Chọn **khu vực** bạn muốn tìm quán
    3. Hoặc **like** một vài quán để hệ thống hiểu sở thích của bạn
    """)
else:
    # Show model info
    col_title, col_info = st.columns([3, 1])
    with col_title:
        st.subheader(f"🎯 {len(recommendations)} gợi ý dành cho bạn")
    with col_info:
        if cf_model.is_trained:
            st.success("🤖 Hybrid: 40% CF + 60% CB")
        else:
            st.info("🎯 Content-Based Only")

    # Display in grid
    for i in range(0, len(recommendations), 3):
        cols = st.columns(3)

        for j in range(3):
            if i + j < len(recommendations):
                rec = recommendations[i + j]
                restaurant = rec['restaurant']

                with cols[j]:
                    with st.container(border=True):
                        # Image
                        st.image(
                            "https://images.unsplash.com/photo-1555992336-cbfad6d9c7b0",
                            use_container_width=True
                        )

                        # Restaurant name
                        st.markdown(f"### {restaurant['name']}")

                        # Rating
                        stars = "⭐" * int(restaurant['average_rating'])
                        st.write(f"{stars} {restaurant['average_rating']}/10")

                        # Info
                        st.write(f"📍 {restaurant['district']}")
                        st.write(
                            f"💰 {int(restaurant['average_price_min']):,}đ - {int(restaurant['avarage_price_max']):,}đ")

                        # Categories
                        categories_str = ", ".join(restaurant['food_categories'][:3])
                        st.caption(f"🍜 {categories_str}")

                        # Reason
                        st.info(f"💡 {rec['reason']}")

                        # Actions
                        col_btn1, col_btn2 = st.columns(2)

                        # Lấy restaurant ID chính xác
                        rest_id = int(restaurant['id'])
                        rest_name = restaurant['name']

                        with col_btn1:
                            if st.button("👁️ Xem", key=f"view_{rest_id}_{i}_{j}", use_container_width=True):
                                add_to_history(rest_id, "viewed")
                                # Lưu tên quán vào session state để trang chi tiết hiển thị
                                st.session_state.selected_restaurant = rest_name
                                # Chuyển trang (cần đúng tên file)
                                st.switch_page("pages/Detail_Place.py")

                        with col_btn2:
                            is_liked = rest_id in user_prefs.get("liked_restaurants", [])
                            like_label = "❤️ Đã thích" if is_liked else "🤍 Thích"

                            if st.button(like_label, key=f"like_{rest_id}_{i}_{j}", use_container_width=True,
                                         disabled=is_liked):
                                if not is_liked:
                                    success = add_to_history(rest_id, "liked")
                                    if success:
                                        st.cache_resource.clear()
                                        st.cache_data.clear()
                                        st.rerun()
                                    else:
                                        st.error("❌ Lỗi khi lưu. Vui lòng thử lại!")

# ----------------------
# TIPS
# ----------------------
st.write("---")
st.subheader("💡 Mẹo để có gợi ý tốt hơn")

tip_cols = st.columns(3)

with tip_cols[0]:
    st.info("""
    **🍜 Chọn món yêu thích**

    Càng nhiều loại món bạn chọn, 
    gợi ý càng chính xác!
    """)

with tip_cols[1]:
    st.info("""
    **❤️ Like quán bạn thích**

    Hệ thống sẽ tìm các quán 
    tương tự để gợi ý.
    """)

with tip_cols[2]:
    st.info("""
    **📍 Chọn khu vực**

    Tìm quán gần nơi bạn 
    thường xuyên lui tới.
    """)

import streamlit as st
import pandas as pd
import re
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api_helper import (
    get_restaurants,
    get_user_prefs,
    update_user_prefs,
    get_recommendations,
    add_to_history
)

st.set_page_config(
    page_title="Hôm nay ăn gì?",
    page_icon="🍽️",
    layout="wide"
)

# ----------------------
# SESSION STATE
# ----------------------
if 'user_id' not in st.session_state:
    st.session_state.user_id = 'current_user'

if 'user_preferences' not in st.session_state:
    st.session_state.user_preferences = None

# ----------------------
# HELPER FUNCTIONS
# ----------------------
def district_sort_key(name):
    if name.startswith("Quận"):
        match = re.search(r"\d+", name)
        if match:
            return (0, int(match.group()))
        else:
            return (0, 999)
    return (1, name)

def parse_json_field(value):
    """Parse JSON string field"""
    if isinstance(value, str):
        try:
            import json
            return json.loads(value)
        except:
            return []
    return value if value else []

@st.cache_data(ttl=300)  # Cache 5 minutes
def load_all_restaurants():
    """Load all restaurants from API"""
    restaurants = get_restaurants()
    if restaurants:
        df = pd.DataFrame(restaurants)
        # Parse JSON fields
        if 'food_categories' in df.columns:
            df['food_categories'] = df['food_categories'].apply(parse_json_field)
        return df
    return pd.DataFrame()

def load_user_preferences():
    """Load user preferences from API"""
    if st.session_state.user_preferences is None:
        prefs = get_user_prefs(st.session_state.user_id)
        st.session_state.user_preferences = prefs
    return st.session_state.user_preferences

def save_user_preferences(prefs):
    """Save user preferences via API"""
    success = update_user_prefs(st.session_state.user_id, prefs)
    if success:
        st.session_state.user_preferences = prefs
    return success

# ----------------------
# LOAD DATA
# ----------------------
full_df = load_all_restaurants()

if full_df.empty:
    st.error("⚠️ Không thể kết nối với API. Vui lòng đảm bảo Flask server đang chạy tại http://localhost:5000")
    st.info("Chạy lệnh: `cd api && python app.py`")
    st.stop()

user_prefs = load_user_preferences()

# ----------------------
# SIDEBAR - User Preferences
# ----------------------
st.sidebar.header("⚙️ Tùy chọn của bạn")

# Get all categories
all_categories = set()
for cats in full_df['food_categories']:
    if isinstance(cats, list):
        all_categories.update(cats)
all_categories = sorted(list(all_categories))

# Get all districts
all_districts = sorted(
    full_df['district'].dropna().unique().tolist(),
    key=district_sort_key
)

# Categories preference
selected_categories = st.sidebar.multiselect(
    "🍜 Món ăn yêu thích",
    options=all_categories,
    default=user_prefs.get("favorite_categories", []),
    help="Chọn các loại món bạn thích"
)

# Districts preference
selected_districts = st.sidebar.multiselect(
    "📍 Khu vực quan tâm",
    options=all_districts,
    default=user_prefs.get("favorite_districts", []),
    help="Chọn các quận bạn muốn tìm quán"
)

# Price range
price_range = st.sidebar.slider(
    "💰 Khoảng giá mong muốn (VNĐ)",
    min_value=0,
    max_value=500000,
    value=(
        user_prefs.get("price_range", [0, 500000])[0],
        user_prefs.get("price_range", [0, 500000])[1]
    ),
    step=10000,
    format="%d đ"
)

# Save preferences button
if st.sidebar.button("💾 Lưu sở thích", type="primary", use_container_width=True):
    new_prefs = {
        'favorite_categories': selected_categories,
        'favorite_districts': selected_districts,
        'price_range': list(price_range),
        'liked_restaurants': user_prefs.get('liked_restaurants', []),
        'viewed_restaurants': user_prefs.get('viewed_restaurants', [])
    }
    
    if save_user_preferences(new_prefs):
        st.sidebar.success("✅ Đã lưu sở thích!")
        st.cache_data.clear()
        st.rerun()
    else:
        st.sidebar.error("❌ Lỗi khi lưu. Vui lòng thử lại!")

# Stats
st.sidebar.write("---")
st.sidebar.write("📊 **Thống kê của bạn:**")

current_prefs = load_user_preferences()
st.sidebar.metric("Quán đã xem", len(current_prefs.get("viewed_restaurants", [])))
st.sidebar.metric("Quán yêu thích", len(current_prefs.get("liked_restaurants", [])))
st.sidebar.metric("Đánh giá", current_prefs.get("total_reviews", 0))

# Show liked restaurants
if current_prefs.get("liked_restaurants"):
    with st.sidebar.expander("❤️ Quán đã thích"):
        for res_id in current_prefs["liked_restaurants"]:
            matching = full_df[full_df['id'] == res_id]
            if not matching.empty:
                st.write(f"• {matching.iloc[0]['name']}")

# Refresh button
if st.sidebar.button("🔄 Làm mới", use_container_width=True):
    st.cache_data.clear()
    st.session_state.user_preferences = None
    st.rerun()

# ----------------------
# MAIN UI
# ----------------------
st.title("🍽️ Hôm nay ăn gì?")
st.caption("Khám phá những gợi ý cá nhân hóa dành riêng cho bạn")

# ----------------------
# GET RECOMMENDATIONS
# ----------------------
with st.spinner("🔍 Đang tìm kiếm gợi ý cho bạn..."):
    recommendations = get_recommendations(st.session_state.user_id, top_k=12)

# ----------------------
# DISPLAY RECOMMENDATIONS
# ----------------------
if not recommendations:
    st.info("""
    👋 Chào mừng bạn đến với TasteMatch!

    Để nhận được gợi ý cá nhân hóa, hãy:
    1. Chọn **món ăn yêu thích** ở sidebar
    2. Chọn **khu vực** bạn muốn tìm quán
    3. Hoặc **like** và **đánh giá** một vài quán để hệ thống hiểu sở thích của bạn
    """)
else:
    # Show model info
    col_title, col_info = st.columns([3, 1])
    with col_title:
        st.subheader(f"🎯 {len(recommendations)} gợi ý dành cho bạn")
    with col_info:
        st.success("🤖 Hybrid Model")

    # Display in grid
    for i in range(0, len(recommendations), 3):
        cols = st.columns(3)

        for j in range(3):
            if i + j < len(recommendations):
                rec = recommendations[i + j]

                with cols[j]:
                    with st.container(border=True):
                        # Image
                        st.image(
                            rec.get('image') or "https://images.unsplash.com/photo-1555992336-cbfad6d9c7b0",
                            use_container_width=True
                        )

                        # Restaurant name
                        st.markdown(f"### {rec['name']}")

                        # Rating
                        rating = rec.get('average_rating', 0)
                        stars = "⭐" * int(rating)
                        st.write(f"{stars} {rating}/10")

                        # Info
                        st.write(f"📍 {rec.get('district', 'N/A')}")
                        
                        price_min = rec.get('average_price_min', 0)
                        price_max = rec.get('avarage_price_max', 0)
                        st.write(f"💰 {int(price_min):,}đ - {int(price_max):,}đ")

                        # Categories
                        food_cats = parse_json_field(rec.get('food_categories', '[]'))
                        
                        if food_cats:
                            categories_str = ", ".join(food_cats[:3])
                            st.caption(f"🍜 {categories_str}")

                        # Recommendation score
                        score = rec.get('recommendation_score', 0)
                        cf_score = rec.get('cf_score', 0)
                        cb_score = rec.get('cb_score', 0)
                        
                        if cf_score > 0 and cb_score > 0:
                            reason = f"💡 Hybrid: {score:.2f}"
                        elif cf_score > 0:
                            reason = f"👥 Collaborative: {score:.2f}"
                        else:
                            reason = f"🎯 Content-Based: {score:.2f}"
                        
                        st.info(reason)

                        # Actions
                        col_btn1, col_btn2 = st.columns(2)

                        rest_id = int(rec['id'])
                        rest_name = rec['name']

                        with col_btn1:
                            if st.button("👁️ Xem", key=f"view_{rest_id}_{i}_{j}", use_container_width=True):
                                # Add to history
                                add_to_history(st.session_state.user_id, rest_id, 'viewed')
                                
                                # Navigate to detail page
                                st.session_state.selected_restaurant = rest_name
                                st.switch_page("pages/Detail_Place.py")

                        with col_btn2:
                            is_liked = rest_id in user_prefs.get("liked_restaurants", [])
                            like_label = "❤️ Đã thích" if is_liked else "🤍 Thích"

                            if st.button(
                                like_label,
                                key=f"like_{rest_id}_{i}_{j}",
                                use_container_width=True,
                                disabled=is_liked
                            ):
                                if not is_liked:
                                    # Add to liked via API
                                    success = add_to_history(st.session_state.user_id, rest_id, 'liked')
                                    
                                    if success:
                                        st.cache_data.clear()
                                        st.session_state.user_preferences = None
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
    **❤️ Like và đánh giá quán**

    Hệ thống sẽ học sở thích 
    của bạn theo thời gian.
    """)

with tip_cols[2]:
    st.info("""
    **📍 Chọn khu vực**

    Tìm quán gần nơi bạn 
    thường xuyên lui tới.
    """)
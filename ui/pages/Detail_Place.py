import streamlit as st
import pandas as pd
import pydeck as pdk
import time as time_module
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api_helper import (
    get_restaurants,
    get_restaurant,
    get_reviews,
    add_review,
    add_to_history
)

st.set_page_config(page_title="Chi tiết địa điểm", page_icon="📍", layout="wide")

# ----------------------
# SESSION STATE
# ----------------------
if 'user_id' not in st.session_state:
    st.session_state.user_id = 'current_user'

if 'selected_restaurant' not in st.session_state:
    st.session_state.selected_restaurant = None

# ----------------------
# HELPER FUNCTIONS
# ----------------------
def parse_json_field(value):
    """Parse JSON string field"""
    if isinstance(value, str):
        try:
            import json
            return json.loads(value)
        except:
            return []
    return value if value else []

# ----------------------
# LOAD DATA
# ----------------------
@st.cache_data(ttl=300)
def load_all_restaurants():
    """Load all restaurants from API"""
    restaurants = get_restaurants()
    if restaurants:
        df = pd.DataFrame(restaurants)
        # Parse JSON fields
        for field in ['food_categories', 'style', 'suitable_time', 'appropriate']:
            if field in df.columns:
                df[field] = df[field].apply(parse_json_field)
        return df
    return pd.DataFrame()

df = load_all_restaurants()

if df.empty:
    st.error("⚠️ Không thể kết nối với API.")
    st.stop()

# ----------------------
# SEARCH BAR
# ----------------------
st.title("📍 Chi tiết địa điểm")

# Restaurant names for autocomplete
restaurant_names = df['name'].tolist()

# Search box
search_query = st.selectbox(
    "🔍 Tìm kiếm quán ăn",
    options=[""] + restaurant_names,
    index=0,
    placeholder="Nhập tên quán..."
)

# Handle search selection
if search_query and search_query != "":
    st.session_state.selected_restaurant = search_query

# ----------------------
# DISPLAY RESTAURANT CARDS
# ----------------------
if not st.session_state.selected_restaurant:
    st.subheader("📋 Tất cả quán ăn")
    st.caption("Chọn một quán để xem chi tiết")

    # Display grid
    cols = st.columns(3)

    for idx, row in df.iterrows():
        col_idx = idx % 3
        with cols[col_idx]:
            with st.container(border=True):
                st.markdown(f"### {row['name']}")
                st.write(f"📍 {row.get('address', 'N/A')}, {row.get('district', 'N/A')}")
                st.write(f"⭐ Đánh giá: **{row.get('average_rating', 0)}/10**")

                # Get review count from API
                reviews = get_reviews(row['id'])
                if reviews:
                    st.caption(f"💬 {len(reviews)} đánh giá")

                if st.button("Xem chi tiết", key=f"btn_{idx}"):
                    st.session_state.selected_restaurant = row['name']
                    st.rerun()

else:
    # ----------------------
    # RESTAURANT DETAIL
    # ----------------------
    restaurant = df[df['name'] == st.session_state.selected_restaurant].iloc[0]
    rest_id = int(restaurant['id'])
    
    # Add to viewed history
    add_to_history(st.session_state.user_id, rest_id, 'viewed')

    # Back button
    if st.button("← Quay lại danh sách"):
        st.session_state.selected_restaurant = None
        st.rerun()

    st.title(f"📍 {restaurant['name']}")

    # Layout 2 columns
    col1, col2 = st.columns([2, 1])

    with col1:
        # ----------------------
        # BASIC INFO
        # ----------------------
        st.image(
            restaurant.get('image') or "https://images.unsplash.com/photo-1555992336-cbfad6d9c7b0",
            caption=f"Không gian {restaurant['name']}",
            use_container_width=True
        )

        # Parse JSON fields
        food_cats = parse_json_field(restaurant.get('food_categories', '[]'))
        styles = parse_json_field(restaurant.get('style', '[]'))
        suitable_times = parse_json_field(restaurant.get('suitable_time', '[]'))
        appropriate = parse_json_field(restaurant.get('appropriate', '[]'))

        st.markdown(f"""
        **📍 Địa chỉ:** {restaurant.get('address', 'N/A')}, {restaurant.get('district', 'N/A')}  
        **🏙️ Thành phố:** {restaurant.get('city', 'N/A')}  
        **⏰ Giờ mở cửa:** {restaurant.get('main_opening_hour', 'N/A')} - {restaurant.get('main_closing_hour', 'N/A')}  
        **🍽️ Loại hình:** {restaurant.get('category', 'N/A')}  
        **💰 Giá trung bình:** {int(restaurant.get('average_price_min', 0)):,}đ - {int(restaurant.get('avarage_price_max', 0)):,}đ
        """)

        # ----------------------
        # MAP 
        # ----------------------
        if pd.notna(restaurant.get('latitude')) and pd.notna(restaurant.get('longitude')):
            st.subheader("🗺️ Vị trí")

            map_df = pd.DataFrame({
                "name": [restaurant["name"]],
                "address": [restaurant.get("address", "")],
                "latitude": [restaurant["latitude"]],
                "longitude": [restaurant["longitude"]]
            })

            layer = pdk.Layer(
                "ScatterplotLayer",
                data=map_df,
                get_position='[longitude, latitude]',
                get_radius=120,
                get_fill_color=[255, 59, 48],
                pickable=True,
                auto_highlight=True
            )

            view_state = pdk.ViewState(
                latitude=restaurant["latitude"],
                longitude=restaurant["longitude"],
                zoom=15
            )

            tooltip = {
                "html": "<b>{name}</b><br/>📍 {address}",
                "style": {
                    "backgroundColor": "white",
                    "color": "black",
                    "fontSize": "13px"
                }
            }

            st.pydeck_chart(
                pdk.Deck(
                    layers=[layer],
                    initial_view_state=view_state,
                    tooltip=tooltip,
                    map_style="mapbox://styles/mapbox/streets-v11"
                ),
                use_container_width=True
            )

    with col2:
        # ----------------------
        # RATINGS
        # ----------------------
        st.subheader("⭐ Đánh giá tổng quan")

        st.metric("Điểm trung bình", f"{restaurant.get('average_rating', 0)}/10")

        # Rating breakdown
        st.write("**Chi tiết đánh giá:**")
        st.progress(restaurant.get('quality_rating', 0) / 10, text=f"Chất lượng: {restaurant.get('quality_rating', 0)}/10")
        st.progress(restaurant.get('service_rating', 0) / 10, text=f"Phục vụ: {restaurant.get('service_rating', 0)}/10")
        st.progress(restaurant.get('price_rating', 0) / 10, text=f"Giá cả: {restaurant.get('price_rating', 0)}/10")
        st.progress(restaurant.get('location_rating', 0) / 10, text=f"Vị trí: {restaurant.get('location_rating', 0)}/10")
        st.progress(restaurant.get('space_rating', 0) / 10, text=f"Không gian: {restaurant.get('space_rating', 0)}/10")

        # Comment stats
        st.write("---")
        st.write(f"**📝 Tổng số bình luận:** {int(restaurant.get('comment_quantity', 0))}")

    # ----------------------
    # ADDITIONAL INFO
    # ----------------------
    st.write("---")

    col3, col4, col5 = st.columns(3)

    with col3:
        st.subheader("🍜 Món ăn")
        for food in food_cats:
            st.write(f"• {food}")

    with col4:
        st.subheader("🎨 Phong cách")
        for style in styles:
            st.write(f"• {style}")

    with col5:
        st.subheader("⏰ Thời gian phù hợp")
        for time in suitable_times:
            st.write(f"• {time}")

    # ----------------------
    # SUITABLE FOR
    # ----------------------
    st.write("---")
    st.subheader("👥 Phù hợp với")

    if appropriate:
        appropriate_cols = st.columns(len(appropriate))
        for idx, app in enumerate(appropriate):
            with appropriate_cols[idx]:
                st.info(app)

    # ----------------------
    # USER RATING SECTION
    # ----------------------
    st.write("---")
    st.subheader("⭐ Viết đánh giá của bạn")

    with st.form(key=f"rating_form_{rest_id}", clear_on_submit=True):
        col_name, col_rating = st.columns([3, 1])

        with col_name:
            user_name = st.text_input("Tên của bạn *", placeholder="Nhập tên của bạn...")

        with col_rating:
            rating = st.slider("Số sao *", 1, 10, 8)

        comment_text = st.text_area(
            "Bình luận *",
            placeholder="Chia sẻ trải nghiệm của bạn về quán này...",
            height=100
        )

        submit_button = st.form_submit_button("📤 Gửi đánh giá", type="primary", use_container_width=True)

        if submit_button:
            if not user_name.strip():
                st.error("⚠️ Vui lòng nhập tên của bạn")
            elif not comment_text.strip():
                st.error("⚠️ Vui lòng nhập bình luận")
            else:
                with st.spinner("Đang lưu đánh giá..."):
                    success = add_review(
                        user_id=st.session_state.user_id,
                        username=user_name.strip(),
                        review_text=comment_text.strip(),
                        rating=rating,
                        res_id=rest_id
                    )

                    if success:
                        st.success("✅ Cảm ơn bạn đã đánh giá!")
                        st.info("💡 Hệ thống đã học được sở thích của bạn từ đánh giá này!")
                        st.balloons()
                        time_module.sleep(1)
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("❌ Lỗi khi lưu đánh giá. Vui lòng thử lại!")

    # ----------------------
    # DISPLAY COMMENTS
    # ----------------------
    st.write("---")

    # Get reviews from API
    all_reviews = get_reviews(rest_id)

    # Separate user reviews and foody reviews
    user_reviews = [r for r in all_reviews if r.get('source') == 'user']
    foody_reviews = [r for r in all_reviews if r.get('source') == 'foody']

    total_reviews = len(all_reviews)

    # Header with tabs
    st.subheader("💬 Đánh giá & Bình luận")

    if total_reviews > 0:
        st.metric("Tổng đánh giá", total_reviews)

        # Tabs
        tab1, tab2 = st.tabs([
            f"👥 Từ người dùng ({len(user_reviews)})",
            f"🍴 Từ Foody ({len(foody_reviews)})"
        ])

        # Tab 1: User Reviews
        with tab1:
            if user_reviews:
                for review in user_reviews:
                    with st.container(border=True):
                        # Header
                        col_user, col_time = st.columns([2, 1])
                        with col_user:
                            st.markdown(f"**👤 {review.get('username', 'Anonymous')}**")
                        with col_time:
                            st.caption(f"🕒 {review.get('timestamp', '')}")

                        # Rating
                        rating_val = review.get('rating', 0)
                        stars = "⭐" * int(rating_val)
                        st.markdown(f"### {stars} {rating_val}/10")

                        # Review text
                        st.write(review.get('review_text', ''))
            else:
                st.info("📝 Chưa có bình luận từ người dùng. Hãy là người đầu tiên!")

        # Tab 2: Foody Reviews
        with tab2:
            if foody_reviews:
                for review in foody_reviews:
                    with st.container(border=True):
                        # Header
                        col_user, col_time = st.columns([2, 1])
                        with col_user:
                            profile_url = review.get('profile_url', '#')
                            username = review.get('username', 'Anonymous')
                            st.markdown(f"**👤 [{username}]({profile_url})**")
                        with col_time:
                            st.caption(f"🕒 {review.get('timestamp', '')}")

                        # Rating
                        rating_val = review.get('rating', 0)
                        stars = "⭐" * int(rating_val)
                        st.markdown(f"### {stars} {rating_val}/10")

                        # Review text
                        review_text = review.get('review_text', '')
                        if len(review_text) > 300:
                            st.write(review_text[:300] + "...")
                            with st.expander("Đọc thêm"):
                                st.write(review_text)
                        else:
                            st.write(review_text)

                        st.caption("📱 Nguồn: Foody.vn")
            else:
                st.info("📝 Chưa có đánh giá từ Foody cho quán này.")
    else:
        st.info("📝 Chưa có bình luận nào. Hãy là người đầu tiên đánh giá quán này!")
import streamlit as st
import pandas as pd
import itertools
import re
import pydeck as pdk
from api_helper import get_restaurants

st.set_page_config(
    page_title="TasteMatch",
    page_icon="🍜",
    layout="wide"
)

def district_sort_key(name):
    if name.startswith("Quận"):
        match = re.search(r"\d+", name)
        if match:
            return (0, int(match.group()))
        else:
            return (0, 999)
    return (1, name)

def parse_json_field(value):
    if isinstance(value, str):
        try:
            import json
            return json.loads(value)
        except:
            return []
    return value if value else []

@st.cache_data(ttl=300)  
def load_data_from_api():
    restaurants = get_restaurants()
    if not restaurants:
        st.error("⚠️ Không thể kết nối với API. Vui lòng đảm bảo Flask server đang chạy!")
        st.info("Chạy lệnh: `cd api && python app.py`")
        st.stop()
    
    df = pd.DataFrame(restaurants)
    
    if 'food_categories' in df.columns:
        df['food_categories'] = df['food_categories'].apply(parse_json_field)
    if 'style' in df.columns:
        df['style'] = df['style'].apply(parse_json_field)
    
    return df

with st.spinner("🔄 Đang tải dữ liệu từ API..."):
    df = load_data_from_api()

st.sidebar.header("🔍 Bộ lọc")

districts = ["Tất cả"] + sorted(
    df[df["district"].notna()]["district"].unique().tolist(),
    key=district_sort_key
)

all_categories = set()
for cats in df['food_categories']:
    if isinstance(cats, list):
        all_categories.update(cats)
categories = ["Tất cả"] + sorted(list(all_categories))

selected_district = st.sidebar.selectbox("Quận", districts)
selected_category = st.sidebar.selectbox("Loại món", categories)

if st.sidebar.button("🔄 Làm mới dữ liệu"):
    st.cache_data.clear()
    st.rerun()

filtered_df = df.copy()

if selected_district != "Tất cả":
    filtered_df = filtered_df[filtered_df["district"] == selected_district]

if selected_category != "Tất cả":
    filtered_df = filtered_df[
        filtered_df["food_categories"].apply(
            lambda x: selected_category in x if isinstance(x, list) else False
        )
    ]

st.title("🗺️ Khám phá địa điểm ăn uống")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Tổng số quán", len(df))
with col2:
    st.metric("Quán đang hiển thị", len(filtered_df))
with col3:
    avg_rating = filtered_df['average_rating'].mean() if not filtered_df.empty else 0
    st.metric("Đánh giá TB", f"{avg_rating:.1f}/10")

st.subheader("📍 Bản đồ quán ăn")

map_df = filtered_df.dropna(subset=["latitude", "longitude"]).copy()

if not map_df.empty:
    scatter_layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_df,
        get_position='[longitude, latitude]',
        get_radius=90,
        get_fill_color=[255, 59, 48],
        pickable=True,
        auto_highlight=True
    )

    view_state = pdk.ViewState(
        latitude=map_df["latitude"].mean(),
        longitude=map_df["longitude"].mean(),
        zoom=12
    )

    tooltip = {
        "html": """
        <b>{name}</b><br/>
        📍 {address}<br/>
        ⭐ Rating: {average_rating}
        """,
        "style": {
            "backgroundColor": "white",
            "color": "black",
            "fontSize": "13px"
        }
    }

    deck = pdk.Deck(
        layers=[scatter_layer],
        initial_view_state=view_state,
        tooltip=tooltip,
        map_style="mapbox://styles/mapbox/streets-v11"
    )

    st.pydeck_chart(deck, use_container_width=True)
else:
    st.info("📍 Không có quán nào có tọa độ")

st.subheader("📋 Danh sách địa điểm")

if filtered_df.empty:
    st.warning("Không tìm thấy quán nào phù hợp với bộ lọc")
else:
    display_df = filtered_df.copy()
    
    if 'food_categories' in display_df.columns:
        display_df['food_categories_str'] = display_df['food_categories'].apply(
            lambda x: ", ".join(x[:3]) if isinstance(x, list) else ""
        )

    preferred_cols = [
        "name",
        "district",
        "address",
        "category",
        "food_categories_str",
        "average_rating",
        "average_price_min",
        "avarage_price_max"
    ]
    
    display_cols = [col for col in preferred_cols if col in display_df.columns]

    column_names = {
        "name": "Tên quán",
        "district": "Quận",
        "address": "Địa chỉ",
        "category": "Loại hình",
        "food_categories_str": "Món ăn",
        "average_rating": "Đánh giá",
        "average_price_min": "Giá min (đ)",
        "avarage_price_max": "Giá max (đ)"
    }
    
    display_data = display_df[display_cols].rename(columns=column_names)
    
    st.dataframe(
        display_data.reset_index(drop=True),
        use_container_width=True,
        hide_index=True
    )

st.write("---")
st.caption("🔌 Powered by TasteMatch API | 📊 Data loaded from Flask API")
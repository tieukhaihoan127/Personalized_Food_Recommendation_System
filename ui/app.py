import streamlit as st
import pandas as pd
import itertools
import re
import json
import pydeck as pdk
import sys
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(ROOT_DIR)

# =======================
# Page config
# =======================
st.set_page_config(
    page_title="TasteMatch",
    page_icon="🍜",
    layout="wide"
)

# =======================
# Utils
# =======================
def district_sort_key(name):
    if name.startswith("Quận"):
        match = re.search(r"\d+", name)
        if match:
            return (0, int(match.group()))
        else:
            return (0, 999)
    return (1, name)

# =======================
# Load data
# =======================
@st.cache_data
def load_data():
    with open("./data/restaurants.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    return pd.DataFrame(data)

df = load_data()

# =======================
# Sidebar – Filters
# =======================
st.sidebar.header("🔍 Bộ lọc")

districts = ["Tất cả"] + sorted(
    df[df["district"].notna()]["district"].unique().tolist(),
    key=district_sort_key
)

# flatten food_categories
all_categories = list(
    set(itertools.chain.from_iterable(df["food_categories"]))
)
categories = ["Tất cả"] + sorted(all_categories)

selected_district = st.sidebar.selectbox("Quận", districts)
selected_category = st.sidebar.selectbox("Loại món", categories)

# =======================
# Filter data
# =======================
filtered_df = df.copy()

if selected_district != "Tất cả":
    filtered_df = filtered_df[
        filtered_df["district"] == selected_district
    ]

if selected_category != "Tất cả":
    filtered_df = filtered_df[
        filtered_df["food_categories"].apply(
            lambda x: selected_category in x
        )
    ]

# =======================
# MAIN UI
# =======================
st.title("🗺️ Khám phá địa điểm ăn uống")
# =======================
# MAP
# =======================
st.subheader("📍 Bản đồ quán ăn")

map_df = filtered_df.dropna(
    subset=["latitude", "longitude"]
).copy()

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

# =======================
# LIST VIEW
# =======================
st.subheader("📋 Danh sách địa điểm")

# Các cột muốn hiển thị (ưu tiên)
preferred_cols = [
    "name",
    "district",
    "address",
    "category",
    "style",
    "average_rating",
    "average_price_min",
    "avarage_price_max"
]

# Chỉ lấy các cột thực sự tồn tại
display_cols = [col for col in preferred_cols if col in filtered_df.columns]

st.dataframe(
    filtered_df[display_cols].reset_index(drop=True),
    use_container_width=True
)

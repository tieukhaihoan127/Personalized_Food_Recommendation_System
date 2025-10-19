# app.py
import streamlit as st
import json
import pandas as pd
import matplotlib.pyplot as plt
from Content_based_Filtering_model import load_and_prepare_data, build_similarity_model, recommend_similar_places

# =======================
# Cấu hình Streamlit
# =======================
st.set_page_config(
    page_title="TasteMatch",
    page_icon="logo.svg",
    layout="wide"
)

# =======================
# Tải dữ liệu & mô hình
# =======================
@st.cache_data
def load_data():
    X = load_and_prepare_data("./restaurants.json")
    tfidf, cosine_sim = build_similarity_model(X)
    return X, cosine_sim

X, cosine_sim = load_data()

# =======================
# Sidebar lựa chọn
# =======================
def custom_sort(name: str):
    if name.startswith("Quận "):
        # Lấy số quận nếu có, còn không thì để 1000 cho các quận đặc biệt
        parts = name.split()
        if parts[1].isdigit():
            return (0, int(parts[1]))   # nhóm 0 = quận số, sort theo số
        else:
            return (1, parts[1])       # nhóm 1 = quận chữ (Bình Thạnh, Tân Bình...)
    elif name.startswith("Thành phố"):
        return (2, name)
    else:  # Huyện
        return (3, name)

restaurants = ['--- Chọn quán yêu thích ---'] + list(X['name'].unique())
districts = ['--- Chọn quận ---'] + sorted(X[X['district'].notna() & (X['district'].str.strip() != '')]['district'].unique(), key=custom_sort)

st.sidebar.image("logo.svg")
selected_district = st.sidebar.selectbox("Choose your District", districts, index=0)
selected_restaurant = st.sidebar.selectbox("Choose your favorite Restaurant", restaurants, index=0)

# =======================
# Tiêu đề & mô tả
# =======================
st.title("TasteMatch: Discover Your Next Favorite Restaurant")
st.text("Find restaurants similar to your favorites using a content-based recommendation system!")

# =======================
# Thống kê quán ăn theo quận
# =======================
df_counts = X['district'].value_counts().reset_index()
df_counts.columns = ['district', 'count']

# Hiển thị bảng và biểu đồ
show_stats = st.checkbox("Hiển thị thống kê quán ăn theo quận", value=True)

if show_stats:
    st.subheader("📊 Số lượng quán ăn theo từng quận")
    st.dataframe(df_counts)
    fig, ax = plt.subplots()
    df_counts.plot(kind="bar", x="district", y="count", ax=ax, legend=False)
    ax.set_ylabel("Số quán ăn")
    st.pyplot(fig)

# =======================
# Hiển thị gợi ý
# =======================
if st.sidebar.button("Show recommendations"):
    if selected_restaurant == "--- Chọn quán yêu thích ---":
        st.subheader(f"Dưới đây là những quán có địa chỉ tại {selected_district}")
        res_in_selected_dis = X[X['district'] == selected_district]
        res_in_selected_dis = res_in_selected_dis[['name', 'address', 'category', 'food_categories', 'style']]
        st.dataframe(res_in_selected_dis.reset_index(drop=True))
        # st.warning("⚠️ Vui lòng chọn một quán yêu thích trước.")
    else:
        st.subheader(f"🍽️ Gợi ý quán tương tự với **{selected_restaurant}**")
        recommendations = recommend_similar_places(X, cosine_sim, selected_restaurant, top_n=10)

        if selected_district != "--- Chọn quận ---":
            recommendations = recommendations[recommendations['district'] == selected_district]

        if recommendations.empty:
            st.info("Không tìm thấy quán tương tự trong quận này.")
        else:
            st.dataframe(recommendations.reset_index(drop=True))

import pandas as pd

# Đọc file JSON
df = pd.read_json("restaurants_reviews.json")

# Ghi ra file CSV
df.to_csv("restaurants_reviews.csv", index=False, encoding='utf-8-sig')

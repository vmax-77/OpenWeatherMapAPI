import os

# API
OPENWEATHER_API_URL = "https://api.openweathermap.org/data/2.5/weather"
OPENWEATHER_TIMEOUT = 10

# Пути
DATA_PATH = "./data"
DATA_FILE = "temperature_data.csv"
DATA_FILE_PATH = os.path.join(DATA_PATH, DATA_FILE)

# Анализ
ANOMALY_SIGMA_THRESHOLD = 2  # 2 стандартных отклонения
MOVING_AVERAGE_WINDOW = 30

# Визуализация
PLOTLY_TEMPLATE = "plotly_white"
MATPLOTLIB_STYLE = "seaborn-v0_8"

# Города и сезоны
SEASONAL_TEMPERATURES = {
    "New York": {"winter": 0, "spring": 10, "summer": 25, "autumn": 15},
    "London": {"winter": 5, "spring": 11, "summer": 18, "autumn": 12},
    "Paris": {"winter": 4, "spring": 12, "summer": 20, "autumn": 13},
    "Tokyo": {"winter": 6, "spring": 15, "summer": 27, "autumn": 18},
    "Moscow": {"winter": -10, "spring": 5, "summer": 18, "autumn": 8},
    "Sydney": {"winter": 12, "spring": 18, "summer": 25, "autumn": 20},
    "Berlin": {"winter": 0, "spring": 10, "summer": 20, "autumn": 11},
    "Beijing": {"winter": -2, "spring": 13, "summer": 27, "autumn": 16},
    "Rio de Janeiro": {"winter": 20, "spring": 25, "summer": 30, "autumn": 25},
    "Dubai": {"winter": 20, "spring": 30, "summer": 40, "autumn": 30},
    "Los Angeles": {"winter": 15, "spring": 18, "summer": 25, "autumn": 20},
    "Singapore": {"winter": 27, "spring": 28, "summer": 28, "autumn": 27},
    "Mumbai": {"winter": 25, "spring": 30, "summer": 35, "autumn": 30},
    "Cairo": {"winter": 15, "spring": 25, "summer": 35, "autumn": 25},
    "Mexico City": {"winter": 12, "spring": 18, "summer": 20, "autumn": 15},
}

MONTH_TO_SEASON = {
    12: "winter", 1: "winter", 2: "winter",
    3: "spring", 4: "spring", 5: "spring",
    6: "summer", 7: "summer", 8: "summer",
    9: "autumn", 10: "autumn", 11: "autumn"
}

SEASON_NAMES_RU = {
    "winter": "Зима",
    "spring": "Весна", 
    "summer": "Лето", 
    "autumn": "Осень"
}
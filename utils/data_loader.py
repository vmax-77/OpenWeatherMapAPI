import pandas as pd
import numpy as np
import os
from datetime import datetime
import streamlit as st
from config import DATA_FILE_PATH, SEASONAL_TEMPERATURES, MONTH_TO_SEASON

def generate_realistic_temperature_data(cities=None, num_years=10):
    """Генерация тестовых данных о температуре"""
    if cities is None:
        cities = list(SEASONAL_TEMPERATURES.keys())
    
    dates = pd.date_range(start="2010-01-01", periods=365 * num_years, freq="D")
    data = []

    for city in cities:
        for date in dates:
            season = MONTH_TO_SEASON[date.month]
            mean_temp = SEASONAL_TEMPERATURES[city][season]
            # Добавляем случайное отклонение
            temperature = np.random.normal(loc=mean_temp, scale=5)
            data.append({
                "city": city, 
                "timestamp": date, 
                "temperature": temperature
            })

    df = pd.DataFrame(data)
    df['season'] = df['timestamp'].dt.month.map(lambda x: MONTH_TO_SEASON[x])
    return df

@st.cache_data
def load_temperature_data():
    """
    Загрузка данных из CSV или генерация новых
    Возвращает DataFrame с историческими данными
    """
    try:
        # Проверяем существование файла
        if not os.path.exists(DATA_FILE_PATH):
            os.makedirs(os.path.dirname(DATA_FILE_PATH), exist_ok=True)
            df = generate_realistic_temperature_data()
            df.to_csv(DATA_FILE_PATH, index=False)
            return df
        
        # Загружаем существующий файл
        df = pd.read_csv(DATA_FILE_PATH)
        
        # Проверяем структуру данных
        required_columns = ['city', 'timestamp', 'temperature', 'season']
        if not all(col in df.columns for col in required_columns):
            raise ValueError("Файл данных имеет некорректную структуру")
        
        # Преобразуем timestamp
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Проверяем наличие данных
        if df.empty:
            df = generate_realistic_temperature_data()
            df.to_csv(DATA_FILE_PATH, index=False)
        
        return df
        
    except Exception as e:
        # В случае ошибки генерируем новые данные
        print(f"Ошибка загрузки данных: {e}. Генерация новых данных.")
        df = generate_realistic_temperature_data()
        os.makedirs(os.path.dirname(DATA_FILE_PATH), exist_ok=True)
        df.to_csv(DATA_FILE_PATH, index=False)
        return df

def get_city_data(df, city_name):
    """Получение данных для конкретного города"""
    if city_name not in df['city'].unique():
        raise ValueError(f"Город {city_name} не найден в данных")
    return df[df['city'] == city_name].copy()

def get_season_data(df, city_name, season):
    """Получение данных для конкретного города и сезона"""
    city_data = get_city_data(df, city_name)
    return city_data[city_data['season'] == season].copy()
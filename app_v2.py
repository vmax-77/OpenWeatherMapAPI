import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
import os
import asyncio
import concurrent.futures

# Импорт из наших модулей
from utils import (
    load_temperature_data,
    generate_realistic_temperature_data,
    TemperatureAnalyzer,
    WeatherAPIHandler,
    DataVisualizer
)
from config import MONTH_TO_SEASON, SEASON_NAMES_RU

# Настройка страницы
st.set_page_config(
    page_title="Анализ температурных данных",
    page_icon="🌡️",
    layout="wide"
)

# Заголовок
st.title("🌡️ Анализ температурных данных и мониторинг текущей температуры через OpenWeatherMap API")
st.markdown("Задача решалась в рамках учебного проекта магистратуры 'Искусственный интеллект'")

# Инициализация данных и обработчиков
if 'df' not in st.session_state:
    st.session_state.df = load_temperature_data()

if 'api_handler' not in st.session_state:
    st.session_state.api_handler = WeatherAPIHandler()

df = st.session_state.df
api_handler = st.session_state.api_handler
analyzer = TemperatureAnalyzer(df)
visualizer = DataVisualizer()

# Создание вкладок
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Анализ данных",
    "🌤️ Текущая погода",
    "📈 Визуализация",
    "⚡ Производительность"
])

with tab1:
    st.header("Анализ исторических данных")

    # Выбор города
    cities = sorted(df['city'].unique())
    selected_city = st.selectbox("Выберите город:", cities)
    
    # Базовые статистики
    st.subheader("📊 Основные статистики")
    
    basic_stats = analyzer.get_basic_stats(selected_city)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Средняя температура", f"{basic_stats['mean']:.1f}°C")
    with col2:
        st.metric("Максимальная", f"{basic_stats['max']:.1f}°C")
    with col3:
        st.metric("Минимальная", f"{basic_stats['min']:.1f}°C")
    with col4:
        st.metric("Стандартное отклонение", f"{basic_stats['std']:.1f}°C")
    
    # Статистика по сезонам
    st.subheader("Статистики по сезонам")
    
    seasonal_stats = analyzer.get_seasonal_stats(selected_city)
    seasonal_df = pd.DataFrame(seasonal_stats).T.round(1)
    seasonal_df.index = [SEASON_NAMES_RU.get(idx, idx) for idx in seasonal_df.index]
    seasonal_df.columns = ['Средняя', 'Станд. отклонение', 'Минимум', 'Максимум', 'Количество дней']
    st.dataframe(seasonal_df)
    
    # Обнаружение аномалий
    st.subheader("Обнаружение аномалий")
    
    anomaly_result = analyzer.detect_anomalies(selected_city)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        bounds = anomaly_result['bounds']
        st.metric("Нормальный диапазон", f"{bounds['lower']:.1f}...{bounds['upper']:.1f}°C")
    with col2:
        st.metric("Всего аномалий", anomaly_result['stats']['n_anomalies'])
    with col3:
        st.metric("Процент аномалий", f"{anomaly_result['stats']['percent_anomalies']:.1f}%")
    
    if not anomaly_result['anomalies'].empty:
        st.write("Последние 10 аномалий:")
        anomalies_display = anomaly_result['anomalies'][['timestamp', 'temperature', 'season']].tail(10).copy()
        anomalies_display['season'] = anomalies_display['season'].map(lambda x: SEASON_NAMES_RU.get(x, x))
        st.dataframe(anomalies_display)
    
    # Скользящее среднее
    st.subheader("Скользящее среднее")
    
    window_size = st.slider("Размер окна (дни):", 7, 90, 30, key="ma_window")
    city_data_with_ma = analyzer.calculate_moving_average(selected_city, window_size)
    
    # Таблица с данными
    st.subheader("Просмотр данных")
    if st.checkbox("Показать первые 30 строк данных"):
        display_data = city_data_with_ma[['timestamp', 'temperature', 'season', 'moving_avg']].head(30).copy()
        display_data['season'] = display_data['season'].map(lambda x: SEASON_NAMES_RU.get(x, x))
        st.dataframe(display_data)

with tab2:
    st.header("Текущая погода через OpenWeatherMap")
    
    # Ввод API ключа
    api_key = st.text_input(
        "Введите ваш OpenWeatherMap API ключ:",
        type="password",
        help="Получите бесплатный ключ на openweathermap.org"
    )
    
    if api_key:
        api_handler.set_api_key(api_key)
        
        # Выбор города для проверки погоды
        weather_city = st.selectbox("Выберите город для проверки погоды:", cities, key="weather_city")
        
        col1, col2 = st.columns(2)
        
        with col1:
            request_type = st.radio("Тип запроса:", ["Синхронный", "Асинхронный"])
        
        if st.button("Получить текущую погоду", type="primary"):
            with st.spinner("Получаем данные о погоде..."):
                try:
                    if request_type == "Синхронный":
                        result = api_handler.get_current_weather_sync(weather_city)
                    else:
                        result = asyncio.run(api_handler.get_current_weather_async(weather_city))
                    
                    if result['success']:
                        weather_data = result['data']
                        
                        st.success(f"Данные получены {result['method']} за {result['elapsed_time']:.2f} секунд")
                        
                        # Отображение данных
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.subheader("🌡️ Текущая погода")
                            st.metric("Температура", f"{weather_data['temperature']:.1f}°C")
                            st.metric("Ощущается как", f"{weather_data['feels_like']:.1f}°C")
                            st.metric("Влажность", f"{weather_data['humidity']}%")
                        
                        with col2:
                            st.subheader("📊 Дополнительно")
                            st.metric("Давление", f"{weather_data['pressure']} гПа")
                            st.metric("Скорость ветра", f"{weather_data['wind_speed']} м/с")
                            st.metric("Описание", weather_data['description'].capitalize())
                        
                        # Проверка на аномальность
                        st.subheader("🔍 Проверка аномальности")
                        
                        # Определяем текущий сезон
                        month = datetime.now().month
                        current_season = MONTH_TO_SEASON.get(month, "winter")
                        
                        # Анализируем текущую температуру
                        current_analysis = analyzer.check_current_temperature(
                            weather_city, 
                            weather_data['temperature'], 
                            current_season
                        )
                        
                        if current_analysis:
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Средняя по сезону", f"{current_analysis['season_mean']:.1f}°C")
                            with col2:
                                bounds = current_analysis['bounds']
                                st.metric("Нормальный диапазон", f"{bounds['lower']:.1f}...{bounds['upper']:.1f}°C")
                            with col3:
                                if current_analysis['is_anomalous']:
                                    st.error("⚠️ Аномальная температура!")
                                else:
                                    st.success("✅ Температура в норме")
                            
                            # График сравнения
                            fig = visualizer.plot_current_temp_comparison(
                                current_analysis, weather_city, current_season
                            )
                            st.pyplot(fig)
                        
                    else:
                        st.error(f"❌ Ошибка {result.get('error_code', '')}: {result['error_message']}")
                        
                except Exception as e:
                    st.error(f"❌ Ошибка: {str(e)}")
    else:
        st.info("🔑 Введите API ключ OpenWeatherMap для получения текущей погоды")

with tab3:
    st.header("📈 Визуализация данных")
    
    # Создаем две колонки
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Выбор города для графиков
        graph_city = st.selectbox("Выберите город для графиков:", cities, key="graph_city")
    
    with col2:
        # Выбор сезона для детального анализа
        seasons = ['winter', 'spring', 'summer', 'autumn']
        season_names = [SEASON_NAMES_RU[s] for s in seasons]
        selected_season_ru = st.selectbox("Выберите сезон (для детального анализа аномалий):", season_names, key="season_select")
        selected_season = {v: k for k, v in SEASON_NAMES_RU.items()}[selected_season_ru]
    
    # Получаем данные для выбранного города
    city_data = df[df['city'] == graph_city].copy()
    
    # 1. Линейный график температуры со скользящим средним
    st.subheader("📊 Линейный график температуры со скользящим средним")
    
    # Вычисляем скользящее среднее
    city_data_sorted = city_data.sort_values('timestamp')
    window_size = st.slider("Размер окна для скользящего среднего (дни):", 7, 90, 30, key="ma_window_viz")
    
    city_data_sorted['moving_avg'] = city_data_sorted['temperature'].rolling(
        window=window_size, center=True, min_periods=1
    ).mean()
    
    # Создаем график
    fig = go.Figure()
    
    # Температура (тонкая линия)
    fig.add_trace(go.Scatter(
        x=city_data_sorted['timestamp'],
        y=city_data_sorted['temperature'],
        mode='lines',
        name='Температура',
        line=dict(color='lightblue', width=1),
        opacity=0.5,
        hovertemplate='%{x|%Y-%m-%d}<br>Температура: %{y:.1f}°C<extra></extra>'
    ))
    
    # Скользящее среднее (толстая линия)
    fig.add_trace(go.Scatter(
        x=city_data_sorted['timestamp'],
        y=city_data_sorted['moving_avg'],
        mode='lines',
        name=f'Скользящее среднее ({window_size} дней)',
        line=dict(color='red', width=3),
        hovertemplate='%{x|%Y-%m-%d}<br>Скользящее среднее: %{y:.1f}°C<extra></extra>'
    ))
    
    # Находим экстремальные значения
    max_temp_idx = city_data_sorted['temperature'].idxmax()
    min_temp_idx = city_data_sorted['temperature'].idxmin()
    
    # Максимальная температура
    fig.add_trace(go.Scatter(
        x=[city_data_sorted.loc[max_temp_idx, 'timestamp']],
        y=[city_data_sorted.loc[max_temp_idx, 'temperature']],
        mode='markers',
        name='Максимум',
        marker=dict(color='darkred', size=12, symbol='triangle-up'),
        hovertemplate='%{x|%Y-%m-%d}<br>Максимум: %{y:.1f}°C<extra></extra>'
    ))
    
    # Минимальная температура
    fig.add_trace(go.Scatter(
        x=[city_data_sorted.loc[min_temp_idx, 'timestamp']],
        y=[city_data_sorted.loc[min_temp_idx, 'temperature']],
        mode='markers',
        name='Минимум',
        marker=dict(color='darkblue', size=12, symbol='triangle-down'),
        hovertemplate='%{x|%Y-%m-%d}<br>Минимум: %{y:.1f}°C<extra></extra>'
    ))
    
    fig.update_layout(
        title=f'Температура в {graph_city} со скользящим средним',
        xaxis_title='Дата',
        yaxis_title='Температура (°C)',
        hovermode='x unified',
        template='plotly_white',  # Используем стандартный шаблон
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 2. Гистограмма распределения и боксплот по сезонам
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Распределение температур")
        
        # Создаем гистограмму вручную, так как visualizer использует PLOTLY_TEMPLATE
        fig_hist = go.Figure()
        
        fig_hist.add_trace(go.Histogram(
            x=city_data['temperature'],
            nbinsx=50,
            name='Распределение',
            marker_color='lightblue',
            opacity=0.7,
            hovertemplate='Температура: %{x:.1f}°C<br>Количество дней: %{y}<extra></extra>'
        ))
        
        # Добавляем статистические линии
        mean_temp = city_data['temperature'].mean()
        std_temp = city_data['temperature'].std()
        
        fig_hist.add_vline(
            x=mean_temp, 
            line_dash="dash", 
            line_color="red",
            annotation_text=f"Средняя: {mean_temp:.1f}°C",
            annotation_position="top right"
        )
        
        fig_hist.add_vline(x=mean_temp - 2*std_temp, line_dash="dot", line_color="orange")
        fig_hist.add_vline(x=mean_temp + 2*std_temp, line_dash="dot", line_color="orange")
        
        fig_hist.update_layout(
            title=f'Распределение температур в {graph_city}',
            xaxis_title='Температура (°C)',
            yaxis_title='Количество дней',
            template='plotly_white',
            showlegend=False
        )
        
        st.plotly_chart(fig_hist, use_container_width=True)
    
    with col2:
        st.subheader("📦 Распределение по сезонам")
        
        # Создаем боксплот вручную
        city_data_display = city_data.copy()
        city_data_display['season_ru'] = city_data_display['season'].map(
            lambda x: SEASON_NAMES_RU.get(x, x)
        )
        
        fig_box = go.Figure()
        
        # Добавляем боксплот для каждого сезона
        seasons_ru = ['Зима', 'Весна', 'Лето', 'Осень']
        colors = ['lightblue', 'lightgreen', 'lightcoral', 'wheat']
        
        for season_ru, color in zip(seasons_ru, colors):
            season_data = city_data_display[city_data_display['season_ru'] == season_ru]['temperature']
            if len(season_data) > 0:
                fig_box.add_trace(go.Box(
                    y=season_data,
                    name=season_ru,
                    marker_color=color,
                    boxmean=True  # Показываем среднее значение
                ))
        
        fig_box.update_layout(
            title=f'Распределение температур по сезонам в {graph_city}',
            yaxis_title='Температура (°C)',
            xaxis_title='Сезон',
            template='plotly_white',
            showlegend=False
        )
        
        st.plotly_chart(fig_box, use_container_width=True)
    
    # 3. Анализ аномалий для конкретного города и сезона
    st.subheader("🔍 Детальный анализ аномалий")
    
    # Получаем данные для выбранного города и сезона
    season_data = city_data[city_data['season'] == selected_season].copy()
    
    if not season_data.empty:
        # Вычисляем статистику для сезона
        mean_temp = season_data['temperature'].mean()
        std_temp = season_data['temperature'].std()
        
        lower_bound = mean_temp - 2 * std_temp
        upper_bound = mean_temp + 2 * std_temp
        
        # Определяем аномалии
        season_data['is_anomaly'] = (
            (season_data['temperature'] < lower_bound) | 
            (season_data['temperature'] > upper_bound)
        )
        
        anomalies = season_data[season_data['is_anomaly']]
        n_anomalies = len(anomalies)
        percent_anomalies = (n_anomalies / len(season_data)) * 100
        
        # Отображаем статистику
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Средняя температура", f"{mean_temp:.1f}°C")
        with col2:
            st.metric("Стандартное отклонение", f"{std_temp:.1f}°C")
        with col3:
            st.metric("Количество аномалий", n_anomalies)
        with col4:
            st.metric("Процент аномалий", f"{percent_anomalies:.1f}%")
        
        # Создаем график аномалий
        fig_anomalies = go.Figure()
        
        # Нормальные точки
        normal_data = season_data[~season_data['is_anomaly']]
        if not normal_data.empty:
            fig_anomalies.add_trace(go.Scatter(
                x=normal_data['timestamp'],
                y=normal_data['temperature'],
                mode='markers',
                name='Нормальные значения',
                marker=dict(color='blue', size=6, opacity=0.5),
                hovertemplate='%{x|%Y-%m-%d}<br>Температура: %{y:.1f}°C<extra></extra>'
            ))
        
        # Аномальные точки
        if not anomalies.empty:
            fig_anomalies.add_trace(go.Scatter(
                x=anomalies['timestamp'],
                y=anomalies['temperature'],
                mode='markers',
                name='Аномалии',
                marker=dict(color='red', size=10, symbol='circle'),
                hovertemplate='%{x|%Y-%m-%d}<br>Аномалия: %{y:.1f}°C<extra></extra>'
            ))
        
        # Линии границ
        fig_anomalies.add_trace(go.Scatter(
            x=[season_data['timestamp'].min(), season_data['timestamp'].max()],
            y=[upper_bound, upper_bound],
            mode='lines',
            name='Верхняя граница (среднее + 2σ)',
            line=dict(color='green', dash='dash', width=1),
            opacity=0.7
        ))
        
        fig_anomalies.add_trace(go.Scatter(
            x=[season_data['timestamp'].min(), season_data['timestamp'].max()],
            y=[lower_bound, lower_bound],
            mode='lines',
            name='Нижняя граница (среднее - 2σ)',
            line=dict(color='orange', dash='dash', width=1),
            opacity=0.7
        ))
        
        # Средняя линия
        fig_anomalies.add_trace(go.Scatter(
            x=[season_data['timestamp'].min(), season_data['timestamp'].max()],
            y=[mean_temp, mean_temp],
            mode='lines',
            name=f'Среднее = {mean_temp:.1f}°C',
            line=dict(color='black', width=2),
            opacity=0.5
        ))
        
        fig_anomalies.update_layout(
            title=f'Аномалии температуры в городе {graph_city} ({SEASON_NAMES_RU[selected_season]})',
            xaxis_title='Дата',
            yaxis_title='Температура (°C)',
            hovermode='closest',
            template='plotly_white',
            height=500,
            showlegend=True
        )
        
        st.plotly_chart(fig_anomalies, use_container_width=True)
        
        # Показываем таблицу с аномалиями
        if not anomalies.empty:
            with st.expander("Показать детали аномалий"):
                anomalies_display = anomalies[['timestamp', 'temperature']].copy()
                anomalies_display['timestamp'] = anomalies_display['timestamp'].dt.strftime('%Y-%m-%d')
                anomalies_display['deviation'] = (anomalies_display['temperature'] - mean_temp).round(1)
                anomalies_display.columns = ['Дата', 'Температура (°C)', 'Отклонение от среднего (°C)']
                st.dataframe(anomalies_display.sort_values('Отклонение от среднего (°C)', ascending=False))
    else:
        st.info(f"Нет данных для города {graph_city} в сезон {SEASON_NAMES_RU[selected_season]}")
    
    # 4. Сравнение городов
    st.subheader("🏙️ Сравнение городов")
    
    compare_cities = st.multiselect(
        "Выберите города для сравнения:",
        cities,
        default=[graph_city, "Moscow", "Berlin", "Beijing", "Dubai"],
        key="compare_cities"
    )
    
    if len(compare_cities) > 1:
        compare_data = df[df['city'].isin(compare_cities)]
        
        # Боксплот для сравнения
        fig_comparison = go.Figure()
        
        colors = px.colors.qualitative.Set3
        
        for i, city in enumerate(compare_cities):
            city_temp_data = compare_data[compare_data['city'] == city]['temperature']
            fig_comparison.add_trace(go.Box(
                y=city_temp_data,
                name=city,
                marker_color=colors[i % len(colors)],
                boxmean=True
            ))
        
        fig_comparison.update_layout(
            title='Сравнение распределения температур',
            yaxis_title='Температура (°C)',
            xaxis_title='Город',
            template='plotly_white',
            showlegend=False
        )
        
        st.plotly_chart(fig_comparison, use_container_width=True)
        
        # Линейный график средних по месяцам
        if not pd.api.types.is_datetime64_any_dtype(compare_data['timestamp']):
            compare_data = compare_data.copy()
            compare_data['timestamp'] = pd.to_datetime(compare_data['timestamp'])
        
        compare_data['month'] = compare_data['timestamp'].dt.month
        monthly_avg = compare_data.groupby(['city', 'month'])['temperature'].mean().reset_index()
        
        fig_monthly = px.line(
            monthly_avg,
            x='month',
            y='temperature',
            color='city',
            title='Средняя температура по месяцам',
            labels={'month': 'Месяц', 'temperature': 'Температура (°C)', 'city': 'Город'},
            markers=True
        )
        
        fig_monthly.update_layout(
            template='plotly_white',
            xaxis=dict(tickmode='array', tickvals=list(range(1, 13)), 
                      ticktext=['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 
                               'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек'])
        )
        
        st.plotly_chart(fig_monthly, use_container_width=True)
        
        # Таблица сравнения статистик
        with st.expander("Показать сравнительную таблицу статистик"):
            comparison_stats = []
            for city in compare_cities:
                city_stats = analyzer.get_basic_stats(city)
                anomaly_result = analyzer.detect_anomalies(city)
                
                comparison_stats.append({
                    'Город': city,
                    'Средняя температура (°C)': f"{city_stats['mean']:.1f}",
                    'Станд. отклонение (°C)': f"{city_stats['std']:.1f}",
                    'Минимум (°C)': f"{city_stats['min']:.1f}",
                    'Максимум (°C)': f"{city_stats['max']:.1f}",
                    'Количество аномалий': anomaly_result['stats']['n_anomalies'],
                    'Процент аномалий (%)': f"{anomaly_result['stats']['percent_anomalies']:.1f}"
                })
            
            comparison_df = pd.DataFrame(comparison_stats)
            st.dataframe(comparison_df)
    
    # 5. Анализ города с наибольшим процентом аномалий
    st.subheader("🏆 Город с наибольшим процентом аномалий")
    
    if st.button("Найти город с наибольшим процентом аномалий", key="find_top_anomaly"):
        with st.spinner("Анализируем данные по всем городам..."):
            # Собираем статистику по всем городам
            all_anomaly_stats = []
            
            for city in cities:
                anomaly_result = analyzer.detect_anomalies(city)
                all_anomaly_stats.append({
                    'Город': city,
                    'Процент аномалий': anomaly_result['stats']['percent_anomalies'],
                    'Количество аномалий': anomaly_result['stats']['n_anomalies'],
                    'Средняя температура': anomaly_result['stats']['mean']
                })
            
            anomaly_df = pd.DataFrame(all_anomaly_stats)
            top_city_row = anomaly_df.loc[anomaly_df['Процент аномалий'].idxmax()]
            
            st.success(f"**Город с наибольшим процентом аномалий:** {top_city_row['Город']}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Процент аномалий", f"{top_city_row['Процент аномалий']:.1f}%")
            with col2:
                st.metric("Количество аномалий", int(top_city_row['Количество аномалий']))
            with col3:
                st.metric("Средняя температура", f"{top_city_row['Средняя температура']:.1f}°C")
            
            # Анализируем аномалии по сезонам для этого города
            city_season_stats = []
            top_city_data = df[df['city'] == top_city_row['Город']]
            
            for season in ['winter', 'spring', 'summer', 'autumn']:
                season_data = top_city_data[top_city_data['season'] == season]
                if len(season_data) > 0:
                    season_mean = season_data['temperature'].mean()
                    season_std = season_data['temperature'].std()
                    
                    lower_bound_season = season_mean - 2 * season_std
                    upper_bound_season = season_mean + 2 * season_std
                    
                    anomalies_season = season_data[
                        (season_data['temperature'] < lower_bound_season) | 
                        (season_data['temperature'] > upper_bound_season)
                    ]
                    
                    city_season_stats.append({
                        'Сезон': SEASON_NAMES_RU[season],
                        'Средняя температура': season_mean,
                        'Станд. отклонение': season_std,
                        'Количество аномалий': len(anomalies_season),
                        'Процент аномалий': (len(anomalies_season) / len(season_data)) * 100
                    })
            
            # Находим сезон с наибольшим процентом аномалий
            season_stats_df = pd.DataFrame(city_season_stats)
            if not season_stats_df.empty:
                top_season_row = season_stats_df.loc[season_stats_df['Процент аномалий'].idxmax()]
                
                st.info(f"**Сезон с наибольшим процентом аномалий в {top_city_row['Город']}:** {top_season_row['Сезон']}")
                
                # Создаем график для этого города и сезона
                top_season = {v: k for k, v in SEASON_NAMES_RU.items()}[top_season_row['Сезон']]
                top_city_season_data = top_city_data[top_city_data['season'] == top_season].copy()
                
                # Вычисляем аномалии
                mean_temp_season = top_season_row['Средняя температура']
                std_temp_season = top_season_row['Станд. отклонение']
                
                lower_bound = mean_temp_season - 2 * std_temp_season
                upper_bound = mean_temp_season + 2 * std_temp_season
                
                top_city_season_data['is_anomaly'] = (
                    (top_city_season_data['temperature'] < lower_bound) | 
                    (top_city_season_data['temperature'] > upper_bound)
                )
                
                # Создаем график
                fig_top = go.Figure()
                
                # Нормальные точки
                normal_top = top_city_season_data[~top_city_season_data['is_anomaly']]
                if not normal_top.empty:
                    fig_top.add_trace(go.Scatter(
                        x=normal_top['timestamp'],
                        y=normal_top['temperature'],
                        mode='markers',
                        name='Нормальные значения',
                        marker=dict(color='blue', size=6, opacity=0.5)
                    ))
                
                # Аномальные точки
                anomalies_top = top_city_season_data[top_city_season_data['is_anomaly']]
                if not anomalies_top.empty:
                    fig_top.add_trace(go.Scatter(
                        x=anomalies_top['timestamp'],
                        y=anomalies_top['temperature'],
                        mode='markers',
                        name='Аномалии',
                        marker=dict(color='red', size=10, symbol='circle')
                    ))
                
                # Границы
                fig_top.add_hline(y=upper_bound, line_dash="dash", line_color="green", 
                                 annotation_text="Верхняя граница")
                fig_top.add_hline(y=lower_bound, line_dash="dash", line_color="orange", 
                                 annotation_text="Нижняя граница")
                fig_top.add_hline(y=mean_temp_season, line_dash="dot", line_color="black", 
                                 annotation_text=f"Среднее: {mean_temp_season:.1f}°C")
                
                fig_top.update_layout(
                    title=f'Аномалии температуры в городе {top_city_row["Город"]} ({top_season_row["Сезон"]})',
                    xaxis_title='Дата',
                    yaxis_title='Температура (°C)',
                    template='plotly_white',
                    height=500,
                    showlegend=True
                )
                
                st.plotly_chart(fig_top, use_container_width=True)

with tab4:
    st.header("⚡ Сравнение производительности")
    
    # 1. Сравнение распараллеливания анализа данных
    st.subheader("1. Распараллеливание анализа данных")

    test_cities_count = st.slider(
        "Количество городов для теста:", 
        2, 20, 10, 
        key="test_cities_perf"
    )
    
    if st.button("Запустить сравнение обработки данных", key="run_perf_test"):
        import concurrent.futures
        
        test_cities = cities[:test_cities_count]
        
        st.write(f"Тестируем на {test_cities_count} городах: {', '.join(test_cities[:5])}...")

        # Последовательная обработка
        start_time = time.time()
        for city in test_cities:
            city_data = df[df['city'] == city]
            mean_temp = city_data['temperature'].mean()
            std_temp = city_data['temperature'].std()
        seq_time = time.time() - start_time
        
        # Параллельная обработка
        def analyze_city(city_name):
            city_data = df[df['city'] == city_name]
            mean_temp = city_data['temperature'].mean()
            std_temp = city_data['temperature'].std()
            return mean_temp, std_temp
        
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = list(executor.map(analyze_city, test_cities))
        par_time = time.time() - start_time
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Последовательно", f"{seq_time:.3f} сек")
        with col2:
            st.metric("Параллельно", f"{par_time:.3f} сек")
        with col3:
            speedup = seq_time / par_time if par_time > 0 else 0
            st.metric("Ускорение", f"{speedup:.1f}x")
        
        # Анализ результатов
        if seq_time < par_time or abs(seq_time - par_time) < 0.001:
            st.warning("""
            **Наблюдение:** Последовательная обработка оказалась не менее эффективной.
            
            **Причины:**
            1. Маленький объем данных
            2. Простые вычисления
            3. Накладные расходы на создание потоков
            """)
        else:
            st.success("""
            **Наблюдение:** Параллельная обработка оказалась эффективнее.
            """)
    
    # 2. Сравнение синхронных/асинхронных запросов к API
    st.subheader("2. Синхронные vs Асинхронные запросы к API")
    
    if api_key and st.button("Запустить сравнение запросов"):
        api_handler.set_api_key(api_key)
        
        test_cities_api = ["London", "Paris", "Berlin", "Moscow", "Tokyo"]
        
        # Синхронный метод
        start_time = time.time()
        sync_results = []
        for city in test_cities_api:
            result = api_handler.get_current_weather_sync(city)
            sync_results.append(result)
        sync_time = time.time() - start_time
        
        # Асинхронный метод
        start_time = time.time()
        try:
            async_results = asyncio.run(api_handler.get_multiple_cities_async(test_cities_api))
            async_time = time.time() - start_time
        except Exception as e:
            st.error(f"Ошибка асинхронного запроса: {str(e)}")
            async_time = time.time() - start_time
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Синхронно (5 городов)", f"{sync_time:.2f} сек")
        with col2:
            st.metric("Асинхронно (5 городов)", f"{async_time:.2f} сек")
        with col3:
            speedup = sync_time / async_time if async_time > 0 else 0
            st.metric("Ускорение", f"{speedup:.1f}x")

# Сайдбар
with st.sidebar:
    st.header("ℹ️ Информация")
    st.markdown(f"""
    ### Исторические данные:
    - Городов: {len(cities)}
    - Записей: {len(df):,}
    - Период: {df['timestamp'].min().date()} - {df['timestamp'].max().date()}
    
    ### Для использования данных о текущей погоде:
    1. Получите API ключ на [openweathermap.org](https://openweathermap.org/api)
    2. Введите ключ во вкладке "Текущая погода"
    3. Выберите город и нажмите "Получить погоду"
    """)
    
    # Кнопка для обновления данных
    if st.button("🔄 Сгенерировать новые данные"):
        st.session_state.df = generate_realistic_temperature_data()
        os.makedirs('./data', exist_ok=True)
        st.session_state.df.to_csv('./data/temperature_data.csv', index=False)
        st.rerun()

# Футер
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p><strong>Контакты для обратной связи</strong></p>
</div>
<div style='text-align: center'>
    <p>Telegram @v_max_77<p>
</div>
<div style='text-align: center'>
    <p>Почта max.240798@mail.ru</p>
</div>
""", unsafe_allow_html=True)
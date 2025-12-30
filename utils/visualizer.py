import plotly.graph_objects as go
import plotly.express as px
import matplotlib.pyplot as plt
import pandas as pd
from config import PLOTLY_TEMPLATE, MATPLOTLIB_STYLE, SEASON_NAMES_RU

class DataVisualizer:
    """Класс для создания визуализаций"""
    
    @staticmethod
    def plot_temperature_timeseries(city_data, show_moving_avg=True, show_anomalies=True):
        """Построение графика временного ряда температуры"""
        fig = go.Figure()
        
        # Сортируем данные по времени
        city_data = city_data.sort_values('timestamp')
        
        # Основная температура
        fig.add_trace(go.Scatter(
            x=city_data['timestamp'],
            y=city_data['temperature'],
            mode='lines',
            name='Температура',
            line=dict(color='blue', width=1),
            opacity=0.7,
            hovertemplate='%{x|%Y-%m-%d}<br>Температура: %{y:.1f}°C<extra></extra>'
        ))
        
        # Скользящее среднее
        if show_moving_avg and 'moving_avg' in city_data.columns:
            fig.add_trace(go.Scatter(
                x=city_data['timestamp'],
                y=city_data['moving_avg'],
                mode='lines',
                name='Скользящее среднее',
                line=dict(color='red', width=2),
                hovertemplate='%{x|%Y-%m-%d}<br>Ср. значение: %{y:.1f}°C<extra></extra>'
            ))
        
        # Аномалии
        if show_anomalies and 'is_anomaly' in city_data.columns:
            anomalies = city_data[city_data['is_anomaly']]
            if not anomalies.empty:
                fig.add_trace(go.Scatter(
                    x=anomalies['timestamp'],
                    y=anomalies['temperature'],
                    mode='markers',
                    name='Аномалии',
                    marker=dict(color='red', size=8, symbol='circle'),
                    hovertemplate='%{x|%Y-%m-%d}<br>Аномалия: %{y:.1f}°C<extra></extra>'
                ))
        
        fig.update_layout(
            title='Историческая температура',
            xaxis_title='Дата',
            yaxis_title='Температура (°C)',
            hovermode='x unified',
            template=PLOTLY_TEMPLATE,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        return fig
    
    @staticmethod
    def plot_temperature_distribution(city_data):
        """Гистограмма распределения температур"""
        fig = px.histogram(
            city_data, 
            x='temperature',
            nbins=50,
            title='Распределение температур',
            labels={'temperature': 'Температура (°C)', 'count': 'Количество дней'},
            opacity=0.7
        )
        
        # Добавляем статистические линии
        mean_temp = city_data['temperature'].mean()
        std_temp = city_data['temperature'].std()
        
        fig.add_vline(
            x=mean_temp, 
            line_dash="dash", 
            line_color="red",
            annotation_text=f"Средняя: {mean_temp:.1f}°C",
            annotation_position="top right"
        )
        
        fig.add_vline(x=mean_temp - 2*std_temp, line_dash="dot", line_color="orange")
        fig.add_vline(x=mean_temp + 2*std_temp, line_dash="dot", line_color="orange")
        
        fig.update_layout(
            template=PLOTLY_TEMPLATE,
            showlegend=False
        )
        
        return fig
    
    @staticmethod
    def plot_seasonal_boxplot(city_data):
        """Боксплот по сезонам"""
        # Преобразуем названия сезонов на русский
        city_data_display = city_data.copy()
        city_data_display['season_ru'] = city_data_display['season'].map(
            lambda x: SEASON_NAMES_RU.get(x, x)
        )
        
        fig = px.box(
            city_data_display,
            x='season_ru',
            y='temperature',
            color='season_ru',
            title='Распределение температур по сезонам',
            labels={'season_ru': 'Сезон', 'temperature': 'Температура (°C)'},
            category_orders={'season_ru': ['Зима', 'Весна', 'Лето', 'Осень']}
        )
        
        fig.update_layout(
            template=PLOTLY_TEMPLATE,
            showlegend=False
        )
        
        return fig
    
    @staticmethod
    def plot_seasonal_profile(seasonal_stats, city_name):
        """Профиль средних температур по сезонам"""
        seasons = ['winter', 'spring', 'summer', 'autumn']
        season_names_ru = [SEASON_NAMES_RU[s] for s in seasons]
        
        means = []
        stds = []
        
        for season in seasons:
            if season in seasonal_stats:
                stats = seasonal_stats[season]
                means.append(stats['mean'])
                stds.append(stats['std'])
            else:
                means.append(None)
                stds.append(None)
        
        fig = go.Figure()
        
        # Столбцы со средними значениями
        fig.add_trace(go.Bar(
            x=season_names_ru,
            y=means,
            name='Средняя температура',
            error_y=dict(type='data', array=stds, visible=True),
            marker_color='lightblue',
            hovertemplate='Сезон: %{x}<br>Средняя: %{y:.1f}°C<extra></extra>'
        ))
        
        fig.update_layout(
            title=f'Сезонный профиль температуры - {city_name}',
            xaxis_title='Сезон',
            yaxis_title='Температура (°C)',
            template=PLOTLY_TEMPLATE
        )
        
        return fig
    
    @staticmethod
    def plot_city_comparison(compare_data):
        """Сравнение нескольких городов"""
        fig = px.box(
            compare_data,
            x='city',
            y='temperature',
            color='city',
            title='Сравнение распределения температур',
            labels={'city': 'Город', 'temperature': 'Температура (°C)'}
        )
        
        fig.update_layout(
            template=PLOTLY_TEMPLATE,
            showlegend=False
        )
        
        return fig
    
    @staticmethod
    def plot_monthly_averages(compare_data):
        """Средние температуры по месяцам для нескольких городов"""
        if not pd.api.types.is_datetime64_any_dtype(compare_data['timestamp']):
            compare_data = compare_data.copy()
            compare_data['timestamp'] = pd.to_datetime(compare_data['timestamp'])
        
        compare_data['month'] = compare_data['timestamp'].dt.month
        monthly_avg = compare_data.groupby(['city', 'month'])['temperature'].mean().reset_index()
        
        fig = px.line(
            monthly_avg,
            x='month',
            y='temperature',
            color='city',
            title='Средняя температура по месяцам',
            labels={'month': 'Месяц', 'temperature': 'Температура (°C)', 'city': 'Город'},
            markers=True
        )
        
        fig.update_layout(
            template=PLOTLY_TEMPLATE,
            xaxis=dict(tickmode='array', tickvals=list(range(1, 13)), 
                      ticktext=['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 
                               'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек'])
        )
        
        return fig
    
    @staticmethod
    def plot_current_temp_comparison(current_analysis, city_name, season):
        """Сравнение текущей температуры с историческими данными (matplotlib)"""
        plt.style.use(MATPLOTLIB_STYLE)
        
        fig, ax = plt.subplots(figsize=(10, 4))
        
        # Диапазон нормальных значений
        ax.axhspan(
            current_analysis['bounds']['lower'], 
            current_analysis['bounds']['upper'], 
            alpha=0.3, color='green', label='Нормальный диапазон (±2σ)'
        )
        
        # Средняя историческая
        ax.axhline(
            y=current_analysis['season_mean'], 
            color='blue', linestyle='--', linewidth=2,
            label=f"Средняя историческая: {current_analysis['season_mean']:.1f}°C"
        )
        
        # Текущая температура
        ax.axhline(
            y=current_analysis['current_temp'], 
            color='red', linewidth=3,
            label=f"Текущая: {current_analysis['current_temp']:.1f}°C"
        )
        
        # Настройки графика
        season_ru = SEASON_NAMES_RU.get(season, season)
        ax.set_title(f'Сравнение текущей температуры с историческими данными ({city_name}, {season_ru})')
        ax.set_ylabel('Температура (°C)')
        ax.legend(loc='upper right')
        ax.grid(True, alpha=0.3)
        
        return fig
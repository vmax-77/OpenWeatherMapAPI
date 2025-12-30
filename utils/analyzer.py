import pandas as pd
import numpy as np
from scipy import stats
from config import ANOMALY_SIGMA_THRESHOLD, MOVING_AVERAGE_WINDOW

class TemperatureAnalyzer:
    """Класс для анализа температурных данных"""
    
    def __init__(self, df):
        self.df = df.copy()
        self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
        self.df = self.df.sort_values('timestamp')
    
    def get_basic_stats(self, city_name=None):
        """Получение базовой статистики"""
        if city_name:
            data = self.df[self.df['city'] == city_name]['temperature']
        else:
            data = self.df['temperature']
        
        return {
            'mean': data.mean(),
            'std': data.std(),
            'min': data.min(),
            'max': data.max(),
            'count': len(data),
            'q25': data.quantile(0.25),
            'q50': data.median(),
            'q75': data.quantile(0.75)
        }
    
    def get_seasonal_stats(self, city_name):
        """Статистика по сезонам для города"""
        city_data = self.df[self.df['city'] == city_name]
        seasonal_stats = {}
        
        for season in ['winter', 'spring', 'summer', 'autumn']:
            season_data = city_data[city_data['season'] == season]['temperature']
            if len(season_data) > 0:
                seasonal_stats[season] = {
                    'mean': season_data.mean(),
                    'std': season_data.std(),
                    'min': season_data.min(),
                    'max': season_data.max(),
                    'count': len(season_data)
                }
        
        return seasonal_stats
    
    def calculate_moving_average(self, city_name, window_size=MOVING_AVERAGE_WINDOW):
        """Вычисление скользящего среднего"""
        city_data = self.df[self.df['city'] == city_name].copy()
        city_data = city_data.sort_values('timestamp')
        city_data['moving_avg'] = city_data['temperature'].rolling(
            window=window_size, center=True, min_periods=1
        ).mean()
        return city_data
    
    def detect_anomalies(self, city_name, sigma_threshold=ANOMALY_SIGMA_THRESHOLD):
        """Обнаружение аномалий в данных города"""
        city_data = self.df[self.df['city'] == city_name].copy()
        
        mean_temp = city_data['temperature'].mean()
        std_temp = city_data['temperature'].std()
        
        lower_bound = mean_temp - sigma_threshold * std_temp
        upper_bound = mean_temp + sigma_threshold * std_temp
        
        city_data['is_anomaly'] = (
            (city_data['temperature'] < lower_bound) | 
            (city_data['temperature'] > upper_bound)
        )
        
        anomalies = city_data[city_data['is_anomaly']]
        
        return {
            'city_data': city_data,
            'anomalies': anomalies,
            'bounds': {'lower': lower_bound, 'upper': upper_bound},
            'stats': {
                'mean': mean_temp,
                'std': std_temp,
                'n_anomalies': len(anomalies),
                'percent_anomalies': (len(anomalies) / len(city_data)) * 100
            }
        }
    
    def check_current_temperature(self, city_name, current_temp, current_season):
        """Проверка текущей температуры на аномальность"""
        # Получаем исторические данные для сезона
        season_data = self.df[
            (self.df['city'] == city_name) & 
            (self.df['season'] == current_season)
        ]['temperature']
        
        if len(season_data) == 0:
            return None
        
        season_mean = season_data.mean()
        season_std = season_data.std()
        
        lower_bound = season_mean - 2 * season_std
        upper_bound = season_mean + 2 * season_std
        
        is_anomalous = current_temp < lower_bound or current_temp > upper_bound
        
        return {
            'current_temp': current_temp,
            'season_mean': season_mean,
            'season_std': season_std,
            'bounds': {'lower': lower_bound, 'upper': upper_bound},
            'is_anomalous': is_anomalous,
            'deviation': current_temp - season_mean
        }
    
    def calculate_trends(self, city_name):
        """Расчет температурных трендов"""
        city_data = self.df[self.df['city'] == city_name].copy()
        city_data = city_data.sort_values('timestamp')
        city_data['days'] = (city_data['timestamp'] - city_data['timestamp'].min()).dt.days
        
        if len(city_data) < 2:
            return None
        
        # Линейная регрессия
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            city_data['days'], city_data['temperature']
        )
        
        return {
            'slope_per_day': slope,
            'slope_per_year': slope * 365,
            'intercept': intercept,
            'r_squared': r_value ** 2,
            'p_value': p_value,
            'trend_direction': 'warming' if slope > 0 else 'cooling',
            'is_significant': p_value < 0.05
        }
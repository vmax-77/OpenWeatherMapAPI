import requests
import aiohttp
import asyncio
from datetime import datetime
import time
from config import OPENWEATHER_API_URL, OPENWEATHER_TIMEOUT

class WeatherAPIHandler:
    """Обработчик запросов к OpenWeatherMap API"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key
    
    def set_api_key(self, api_key):
        """Установка API ключа"""
        self.api_key = api_key
    
    def validate_api_key(self):
        """Проверка валидности API ключа"""
        if not self.api_key:
            return False, "API ключ не установлен"
        
        # Простая проверка формата
        if len(self.api_key) < 20:
            return False, "API ключ слишком короткий"
        
        return True, "API ключ валиден"
    
    def get_current_weather_sync(self, city_name):
        """Синхронный запрос текущей погоды"""
        if not self.api_key:
            raise ValueError("API ключ не установлен")
        
        params = {
            'q': city_name,
            'appid': self.api_key,
            'units': 'metric',
            'lang': 'ru'
        }
        
        start_time = time.time()
        try:
            response = requests.get(
                OPENWEATHER_API_URL, 
                params=params, 
                timeout=OPENWEATHER_TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                elapsed_time = time.time() - start_time
                
                return {
                    'success': True,
                    'data': self._parse_weather_data(data),
                    'elapsed_time': elapsed_time,
                    'method': 'sync'
                }
            else:
                error_data = response.json() if response.text else {}
                return {
                    'success': False,
                    'error_code': response.status_code,
                    'error_message': error_data.get('message', f"Ошибка {response.status_code}"),
                    'elapsed_time': time.time() - start_time
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error_code': 0,
                'error_message': f"Ошибка подключения: {str(e)}",
                'elapsed_time': time.time() - start_time
            }
        except Exception as e:
            return {
                'success': False,
                'error_code': 0,
                'error_message': f"Неожиданная ошибка: {str(e)}",
                'elapsed_time': time.time() - start_time
            }
    
    async def get_current_weather_async(self, city_name):
        """Асинхронный запрос текущей погоды"""
        if not self.api_key:
            raise ValueError("API ключ не установлен")
        
        params = {
            'q': city_name,
            'appid': self.api_key,
            'units': 'metric',
            'lang': 'ru'
        }
        
        start_time = time.time()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    OPENWEATHER_API_URL, 
                    params=params, 
                    timeout=OPENWEATHER_TIMEOUT
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        elapsed_time = time.time() - start_time
                        
                        return {
                            'success': True,
                            'data': self._parse_weather_data(data),
                            'elapsed_time': elapsed_time,
                            'method': 'async'
                        }
                    else:
                        error_data = await response.json() if response.text else {}
                        return {
                            'success': False,
                            'error_code': response.status,
                            'error_message': error_data.get('message', f"Ошибка {response.status}"),
                            'elapsed_time': time.time() - start_time
                        }
                        
        except aiohttp.ClientError as e:
            return {
                'success': False,
                'error_code': 0,
                'error_message': f"Ошибка подключения: {str(e)}",
                'elapsed_time': time.time() - start_time
            }
        except Exception as e:
            return {
                'success': False,
                'error_code': 0,
                'error_message': f"Неожиданная ошибка: {str(e)}",
                'elapsed_time': time.time() - start_time
            }
    
    async def get_multiple_cities_async(self, cities_list):
        """Асинхронный запрос погоды для нескольких городов"""
        tasks = [self.get_current_weather_async(city) for city in cities_list]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Обработка результатов
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    'city': cities_list[i],
                    'success': False,
                    'error_message': str(result)
                })
            else:
                result['city'] = cities_list[i]
                processed_results.append(result)
        
        return processed_results
    
    def _parse_weather_data(self, data):
        """Парсинг данных от API"""
        return {
            'temperature': data['main']['temp'],
            'feels_like': data['main']['feels_like'],
            'humidity': data['main']['humidity'],
            'pressure': data['main']['pressure'],
            'description': data['weather'][0]['description'],
            'wind_speed': data['wind']['speed'],
            'city': data['name'],
            'country': data['sys']['country'],
            'timestamp': datetime.fromtimestamp(data['dt'])
        }
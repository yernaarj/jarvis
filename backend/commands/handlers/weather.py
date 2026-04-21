import requests
import logging

logger = logging.getLogger(__name__)

WEATHER_DESCRIPTIONS = {
    'clear sky': 'ясно',
    'few clouds': 'небольшая облачность',
    'scattered clouds': 'переменная облачность',
    'broken clouds': 'облачно',
    'overcast clouds': 'пасмурно',
    'light rain': 'небольшой дождь',
    'moderate rain': 'умеренный дождь',
    'heavy intensity rain': 'сильный дождь',
    'thunderstorm': 'гроза',
    'snow': 'снег',
    'light snow': 'небольшой снег',
    'mist': 'туман',
    'fog': 'туман',
    'haze': 'дымка',
    'drizzle': 'морось',
}


def get_weather(city: str = 'Алматы') -> str:
    """Получает текущую погоду для города через OpenWeatherMap API"""
    from config import settings

    api_key = settings.OPENWEATHER_API_KEY
    if not api_key:
        logger.error("❌ OPENWEATHER_API_KEY не задан в .env")
        return "Не могу получить погоду — не настроен API ключ"

    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            'q': city,
            'appid': api_key,
            'units': 'metric',
            'lang': 'ru',
        }
        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 404:
            logger.warning(f"⚠️ Город не найден: {city}")
            return f"Не удалось найти город {city}"

        response.raise_for_status()
        data = response.json()

        temp = round(data['main']['temp'])
        feels_like = round(data['main']['feels_like'])
        humidity = data['main']['humidity']
        wind_speed = round(data['wind']['speed'])
        description = data['weather'][0]['description']

        logger.info(f"✅ Погода получена для города {city}")
        return (
            f"Погода в городе {city}: {description}, "
            f"температура {temp} градусов, ощущается как {feels_like}, "
            f"влажность {humidity} процентов, ветер {wind_speed} метров в секунду"
        )

    except requests.exceptions.ConnectionError:
        logger.error("❌ Нет подключения к интернету")
        return "Не могу получить погоду — нет подключения к интернету"
    except Exception as e:
        logger.error(f"❌ Ошибка получения погоды: {e}")
        return "Не удалось получить данные о погоде"

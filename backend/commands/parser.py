from typing import Optional, Dict, Any
import re


class CommandParser:
    def __init__(self):
        # Паттерны команд
        self.patterns = {
            # Браузер и поиск
            'browser': r'(открой|запусти|включи).*(браузер|chrome|firefox)',
            'search': r'(найди|поищи|гугл|google|search)\s+(.+)',
            'youtube': r'(youtube|ютуб|ютьюб).*(найди|поищи)?\s*(.+)?',
            
            # Приложения
            'app_vscode': r'(открой|запусти|включи).*(vscode|code|visual studio code|vs code)',
            'app_discord': r'(открой|запусти|включи).*(discord|дискорд)',
            'app_telegram': r'(открой|запусти|включи).*(telegram|телеграм)',
            'app_spotify': r'(открой|запусти|включи).*(spotify|спотифай)',
            'app_notepad': r'(открой|запусти|включи).*(notepad|блокнот)',
            'app_calc': r'(открой|запусти|включи).*(калькулятор|calculator|calc)',
            'app_explorer': r'(открой|запусти|включи).*(проводник|explorer|папк)',
            
            # Системные команды
            'time': r'(время|который час|сколько времени)',
            'date': r'(дата|какое число|какой день)',
            'volume_up': r'(прибавь|увеличь|громче|больше).*(звук|громкость)',
            'volume_down': r'(убавь|уменьши|тише|меньше).*(звук|громкость)',
            'volume_mute': r'(отключи|выключи|включи).*(звук|громкость)',
            'screenshot': r'(скриншот|снимок экрана|сделай фото)',
            'lock': r'(заблокируй|залочь).*(компьютер|пк|экран)',
            'shutdown': r'(выключи|вырубай).*(компьютер|пк)',
            
            # Выход
            'exit': r'(выход|стоп|хватит|закрой|выключись)',
        }
    
    def parse(self, text: str) -> Dict[str, Any]:
        """Парсит текст команды и возвращает структуру"""
        text = text.lower().strip()
        
        # Проверяем каждый паттерн
        for command_type, pattern in self.patterns.items():
            match = re.search(pattern, text)
            if match:
                return {
                    'type': command_type,
                    'text': text,
                    'match': match,
                    'groups': match.groups() if match else None
                }
        
        # Если не нашли - неизвестная команда
        return {
            'type': 'unknown',
            'text': text,
            'match': None,
            'groups': None
        }
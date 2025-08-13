import json
import locale
import os
from typing import Dict, Optional


class LocalizationManager:
    """Менеджер локализации для лаунчера"""

    def __init__(self, lang_dir: Optional[str] = None):
        self.lang_dir = lang_dir or os.path.join(os.path.dirname(__file__), "lang")
        self.current_language = "en"  # По умолчанию всегда английский
        self.translations = {}
        self.available_languages = {}
        self._load_available_languages()

    def _load_available_languages(self):
        """Загружает список доступных языков из JSON файлов"""
        if not os.path.exists(self.lang_dir):
            return

        for filename in os.listdir(self.lang_dir):
            if filename.startswith("lang_") and filename.endswith(".json"):
                lang_code = filename[5:-5]  # Убираем "lang_" и ".json"
                lang_path = os.path.join(self.lang_dir, filename)

                try:
                    with open(lang_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        metadata = data.get('metadata', {})

                        self.available_languages[lang_code] = {
                            'name': metadata.get('language_name', lang_code.upper()),
                            'qt_translation': metadata.get('qt_translation', f'qtbase_{lang_code}'),
                            'language': metadata.get('language', lang_code)
                        }
                except Exception as e:
                    print(f"Error loading language file {filename}: {e}")

    def get_available_languages(self) -> Dict[str, str]:
        """Возвращает словарь доступных языков {code: name}"""
        return {code: info['name'] for code, info in self.available_languages.items()}

    def get_qt_translation_name(self, language_code: str) -> str:
        """Возвращает имя Qt перевода для указанного языка"""
        return self.available_languages.get(language_code, {}).get('qt_translation', 'qtbase_en')

    def detect_system_language(self) -> str:
        """Определяет системный язык пользователя"""
        try:
            # Получаем локаль системы
            system_locale = locale.getdefaultlocale()[0]

            if system_locale:
                # Извлекаем код языка (первые 2 символа)
                lang_code = system_locale[:2].lower()

                # Проверяем, есть ли такой язык в доступных
                if lang_code == 'ru' and 'ru' in self.available_languages:
                    return 'ru'
                elif lang_code == 'en' and 'en' in self.available_languages:
                    return 'en'

        except Exception as e:
            print(f"Error detecting system language: {e}")

        # По умолчанию английский
        return 'en'

    def load_language(self, language_code: str) -> bool:
        """Загружает переводы для указанного языка"""
        if language_code not in self.available_languages:
            return False

        lang_file = os.path.join(self.lang_dir, f"lang_{language_code}.json")

        try:
            with open(lang_file, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)
                self.current_language = language_code
                return True
        except Exception as e:
            print(f"Error loading language {language_code}: {e}")
            return False

    def get_text(self, key: str, **kwargs) -> str:
        """Получает переведенный текст по ключу с поддержкой форматирования"""
        # Разбиваем ключ на части (например, "ui.language_label")
        keys = key.split('.')
        value = self.translations

        try:
            for k in keys:
                value = value[k]

            # Убеждаемся что это строка
            if not isinstance(value, str):
                return f"[{key}]"

            # Обрабатываем escape-последовательности
            value = self._process_escape_sequences(value)

            # Если есть параметры для форматирования
            if kwargs:
                return value.format(**kwargs)

            return value
        except (KeyError, TypeError, AttributeError):
            # Если ключ не найден, возвращаем сам ключ как fallback
            return f"[{key}]"

    def _process_escape_sequences(self, text: str) -> str:
        """Обрабатывает escape-последовательности в тексте"""
        if not text:
            return text
        
        # Обрабатываем основные escape-последовательности
        escape_sequences = {
            '\\n': '\n',    # Перевод строки
            '\\t': '\t',    # Табуляция
            '\\r': '\r',    # Возврат каретки
            '\\"': '"',     # Кавычка
            "\\'": "'",     # Апостроф
            '\\\\': '\\'    # Обратный слеш (должен быть последним!)
        }
        
        result = text
        for escape_seq, replacement in escape_sequences.items():
            result = result.replace(escape_seq, replacement)
        
        return result

    def get_current_language(self) -> str:
        """Возвращает текущий язык"""
        return self.current_language

    def get_current_language_name(self) -> str:
        """Возвращает название текущего языка"""
        return self.available_languages.get(self.current_language, {}).get('name', self.current_language.upper())


# Глобальный экземпляр менеджера локализации
_localization_manager = None

def get_localization_manager() -> LocalizationManager:
    """Возвращает глобальный экземпляр менеджера локализации"""
    global _localization_manager
    if _localization_manager is None:
        _localization_manager = LocalizationManager()
        # Загружаем базовую локализацию (русский по умолчанию для инициализации)
        # Это нужно для корректной работы tr() до того как лаунчер настроит язык
        if 'ru' in _localization_manager.available_languages:
            _localization_manager.load_language('ru')
        elif 'en' in _localization_manager.available_languages:
            _localization_manager.load_language('en')
    return _localization_manager

def tr(key: str, **kwargs) -> str:
    """Сокращенная функция для получения переводов"""
    return get_localization_manager().get_text(key, **kwargs)

def init_localization(language_code: Optional[str] = None) -> bool:
    """Инициализирует систему локализации"""
    manager = get_localization_manager()

    if language_code is None:
        # Если язык не указан, используем английский по умолчанию
        language_code = 'en'

    return manager.load_language(language_code)

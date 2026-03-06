# utils/profile_manager.py
import json
import os
from pathlib import Path
from typing import Optional


class ProfileManager:
    """Управление профилями настроек тестов"""
    
    def __init__(self):
        # Системная папка для профилей
        if os.name == 'nt':  # Windows
            base_path = Path(os.environ.get('APPDATA', ''))
        else:  # Linux/Mac
            base_path = Path.home() / '.config'
        
        self.profiles_dir = base_path / 'Psychoanalyst' / 'configs'
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
    
    def get_profile_path(self, profile_name: str) -> Path:
        """Получает путь к файлу профиля"""
        # Очищаем имя от недопустимых символов
        safe_name = "".join(c for c in profile_name if c.isalnum() or c in ' -_').strip()
        return self.profiles_dir / f"{safe_name}.json"
    
    def list_profiles(self) -> list:
        """Возвращает список всех профилей"""
        profiles = []
        if self.profiles_dir.exists():
            for file in self.profiles_dir.glob('*.json'):
                profiles.append(file.stem)  # Имя без .json
        return sorted(profiles)
    
    def save_profile(self, profile_name: str, config: dict) -> bool:
        """Сохраняет профиль"""
        try:
            profile_path = self.get_profile_path(profile_name)
            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Ошибка сохранения профиля: {e}")
            return False
    
    def load_profile(self, profile_name: str) -> Optional[dict]:
        """Загружает профиль"""
        try:
            profile_path = self.get_profile_path(profile_name)
            if not profile_path.exists():
                return None
            with open(profile_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Ошибка загрузки профиля: {e}")
            return None
    
    def delete_profile(self, profile_name: str) -> bool:
        """Удаляет профиль"""
        try:
            profile_path = self.get_profile_path(profile_name)
            if profile_path.exists():
                profile_path.unlink()
                return True
            return False
        except Exception as e:
            print(f"Ошибка удаления профиля: {e}")
            return False
    
    def profile_exists(self, profile_name: str) -> bool:
        """Проверяет существование профиля"""
        profile_path = self.get_profile_path(profile_name)
        return profile_path.exists()
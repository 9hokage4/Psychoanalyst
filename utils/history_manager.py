# utils/history_manager.py
"""
Менеджер истории обработок. Сохраняет метаданные и агрегированные результаты.
"""
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np


class HistoryManager:
    def __init__(self):
        import os
        if os.name == 'nt':
            base = Path(os.environ.get('APPDATA', str(Path.home())))
        else:
            base = Path.home() / '.config'
        self.base_dir = base / 'Psychoanalyst' / 'history'
        print("[DEBUG] History directory:", self.base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.base_dir / "index.json"
        self._load_index()

    def _load_index(self):
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    self.records = json.load(f)
            except Exception as e:
                print(f"Ошибка загрузки индекса: {e}")
                self.records = []
        else:
            self.records = []

    def _save_index(self):
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self.records, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения индекса: {e}")

    def add_record(self, metadata: Dict[str, Any], summary_data: Dict, charts_data: Dict) -> str:
        record_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        record_dir = self.base_dir / record_id
        record_dir.mkdir(exist_ok=True)

        metadata["id"] = record_id
        metadata["timestamp"] = datetime.now().isoformat()

        try:
            with open(record_dir / "metadata.json", 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            summary_json = self._serialize_summary_data(summary_data)
            with open(record_dir / "summary_data.json", 'w', encoding='utf-8') as f:
                json.dump(summary_json, f, ensure_ascii=False)

            charts_json = self._serialize_charts_data(charts_data)
            with open(record_dir / "charts_data.json", 'w', encoding='utf-8') as f:
                json.dump(charts_json, f, ensure_ascii=False)

            self.records.append(metadata)
            self._save_index()
            return record_id
        except Exception as e:
            print(f"Ошибка сохранения записи {record_id}: {e}")
            shutil.rmtree(record_dir, ignore_errors=True)
            return ""

    def _serialize_summary_data(self, summary_data: Dict) -> Dict:
        result = {}
        for key, value in summary_data.items():
            if key in ("group_summary", "course_summary"):
                serialized_groups = {}
                for group_name, group_info in value.items():
                    if isinstance(group_info, dict) and "table" in group_info:
                        table_df = group_info["table"]
                        if isinstance(table_df, pd.DataFrame):
                            df_copy = table_df.copy()
                            df_copy = df_copy.replace({np.nan: None})
                            # Сохраняем как словарь
                            table_dict = json.loads(df_copy.to_json(orient='split', force_ascii=False))
                            serialized_groups[group_name] = {
                                "table": table_dict,
                                "total_respondents": group_info["total_respondents"]
                            }
                        else:
                            serialized_groups[group_name] = group_info
                    else:
                        serialized_groups[group_name] = group_info
                result[key] = serialized_groups
            elif key in ("level_order", "level_ru", "has_group", "has_course"):
                result[key] = value
            elif key == "scales_config":
                result[key] = self._serialize_scales_config(value)
            else:
                try:
                    json.dumps(value)
                    result[key] = value
                except:
                    pass
        return result

    def _serialize_scales_config(self, scales_config: Dict) -> Dict:
        serialized = {}
        for scale_name, scale_info in scales_config.items():
            safe_info = {
                "title_ru": scale_info.get("title_ru", scale_name),
                "qnums": scale_info.get("qnums", []),
                "bounds": scale_info.get("bounds", {})
            }
            serialized[scale_name] = safe_info
        return serialized

    def _serialize_charts_data(self, charts_data: Dict) -> Dict:
        result = {}
        for key, value in charts_data.items():
            if isinstance(value, pd.DataFrame):
                df_copy = value.copy()
                df_copy = df_copy.replace({np.nan: None})
                # Сохраняем как словарь
                result[key] = json.loads(df_copy.to_json(orient='split', force_ascii=False))
            else:
                try:
                    json.dumps(value)
                    result[key] = value
                except:
                    pass
        return result

    def get_all_records(self) -> List[Dict]:
        valid_records = []
        for rec in self.records:
            record_id = rec.get("id")
            if record_id and (self.base_dir / record_id).exists():
                valid_records.append(rec)
        if len(valid_records) != len(self.records):
            self.records = valid_records
            self._save_index()
        return sorted(valid_records, key=lambda x: x.get("timestamp", ""), reverse=True)

    def get_record_data(self, record_id: str) -> Optional[Dict]:
        record_dir = self.base_dir / record_id
        if not record_dir.exists():
            return None

        try:
            with open(record_dir / "summary_data.json", 'r', encoding='utf-8') as f:
                summary_json = json.load(f)
            summary_data = self._deserialize_summary_data(summary_json)

            with open(record_dir / "charts_data.json", 'r', encoding='utf-8') as f:
                charts_json = json.load(f)
            charts_data = self._deserialize_charts_data(charts_json)

            return {
                "summary_data": summary_data,
                "charts_data": charts_data
            }
        except Exception as e:
            print(f"Ошибка загрузки записи {record_id}: {e}")
            return None

    def _deserialize_summary_data(self, data: Dict) -> Dict:
        import json as json_lib
        result = {}
        for key, value in data.items():
            if key in ("group_summary", "course_summary"):
                restored_groups = {}
                for group_name, group_info in value.items():
                    if isinstance(group_info, dict) and "table" in group_info:
                        table_raw = group_info["table"]
                        # Если это строка – парсим JSON
                        if isinstance(table_raw, str):
                            try:
                                table_dict = json_lib.loads(table_raw)
                            except Exception:
                                table_dict = {"data": [], "columns": [], "index": []}
                        else:
                            table_dict = table_raw
                        try:
                            df = pd.DataFrame(
                                data=table_dict.get("data", []),
                                columns=table_dict.get("columns", []),
                                index=table_dict.get("index", [])
                            )
                            restored_groups[group_name] = {
                                "table": df,
                                "total_respondents": group_info["total_respondents"]
                            }
                        except Exception as e:
                            print(f"Ошибка восстановления DataFrame для {group_name}: {e}")
                            restored_groups[group_name] = {
                                "table": pd.DataFrame(),
                                "total_respondents": group_info.get("total_respondents", 0)
                            }
                    else:
                        restored_groups[group_name] = group_info
                result[key] = restored_groups
            elif key == "scales_config":
                result[key] = value
            else:
                result[key] = value
        return result

    def _deserialize_charts_data(self, data: Dict) -> Dict:
        import json as json_lib
        result = {}
        for key, value in data.items():
            # value может быть строкой JSON или уже словарём
            if isinstance(value, str):
                try:
                    value = json_lib.loads(value)
                except Exception:
                    value = {}
            if isinstance(value, dict) and "data" in value:
                try:
                    df = pd.DataFrame(
                        data=value.get("data", []),
                        columns=value.get("columns", []),
                        index=value.get("index", [])
                    )
                    result[key] = df
                except Exception as e:
                    print(f"Ошибка восстановления charts_data[{key}]: {e}")
                    result[key] = pd.DataFrame()
            else:
                result[key] = value if not isinstance(value, str) else pd.DataFrame()
        return result

    def delete_record(self, record_id: str) -> bool:
        record_dir = self.base_dir / record_id
        if not record_dir.exists():
            return False
        try:
            shutil.rmtree(record_dir)
            self.records = [r for r in self.records if r.get("id") != record_id]
            self._save_index()
            return True
        except Exception as e:
            print(f"Ошибка удаления записи {record_id}: {e}")
            return False
    

    def clear_all(self) -> bool:
        try:
            for record in self.records[:]:
                record_id = record.get("id")
                if record_id:
                    record_dir = self.base_dir / record_id
                    if record_dir.exists():
                        shutil.rmtree(record_dir)
            self.records = []
            self._save_index()
            return True
        except Exception as e:
            print(f"Ошибка очистки истории: {e}")
            return False
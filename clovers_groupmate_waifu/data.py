from pydantic import BaseModel
from collections import Counter
from pathlib import Path


class GroupData(BaseModel):
    """
    群数据
    """

    record_couple: dict[str, str] = {}
    """CP记录"""
    record_lock: dict[str, str] = {}
    """CP锁定记录"""
    record_yinpa1: Counter[str] = {}
    """银趴主动记录"""
    record_yinpa0: Counter[str] = {}
    """银趴被动记录"""


class DataBase(BaseModel):
    waifu_data: dict[str, GroupData] = {}
    protect_uids: set = set()
    "保护名单"

    @classmethod
    def load(cls, path: str | Path):
        file = Path(path)
        if file.exists():
            with open(file, "r", encoding="utf8") as f:
                data = cls.model_validate_json(f.read())
        else:
            data = cls()
        return data

    def save(self, path: str | Path):
        Path(path).parent.mkdir(exist_ok=True)
        with open(path, "w", encoding="utf8") as f:
            f.write(self.model_dump_json(indent=4))

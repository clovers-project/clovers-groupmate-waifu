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
    record_yinpa1: Counter[str] = Counter()
    """银趴主动记录"""
    record_yinpa0: Counter[str] = Counter()
    """银趴被动记录"""


class User(BaseModel):
    user_id: str
    nickname: str
    card: str
    avatar: str
    last_sent_time: int = 0
    group_nickname_dict: dict[str, str] = {}

    def group_nickname(self, group_id: str):
        return self.group_nickname_dict.get(group_id) or self.nickname


class DataBase(BaseModel):
    record: dict[str, GroupData] = {}
    protect_uids: set[str] = set()
    "保护名单"
    user_data: dict[str, User] = {}

    def update_nickname(self, user_list: list[User], group_id: str):
        for user in user_list:
            if user.user_id in self.user_data:
                self.user_data[user.user_id].group_nickname_dict[group_id] = user.card
            else:
                user.group_nickname_dict[group_id] = user.card
                self.user_data[user.user_id] = user

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
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf8") as f:
            f.write(self.model_dump_json(indent=4))

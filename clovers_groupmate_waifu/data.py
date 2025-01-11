from pydantic import BaseModel, Field
from collections import Counter
from pathlib import Path
from typing import TypedDict


class MemberInfo(TypedDict):
    group_id: str
    user_id: str
    nickname: str
    card: str
    avatar: str
    last_sent_time: int


class Member(BaseModel):
    """群成员数据"""

    group_id: str
    user_id: str
    nickname: str = ""
    card: str = ""
    avatar: str = ""
    last_sent_time: int = 0

    cp_count: Counter[str] = Counter()
    """成为CP的次数"""
    daycp_count: Counter[str] = Counter()
    """成为日度CP的天数"""
    at_count: Counter[str] = Counter()
    """@对方的次数"""
    today_at_count: Counter[str] = Counter()
    """今日@对方的次数"""

    @property
    def name(self):
        return self.card or self.nickname or self.user_id

    def update(self, info: MemberInfo):
        self.group_id = info["group_id"]
        self.user_id = info["user_id"]
        self.nickname = info["nickname"]
        self.card = info["card"]
        self.avatar = info["avatar"]
        self.last_sent_time = info["last_sent_time"]


class GroupData(BaseModel):
    """
    群数据
    """

    group_id: str
    """群号"""
    members: dict[str, Member] = {}
    """群成员列表"""
    couple: dict[str, str] = {}
    """CP记录"""
    locked_couple: dict[str, str] = {}
    """CP锁定"""
    yinpa1: Counter[str] = Counter()
    """银趴主动记录"""
    yinpa0: Counter[str] = Counter()
    """银趴被动记录"""

    def member(self, user_id: str):
        if user_id not in self.members:
            self.members[user_id] = Member(group_id=self.group_id, user_id=user_id)
        return self.members[user_id]

    def update(self, user_list: list[MemberInfo]):
        """user_list中的用户必须是群组的全部成员"""
        uids = set(set(self.members.keys()))
        uids_in_group = set()
        for user in user_list:
            user_id = user["user_id"]
            uids_in_group.add(user_id)
            self.member(user_id).update(user)
        for user_id in uids.difference(uids_in_group):
            del self.members[user_id]

    def waifu_list(self, last_sent_time: int | float, exclusion: set[str] = set()) -> list[Member]:
        users = []
        for user_id in set(self.members.keys()).difference(exclusion):
            user = self.members[user_id]
            if user.last_sent_time != 0 and user.last_sent_time < last_sent_time:
                continue
            users.append(user)
        return users

    def record_cp(self, user_id: str, cp_id: str):
        self.couple[user_id] = cp_id
        self.member(user_id).cp_count[cp_id] += 1
        self.couple[cp_id] = user_id
        self.member(cp_id).cp_count[user_id] += 1

    def record_lock_cp(self, user_id: str, cp_id: str):
        self.locked_couple[user_id] = cp_id
        self.record_cp(user_id, cp_id)

    def disband(self, user_id: str):
        if user_id not in self.couple:
            return
        waifu_id = self.couple[user_id]
        del self.couple[waifu_id]
        if waifu_id in self.locked_couple:
            del self.locked_couple[waifu_id]
        del self.couple[user_id]
        if user_id in self.locked_couple:
            del self.locked_couple[user_id]

    def in_locking(self, user_id: str):
        waifu_id = self.couple.get(user_id)
        if waifu_id is None:
            return False
        return self.locked_couple.get(user_id) == waifu_id and self.locked_couple.get(waifu_id) == user_id


class DataBase(BaseModel):
    groups: dict[str, GroupData] = {}
    protect_uids: set[str] = set()
    """受保护的uid，相当于被排除使用"""
    file: Path | None = Field(None, exclude=True)

    @classmethod
    def load(cls, path: str | Path):
        file = Path(path)
        if file.exists():
            with open(file, "r", encoding="utf8") as f:
                data = cls.model_validate_json(f.read())
                data.file = file
        else:
            file.parent.mkdir(parents=True, exist_ok=True)
            data = cls(file=file)
        return data

    def save(self):
        assert self.file is not None, "file not set"
        with open(self.file, "w", encoding="utf8") as f:
            f.write(self.model_dump_json(indent=4))

    def group(self, group_id: str):
        if group_id not in self.groups:
            self.groups[group_id] = GroupData(group_id=group_id)
        return self.groups[group_id]

from pydantic import BaseModel, Field
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


class UserInfo(BaseModel):
    group_id: str
    user_id: str
    nickname: str
    card: str
    avatar: str
    last_sent_time: int = 0

    @property
    def name(self):
        return self.nickname or self.card or self.user_id


class User(BaseModel):
    user_id: str
    card: str
    avatar: str
    last_sent_time: int = 0
    group_nickname_dict: dict[str, str] = {}

    def nickname(self, group_id: str):
        return self.group_nickname_dict.get(group_id) or self.card

    @classmethod
    def from_info(cls, info: UserInfo):
        return cls(
            user_id=info.user_id,
            card=info.card,
            avatar=info.avatar,
            last_sent_time=info.last_sent_time,
            group_nickname_dict={info.group_id: info.name},
        )

    def update(self, info: UserInfo):
        self.user_id = info.user_id
        self.card = info.card
        self.avatar = info.avatar
        self.last_sent_time = info.last_sent_time
        self.group_nickname_dict[info.group_id] = info.nickname


class DataBase(BaseModel):
    record: dict[str, GroupData] = {}
    protect_uids: set[str] = set()
    user_data: dict[str, User] = {}
    group_userlist: dict[str, set[str]] = {}
    file: Path | None = Field(None, exclude=True)

    def update(self, user_list: list[UserInfo]):
        """user_list中的用户必须是群组的全部成员"""
        group_userlist: dict[str, set[str]] = {}
        for user_info in user_list:
            user_id = user_info.user_id
            group_userlist.setdefault(user_info.group_id, set()).add(user_id)
            if user_id in self.user_data:
                self.user_data[user_id].update(user_info)
            else:
                self.user_data[user_id] = User.from_info(user_info)
        self.group_userlist.update(group_userlist)

    def waifu_list(self, group_id: str, last_sent_time: int | float, exclusion: set[str] = set()) -> list[User]:
        namelist = self.group_userlist.get(group_id)
        if not namelist:
            return []
        exclusion = exclusion | self.protect_uids

        def condition(user: User):
            if user.user_id in exclusion:
                return False
            if last_sent_time != 0 and user.last_sent_time < last_sent_time:
                return False
            return True

        return [user for user_id in namelist if ((user := self.user_data.get(user_id)) and condition(user))]

    @classmethod
    def load(cls, path: str | Path):
        file = Path(path)
        if file.exists():
            with open(file, "r", encoding="utf8") as f:
                data = cls.model_validate_json(f.read())
                data.file
        else:
            file.parent.mkdir(parents=True, exist_ok=True)
            data = cls(file=file)
        return data

    def save(self):
        assert self.file is not None, "file not set"
        with open(self.file, "w", encoding="utf8") as f:
            f.write(self.model_dump_json(indent=4))

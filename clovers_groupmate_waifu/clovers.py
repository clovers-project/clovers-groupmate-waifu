from clovers.core.plugin import Event as CloversEvent
from pydantic import BaseModel


class User(BaseModel):
    user_id: str
    nickname: str
    avatar: str


class Event:
    def __init__(self, event: CloversEvent):
        self.event: CloversEvent = event

    @property
    def user_id(self) -> str:
        return self.event.kwargs["user_id"]

    @property
    def group_id(self) -> str:
        return self.event.kwargs["group_id"]

    @property
    def nickname(self) -> str:
        return self.event.kwargs["nickname"]

    @property
    def permission(self) -> int:
        return self.event.kwargs["permission"]

    @property
    def to_me(self) -> bool:
        return self.event.kwargs["to_me"]

    @property
    def at(self) -> list[str]:
        return self.event.kwargs["at"]

    @property
    def avatar(self) -> str:
        return self.event.kwargs["avatar"]

    @property
    def group_mamber_info(self) -> list[User]:
        return self.event.kwargs["group_mamber_info"]

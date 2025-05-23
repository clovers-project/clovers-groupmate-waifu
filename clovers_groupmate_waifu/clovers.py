from collections.abc import AsyncGenerator
from io import BytesIO
from clovers import Event as CloversEvent, Result, Plugin
from .data import MemberInfo


class Event:
    def __init__(self, event: CloversEvent):
        self.event: CloversEvent = event

    @property
    def message(self) -> str:
        return self.event.message

    @property
    def user_id(self) -> str:
        return self.event.properties["user_id"]

    @property
    def group_id(self) -> str:
        return self.event.properties["group_id"]

    @property
    def nickname(self) -> str:
        return self.event.properties["nickname"]

    @property
    def permission(self) -> int:
        return self.event.properties["permission"]

    @property
    def to_me(self) -> bool:
        return self.event.properties["to_me"]

    @property
    def at(self) -> list[str]:
        return self.event.properties["at"]

    @property
    def avatar(self) -> str:
        return self.event.properties["avatar"]

    async def group_member_list(self, group_id: str) -> list[MemberInfo]:
        return await self.event.call("group_member_list", group_id)

    async def group_member_info(self, group_id: str, user_id: str) -> MemberInfo:
        return await self.event.call("group_member_info", group_id, user_id)


def build_result(result):
    if isinstance(result, Result):
        return result
    if isinstance(result, str):
        return Result("text", result)
    if isinstance(result, BytesIO):
        return Result("image", result)
    if isinstance(result, list):
        return Result("list", [build_result(seg) for seg in result])
    if isinstance(result, AsyncGenerator):

        async def output():
            async for x in result:
                yield build_result(x)

        return Result("segmented", output())


def create_plugin() -> Plugin:
    return Plugin(build_event=lambda event: Event(event), build_result=build_result)


def at_text_image_result(at: str, text: str, image: bytes | None):
    return Result("list", [Result("at", at), Result("text", text), Result("image", image) if image else Result("text", "None")])


def at_result(user_id: str, result):
    return Result("list", [Result("at", user_id), build_result(result)])

from io import BytesIO
from clovers import EventProtocol, Result, Plugin
from typing import Protocol, Literal, overload
from collections.abc import AsyncGenerator
from .data import MemberInfo


class PropertiesProtocol(Protocol):
    Bot_Nickname: str
    user_id: str
    group_id: str | None
    to_me: bool
    nickname: str
    avatar: str
    group_avatar: str | None
    image_list: list[str]
    permission: int
    at: list[str]


class Event(PropertiesProtocol, EventProtocol, Protocol):
    group_id: str

    @overload
    async def call(self, key: Literal["group_member_list"], group_id: str, /) -> list[MemberInfo]: ...

    @overload
    async def call(self, key: Literal["group_member_info"], group_id: str, user_id: str, /) -> MemberInfo: ...


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
    plugin = Plugin(build_result=build_result)
    plugin.set_protocol("properties", PropertiesProtocol)
    return plugin


def at_text_image_result(at: str, text: str, image: bytes | None):
    return Result("list", [Result("at", at), Result("text", text), Result("image", image) if image else Result("text", "None")])


def at_result(user_id: str, result):
    return Result("list", [Result("at", user_id), build_result(result)])

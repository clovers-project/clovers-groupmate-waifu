from io import BytesIO
from pathlib import Path
from clovers import Result, Plugin
from collections.abc import AsyncGenerator
from clovers_client import Event


async def segmented_output(result: AsyncGenerator):
    async for x in result:
        yield build_result(x)


def build_result(result):
    match result:
        case Result():
            return result
        case str():
            return Result("text", result)
        case bytes() | Path() | BytesIO():
            return Result("image", result)
        case list():
            return Result("list", [build_result(seg) for seg in result if seg])
        case AsyncGenerator():
            return Result("segmented", segmented_output(result))


PLUGIN = Plugin[Event](build_result=build_result)
PLUGIN.require("clovers-apscheduler")
PLUGIN.protocol = Event

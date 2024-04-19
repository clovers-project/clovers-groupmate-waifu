import random
import asyncio
import time
from clovers_apscheduler import scheduler
from pathlib import Path
from io import BytesIO
from collections.abc import AsyncGenerator
from clovers.core.plugin import Plugin, Result
from .clovers import Event
from .data import DataBase, GroupData
from clovers.core.config import config as clovers_config
from .config import Config


from .utils import *

config_key = __package__
config_data = Config.model_validate(clovers_config.get(config_key, {}))
"""主配置类"""
clovers_config[config_key] = config_data.model_dump()


def build_result(result):
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
    return result


waifu_path = Path(config_data.waifu_path)
waifu_data_file = waifu_path / "waifu_data"
waifu_data = DataBase.load(waifu_data_file)

plugin = Plugin(build_event=lambda event: Event(event), build_result=build_result)
if config_data.waifu_reset:

    def reset_data():
        waifu_data.__init__()

else:

    def reset_data():
        for group_data in waifu_data.waifu_data.values():
            group_data.record_yinpa0.clear()
            group_data.record_yinpa1.clear()
            group_data.record_couple = {k: v for k, v in group_data.record_couple.items() if k != v}


scheduler.add_job(reset_data, "cron", hour=0, misfire_grace_time=120)


@plugin.handle({"重置娶群友记录"}, {"permission"})
async def _(event: Event):
    if event.permission != 3:
        return
    reset_data()
    return "娶群友记录已重置"


@plugin.handle({"设置娶群友保护"}, {"permission", "nickname", "user_id", "at", "group_mamber_info"})
async def _(event: Event):
    if not event.at:
        waifu_data.protect_uids.add(event.user_id)
        namelist = event.nickname
    elif event.permission != 3:
        return "保护失败。你无法为其他人设置保护。"
    else:
        waifu_data.protect_uids = waifu_data.protect_uids | set(event.at)
        namelist = "\n".join(user.nickname for user in event.group_mamber_info)
    waifu_data.save(waifu_data_file)
    return f"保护成功！\n保护名单为：\n{namelist}"


@plugin.handle({"解除娶群友保护"}, {"permission", "nickname", "user_id", "at"})
async def _(event: Event):
    if not event.at:
        if event.user_id in waifu_data.protect_uids:
            waifu_data.protect_uids.remove(event.user_id)
            waifu_data.save(waifu_data_file)
            return "解除保护成功！"
        return "你不在保护名单内。"
    elif event.permission != 3:
        return "解除保护失败。你无法为其他人解除保护。"
    else:
        waifu_data.protect_uids = waifu_data.protect_uids & set(event.at)
        return f"解除保护成功！"


@plugin.handle({"查看娶群友保护名单"}, {"user_id", "group_mamber_info"})
async def _(event: Event):
    return "\n".join(user.nickname for user in event.group_mamber_info if user.user_id in waifu_data.protect_uids)


waifu_cd_bye = config_data.waifu_cd_bye
waifu_save = config_data.waifu_save
waifu_reset = config_data.waifu_reset
last_sent_time_filter = config_data.waifu_last_sent_time_filter
HE = config_data.waifu_he
BE = HE + config_data.waifu_be
NTR = config_data.waifu_ntr
yinpa_HE = config_data.yinpa_he
yinpa_BE = yinpa_HE + config_data.yinpa_be
yinpa_CP = config_data.yinpa_cp
yinpa_CP = yinpa_HE if yinpa_CP == 0 else yinpa_CP

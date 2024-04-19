import random
import asyncio
import time
from clovers_apscheduler import scheduler
from pathlib import Path
from io import BytesIO
from collections.abc import AsyncGenerator
from clovers.utils.tools import download_url
from clovers.core.plugin import Plugin, Result
from .clovers import Event
from .data import DataBase, GroupData, User
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

record = waifu_data.record
protect_uids = waifu_data.protect_uids

plugin = Plugin(build_event=lambda event: Event(event), build_result=build_result)
if config_data.waifu_reset:

    def reset_data():
        waifu_data.record.clear()

else:

    def reset_data():
        for group_data in record.values():
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
        protect_uids.add(event.user_id)
        namelist = event.nickname
    elif event.permission != 3:
        return "保护失败。你无法为其他人设置保护。"
    else:
        waifu_data.protect_uids = protect_uids | set(event.at)
        namelist = "\n".join(user.nickname for user in await event.group_mamber_info())
    waifu_data.save(waifu_data_file)
    return f"保护成功！\n保护名单为：\n{namelist}"


@plugin.handle({"解除娶群友保护"}, {"permission", "nickname", "user_id", "at"})
async def _(event: Event):
    if not event.at:
        if event.user_id in protect_uids:
            protect_uids.remove(event.user_id)
            waifu_data.save(waifu_data_file)
            return "解除保护成功！"
        return "你不在保护名单内。"
    elif event.permission != 3:
        return "解除保护失败。你无法为其他人解除保护。"
    else:
        waifu_data.protect_uids = protect_uids & set(event.at)
        return f"解除保护成功！"


@plugin.handle({"查看娶群友保护名单"}, {"user_id", "group_mamber_info"})
async def _(event: Event):
    return "\n".join(user.nickname for user in await event.group_mamber_info() if user.user_id in waifu_data.protect_uids)


happy_end_tips = [
    "好耶~",
    "婚礼？启动！",
    "需要咱主持婚礼吗qwq",
    "不许秀恩爱！",
    "(响起婚礼进行曲♪)",
    "比翼从此添双翅，连理于今有合枝。\n琴瑟和鸣鸳鸯栖，同心结结永相系。",
    "金玉良缘，天作之合，郎才女貌，喜结同心。",
    "繁花簇锦迎新人，车水马龙贺新婚。",
    "乾坤和乐，燕尔新婚。",
    "愿天下有情人终成眷属。",
    "花团锦绣色彩艳，嘉宾满堂话语喧。",
    "火树银花不夜天，春归画栋双栖燕。",
    "红妆带绾同心结，碧树花开并蒂莲。",
    "一生一世两情相悦，三世尘缘四世同喜",
    "玉楼光辉花并蒂，金屋春暖月初圆。",
    "笙韵谱成同生梦，烛光笑对含羞人。",
    "祝你们百年好合,白头到老。",
    "祝你们生八个。",
]


@plugin.handle({"娶群友"}, {"group_id", "user_id", "nickname", "at", "group_mamber_info"})
async def _(event: Event):
    group_id = event.group_id
    record_couple = record.setdefault(group_id, GroupData()).record_couple

    def end(tips: str, avatar: bytes | None):
        return [f"{tips}", BytesIO(avatar) if avatar else "None"]

    if event.at:
        waifu_id = event.at[0]
        if couple_id := record_couple.get(event.user_id):
            waifu = waifu_data.user_data[couple_id]
            avatar = await download_url(waifu.avatar)
            tips = random.choice(happy_end_tips) if couple_id == waifu_id else "你已经有CP了，不许花心哦~"
        elif waifu_id in waifu_data.protect_uids:
            return
        elif waifus_waifu_id := record_couple.get(waifu_id):
            waifus_waifu = waifu_data.user_data[waifus_waifu_id]
            avatar = await download_url(waifus_waifu.avatar)
            return end(f"ta已经名花有主了~\nta的CP：{waifus_waifu.group_nickname(group_id)}", avatar)
    else:
        member = await event.group_mamber_info()
        # 更新一下用户数据库


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

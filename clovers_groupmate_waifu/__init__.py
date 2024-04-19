import random
import asyncio
import time
from clovers_apscheduler import scheduler
from pathlib import Path
from io import BytesIO
from collections.abc import AsyncGenerator, Callable
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
user_data = waifu_data.user_data

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


happy_end_tips = config_data.happy_end_tips
bad_end_tips = config_data.bad_end_tips
waifu_he = config_data.waifu_he
waifu_be = waifu_he + config_data.waifu_be
waifu_ntr = config_data.waifu_ntr
waifu_last_sent_time_filter = config_data.waifu_last_sent_time_filter


@plugin.handle({"娶群友"}, {"group_id", "user_id", "nickname", "avatar", "at", "group_mamber_info"})
async def _(event: Event):
    group_id = event.group_id
    user_id = event.user_id
    group_record = record.setdefault(group_id, GroupData())
    record_couple = group_record.record_couple
    record_lock = group_record.record_lock

    def end(tips: str, avatar: bytes | None):
        return [tips, BytesIO(avatar) if avatar else "None"]

    if event.at:
        waifu_id = event.at[0]
        if couple_id := record_couple.get(user_id):
            waifu = user_data[couple_id]
            if couple_id == waifu_id:
                tips = random.choice(happy_end_tips)
                record_lock[user_id] = couple_id
            else:
                tips = "你已经有CP了，不许花心哦~"
            avatar = await download_url(waifu.avatar)
            return end(f"{tips}\n你的CP：{waifu.group_nickname(group_id)}", avatar)
        elif waifu_id in waifu_data.protect_uids:
            return
        elif waifus_waifu_id := record_couple.get(waifu_id):
            waifus_waifu = user_data[waifus_waifu_id]
            avatar = await download_url(waifus_waifu.avatar)
            return end(f"ta已经名花有主了~\nta的CP：{waifus_waifu.group_nickname(group_id)}", avatar)
        else:
            randvalue = random.randint(1, 100)
            if randvalue <= waifu_he:
                waifu_data.update_nickname(await event.group_mamber_info(), group_id)
                waifu = waifu_data.user_data[waifu_id]
                avatar = await download_url(waifu.avatar)
                record_lock[user_id] = waifu_id
                record_couple[user_id] = waifu_id
                record_couple[waifu_id] = user_id
                return end(f"恭喜你娶到了群友：{waifu.group_nickname(group_id)}", avatar)
            elif randvalue <= waifu_be:
                record_couple[user_id] = user_id
            avatar = await download_url(event.avatar)
            return end(f"{random.choice(bad_end_tips)}\n恭喜你娶到了你自己。", avatar)
    else:
        if couple_id := record_couple.get(user_id):
            waifu = user_data[couple_id]
            if couple_id == waifu_id:
                tips = random.choice(happy_end_tips)
                record_lock[user_id] = couple_id
            else:
                tips = "你已经有CP了，不许花心哦~"
            avatar = await download_url(waifu.avatar)
            return end(f"{tips}\n你的CP：{waifu.group_nickname(group_id)}", avatar)

        # 更新储存的用户名
        waifu_data.update_nickname(await event.group_mamber_info(), group_id)
        last_time = time.time() - waifu_last_sent_time_filter
        exclusion = set(record_couple.keys()) | protect_uids

        def condition(user: User):
            last_sent_time = user.last_sent_time
            if last_sent_time != 0 and last_sent_time < last_time:
                return False
            if user.user_id in exclusion:
                return False
            return True

        waifu_id = random.choice([user_id for user_id, user in user_data.items() if condition(user)])


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

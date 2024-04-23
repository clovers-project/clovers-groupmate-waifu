import random
import time
from clovers_apscheduler import scheduler
from pathlib import Path
from io import BytesIO
from collections.abc import AsyncGenerator
from clovers.utils.tools import download_url
from clovers.utils.linecard import linecard_to_png, FontManager
from clovers.core.plugin import Plugin, Result
from .clovers import Event
from .data import DataBase, GroupData, User
from clovers.core.config import config as clovers_config
from .config import Config

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
waifu_data_file = waifu_path / "waifu_data.json"
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


@plugin.handle({"设置娶群友保护"}, {"permission", "nickname", "user_id", "at", "group_member_list"})
async def _(event: Event):
    if not event.at:
        protect_uids.add(event.user_id)
        namelist = event.nickname
    elif event.permission != 3:
        return "保护失败。你无法为其他人设置保护。"
    else:
        waifu_data.protect_uids = protect_uids | set(event.at)
        namelist = "\n".join(user.nickname for user in await event.group_member_list())
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


@plugin.handle({"查看娶群友保护名单"}, {"user_id", "group_member_list"})
async def _(event: Event):
    return "\n".join(user.nickname for user in await event.group_member_list() if user.user_id in waifu_data.protect_uids)


waifu_last_sent_time_filter = config_data.waifu_last_sent_time_filter

fontname = config_data.fontname
fallback = config_data.fallback_fonts

font_manager = FontManager(fontname, fallback, (30, 40, 60))


def text_to_png(text: str):
    return linecard_to_png(text, font_manager, font_size=40, bg_color="white")


def waifu_result(user_id: str | int, tips: str, avatar: bytes | None):

    waifu_data.save(waifu_data_file)
    return [Result("at", user_id), tips, BytesIO(avatar) if avatar else "None"]


happy_end_tips = config_data.happy_end_tips
bad_end_tips = config_data.bad_end_tips
waifu_he = config_data.waifu_he
waifu_be = waifu_he + config_data.waifu_be
waifu_ntr = config_data.waifu_ntr


def waifu_list(exclusion: set[str]):
    last_time = time.time() - waifu_last_sent_time_filter
    exclusion = exclusion | protect_uids

    def condition(user: User):
        last_sent_time = user.last_sent_time
        if user.user_id in exclusion:
            return False
        if last_sent_time != 0 and last_sent_time < last_time:
            return False
        return True

    return [user for user in user_data.values() if condition(user)]


@plugin.handle({"娶群友"}, {"group_id", "user_id", "nickname", "avatar", "at", "group_member_list"})
async def _(event: Event):
    group_id = event.group_id
    user_id = event.user_id
    group_record = record.setdefault(group_id, GroupData())
    record_couple = group_record.record_couple
    record_lock = group_record.record_lock

    if event.at:
        waifu_id = event.at[0]
        couple_id = record_couple.get(user_id)
        if couple_id := record_couple.get(user_id):
            waifu = user_data[couple_id]
            if couple_id == waifu_id:
                tips = random.choice(happy_end_tips)
                record_lock[user_id] = couple_id
            elif user_id not in record_lock and random.randint(1, 100) <= waifu_he:
                del record_lock[couple_id]
                del record_couple[couple_id]
                waifu_data.update_nickname(await event.group_member_list(), group_id)
                waifu = user_data[waifu_id]
                avatar = await download_url(waifu.avatar)
                record_lock[user_id] = waifu_id
                record_couple[user_id] = waifu_id
                record_couple[waifu_id] = user_id
                waifu_data.save(waifu_data_file)
                return waifu_result(user_id, f"恭喜你娶到了群友：{waifu.group_nickname(group_id)}", avatar)
            else:
                tips = "你已经有CP了，不许花心哦~"
            avatar = await download_url(waifu.avatar)
            return waifu_result(user_id, f"{tips}\n你的CP：{waifu.group_nickname(group_id)}", avatar)
        elif waifu_id in waifu_data.protect_uids:
            return
        elif waifus_waifu_id := record_couple.get(waifu_id):
            waifus_waifu = user_data[waifus_waifu_id]
            avatar = await download_url(waifus_waifu.avatar)
            return waifu_result(user_id, f"ta已经名花有主了~\nta的CP：{waifus_waifu.group_nickname(group_id)}", avatar)
        else:
            randvalue = random.randint(1, 100)
            if randvalue <= waifu_he:
                waifu_data.update_nickname(await event.group_member_list(), group_id)
                waifu = user_data[waifu_id]
                avatar = await download_url(waifu.avatar)
                record_lock[user_id] = waifu_id
                record_couple[user_id] = waifu_id
                record_couple[waifu_id] = user_id
                return waifu_result(user_id, f"恭喜你娶到了群友：{waifu.group_nickname(group_id)}", avatar)
            elif randvalue <= waifu_be:
                record_couple[user_id] = user_id
            avatar = await download_url(event.avatar)
            return waifu_result(user_id, f"{random.choice(bad_end_tips)}\n恭喜你娶到了你自己。", avatar)
    else:
        waifu_id = record_couple.get(user_id)
        if not waifu_id:
            waifu_data.update_nickname(await event.group_member_list(), group_id)
            waifu = random.choice(waifu_list(set(record_couple.keys())))
            waifu_id = waifu.user_id
        else:
            waifu = user_data[waifu_id]
        record_couple[user_id] = waifu_id
        record_couple[waifu_id] = user_id
        avatar = await download_url(waifu.avatar)
        return waifu_result(user_id, f"恭喜你娶到了群友：{waifu.group_nickname(group_id)}", avatar)


@plugin.handle({"查看娶群友卡池"}, {"group_id"})
async def _(event: Event):
    group_id = event.group_id
    record_couple = record.setdefault(group_id, GroupData()).record_couple
    waifu_data.update_nickname(await event.group_member_list(), group_id)
    output = ["卡池（前80位）：\n----"]
    namelist = [waifu.group_nickname(group_id) for waifu in waifu_list(set(record_couple.keys()))[:80]]
    if not namelist:
        return "群友已经被娶光了。下次早点来吧。"
    output += namelist
    return text_to_png("\n".join(output))


@plugin.handle({"本群CP", "本群cp"}, {"group_id"})
async def _(event: Event):
    group_id = event.group_id
    record_couple = record.setdefault(group_id, GroupData()).record_couple
    if not record_couple:
        return "本群暂无cp哦~"
    name_pairs = {}
    seen = set()
    for k, v in record_couple.items():
        if k not in seen:
            name_pairs[user_data[k].group_nickname(group_id)] = user_data[v].group_nickname(group_id)
            seen.add(k)
            seen.add(v)
    output = ["本群CP：\n----"]
    output += [f"[color][red]♥ [nowrap]\n{k}|{v}" for k, v in name_pairs.items()]
    return text_to_png("\n".join(output))


@plugin.handle({"透群友"}, {"group_id", "user_id", "at", "group_member_list"})
async def _(event: Event):
    pass


@plugin.handle({"透群友记录", "色色记录", "涩涩记录"}, {"group_id", "user_id", "at", "group_member_list"})
async def _(event: Event):
    pass


__plugin__ = plugin

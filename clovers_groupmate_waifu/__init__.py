import random
import time
from clovers_apscheduler import scheduler
from pathlib import Path
from io import BytesIO
from collections.abc import AsyncGenerator, Callable
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
            group_data.record_couple = {k: v for k, v in group_data.record_couple.items() if k != v}


scheduler.add_job(reset_data, "cron", hour=0, misfire_grace_time=120)


@plugin.handle({"重置娶群友记录"}, {"permission"})
async def _(event: Event):
    if event.permission != 3:
        return
    reset_data()
    return "娶群友记录已重置"


@plugin.handle({"设置娶群友保护"}, {"permission", "nickname", "user_id", "at"}, {"group_member_list"})
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


@plugin.handle({"查看娶群友保护名单"}, {"user_id"}, {"group_member_list"})
async def _(event: Event):
    return "\n".join(user.nickname for user in await event.group_member_list() if user.user_id in waifu_data.protect_uids)


waifu_last_sent_time_filter = config_data.waifu_last_sent_time_filter

fontname = config_data.fontname
fallback = config_data.fallback_fonts

font_manager = FontManager(fontname, fallback, (30, 40, 60))

text_to_png: Callable[[str], BytesIO]
text_to_png = lambda text: linecard_to_png(text, font_manager, font_size=40, bg_color="white")
waifu_result: Callable[[str | int, str, bytes | None], list]
waifu_result = lambda user_id, tips, avatar: [Result("at", user_id), tips, BytesIO(avatar) if avatar else "None"]
locked_check: Callable[[dict[str, str], str, str], bool]
locked_check = lambda lock_data, uid0, uid1: lock_data.get(uid0) == uid1 and lock_data.get(uid1) == uid0


happy_end_tips = config_data.happy_end_tips
bad_end_tips = config_data.bad_end_tips
waifu_he = config_data.waifu_he
waifu_be = waifu_he + config_data.waifu_be
waifu_ntr = config_data.waifu_ntr
waifu_ntr_be = waifu_ntr + config_data.waifu_be


def waifu_list(exclusion: set[str] = set()):
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


@plugin.handle({"娶群友"}, {"group_id", "user_id", "nickname", "avatar", "at"}, {"group_member_list"})
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
                tips = random.choice(happy_end_tips) + "\n你的CP："
                record_lock[user_id] = couple_id
                waifu_data.save(waifu_data_file)
            elif user_id not in record_lock and random.randint(1, 100) <= waifu_he:
                if couple_id in record_lock:
                    del record_lock[couple_id]
                del record_couple[couple_id]
                waifu_data.update_nickname(await event.group_member_list(), group_id)
                waifu = user_data[waifu_id]
                avatar = await download_url(waifu.avatar)
                record_lock[user_id] = waifu_id
                record_couple[user_id] = waifu_id
                record_couple[waifu_id] = user_id
                waifu_data.save(waifu_data_file)
                tips = "恭喜你娶到了群友！"
            else:
                tips = "你已经有CP了，不许花心哦~\n你的CP："
            tips += waifu.group_nickname(group_id)
        elif waifu_id in waifu_data.protect_uids:
            return
        elif waifus_waifu_id := record_couple.get(waifu_id):
            waifu = user_data[waifus_waifu_id]
            tips = f"ta已经名花有主了~\nta的CP：{waifu.group_nickname(group_id)}"
            if not locked_check(record_lock, waifus_waifu_id, waifu_id):
                randvalue = random.randint(1, 100)
                if randvalue <= waifu_ntr:
                    waifu = user_data[waifu_id]
                    tips += f"\n但是...\n恭喜你抢到了群友{waifu.group_nickname(group_id)}"
                    if waifus_waifu_id in record_lock:
                        del record_lock[waifus_waifu_id]
                    del record_couple[waifus_waifu_id]
                    record_lock[user_id] = waifu_id
                    record_couple[user_id] = waifu_id
                    record_couple[waifu_id] = user_id
                    waifu_data.save(waifu_data_file)
                elif randvalue <= waifu_ntr_be:
                    record_couple[user_id] = user_id
                    waifu_data.save(waifu_data_file)
                    if user_id in user_data:
                        waifu = user_data[user_id]
                    else:
                        waifu = user_data[user_id] = User(user_id=user_id, nickname=event.nickname, card="", avatar=event.avatar)
                    tips += "不过好消息是...\n你娶到了你自己！"
        else:
            randvalue = random.randint(1, 100)
            waifu_data.update_nickname(await event.group_member_list(), group_id)
            if randvalue <= waifu_he:
                waifu = user_data[waifu_id]
                avatar = await download_url(waifu.avatar)
                record_lock[user_id] = waifu_id
                record_couple[user_id] = waifu_id
                record_couple[waifu_id] = user_id
                waifu_data.save(waifu_data_file)
                tips = f"恭喜你娶到了群友：{waifu.group_nickname(group_id)}"
            elif randvalue <= waifu_be:
                record_couple[user_id] = user_id
                waifu = user_data[user_id]
                waifu_data.save(waifu_data_file)
                tips = f"{random.choice(bad_end_tips)}\n恭喜你娶到了你自己。"
            else:
                return [Result("at", user_id), f"{random.choice(bad_end_tips)}\n你没有娶到群友。"]
    else:
        waifu_id = record_couple.get(user_id)
        if not waifu_id:
            waifu_data.update_nickname(await event.group_member_list(), group_id)
            waifu = random.choice(waifu_list(set(record_couple.keys())))
            waifu_id = waifu.user_id
            record_couple[user_id] = waifu_id
            record_couple[waifu_id] = user_id
            waifu_data.save(waifu_data_file)
        else:
            waifu = user_data[waifu_id]
        tips = f"恭喜你娶到了群友：{waifu.group_nickname(group_id)}"
    avatar = await download_url(waifu.avatar)
    return waifu_result(user_id, tips, avatar)


@plugin.handle({"离婚", "分手"}, {"group_id", "user_id", "to_me"})
async def _(event: Event):
    if not event.to_me:
        return
    group_id = event.group_id
    user_id = event.user_id
    group_record = record.setdefault(group_id, GroupData())
    record_couple = group_record.record_couple
    record_lock = group_record.record_lock
    waifu_id = record_couple.get(user_id)
    if not waifu_id or waifu_id == user_id:
        return [Result("at", user_id), "你还没有CP哦"]
    result = [Result("at", user_id), "你们已经是单身了。"]

    if locked_check(record_lock, user_id, waifu_id):

        @plugin.temp_handle(f"分手 {group_id} {user_id}", extra_args={"group_id", "user_id"})
        async def _(event: Event, finish):
            if event.group_id != group_id or event.user_id != user_id:
                return
            match event.event.raw_command:
                case "确认":
                    del record_lock[user_id]
                    del record_lock[waifu_id]
                    del record_couple[user_id]
                    del record_couple[waifu_id]
                    waifu_data.save(waifu_data_file)
                    finish()
                    return result
                case "取消":
                    finish()
                    return [Result("at", user_id), "祝你们百年好合"]

        return [Result("at", user_id), "你们已经互相锁定了，请问真的要分手吗？【确认 or 取消】"]

    if user_id in record_lock:
        del record_lock[user_id]
    if waifu_id in record_lock:
        del record_lock[waifu_id]
    del record_couple[user_id]
    del record_couple[waifu_id]
    waifu_data.save(waifu_data_file)
    return result


@plugin.handle({"查看娶群友卡池"}, {"group_id"}, {"group_member_list"})
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
    output += [f"[color][red]♥[nowrap]\n {k} | {v}" for k, v in name_pairs.items()]
    return text_to_png("\n".join(output))


yinpa_he = config_data.yinpa_he
yinpa_cp = config_data.yinpa_cp


@plugin.handle({"透群友"}, {"group_id", "user_id", "at"}, {"group_member_list"})
async def _(event: Event):
    group_id = event.group_id
    user_id = event.user_id
    group_record = record.setdefault(group_id, GroupData())
    group_record.record_yinpa1[user_id] += 1
    record_couple = group_record.record_couple
    waifu_id = record_couple.get(user_id)
    if event.at:
        yinpa_id = event.at[0]
        randvalue = yinpa_cp if yinpa_id == waifu_id else yinpa_he
        if random.randint(1, 100) >= randvalue:
            return [Result("at", user_id), "不可以涩涩"]
        yinpa = user_data[yinpa_id]
    else:
        waifu_data.update_nickname(await event.group_member_list(), group_id)
        yinpa = random.choice(waifu_list())
        yinpa_id = yinpa.user_id
    group_record.record_yinpa0[yinpa_id] += 1

    if yinpa_id == waifu_id:
        tips = "恭喜你涩到了你的老婆！"
    elif yinpa_id == user_id:
        tips = "恭喜你涩到了你自己！"
        group_record.record_yinpa0[yinpa_id] -= 1
    else:
        tips = "恭喜你涩到了群友！"
    waifu_data.save(waifu_data_file)
    avatar = await download_url(yinpa.avatar)
    return waifu_result(user_id, f"{tips}\n伱的涩涩对象是、{yinpa.group_nickname(group_id)}", avatar)


@plugin.handle({"透群友记录", "色色记录", "涩涩记录"}, {"group_id", "user_id", "at"}, {"group_member_list"})
async def _(event: Event):
    group_id = event.group_id
    group_record = record.setdefault(group_id, GroupData())
    output = []
    single_result = lambda uid, times: f"[color][red]♥[nowrap]\n {user_data[uid].group_nickname(group_id)}  [nowrap]\n[right]{times} 次"
    record1 = ["透群友记录\n----\n"] + [single_result(k, v) for k, v in group_record.record_yinpa1.items() if v > 1]
    output.append(text_to_png("\n".join(record1)))
    record0 = ["群友被透记录\n----\n"] + [single_result(k, v) for k, v in group_record.record_yinpa0.items() if v > 1]
    output.append(text_to_png("\n".join(record0)))
    return output


__plugin__ = plugin

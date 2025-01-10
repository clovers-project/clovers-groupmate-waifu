import random
import time
from clovers_apscheduler import scheduler
from pathlib import Path
from clovers_utils.tools import download_url
from clovers_utils.linecard import linecard_to_png, FontManager
from clovers.config import config as clovers_config
from .clovers import Event, plugin, at_result, at_text_image_result
from .data import DataBase, GroupData, User
from .config import Config

config_key = __package__
config_data = Config.model_validate(clovers_config.get(config_key, {}))
clovers_config[config_key] = config_data.model_dump()


waifu_path = Path(config_data.waifu_path)
waifu_data = DataBase.load(waifu_path / "waifu_data.json")

record = waifu_data.record
protect_uids = waifu_data.protect_uids
user_data = waifu_data.user_data

if config_data.waifu_reset:

    def reset_data():
        waifu_data.record.clear()

else:

    def reset_data():
        for group_data in record.values():
            group_data.record_couple = {k: v for k, v in group_data.record_couple.items() if k != v}


scheduler.add_job(reset_data, "cron", hour=0, misfire_grace_time=120)


@plugin.handle(["重置娶群友记录"], ["permission"])
async def _(event: Event):
    if event.permission != 3:
        return
    reset_data()
    return "娶群友记录已重置"


@plugin.handle(["设置娶群友保护"], ["permission", "user_id", "at"])
async def _(event: Event):
    if not event.at:
        protect_uids.add(event.user_id)
    elif event.permission != 3:
        return "保护失败。你无法为其他人设置保护。"
    else:
        waifu_data.protect_uids = protect_uids | set(event.at)
    waifu_data.save()
    return "保护成功！"


@plugin.handle(["解除娶群友保护"], ["permission", "nickname", "user_id", "at"])
async def _(event: Event):
    if not event.at:
        if event.user_id in protect_uids:
            protect_uids.remove(event.user_id)
            waifu_data.save()
            return "解除保护成功！"
        return "你不在保护名单内。"
    elif event.permission != 3:
        return "解除保护失败。你无法为其他人解除保护。"
    else:
        waifu_data.protect_uids = protect_uids & set(event.at)
        return f"解除保护成功！"


@plugin.handle(["查看娶群友保护名单"], ["group_id"])
async def _(event: Event):
    group_userlist = waifu_data.group_userlist.get(event.group_id)
    if not group_userlist:
        return "该群无保护名单。"
    namelist = [user.nickname(event.group_id) for user_id in group_userlist if (user := waifu_data.user_data.get(user_id))]
    return "\n".join(namelist)


waifu_last_sent_time_filter = config_data.waifu_last_sent_time_filter

fontname = config_data.fontname
fallback = config_data.fallback_fonts

font_manager = FontManager(fontname, fallback, (30, 40, 60))


def text_to_png(text: str):
    return linecard_to_png(text, font_manager, font_size=40, bg_color="white")


def locked_check(lock_data: dict[str, str], uid0: str, uid1: str):
    return lock_data.get(uid0) == uid1 and lock_data.get(uid1) == uid0


happy_end_tips = config_data.happy_end_tips
bad_end_tips = config_data.bad_end_tips
waifu_he = config_data.waifu_he
waifu_be = waifu_he + config_data.waifu_be
waifu_ntr = config_data.waifu_ntr
waifu_ntr_be = waifu_ntr + config_data.waifu_be


@plugin.handle(["娶群友"], ["group_id", "user_id", "nickname", "at", "avatar"])
async def _(event: Event):
    group_id = event.group_id
    user_id = event.user_id
    group_record = record.setdefault(group_id, GroupData())
    record_couple = group_record.record_couple
    record_lock = group_record.record_lock
    couple_id = record_couple.get(user_id)
    if couple_id == user_id:
        return at_result(user_id, f"{random.choice(bad_end_tips)}\n你没有娶到群友。")
    if event.at:  # 如果 at了别的群友
        waifu_id = event.at[0]
        if couple_id:  # 判断自己是否有 CP
            if couple_id == waifu_id:  # 如果 at 到自己的 CP：HE
                record_lock[user_id] = couple_id
                waifu_data.save(waifu_data_file)
                waifu = user_data[couple_id]
                waifu_info = await event.group_member_info(group_id, waifu_id)
                waifu.update(waifu_info)
                return at_text_image_result(
                    user_id,
                    f"{random.choice(happy_end_tips)}\n你的CP：{waifu_info.name}",
                    await download_url(waifu.avatar),
                )
            elif user_id not in record_lock:  # 如果自己未主动锁定对方
                if random.randint(1, 100) > waifu_he:
                    return at_result(user_id, f"{random.choice(bad_end_tips)}\n你没有娶到群友。")
                if couple_id in record_lock:
                    del record_lock[couple_id]
                del record_couple[couple_id]
                record_lock[user_id] = waifu_id
                record_couple[user_id] = waifu_id
                record_couple[waifu_id] = user_id
                waifu_info = await event.group_member_info(group_id, waifu_id)
                if waifu_id in user_data:
                    waifu = user_data[waifu_id]
                    waifu.update(waifu_info)
                else:
                    waifu = user_data[waifu_id] = User.from_info(waifu_info)
                waifu_data.save(waifu_data_file)
                return at_text_image_result(
                    user_id,
                    f"恭喜你娶到了群友！\n【{waifu_info.name}】",
                    await download_url(waifu.avatar),
                )
            else:
                waifu = user_data[couple_id]
                return at_text_image_result(
                    user_id,
                    f"你已经有CP了，不许花心哦~\n你的CP：{waifu.nickname(group_id)}\n",
                    await download_url(waifu.avatar),
                )
        elif waifu_id in waifu_data.protect_uids:  # 如果对方在保护列表
            return
        elif waifus_waifu_id := record_couple.get(waifu_id):  # 如果对方有 CP 记录
            if waifus_waifu_id == waifu_id:  # 对方被锁定单身立即配对
                record_lock[user_id] = waifu_id
                record_couple[user_id] = waifu_id
                record_couple[waifu_id] = user_id
                waifu = user_data[waifu_id]
                waifu_info = await event.group_member_info(group_id, waifu_id)
                waifu.update(waifu_info)
                waifu_data.save(waifu_data_file)
                return at_text_image_result(
                    user_id,
                    f"恭喜你娶到了群友！\n【{waifu_info.name}】",
                    await download_url(waifu.avatar),
                )
            waifus_waifu = user_data[waifus_waifu_id]
            tips = f"ta已经名花有主了~\nta的CP：{waifus_waifu.nickname(group_id)}"
            if locked_check(record_lock, waifus_waifu_id, waifu_id):  # 对方在 CP 锁定则不可配对
                return at_text_image_result(user_id, tips, await download_url(waifus_waifu.avatar))
            randvalue = random.randint(1, 100)
            if randvalue > waifu_ntr_be:  # ntr NE
                return at_text_image_result(user_id, tips, await download_url(waifus_waifu.avatar))
            if randvalue <= waifu_ntr:  # ntr HE
                waifu_info = await event.group_member_info(group_id, waifu_id)
                waifu = user_data[waifu_id]
                waifu.update(waifu_info)
                tips += f"\n但是...\n恭喜你抢到了群友{waifu_info.name}"
                if waifus_waifu_id in record_lock:
                    del record_lock[waifus_waifu_id]
                del record_couple[waifus_waifu_id]
                record_lock[user_id] = waifu_id
                record_couple[user_id] = waifu_id
                record_couple[waifu_id] = user_id
                waifu_data.save(waifu_data_file)
                return at_text_image_result(user_id, tips, await download_url(waifu.avatar))
            else:  # ntr BE
                record_couple[user_id] = user_id
                waifu_data.save(waifu_data_file)
                if user_id in user_data:
                    waifu = user_data[user_id]
                    waifu.group_nickname_dict[group_id] = event.nickname
                    waifu.last_sent_time = int(time.time())
                else:
                    waifu = user_data[user_id] = User(
                        user_id=user_id,
                        card=event.nickname,
                        avatar=event.avatar,
                        last_sent_time=int(time.time()),
                        group_nickname_dict={group_id: event.nickname},
                    )
                tips += "不过好消息是...\n你娶到了你自己！"
                return at_text_image_result(user_id, tips, await download_url(event.avatar))
        else:
            randvalue = random.randint(1, 100)
            if randvalue <= waifu_he:  # 成功指定
                waifu_info = await event.group_member_info(group_id, waifu_id)
                if waifu_id in user_data:
                    waifu = user_data[waifu_id]
                else:
                    waifu = user_data[waifu_id] = User.from_info(waifu_info)
                record_lock[user_id] = waifu_id
                record_couple[user_id] = waifu_id
                record_couple[waifu_id] = user_id
                waifu_data.save(waifu_data_file)
                return at_text_image_result(
                    user_id,
                    f"恭喜你娶到了群友！\n【{waifu_info.name}】",
                    await download_url(waifu.avatar),
                )
            elif randvalue <= waifu_be:  # 锁定单身
                record_couple[user_id] = user_id
                if user_id not in user_data:
                    user_data[user_id] = User(
                        user_id=user_id,
                        card=event.nickname,
                        avatar=event.avatar,
                        last_sent_time=int(time.time()),
                        group_nickname_dict={group_id: event.nickname},
                    )
                waifu_data.save(waifu_data_file)
                return at_text_image_result(
                    user_id,
                    f"{random.choice(bad_end_tips)}\n恭喜你娶到了你自己。",
                    await download_url(event.avatar),
                )
            else:  # 失败
                return at_result(user_id, f"{random.choice(bad_end_tips)}\n你没有娶到群友。")
    if not couple_id:
        waifu_data.update(await event.group_member_list(group_id))
        waifu = random.choice(waifu_data.waifu_list(group_id, time.time() - waifu_last_sent_time_filter, set(record_couple.keys())))
        waifu_id = waifu.user_id
        record_couple[user_id] = waifu_id
        record_couple[waifu_id] = user_id
        waifu_data.save()
    else:
        waifu = user_data[couple_id]
    return at_text_image_result(
        user_id,
        f"恭喜你娶到了群友：{waifu.nickname(group_id)}",
        await download_url(waifu.avatar),
    )


def to_me(event: Event):
    return event.to_me


@plugin.handle(["离婚", "分手"], ["group_id", "user_id", "to_me"], rule=to_me)
async def _(event: Event):
    group_id = event.group_id
    user_id = event.user_id
    group_record = record.setdefault(group_id, GroupData())
    record_couple = group_record.record_couple
    record_lock = group_record.record_lock
    waifu_id = record_couple.get(user_id)
    if not waifu_id or waifu_id == user_id:
        return at_result(user_id, "你还没有CP哦")

    if locked_check(record_lock, user_id, waifu_id):

        def authn(event: Event):
            return event.group_id == group_id and event.group_id == group_id

        @plugin.temp_handle(f"分手 {group_id} {user_id}", ["group_id", "user_id"], rule=authn)
        async def _(event: Event, finish):
            match event.command:
                case "确认":
                    del record_lock[user_id]
                    del record_lock[waifu_id]
                    del record_couple[user_id]
                    del record_couple[waifu_id]
                    waifu_data.save()
                    finish()
                    return at_result(user_id, "你们已经是单身了。")
                case "取消":
                    finish()
                    return at_result(user_id, "你们要幸福哦~")

        return at_result(user_id, "你们已经互相锁定了，请问真的要分手吗？【确认 or 取消】")

    if user_id in record_lock:
        del record_lock[user_id]
    if waifu_id in record_lock:
        del record_lock[waifu_id]
    del record_couple[user_id]
    del record_couple[waifu_id]
    waifu_data.save()
    return at_result(user_id, "你们已经是单身了。")


@plugin.handle(["查看娶群友卡池"], ["group_id"])
async def _(event: Event):
    group_id = event.group_id
    record_couple = record.setdefault(group_id, GroupData()).record_couple
    output = ["卡池（前80位）：\n----"]
    waifus = [waifu for waifu in waifu_data.waifu_list(group_id, time.time() - waifu_last_sent_time_filter, set(record_couple.keys()))]
    waifus.sort(key=lambda waifu: waifu.last_sent_time, reverse=True)
    namelist = [waifu.nickname(group_id) for waifu in waifus[:80]]
    if not namelist:
        return "群友已经被娶光了。下次早点来吧。"
    output += namelist
    return text_to_png("\n".join(output))


@plugin.handle(["本群CP", "本群cp"], ["group_id"])
async def _(event: Event):
    group_id = event.group_id
    record_couple = record.setdefault(group_id, GroupData()).record_couple
    if not record_couple:
        return "本群暂无cp哦~"
    name_pairs = {}
    seen = set()
    for k, v in record_couple.items():
        if k not in seen:
            name_pairs[user_data[k].nickname(group_id)] = user_data[v].nickname(group_id)
            seen.add(k)
            seen.add(v)
    output = ["本群CP：\n----"]
    output += [f"[color][red]♥[nowrap]\n {k} | {v}" for k, v in name_pairs.items()]
    return text_to_png("\n".join(output))


yinpa_he = config_data.yinpa_he
yinpa_cp = config_data.yinpa_cp


@plugin.handle(["透群友"], ["group_id", "user_id", "at"])
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
            return at_result(user_id, "不可以涩涩")
        yinpa = user_data[yinpa_id]
    else:
        waifu_data.update(await event.group_member_list(group_id))
        yinpa = random.choice(waifu_data.waifu_list(group_id, time.time() - waifu_last_sent_time_filter, set(record_couple.keys())))
        yinpa_id = yinpa.user_id
    group_record.record_yinpa0[yinpa_id] += 1
    if yinpa_id == waifu_id:
        tips = "恭喜你涩到了你的老婆！"
    elif yinpa_id == user_id:
        tips = "恭喜你涩到了你自己！"
        group_record.record_yinpa0[yinpa_id] -= 1
    else:
        tips = "恭喜你涩到了群友！"
    waifu_data.save()
    return at_text_image_result(user_id, f"{tips}\n伱的涩涩对象是、{yinpa.nickname(group_id)}", await download_url(yinpa.avatar))


@plugin.handle(["透群友记录", "色色记录", "涩涩记录"], ["group_id", "user_id", "at"])
async def _(event: Event):
    group_id = event.group_id
    group_record = record.setdefault(group_id, GroupData())
    output = []
    single_result = lambda uid, times: f"[color][red]♥[nowrap]\n {user_data[uid].nickname(group_id)}  [nowrap]\n[right]{times} 次"
    record1 = ["透群友记录\n----\n"] + [single_result(k, v) for k, v in group_record.record_yinpa1.items() if v > 1]
    output.append(text_to_png("\n".join(record1)))
    record0 = ["群友被透记录\n----\n"] + [single_result(k, v) for k, v in group_record.record_yinpa0.items() if v > 1]
    output.append(text_to_png("\n".join(record0)))
    return output


__plugin__ = plugin

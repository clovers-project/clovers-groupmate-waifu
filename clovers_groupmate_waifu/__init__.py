import random
import time
import asyncio
from clovers_apscheduler import scheduler
from pathlib import Path
from clovers_utils.tools import download_url
from .clovers import Event, plugin, at_result, at_text_image_result
from .data import Member, DataBase
from .config import waifu_config
from .output import draw_couple, draw_list, draw_sese

waifu_data = DataBase.load(Path(waifu_config.waifu_path) / "waifu_data.json")

groups = waifu_data.groups
protect_uids = waifu_data.protect_uids

if waifu_config.waifu_reset:

    def reset_data():
        for group in groups.values():
            for self_id, waifu_id in group.couple.items():
                member = group.member(self_id)
                member.daycp_count[waifu_id] += 1
                member.today_at_count.clear()
            group.couple.clear()
            group.locked_couple.clear()
        waifu_data.save()

else:

    def reset_data():
        for group in groups.values():
            for self_id, waifu_id in group.couple.items():
                member = group.member(self_id)
                member.daycp_count[waifu_id] += 1
                member.today_at_count.clear()
            group.couple = {k: v for k, v in group.couple.items() if k != v}
        waifu_data.save()


scheduler.add_job(reset_data, "cron", hour=0, misfire_grace_time=120)

if waifu_config.at_listen:

    def has_at(event: Event):
        return bool(event.at)

    @plugin.handle(None, ["group_id", "user_id", "at"], rule=has_at)
    async def _(event: Event):
        group_id = event.group_id
        user_id = event.user_id
        member = waifu_data.group(group_id).member(user_id)
        for uid in event.at:
            member.at_count[uid] += 1
            member.today_at_count[uid] += 1


def superusers(event: Event):
    return event.permission == 3


@plugin.handle(["重置娶群友记录"], ["permission"], rule=superusers)
async def _(event: Event):
    reset_data()
    return "娶群友记录已重置"


@plugin.handle(["设置娶群友保护"], ["permission", "user_id", "at"])
async def _(event: Event):
    if not event.at:
        protect_uids.add(event.user_id)
    elif superusers(event):
        waifu_data.protect_uids.update(event.at)
    else:
        return "保护失败。你无法为其他人设置保护。"
    waifu_data.save()
    return "保护成功！"


@plugin.handle(["解除娶群友保护"], ["permission", "nickname", "user_id", "at"])
async def _(event: Event):
    if not event.at:
        if event.user_id in protect_uids:
            protect_uids.remove(event.user_id)
        else:
            return "你不在保护名单内。"
    elif superusers(event):
        protect_uids.difference_update(event.at)
    else:
        return "解除保护失败。你无法为其他人解除保护。"
    waifu_data.save()
    return f"解除保护成功！"


@plugin.handle(["查看娶群友保护名单"], ["group_id"])
async def _(event: Event):
    group = groups.get(event.group_id)
    if not group:
        return "该群无记录。"
    uids = protect_uids & set(group.members.keys())
    if not uids:
        return "该群无保护名单。"
    return "\n".join(f"{group.member(user_id).name} {user_id}" for user_id in uids)


waifu_last_sent_time_filter = waifu_config.waifu_last_sent_time_filter

happy_end_tips = waifu_config.happy_end_tips
bad_end_tips = waifu_config.bad_end_tips

waifu_he = waifu_config.waifu_he
waifu_be = waifu_he + waifu_config.waifu_be
waifu_ntr = waifu_config.waifu_ntr
waifu_ntr_be = waifu_ntr + waifu_config.waifu_be


def statistic(member: Member, waifu: Member):
    yield f"你们成为CP的次数{member.cp_count[waifu.user_id]}"
    yield f"你们成为日度CP的天数{member.daycp_count[waifu.user_id]}"
    at_count = member.at_count[waifu.user_id]
    if at_count > 0:
        yield f"你今天@ta{member.today_at_count[waifu.user_id]}次，总计@ta{at_count}次"
    be_at_count = waifu.at_count[member.user_id]
    if be_at_count > 0:
        yield f"ta今天@你{waifu.today_at_count[member.user_id]}次，总计@你{be_at_count}次"


@plugin.handle(["娶群友"], ["group_id", "user_id", "at", "avatar"])
async def _(event: Event):
    group_id = event.group_id
    user_id = event.user_id
    group = waifu_data.group(group_id)
    couple_id = group.couple.get(user_id)
    if couple_id == user_id:  # 如果自己被锁定单身，直接进入 BE
        return at_result(user_id, f"{random.choice(bad_end_tips)}\n你今天娶不到群友了。")
    if event.at and (waifu_id := event.at[0]) != user_id:  # 如果 at 了别的群友
        if couple_id:  # 在自己有 CP 的情况下
            if couple_id == waifu_id:  # 如果 at 到自己的 CP 直接进入 HE
                group.locked_couple[user_id] = couple_id
                waifu = group.member(couple_id)
                waifu.update(await event.group_member_info(group_id, couple_id))
                member = group.member(user_id)
                waifu_data.save()
                message = [f"你们已经是CP了哦~\n你的CP是【{waifu.name}】"]
                message.extend(statistic(member, waifu))
                message.append(random.choice(happy_end_tips))
                return at_text_image_result(user_id, "\n".join(message), await download_url(waifu.avatar))
            elif user_id not in group.locked_couple:  # 如果自己未主动锁定自己现在的 CP 则进入指定判定
                randvalue = random.randint(1, 100)
                if randvalue <= waifu_he:  # 成功指定
                    group.record_lock_cp(user_id, waifu_id)
                    waifu = group.member(waifu_id)
                    waifu.update(await event.group_member_info(group_id, waifu_id))
                    waifu_data.save()
                    return at_text_image_result(user_id, f"恭喜你娶到了群友！\n【{waifu.name}】", await download_url(waifu.avatar))
                elif randvalue <= waifu_be:  # 锁定单身
                    group.couple[user_id] = user_id
                    group.member(user_id).cp_count[user_id] += 1
                    waifu_data.save()
                    return at_text_image_result(
                        user_id,
                        random.choice(bad_end_tips) + "\n恭喜你娶到了你自己。",
                        await download_url(event.avatar),
                    )
                else:  # 失败指定
                    return at_result(user_id, f"{random.choice(bad_end_tips)}\n你没有娶到群友。")
            else:  # 如果自己主动锁定了自己现在的 CP，则不允许再配对
                waifu = group.member(couple_id)
                return at_text_image_result(
                    user_id,
                    f"你已经有CP了，不许花心哦~\n你的CP：【{waifu.name}】\n",
                    await download_url(waifu.avatar),
                )
        elif waifus_waifu_id := group.couple.get(waifu_id):  # 如果对方有 CP 记录
            if waifus_waifu_id == waifu_id:  # 对方被锁定单身立即配对
                group.record_lock_cp(user_id, waifu_id)
                waifu = group.member(waifu_id)
                waifu.update(await event.group_member_info(group_id, waifu_id))
                waifu_data.save()
                return at_text_image_result(user_id, f"恭喜你娶到了群友！\n【{waifu.name}】", await download_url(waifu.avatar))
            waifus_waifu = group.member(waifus_waifu_id)
            tips = f"ta已经名花有主了~\nta的CP：{waifus_waifu.name}"
            # 对方在 CP 锁定则不可配对 or 触发 NTR NE 判定
            if group.in_locking(waifu_id) or ((randvalue := random.randint(1, 100)) > waifu_ntr_be):
                return at_text_image_result(user_id, tips, await download_url(waifus_waifu.avatar))
            if randvalue <= waifu_ntr:  # 触发 NTR HE 判定
                group.disband(waifu_id)
                waifu = group.member(waifu_id)
                waifu.update(await event.group_member_info(group_id, waifu_id))
                group.record_lock_cp(user_id, waifu_id)
                waifu_data.save()
                tips += f"\n但是...\n恭喜你抢到了群友{waifu.name}"
                return at_text_image_result(user_id, tips, await download_url(waifu.avatar))
            else:  # 触发 NTR BE 判定
                group.couple[user_id] = user_id
                group.member(user_id).cp_count[user_id] += 1
                waifu_data.save()
                tips += "不过好消息是...\n你娶到了你自己！"
                return at_text_image_result(user_id, tips, await download_url(event.avatar))
        else:  # 双方都没有 CP 记录,进入指定判定
            randvalue = random.randint(1, 100)
            if randvalue <= waifu_he:  # 成功指定
                group.record_lock_cp(user_id, waifu_id)
                waifu = group.member(waifu_id)
                waifu.update(await event.group_member_info(group_id, waifu_id))
                waifu_data.save()
                return at_text_image_result(user_id, f"恭喜你娶到了群友！\n【{waifu.name}】", await download_url(waifu.avatar))
            elif randvalue <= waifu_be:  # 锁定单身
                group.couple[user_id] = user_id
                group.member(user_id).cp_count[user_id] += 1
                waifu_data.save()
                return at_text_image_result(
                    user_id,
                    random.choice(bad_end_tips) + "\n恭喜你娶到了你自己。",
                    await download_url(event.avatar),
                )
            else:  # 失败指定
                return at_result(user_id, f"{random.choice(bad_end_tips)}\n你没有娶到群友。")
    else:  # 如果没有 at 其他群友
        if couple_id:  # 自己有 CP 记录，直接配对到 CP，否则随机配对
            waifu = group.member(couple_id)
        else:
            group.update(await event.group_member_list(group_id))
            waifu_list = group.waifu_list(time.time() - waifu_last_sent_time_filter, set(group.couple.keys()))
            if waifu_list:
                waifu = random.choice(waifu_list)
                group.record_cp(user_id, waifu.user_id)
            else:
                return at_result(user_id, f"{random.choice(bad_end_tips)}\n群友已经全部配对了，下次早点来吧~")
            waifu_data.save()
        return at_text_image_result(user_id, f"恭喜你娶到了群友：【{waifu.name}】", await download_url(waifu.avatar))


def to_me(event: Event):
    return event.to_me


@plugin.handle(["离婚", "分手"], ["group_id", "user_id", "to_me"], rule=to_me)
async def _(event: Event):
    group_id = event.group_id
    user_id = event.user_id
    group = waifu_data.group(group_id)
    waifu_id = group.couple.get(user_id)
    if not waifu_id or waifu_id == user_id:
        return at_result(user_id, "你还没有CP哦")

    if group.in_locking(user_id):

        def authn(event: Event):
            return event.group_id == group_id and event.user_id == user_id

        @plugin.temp_handle(f"分手 {group_id} {user_id}", ["group_id", "user_id"], rule=authn)
        async def _(event: Event, finish):
            match event.command:
                case "确认":
                    group.disband(user_id)
                    waifu_data.save()
                    finish()
                    return at_result(user_id, "你们已经是单身了。")
                case "取消":
                    finish()
                    return at_result(user_id, "你们要幸福哦~")

        return at_result(user_id, "你们已经互相锁定了，请问真的要分手吗？【确认 or 取消】")
    group.disband(user_id)
    waifu_data.save()
    return at_result(user_id, "你们已经是单身了。")


@plugin.handle(["查看娶群友卡池"], ["group_id"])
async def _(event: Event):
    group_id = event.group_id
    group = waifu_data.group(group_id)
    waifus = [waifu for waifu in group.waifu_list(time.time() - waifu_last_sent_time_filter, set(group.couple.keys()))]
    if not waifus:
        return "群友已经被娶光了。下次早点来吧。"
    waifus.sort(key=lambda waifu: waifu.last_sent_time, reverse=True)
    urls = []
    texts: list[str] = []
    for waifu in waifus[:20]:
        urls.append(waifu.avatar)
        texts.append(waifu.name or "UNDEFINED")
    avatars = await asyncio.gather(*map(download_url, urls))
    return draw_list("群友卡池[font size = 30,color = gray]（前20位）", list(zip(avatars, texts)))


@plugin.handle(["本群CP", "本群cp"], ["group_id"])
async def _(event: Event):
    group_id = event.group_id
    group = waifu_data.group(group_id)
    if not group.couple:
        return "本群暂无cp哦~"
    seen = set()
    p1_names: list[str] = []
    p1_avatar_urls: list[str] = []
    p0_names: list[str] = []
    p0_avatar_urls: list[str] = []

    for uid1, uid0 in group.couple.items():
        if uid1 not in seen:
            p1 = group.member(uid1)
            p1_names.append(p1.name)
            p1_avatar_urls.append(p1.avatar)
            p0 = group.member(uid0)
            p0_names.append(p0.name)
            p0_avatar_urls.append(p0.avatar)
            seen.add(uid1)
            seen.add(uid0)
    p1_avatars, p0_avatars = await asyncio.gather(
        asyncio.gather(*map(download_url, p1_avatar_urls)),
        asyncio.gather(*map(download_url, p0_avatar_urls)),
    )

    return draw_couple("本群CP", list(zip(p1_avatars, p1_names, p0_avatars, p0_names)))


yinpa_he = waifu_config.yinpa_he
yinpa_cp = waifu_config.yinpa_cp


@plugin.handle(["透群友"], ["group_id", "user_id", "at"])
async def _(event: Event):
    group_id = event.group_id
    user_id = event.user_id
    group = waifu_data.group(group_id)
    group.yinpa1[user_id] += 1
    waifu_id = group.couple.get(user_id)
    if event.at:
        pet_id = event.at[0]
        checkpoint = yinpa_cp if pet_id == waifu_id else yinpa_he
        if random.randint(1, 100) >= checkpoint:
            return at_result(user_id, "不可以涩涩")
        pet = group.member(pet_id)
        pet.update(await event.group_member_info(group_id, pet_id))
    else:
        group.update(await event.group_member_list(group_id))
        pets = group.waifu_list(time.time() - waifu_last_sent_time_filter, set(group.locked_couple.keys()))
        if not pets:
            return "这里已经没有人了，下次早点来吧~"
        pet = random.choice(pets)
        pet_id = pet.user_id
    group.yinpa0[pet_id] += 1
    waifu_data.save()
    if pet_id == waifu_id:
        tips = "恭喜你涩到了你的老婆！"
    elif pet_id == user_id:
        tips = "恭喜你涩到了你自己！"
    else:
        tips = "恭喜你涩到了群友！"
    return at_text_image_result(user_id, f"{tips}\n你的涩涩对象是：【{pet.name}】", await download_url(pet.avatar))


@plugin.handle(["色色记录", "涩涩记录"], ["group_id"])
async def _(event: Event):
    group_id = event.group_id
    group = waifu_data.group(group_id)
    output = []

    async def single_result(uid: str, times: int):
        member = group.member(uid)
        return await download_url(member.avatar), f"[font color = red]♥[font color = black] {member.name}[right]{times} 次"

    p1_data, p0_data = await asyncio.gather(
        asyncio.gather(*[single_result(uid, times) for uid, times in group.yinpa1.items() if times > 0]),
        asyncio.gather(*[single_result(uid, times) for uid, times in group.yinpa0.items() if times > 0]),
    )
    if p1_data:
        output.append(draw_sese("透群友记录", p1_data))
    if p0_data:
        output.append(draw_sese("群友被透记录", p0_data))
    return output or "暂无记录"

__plugin__ = plugin

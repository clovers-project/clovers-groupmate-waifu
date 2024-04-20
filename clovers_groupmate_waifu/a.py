# 透群友
async def yinpa_rule(bot: Bot, event: GroupMessageEvent, state: T_State) -> bool:
    """
    规则：透群友
    """
    msg = event.message.extract_plain_text()
    if not msg.startswith("透群友"):
        return False
    group_id = event.group_id
    user_id = event.user_id
    protect_set = protect_list.get(group_id, set())
    if user_id in protect_set:
        return False
    at = get_message_at(event.message)
    yinpa_id = None
    tips = "伱的涩涩对象是、"
    if at:
        at = at[0]
        if at in protect_set:
            return False
        if at == user_id:
            msg = f"恭喜你涩到了你自己！" + MessageSegment.image(file=await user_img(user_id))
            await bot.send(event, msg, at_sender=True)
            return False
        X = random.randint(1, 100)
        if at == record_CP.get(group_id, {}).get(user_id, 0):
            if 0 < X <= yinpa_CP:
                yinpa_id = at
                tips = "恭喜你涩到了你的老婆！"
            else:
                await bot.send(event, "你的老婆拒绝和你涩涩！", at_sender=True)
                return False
        elif 0 < X <= yinpa_HE:
            yinpa_id = at
            tips = "恭喜你涩到了群友！"
        elif yinpa_HE < X <= yinpa_BE:
            yinpa_id = user_id
    if not yinpa_id:
        member_list = await bot.get_group_member_list(group_id=group_id)
        lastmonth = event.time - last_sent_time_filter
        yinpa_ids = [
            user_id for member in member_list if (user_id := member["user_id"]) not in protect_set and member["last_sent_time"] > lastmonth
        ]
        if yinpa_ids:
            yinpa_id = random.choice(yinpa_ids)
        else:
            return False
    state["yinpa"] = yinpa_id, tips
    return True


yinpa = on_message(rule=yinpa_rule, priority=90, block=True)


@yinpa.handle()
async def _(bot: Bot, event: GroupMessageEvent, state: T_State):
    group_id = event.group_id
    user_id = event.user_id
    yinpa_id, tips = state["yinpa"]
    if yinpa_id == user_id:
        await yinpa.finish("不可以涩涩！", at_sender=True)
    else:
        record_yinpa1[user_id] = record_yinpa1.get(user_id, 0) + 1
        save(record_yinpa1_file, record_yinpa1)
        record_yinpa2[user_id] = record_yinpa2.get(yinpa_id, 0) + 1
        save(record_yinpa2_file, record_yinpa2)
        member = await bot.get_group_member_info(group_id=group_id, user_id=yinpa_id)
        msg = tips + MessageSegment.image(file=await user_img(yinpa_id)) + f"『{(member['card'] or member['nickname'])}』！"
        await yinpa.finish(msg, at_sender=True)


# 查看涩涩记录

yinpa_list = on_command("涩涩记录", aliases={"色色记录"}, priority=90, block=True)


@yinpa_list.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    group_id = event.group_id
    msg_list = []
    # 输出卡池
    member_list = await bot.get_group_member_list(group_id=event.group_id)
    lastmonth = event.time - last_sent_time_filter
    protect_set = protect_list.get(group_id, set())
    member_list = [member for member in member_list if member["user_id"] not in protect_set and member["last_sent_time"] > lastmonth]
    member_list.sort(key=lambda x: x["last_sent_time"], reverse=True)
    msg = "卡池：\n——————————————\n"
    msg += "\n".join([(member["card"] or member["nickname"]) for member in member_list[:80]])
    msg_list.append(
        {
            "type": "node",
            "data": {
                "name": "卡池",
                "uin": event.self_id,
                "content": MessageSegment.image(text_to_png(msg)),
            },
        }
    )

    # 输出透群友记录

    record = [((member["card"] or member["nickname"]), times) for member in member_list if (times := record_yinpa1.get(member["user_id"]))]
    record.sort(key=lambda x: x[1], reverse=True)
    msg = "\n".join([f"[align=left]{nickname}[/align][align=right]今日透群友 {times} 次[/align]" for nickname, times in record])
    if msg:
        msg_list.append(
            {
                "type": "node",
                "data": {
                    "name": "记录①",
                    "uin": event.self_id,
                    "content": MessageSegment.image(bbcode_to_png("涩涩记录①：\n——————————————\n" + msg)),
                },
            }
        )

    # 输出被透记录

    record = [((member["card"] or member["nickname"]), times) for member in member_list if (times := record_yinpa2.get(member["user_id"]))]
    record.sort(key=lambda x: x[1], reverse=True)

    msg = "涩涩记录②：\n——————————————\n"
    msg = "\n".join([f"[align=left]{nickname}[/align][align=right]今日被透 {times} 次[/align]" for nickname, times in record])
    if msg:
        msg_list.append(
            {
                "type": "node",
                "data": {
                    "name": "记录②",
                    "uin": event.self_id,
                    "content": MessageSegment.image(bbcode_to_png("涩涩记录②：\n——————————————\n" + msg)),
                },
            }
        )

    await bot.send_group_forward_msg(group_id=event.group_id, messages=msg_list)
    await yinpa_list.finish()

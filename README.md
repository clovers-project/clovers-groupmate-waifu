<div align="center">

# clovers-groupmate-waifu

_✨ 娶群友 ✨_

<img src="https://img.shields.io/badge/python-3.12+-blue.svg" alt="python">
<a href="./LICENSE"><img src="https://img.shields.io/github/license/KarisAya/clovers_groupmate_waifu.svg" alt="license"></a>
<a href="https://pypi.python.org/pypi/clovers_groupmate_waifu"><img src="https://img.shields.io/pypi/v/clovers_groupmate_waifu.svg" alt="pypi"></a>
<a href="https://pypi.python.org/pypi/clovers_groupmate_waifu"><img src="https://img.shields.io/pypi/dm/clovers_groupmate_waifu" alt="pypi download"></a>

</div>

## 💿 安装

```bash
pip install clovers_groupmate_waifu
```

## ⚙️ 配置

<details>

<summary>在 clovers 配置文件内按需添加下面的配置项</summary>

```toml
[clovers_groupmate_waifu]
# 默认显示字体
fontname = "simsun"
# 默认备用字体
fallback_fonts = [ "Arial", "Tahoma", "Microsoft YaHei", "Segoe UI", "Segoe UI Emoji", "Segoe UI Symbol", "Helvetica Neue", "PingFang SC", "Hiragino Sans GB", "Source Han Sans SC", "Noto Sans SC", "Noto Sans CJK JP", "WenQuanYi Micro Hei", "Apple Color Emoji", "Noto Color Emoji",]
# 文件记录存档路径
waifu_path = "./data/waifu/"
# 是否每日重置cp记录
waifu_reset = true
# 指定成功概率
waifu_he = 40
# 指定失败概率
waifu_be = 20
# NTR概率
waifu_ntr = 50
# 成功提示列表
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
# 失败提示列表
bad_end_tips = [
    "你没有娶到群友，强者注定孤独，加油！",
    "找不到对象.jpg",
    "雪花飘飘北风萧萧～天地一片苍茫。",
    "要不等着分配一个对象？",
    "恭喜伱没有娶到老婆~",
    "醒醒，伱没有老婆。",
    "哈哈哈哈哈哈哈哈哈",
    "智者不入爱河，建设美丽中国。",
    "智者不入爱河，我们终成富婆",
    "智者不入爱河，寡王一路硕博",
]
# 娶群友发言时间过滤
waifu_last_sent_time_filter = 2592000
# 指定涩涩成功率
yinpa_he = 50
# 指定cp涩涩成功率
yinpa_cp = 50
```

</details>

## 🎉 功能介绍

### 锁定机制

如果是通过@成功娶到的群友会和自己进入锁定。

一般情况下对方娶群友会娶到自己。但是对方@其他人娶群友的话，会无视你的锁定进入对方的成功判断。

如果对方也@自己的话，那么两个人会进入互相锁定，无法被 NTR,分手会有进一步确认等其他机制。

`娶群友`,`娶群友@name`

纯爱 **双向奔赴版**，两个人会互相抽到对方。

如果 at 的话，有机会娶到 at 的人。。。

`分手` `离婚`

把两个人重置为单身

`本群cp`

查看当前群内的 cp

`查看娶群友卡池`

查看当前群可以娶到的群友列表

`透群友`

ntr ~~宫吧老哥狂喜版~~，每次抽到的结果都不一样。

`涩涩记录`

查看当前群的群友今日透群友次数和被透的次数，记录是跨群的。~~也就是说群友在别的群挨透也会在记录里显示出来~~

~~群友背地里玩的挺花（bushi）~~

**管理员指令**：`重置娶群友记录`

重置娶群友记录

`设置娶群友保护`,

**管理员指令**：`设置娶群友保护@someone@someother`

将自己或 at 的人（可以 at 多人）加入保护名单。名单内的群友无法触发娶群友或透群友，也无法作为娶群友或透群友的目标。

`解除娶群友保护`,

**管理员指令**：`解除娶群友保护@someone@someother`

将自己或 at 的人（可以 at 多人）从保护名单删除

`查看娶群友保护名单`

查看娶群友保护的保护名单

## 📞 联系

如有建议，bug 反馈等可以加群

机器人 bug 研究中心（闲聊群） 744751179

永恒之城（测试群） 724024810

![群号](https://github.com/KarisAya/clovers/blob/master/%E9%99%84%E4%BB%B6/qrcode_1676538742221.jpg)

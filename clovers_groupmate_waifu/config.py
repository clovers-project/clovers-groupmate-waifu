from pydantic import BaseModel
from pathlib import Path


class Config(BaseModel):
    waifu_path: str = str(Path("./data/waifu/").absolute())
    """文件记录存档路径"""
    waifu_reset: bool = True
    """是否每日重置cp记录"""

    waifu_cd_bye: int = 3600
    waifu_save: bool = True

    waifu_he: int = 40
    waifu_be: int = 20
    waifu_ntr: int = 50
    yinpa_he: int = 50
    yinpa_be: int = 0
    yinpa_cp: int = 80
    waifu_last_sent_time_filter: int = 2592000

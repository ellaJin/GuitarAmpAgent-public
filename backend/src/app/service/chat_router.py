# app/service/chat_router.py

ROUTE_INVENTORY   = "INVENTORY"
ROUTE_MANUAL_QA   = "MANUAL_QA"
ROUTE_TONE_RECIPE = "TONE_RECIPE"
ROUTE_OTHER       = "OTHER"


def route_query(user_input: str) -> str:
    text = (user_input or "").strip().lower()
    if not text:
        return ROUTE_OTHER

    # ================= INVENTORY =================
    zh_inventory = any(k in text for k in [
        "多少", "几种", "几个", "哪些设备", "我的设备",
        "绑定了", "绑定的设备", "设备列表",
        "激活设备", "当前设备"
    ])
    en_inventory = any(k in text for k in [
        "how many", "what devices", "which devices", "my devices",
        "device list", "list devices",
        "active device", "current device",
        "linked devices", "bound devices"
    ])
    if zh_inventory or en_inventory:
        return ROUTE_INVENTORY

    # ================= TONE_RECIPE =================
    # —— 强信号：歌曲 / 音色 / 参数 / 预设 ——
    zh_tone = any(k in text for k in [
        "这首歌", "那首歌", "歌曲", "曲子",
        "音色", "音色链", "效果链",
        "怎么调音色", "给参数", "参数", "数值",
        "预设", "复刻", "还原",
        "要不要失真", "失真多少", "增益多少",
        "延迟多少", "混响多少"
    ])
    en_tone = any(k in text for k in [
        "tone", "sound like", "get the tone", "dial in",
        "settings", "values", "exact values",
        "preset", "patch", "signal chain",
        "gain", "drive", "distortion", "overdrive",
        "delay", "reverb", "chorus", "compressor", "eq"
    ])
    song_cue = any(k in text for k in [
        " by ",        # e.g. "hotel california by eagles"
        "song", "track",
        "cover", "solo tone", "rhythm tone",
        "《", "》", "“", "”", "\"", "'"
    ])

    # 组合规则：歌曲/音色信号 + 参数/设置信号 → TONE_RECIPE
    if (zh_tone and ("音色" in text or "参数" in text or "数值" in text)) \
       or (en_tone and ("tone" in text or "settings" in text or "preset" in text)) \
       or (song_cue and (zh_tone or en_tone)):
        return ROUTE_TONE_RECIPE

    # ================= MANUAL_QA =================
    hardware_cues = [
        "midi", "battery", "电池", "power", "电源", "9v", "adapter", "适配器",
        "otg", "usb", "recording", "录音", "calibration", "校准", "calibrate",
        "headphones", "耳机", "output", "input", "interface", "接口",
        "update", "firmware", "固件", "升级", "factory reset", "恢复出厂"
    ]

    zh_manual = any(k in text for k in [
        "怎么用", "如何", "在哪里", "在哪",
        "怎么连接", "插哪里", "怎么插",
        "怎么保存", "怎么导入", "怎么导出",
        "模块", "接口", "说明书", "手册",
        "fx loop", "send", "return"
    ]) or any(k in text for k in hardware_cues if k in text)  # 命中硬件词也进 QA

    en_manual = any(k in text for k in [
        "how do i", "how to", "help me with",
        "where is", "where can i find",
        "how to connect", "how to save",
        "import", "export", "setup",
        "module", "interface", "manual",
        "fx loop", "send", "return"
    ]) or any(k in text for k in hardware_cues if k in text)

    if zh_manual or en_manual:
        return ROUTE_MANUAL_QA

    return ROUTE_OTHER

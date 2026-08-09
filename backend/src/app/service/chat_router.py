# app/service/chat_router.py

ROUTE_INVENTORY   = "INVENTORY"
ROUTE_MANUAL_QA   = "MANUAL_QA"
ROUTE_TONE_RECIPE = "TONE_RECIPE"
ROUTE_OTHER       = "OTHER"


def has_song_reference(text: str) -> bool:
    """
    True if the (lowercased) input plausibly names a specific song/artist,
    as opposed to a bare topic word like "settings" or "preset". Single
    source of truth for "is there a song here": route_query uses it to
    decide whether to route to TONE_RECIPE at all, and handle_tone_recipe
    (tone_recipe_handler.py) uses it again, independently, right before it
    would generate a recipe.
    """
    return any(k in text for k in [
        " by ",        # e.g. "hotel california by eagles"
        "song", "track",
        "cover", "solo tone", "rhythm tone",
        "want to play",  # e.g. "i want to play AC/DC TNT"
        "《", "》", "“", "”", "\"", "'"
    ])


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
        "delay", "reverb", "chorus", "compressor", "eq",
        "effect",  # covers "effect"/"effects" via substring match
    ])
    song_cue = has_song_reference(text)

    # TONE_RECIPE requires an actual song/artist reference. zh_tone/en_tone
    # alone are ordinary manual vocabulary ("settings", "preset", "参数") --
    # they used to be able to fire this route standalone via a confirmer
    # clause, which is what mis-routed things like "what is preset?" and
    # "...settings for a ... effect?" here. A bare topic noun with no song
    # now falls through to MANUAL_QA below, where it belongs.
    if song_cue and (zh_tone or en_tone):
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

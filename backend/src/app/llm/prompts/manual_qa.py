# app/llm/prompts/manual_qa.py
from dataclasses import dataclass

@dataclass(frozen=True)
class ManualQaPromptParams:
    device_name: str
    user_name: str

def build_manual_qa_system_prompt(p: ManualQaPromptParams) -> str:
    return f"""
You are the Technical Support Expert for {p.device_name}.

### MANDATORY PROTOCOL:
- DO NOT answer based on your pre-trained knowledge. 
- You MUST call 'search_manual_chunks' for every technical query to provide the EXACT manual reference.
- If you don't call the tool, you are failing your mission.

### RESPONSE FORMAT:
- [Technical Explanation]: Match the user's language.
- 🎸 Native Gear Talk: 2-3 bullet points in English.
""".strip()


def build_manual_qa_query_extension(user_input: str, device_name: str) -> str:
    query = user_input.lower()

    # 定义吉他手常用的“黑话”到手册“官方术语”的映射
    if any(k in query for k in ["fx loop", "4 cable", "4cm", "send", "return"]):
        # 强制加入手册标题中极大概率出现的词：'application scenario', 'power amplifier'
        # 移除用户提问中的语气词，直接构造高权重搜索短语
        return f"{device_name} application scenario connection to a guitar power amplifier FX LOOP"

    # 针对录音/USB问题的扩展
    if any(k in query for k in ["usb", "recording", "audio interface", "otg"]):
        return f"{device_name} computer recording setup mobile device OTG digital audio"

    return user_input
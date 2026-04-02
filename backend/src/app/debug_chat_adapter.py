# backend/src/app/debug_chat_adapter.py
from app.adapters.chat_adapter import to_chat_query_request, to_chat_query_context

class Msg:
    def __init__(self, role, content):
        self.role = role
        self.content = content

req = to_chat_query_request(
    message="hello",
    history=[Msg("human", "hi"), Msg("ai", "hello")]
)

ctx = to_chat_query_context(
    user_id="u1",
    user_name="Alice",
    active_device="GE150"
)

print(req)
print(ctx)

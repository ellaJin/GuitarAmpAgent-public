from agents.deep_agent import build_deep_agent


def cli_loop():
    agent = build_deep_agent()
    print("✨ Physics Deep Agent started. Type 'exit' to quit.\n")

    messages = []

    while True:
        q = input("你：")
        if q.strip().lower() in {"exit", "quit"}:
            break

        messages.append({"role": "user", "content": q})
        payload = {"messages": messages}

        result = agent.invoke(payload)
        msgs = result.get("messages", [])
        if msgs:
            reply = msgs[-1].get("content", "")
        else:
            reply = str(result)

        messages.append({"role": "assistant", "content": reply})
        print("\nAgent：", reply, "\n")


if __name__ == "__main__":
    cli_loop()

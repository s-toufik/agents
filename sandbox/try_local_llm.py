import asyncio

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage

from agentic_core.infrastructure.http.adapter.httpx.factory import HttpxFactory


async def main():
    client = HttpxFactory().instance_async_http_client

    llm = ChatOpenAI(
        base_url="http://nautilus:1234/v1",
        api_key="lm_studio",
        model="google/gemma-3-1b",
        http_async_client=client,
    )

    # 🧠 memory container
    messages = []

    print("Chat started (type 'exit' to quit)\n")

    while True:
        user_input = input("You: ")

        if user_input.lower() == "exit":
            break

        # add user message
        messages.append(HumanMessage(content=user_input))

        # call model with full history
        response = await llm.ainvoke(messages)

        # print response
        print("\nAI:", response.content, "\n")

        # store assistant response
        messages.append(AIMessage(content=response.content))


if __name__ == "__main__":
    asyncio.run(main())

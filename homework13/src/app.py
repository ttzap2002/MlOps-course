import asyncio
import json
from contextlib import AsyncExitStack

import requests
from openai import OpenAI
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

import os

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

class MCPManager:
    def __init__(self, servers: dict[str, str]):
        self.servers = servers
        self.clients = {}
        self.tools = []  # in OpenAI format
        self._stack = AsyncExitStack()

    async def __aenter__(self):
        for url in self.servers.values():
            # initialize MCP session with Streamable HTTP client
            read, write, session_id = await self._stack.enter_async_context(
                streamable_http_client(url)
            )
            session = await self._stack.enter_async_context(ClientSession(read, write))
            await session.initialize()

            # use /list_tools MCP endpoint to get tools
            # parse each one to get OpenAI-compatible schema
            tools_resp = await session.list_tools()
            for t in tools_resp.tools:
                self.clients[t.name] = session
                self.tools.append(
                    {
                        "type": "function",
                        "function": {
                            "name": t.name,
                            "description": t.description,
                            "parameters": t.inputSchema,
                        },
                    }
                )

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._stack.aclose()

    async def call_tool(self, name: str, args: dict) -> dict | str:
        result = await self.clients[name].call_tool(name, arguments=args)
        return result.content[0].text

async def process_agent_turn(client: OpenAI, mcp: MCPManager, messages: list[dict]) -> str:
    MAX_ITERATIONS = 10

    for _ in range(MAX_ITERATIONS):
        response = client.chat.completions.create(
            model="",
            messages=messages,
            tools=mcp.tools,
            tool_choice="auto",
            max_completion_tokens=1000,
            extra_body={"chat_template_kwargs": {"enable_thinking": False}},
        )

        response = response.choices[0].message
        if not response.tool_calls:
            return response.content

        messages.append(response)
        for tool_call in response.tool_calls:
            func_name = tool_call.function.name
            func_args = json.loads(tool_call.function.arguments)

            print(f"Executing tool '{func_name}'")
            func_result = await mcp.call_tool(func_name, func_args)

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": func_name,
                    "content": str(func_result),
                }
            )

    return "The request could not be completed"

async def run_agent() -> str:
    mcp_servers = {
        "weather_forecast": "http://localhost:8001/mcp",
        "tavily": f"https://mcp.tavily.com/mcp?tavilyApiKey={TAVILY_API_KEY}"
    }

    vllm_client = OpenAI(api_key="EMPTY", base_url="http://localhost:8000/v1")

    system_prompt = (
        "You are a helpful Trip Planning Assistant. "
        "Use available tools (weather, search) to help plan trips. "
        "Please answer only questions related to travel, geography, weather, or trip planning. "
        "If user asks about coding, math, or politics, politely refuse. "
        "Always verify weather before recommending dates."
    )
    exits_keyword = {"quit", "exit", "q()"}
    messages = [{"role": "system", "content": system_prompt}]

    async with MCPManager(mcp_servers) as mcp:
        print("Welcome to the trip planner (Type quit, exit, q() )")

        while True:
            user_input = input("> User: ")

            if user_input.lower() in exits_keyword:
                break

            messages.append({"role": "user", "content": user_input})
            answer = await process_agent_turn(vllm_client, mcp, messages)
            print(f"\nAgent: {answer}\n")

if __name__ == "__main__":
    asyncio.run(run_agent())


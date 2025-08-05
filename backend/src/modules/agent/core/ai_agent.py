import random

from agents import Agent, function_tool, set_default_openai_client
from openai import AsyncOpenAI
from src.common.config import settings


@function_tool
def how_many_jokes() -> int:
    return random.randint(1, 10)


class AIAgent:
    def __init__(self):
        self.agent = Agent(
            name="Joker",
            instructions="First call the `how_many_jokes` tool, then tell that many jokes.",
            model="gpt-4o-mini",
            tools=[how_many_jokes],
        )

        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        set_default_openai_client(client)

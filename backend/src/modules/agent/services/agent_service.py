import asyncio
import json
from typing import AsyncGenerator

from agents import ItemHelpers, Runner
from src.common.logger import logger
from src.modules.agent.core.ai_agent import AIAgent
from src.modules.agent.repositories.agent_status_repository import (
    AgentStatusRepository,
)
from src.modules.agent.schemas.agent_schemas import (
    AgentCompleteEvent,
    AgentErrorEvent,
    AgentEvent,
    LLMOutputEvent,
    ToolCallEvent,
    ToolOutputEvent,
)


class AgentService:
    def __init__(self, ai_agent: AIAgent, repository: AgentStatusRepository):
        self.ai_agent = ai_agent
        self.repository = repository

    async def run_agent(
        self, run_id: str, input_text: str = "Hello"
    ) -> AsyncGenerator[AgentEvent, None]:
        try:
            result = Runner.run_streamed(
                self.ai_agent.agent,
                input=input_text,
            )

            logger.info("=== Agent run starting ===")

            async for event in result.stream_events():
                # logger.info(f"Agent event: {event}")

                if (
                    event.type == "raw_response_event"
                    or event.type == "agent_updated_stream_event"
                ):
                    continue

                elif event.type == "run_item_stream_event":
                    if event.item.type == "tool_call_item":
                        tool_name = event.item.raw_item.name
                        tool_args = event.item.raw_item.arguments

                        if isinstance(tool_args, str):
                            tool_args = json.loads(tool_args)
                        elif tool_args is None:
                            tool_args = {}

                        yield ToolCallEvent(
                            run_id=run_id,
                            tool_name=tool_name,
                            tool_args=tool_args,
                            message="Tool called",
                        )

                    elif event.item.type == "tool_call_output_item":
                        tool_name = getattr(event.item, "tool_name", None)
                        if not tool_name and hasattr(event.item, "raw_item"):
                            tool_name = getattr(event.item.raw_item, "name", None)

                        yield ToolOutputEvent(
                            run_id=run_id,
                            tool_name=tool_name or "unknown",
                            output=event.item.output,
                            message="Tool output received",
                        )

                    elif event.item.type == "message_output_item":
                        content = ItemHelpers.text_message_output(event.item)
                        yield LLMOutputEvent(
                            run_id=run_id,
                            content=content,
                            is_complete=True,
                            message="LLM output received",
                        )

            yield AgentCompleteEvent(
                run_id=run_id,
                final_output="Agent run completed successfully",
                message="Agent run completed",
            )

            logger.info("=== Agent run complete ===")

        except Exception as e:
            logger.error(f"Agent run failed: {e}")
            yield AgentErrorEvent(
                run_id=run_id,
                error_message=str(e),
                error_type=type(e).__name__,
                message="Agent run failed",
            )

    async def run_agent_with_publishing(
        self, run_id: str, input_text: str = "Hello"
    ) -> None:
        try:
            logger.info(f"Starting agent run with publishing: {run_id}")
            await asyncio.sleep(60)

            async for event in self.run_agent(run_id=run_id, input_text=input_text):
                logger.info(f"Agent event: {event}")
                success = await self.repository.publish_event(
                    run_id=run_id, event=event
                )

                if not success:
                    logger.error(
                        f"Failed to publish event {event.event_type} for run {run_id}"
                    )

            logger.info(f"Completed agent run with publishing: {run_id}")

        except Exception as e:
            logger.error(f"Agent run failed for {run_id}: {e}")
            error_event = AgentErrorEvent(
                run_id=run_id,
                error_message=str(e),
                error_type=type(e).__name__,
                message="Agent run failed",
            )
            await self.repository.publish_event(run_id, error_event)
            raise

        finally:
            await self.repository.cleanup_channel(run_id)

"""
Custom PyRIT PromptTarget for the LOCAL FastAPI LangGraph agent.

The agent server (single_node_graph/server.py) exposes:
  POST /conversation  →  {"thread_id": "<uuid>"}
  POST /chat          →  {"thread_id": "...", "message": "..."}
                     ←  {"response": "..."}

This wrapper creates ONE thread per instantiation so all prompts within a
PyRIT orchestrator run share the same LangGraph conversation context.
To isolate prompts, create a new instance of FastAPIAgentTarget per prompt.
"""

import asyncio
import requests
from typing import Optional

from pyrit.models import Message, MessagePiece
from pyrit.prompt_target import PromptTarget


class FastAPIAgentTarget(PromptTarget):
    """
    PyRIT target that routes prompts through the local LangGraph FastAPI agent.

    Parameters
    ----------
    base_url : str
        Base URL of the running FastAPI server (default: http://localhost:8000)
    timeout : int
        HTTP request timeout in seconds (default: 30)
    new_thread_per_request : bool
        If True, creates a fresh conversation thread for every prompt.
        If False, reuses a single thread across all prompts in the session.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        timeout: int = 30,
        new_thread_per_request: bool = True,
    ):
        super().__init__()
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._new_thread_per_request = new_thread_per_request
        self._session_thread_id: Optional[str] = None

        if not new_thread_per_request:
            self._session_thread_id = self._create_thread()

    def _create_thread(self) -> str:
        """Call /conversation to get a new thread_id from the agent."""
        resp = requests.post(
            f"{self._base_url}/conversation",
            timeout=self._timeout,
        )
        resp.raise_for_status()
        return resp.json()["thread_id"]

    def _chat(self, thread_id: str, message: str) -> str:
        """Send a message to /chat and return the agent's text response."""
        resp = requests.post(
            f"{self._base_url}/chat",
            json={"thread_id": thread_id, "message": message},
            timeout=self._timeout,
        )
        resp.raise_for_status()
        return resp.json()["response"]

    def is_json_response_supported(self) -> bool:
        return False

    async def send_prompt_async(self, *, message: Message) -> list[Message]:
        """
        PyRIT calls this for each prompt. Runs the HTTP call in a
        thread-pool executor so the async event loop is not blocked.
        """
        request_piece = message.get_piece()
        prompt_text = request_piece.converted_value
        conversation_id = request_piece.conversation_id

        loop = asyncio.get_event_loop()
        response_text = await loop.run_in_executor(
            None,
            self._send_sync,
            prompt_text,
        )

        response_piece = MessagePiece(
            role="assistant",
            original_value=response_text,
            converted_value=response_text,
            conversation_id=conversation_id,
        )

        return [Message(message_pieces=[response_piece])]

    def _send_sync(self, prompt_text: str) -> str:
        """Synchronous inner call — runs inside executor."""
        if self._new_thread_per_request:
            thread_id = self._create_thread()
        else:
            thread_id = self._session_thread_id
        return self._chat(thread_id, prompt_text)

    @classmethod
    def is_target_online(cls, base_url: str = "http://localhost:8000") -> bool:
        """Quick health check — returns True if the server responds."""
        try:
            resp = requests.post(f"{base_url}/conversation", timeout=3)
            return resp.status_code == 200
        except Exception:
            return False

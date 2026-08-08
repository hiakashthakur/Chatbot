from collections import defaultdict
from typing import Dict, List

from app.logger import logger


class MemoryService:
    """
    Service responsible for storing and retrieving
    conversation history.
    """

    def __init__(self) -> None:
        logger.info("Initializing Memory Service")

        self.memory: Dict[str, List[dict]] = defaultdict(list)

        logger.info("Memory Service Initialized")

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str
    ) -> None:
        """
        Add a message to conversation history.
        """

        self.memory[session_id].append(
            {
                "role": role,
                "content": content
            }
        )

        logger.info(
            f"Message added to session: {session_id}"
        )

    def get_history(
        self,
        session_id: str
    ) -> List[dict]:
        """
        Return conversation history.
        """

        logger.info(
            f"Fetching history for session: {session_id}"
        )

        return self.memory.get(session_id, [])

    def clear_history(
        self,
        session_id: str
    ) -> None:
        """
        Clear conversation history.
        """

        if session_id in self.memory:
            del self.memory[session_id]

        logger.info(
            f"History cleared for session: {session_id}"
        )


    def get_formatted_history(
        self,
        session_id: str,
        max_messages: int = 10
    ) -> str:
        """
        Return formatted conversation history.
        """

        history = self.get_history(session_id)[-max_messages:]

        if not history:
            return ""

        history_text = ""

        for message in history:

            history_text += (
                f"{message['role'].capitalize()}: "
                f"{message['content']}\n"
            )

        return history_text.strip()
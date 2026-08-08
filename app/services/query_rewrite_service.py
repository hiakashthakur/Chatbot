from app.logger import logger
from app.exceptions.llm_exception import LLMException


class QueryRewriteService:
    """
    Service responsible for rewriting follow-up questions
    into standalone search queries.
    """

    def __init__(self, llm_service):
        logger.info(
            "Initializing Query Rewrite Service"
        )

        self.llm_service = llm_service

        logger.info(
            "Query Rewrite Service Initialized"
        )

    async def rewrite(
        self,
        question: str,
        history: str
    ) -> str:
        """
        Rewrite a question into a standalone query
        using conversation history.
        """

        if not question.strip():
            raise LLMException(
                "Question cannot be empty."
            )

        # No history means there is nothing to rewrite.
        if not history.strip():
            return question.strip()

        prompt = f"""
            You are a query rewriting assistant for a RAG system.

            Your task is to rewrite the user's latest question
            into a standalone search query.

            Use the conversation history to resolve:
            - pronouns such as "it", "this", "that", "they"
            - references to previous questions
            - incomplete follow-up questions
            - missing context

            Rules:
            1. Return ONLY the rewritten question.
            2. Do NOT answer the question.
            3. Do NOT add explanations.
            4. Preserve the user's original intent.
            5. If the question is already standalone, return it unchanged.
            6. Do not invent information that is not present in the conversation.

            Conversation History:
            {history}

            Latest User Question:
            {question}

            Standalone Search Query:
            """

        try:

            rewritten_question = await self.llm_service.agenerate(
                prompt
            )

            rewritten_question = (
                rewritten_question
                .strip()
                .strip('"')
                .strip("'")
            )

            if not rewritten_question:

                raise LLMException(
                    "Query rewriting returned an empty response."
                )

            logger.info(
                f"Query rewritten successfully: "
                f"{rewritten_question}"
            )

            return rewritten_question

        except LLMException:
            raise

        except Exception as e:

            logger.exception(
                "Failed to rewrite query"
            )

            raise LLMException(
                f"Query Rewrite Error: {str(e)}"
            ) from e
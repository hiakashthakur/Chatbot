from google import genai

from app.config import Config
from app.logger import logger
from app.exceptions.llm_exception import LLMException


class LLMService:
    """
    Service responsible for interacting with the Gemini LLM.
    """

    def __init__(self) -> None:
        logger.info("Initializing LLM Service")

        if not Config.GEMINI_API_KEY:
            raise LLMException("Gemini API Key is missing.")

        self.client = genai.Client(
            api_key=Config.GEMINI_API_KEY
        )

        self.model = Config.LLM_MODEL

        logger.info("LLM Service Initialized Successfully")

    def generate(self, prompt: str) -> str:
        """
        Generate response from Gemini model.

        Args:
            prompt (str): Prompt to send to Gemini.

        Returns:
            str: Generated response.
        """

        if not prompt.strip():
            raise LLMException("Prompt cannot be empty.")

        try:
            logger.info("Generating response from Gemini")

            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
            )

            logger.info("Response generated successfully")

            return response.text

        except Exception as e:
            logger.exception("Failed to generate response")

            raise LLMException(
                f"Gemini API Error: {str(e)}"
            ) from e

    async def agenerate(
        self,
        prompt: str
    ):
        """
        Async response generation.
        """

        try:

            logger.info(
                "Generating Async Response"
            )

            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=prompt
            )

            logger.info(
                "Async Response Generated"
            )

            return response.text

        except Exception as e:

            raise LLMException(
                str(e)
            ) from e

    def stream_generate(self, prompt: str):
        """
        Stream response from Gemini model.
        """

        if not prompt.strip():
            raise LLMException("Prompt cannot be empty.")

        try:
            logger.info("Generating Streaming Response")

            response = self.client.models.generate_content_stream(
                model=self.model,
                contents=prompt
            )

            for chunk in response:

                if chunk.text:
                    yield chunk.text

            logger.info("Streaming Completed")

        except Exception as e:

            logger.exception("Streaming Failed")

            raise LLMException(
                f"Gemini Streaming Error : {str(e)}"
            ) from e
    
    async def astream_generate(
        self,
        prompt: str
    ):
        """
        Async streaming response.
        """

        try:

            logger.info(
                "Generating Async Stream"
            )

            response = await self.client.aio.models.generate_content_stream(
                model=self.model,
                contents=prompt
            )
            
            async for chunk in response:

                if chunk.text:

                    yield chunk.text

            logger.info(
                "Async Stream Completed"
            )

        except Exception as e:

            raise LLMException(
                str(e)
            ) from e
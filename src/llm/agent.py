import base64
import json
from functools import cache
from typing import Literal, Optional

import randomname
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import AzureChatOpenAI, AzureOpenAI
from loguru import logger
from PIL import Image

import src.llm.prompt as prompt
from src.llm.places import PlacesTool
from src.settings import Settings


class OpenAITool:
    """
    A class that provides tools for generating vision and card responses using the Azure OpenAI API.

    Args:
        settings (Settings): An instance of the Settings class containing API configuration.

    Attributes:
        _client (AsyncAzureOpenAI): An instance of the AsyncAzureOpenAI client for making API requests.

    """

    def __init__(self, settings: Settings) -> None:
        """
        Initializes the tool.

        Args:
            settings (Settings): An instance of the Settings class containing the required Azure OpenAI API key, version and endpoint.

        Returns:
            None
        """
        common_client_args = {
            "api_key": settings.AZURE_OPENAI_API_KEY,
            "openai_api_version": settings.AZURE_OPENAI_API_VERSION,
            "azure_endpoint": settings.AZURE_OPENAI_API_BASE,
            "streaming": False,
            "metadata": {"container_app_name": settings.CONTAINER_APP_NAME},
        }

        if settings.LANGSMITH_TRACER:
            common_client_args["callbacks"] = [settings.LANGSMITH_TRACER]

        self._vision_chain = self._build_vision_chain(settings, common_client_args)
        self._agent_chain = self._build_agent_chain(settings, common_client_args)

        self._run_name = "img2card"

    def _build_vision_chain(self, settings, common_client_args):
        def _prompt_generator(data_dict: dict):
            messages = [
                HumanMessage(
                    content=[
                        {"type": "text", "text": prompt.VISION_TOOL},
                        {"type": "image_url", "image_url": {"url": f"data:{data_dict['format']};base64,{data_dict['image']}", 
                                                            "detail": data_dict['detail']}},
                    ],
                )
            ]
            return messages

        llm = AzureChatOpenAI(
            **common_client_args,
            azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT_VISION,
            model_name="gpt-4-vision-preview",
            max_tokens=500,
        )

        return _prompt_generator | llm | StrOutputParser()

    def _build_agent_chain(self, settings, common_client_args):
        llm = AzureOpenAI(
            **common_client_args,
            model_name="gpt-3.5-turbo-instruct",
            azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT_AGENT,
        )

        message = f"""Role:
{prompt.AGENT_SYSTEM}

JSON:
{{vision_transcription}}

Instructions:
{prompt.AGENT_TOOL}

Response:
"""
        card_prompt = PromptTemplate.from_template(message)
        return card_prompt | llm | StrOutputParser()

    def _image_base64_format(self, image_path):
        format = Image.open(image_path).format.lower()

        if "jpg" in format or "jpeg" in format:
            return "image/jpeg"
        if "png" in format:
            return "image/png"
        raise ValueError(f"Unsupported image format: {format}")

    def _image_encode(self, image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    @property
    def run_name(self) -> Optional[str]:
        """
        Get the name of the run.

        Returns:
            Optional[str]: The name of the run.

        """
        return self._run_name

    @run_name.setter
    def run_name(self, name: Optional[str]) -> None:
        """
        Set the name of the run.

        Args:
            name (Optional[str]): The name of the run.

        """
        self._run_name = name

    async def generate_vision(self, image_path: str, detail: Literal["low", "high"] = "low") -> str:
        """
        Generates a vision response based on the provided card image.

        Args:
            card (str): The base64-encoded image of the card.
            detail (Literal["low", "high"], optional): The level of detail for the vision response. Defaults to "low".

        Returns:
            str: The generated vision response.

        """
        image = self._image_encode(image_path)
        format = self._image_base64_format(image_path)

        vision_response = await self._vision_chain.ainvoke({"image": image, "format": format, "detail": detail},
                                                           config={"run_name": self.run_name, "tags": ["vision"]})

        return vision_response

    async def generate_card(self, vision_transcription: str) -> str:
        """
        Generates a card response based on the provided vision transcription.

        Args:
            vision_transcription (str): The transcription of the vision response.

        Returns:
            str: The generated card response.

        """
        card_response = await self._agent_chain.ainvoke({"vision_transcription": vision_transcription}, config={"run_name": self.run_name, "tags": ["agent"]})

        return card_response


class CardAgent:
    """
    Represents an agent that creates contact cards based on transcriptions generated from the images and place's searching.

    Args:
        settings (Settings): The settings object containing configuration options.

    Attributes:
        _settings (Settings): The settings object containing configuration options.
        _places (PlacesTool): The tool for searching places.
        _llm (OpenAITool): The tool for generating vision transcriptions from images.

    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._places = PlacesTool(settings)
        self._llm = OpenAITool(settings)

    async def create_card(
        self, image_path: str, detail: str = "low", lat: Optional[float] = None, lon: Optional[float] = None
    ) -> str:
        """
        Creates a card based on the provided image path and additional details.

        Args:
            image_path (str): The path to the image file.
            detail (str, optional): The level of detail for generating the vision. Defaults to "low".
            lat (float, optional): The latitude coordinate. Defaults to None.
            lon (float, optional): The longitude coordinate. Defaults to None.

        Returns:
            str: The generated card.
        """
        self._llm.run_name = randomname.get_name()
        vision_transcription = await self._llm.generate_vision(image_path, detail)
        logger.info(f"vision: {vision_transcription}")
        if "venue" in vision_transcription:
            try:
                query = " ".join(
                    [value for key, value in self._normalize_json(vision_transcription).items() if "venue" in key]
                )
                vision_transcription = self._places.search(image_path, query, lat, lon)
                if vision_transcription:
                    vision_transcription = json.dumps(vision_transcription)
                else:
                    # TODO: if detail == "low", try again with detail == "high
                    return None
            except Exception:
                logger.exception("Error parsing vision")
        card = await self._llm.generate_card(vision_transcription)
        logger.debug(f"card: {card}")
        card = self._postprocess(card)
        return card

    def _postprocess(self, card: str) -> str:
        BEGIN_CARD = "BEGIN:VCARD"
        END_CARD = "END:VCARD"
        idx_start = card.find(BEGIN_CARD)
        idx_end = card.find(END_CARD)
        return card[idx_start : idx_end + len(END_CARD)]

    def _normalize_json(self, text: str) -> dict:
        return json.loads(text.strip("`").lstrip("json"))


@cache
def build_agent():
    """
    Builds and returns a CardAgent object based on the settings obtained from get_settings().

    Returns:
        CardAgent: The built CardAgent object.
    """
    from src.settings import get_settings

    settings = get_settings()
    return CardAgent(settings)

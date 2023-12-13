from functools import cache
from openai import AsyncAzureOpenAI
import base64
from loguru import logger

from src.settings import Settings
import src.llm.prompt as prompt


class CardAgent:
    def __init__(self, settings: Settings) -> None:
        self.client = AsyncAzureOpenAI(api_key=settings.AZURE_OPENAI_API_KEY,
                                       api_version=settings.AZURE_OPENAI_API_VERSION,
                                       azure_endpoint=settings.AZURE_OPENAI_API_BASE)
        self._settings = settings

    async def create_card(self, image_path: str) -> str:
        image = self._encode_image(image_path)
        vision = await self._generate_vision(image)
        logger.info(f"vision: {vision}")
        card = await self._generate_card(vision)
        logger.info(f"card: {card}")
        card = self._postprocess(card)
        return card

    async def _generate_vision(self, card: str) -> str:
        messages = [
            {'role': 'user', 'content': [{'type': 'text',
                                        'text': prompt.VISION}, 
                                        {'type': 'image_url',
                                        'image_url': {'url': f"data:image/jpeg;base64,{card}", 'detail': 'low'}}]},
        ]

        result = await self.client.chat.completions.create(messages=messages, model=self._settings.AZURE_OPENAI_DEPLOYMENT_VISION, 
                                                           max_tokens=500, stream=False)
        vision_response = result.choices[0].message.content
        return vision_response

    async def _generate_card(self, vision: str) -> str:
        messages = [
            {'role': 'system', 'content': 'you are an expert in vCard format'},
            {'role': 'assistant', 'content': vision},
            {'role': 'user', 'content': prompt.AGENT},
        ]

        result = await self.client.chat.completions.create(messages=messages, model="agent", stream=False)
        card_response = result.choices[0].message.content
        return card_response

    def _postprocess(self, card: str) -> str:
        BEGIN_CARD = "BEGIN:VCARD"
        END_CARD = "END:VCARD"
        idx_start = card.find(BEGIN_CARD)
        idx_end = card.find(END_CARD)
        return card[idx_start:idx_end+len(END_CARD)]

    def _encode_image(self, image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

@cache
def make_agent():
    from src.settings import get_settings

    settings = get_settings()
    return CardAgent(settings)
import base64
import json
from functools import cache
from typing import Literal, Optional, Protocol

import randomname
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_openai import AzureChatOpenAI
from loguru import logger
from PIL import Image
from langchain_core.runnables import RunnablePassthrough, RunnableParallel, RunnableLambda, RunnableSequence, Runnable
import src.llm.prompt as prompt
from src.llm.places import PlacesTool
from src.settings import Settings

class ImageEncoder:
    @staticmethod
    def encode(image_path: str) -> tuple[str, str]:
        format = Image.open(image_path).format.lower()
        match format:
            case "jpg" | "jpeg":
                mime_type = "image/jpeg"
            case "png":
                mime_type = "image/png"
            case _:
                raise ValueError(f"Unsupported image format: {format}")

        with open(image_path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode("utf-8")
        return encoded, mime_type

class LLMChain(Protocol):
    async def ainvoke(self, inputs: dict, config: Optional[dict] = None) -> str:
        ...

class ImageTranscriptionChain:
    def __init__(self, llm: AzureChatOpenAI):
        self._chain = self._build_chain(llm)

    @property
    def chain(self) -> Runnable:
        return self._chain

    def _build_chain(self, llm: AzureChatOpenAI) -> LLMChain:
        def _prompt_generator(data_dict: dict):
            return [
                HumanMessage(
                    content=[
                        {"type": "text", "text": prompt.VISION_TOOL},
                        {"type": "image_url", "image_url": {"url": f"data:{data_dict['format']};base64,{data_dict['image']}", 
                                                            "detail": data_dict['detail']}},
                    ],
                )
            ]
        return _prompt_generator | llm | JsonOutputParser()

class VcfGeneratorChain:
    def __init__(self, llm: AzureChatOpenAI):
        self._chain = self._build_chain(llm)
    
    @property
    def chain(self) -> Runnable:
        return self._chain

    def _build_chain(self, llm: AzureChatOpenAI) -> LLMChain:
        card_prompt = ChatPromptTemplate.from_messages([
            ("system", prompt.AGENT_SYSTEM),
            ("ai", "JSON:\n{vision_transcription}"),
            ("human", prompt.AGENT_TOOL),
        ])
        return card_prompt | llm | StrOutputParser()

class ToolFactory:
    def __init__(self, settings: Settings):
        llm = self._create_llm(settings)
        self._vision_chain = ImageTranscriptionChain(llm)
        self._agent_chain = VcfGeneratorChain(llm)
        self._venue_processor = VenueProcessor(settings)

    def _get_settings_args(self, settings: Settings) -> dict:
        args = {
            "api_key": settings.AZURE_OPENAI_API_KEY,
            "openai_api_version": settings.AZURE_OPENAI_API_VERSION,
            "azure_endpoint": settings.AZURE_OPENAI_API_BASE,
            "streaming": False,
            "metadata": {"container_app_name": settings.CONTAINER_APP_NAME},
        }
        if settings.LANGSMITH_TRACER:
            args["callbacks"] = [settings.LANGSMITH_TRACER]
        return args

    def _create_llm(self, settings: Settings, *args, **kwargs) -> AzureChatOpenAI:
        default_args = {
            "azure_deployment": settings.AZURE_OPENAI_DEPLOYMENT_VISION,
            "model_name": "gpt-4o-mini",
            "max_tokens": 500,
        }
        common_client_args = self._get_settings_args(settings) | default_args | kwargs

        return AzureChatOpenAI(
            *args,
            **common_client_args,
        )
    
    @property
    def image_transcription(self) -> Runnable:
        return self._vision_chain.chain

    @property
    def card_generation(self) -> Runnable:
        return self._agent_chain.chain

    @property
    def venue_description(self) -> Runnable:
        return self._venue_processor
    
class CardAgent:
    def __init__(self, settings: Settings):
        self._tool_factory = ToolFactory(settings)
        self._chain = self._build_chain()

    def _build_chain(self) -> RunnableSequence:
        return (
            {
                "vision_transcription": self._tool_factory.image_transcription,
                "args": RunnablePassthrough(),
            }
            | self._tool_factory.venue_description
            | self._tool_factory.card_generation
            | self._vcf_parser
        )

    async def create_card(self, image_path: str, lat: float, lon: float, detail: str = "low") -> Optional[str]:
        image, format = ImageEncoder.encode(image_path)
        
        try:
            result = await self._chain.ainvoke({"image": image, "format": format, "detail": detail, "lat": lat, "lon": lon}, 
                                               config={"run_name": randomname.get_name()})
            return result
        except Exception as e:
            logger.exception(f"Error creating card: {e}")
            return None

    @staticmethod
    def _vcf_parser(card: str) -> str:
        BEGIN_CARD, END_CARD = "BEGIN:VCARD", "END:VCARD"
        idx_start = card.find(BEGIN_CARD)
        idx_end = card.find(END_CARD)
        return card[idx_start : idx_end + len(END_CARD)]

class VenueProcessor(Runnable):
    def __init__(self, settings: Settings):
        self._places = PlacesTool(settings)

    def invoke(self, inputs: dict, *args) -> dict:
        vision_transcription = inputs['vision_transcription']
        lat = inputs['args']['lat']
        lon = inputs['args']['lon']

        if isinstance(vision_transcription, str):
            vision_transcription = json.loads(vision_transcription.strip("`").lstrip("json"))

        if isinstance(vision_transcription, dict):
            query = " ".join([value for key, value in vision_transcription.items() if "venue" in key])

        if query:
            try:
                result = self._places.simple_search(query, lat, lon)
                if result:
                    return {"vision_transcription": json.dumps(result)}
            except Exception:
                logger.exception("Error parsing vision")
        
        return {"vision_transcription": vision_transcription}

@cache
def build_agent():
    from src.settings import get_settings
    settings = get_settings()
    return CardAgent(settings)

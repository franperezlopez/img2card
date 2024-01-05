import types
from unittest.mock import AsyncMock

import pytest
from pytest_mock import MockerFixture


@pytest.mark.asyncio
async def test_generate_vision(mocker: MockerFixture, exif_image_path: str, vision_venue_data: str, mocked_client_ainvoke: AsyncMock):
    settings = mocker.MagicMock()
    response = types.SimpleNamespace()
    response.content = vision_venue_data
    mocked_client_ainvoke.return_value = response

    from src.llm.agent import OpenAITool
    tool = OpenAITool(settings)
    vision = await tool.generate_vision(exif_image_path)

    mocked_client_ainvoke.assert_called_once()
    assert vision == vision_venue_data

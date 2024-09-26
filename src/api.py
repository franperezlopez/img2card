from pathlib import Path
from typing import Annotated, Optional
from fastapi import Depends, FastAPI, File, UploadFile, BackgroundTasks, middleware
from fastapi.responses import FileResponse
from PIL import Image
import os
import tempfile
from loguru import logger
from fastapi.middleware.cors import CORSMiddleware

from src.llm.agent import CardAgent, build_agent
from src.llm.places import EXIFHelper
from src.utils import is_empty
from dataclasses import dataclass
from pydantic import BaseModel
from loguru import logger

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001", "http://localhost:3000"],  # Add your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Location(BaseModel):
    latitude: float
    longitude: float

async def call_agent(agent: CardAgent, image_url, detail: str = "low", location: Optional[Location] = None):
    logger.info("Calling agent ...")
    kwargs = {}
    if location:
        kwargs["lat"] = location.latitude
        kwargs["lon"] = location.longitude
    event = await agent.create_card(image_url, detail=detail, **kwargs)
    return event


async def handle_image(agent: CardAgent, image_path: str, detail: str = "low", location: Optional[Location] = None):
    def _normalize_fn(text: str):
        term = "FN:"
        idx = text.find(term)
        idx_end = text.find("\n", idx)
        return text[idx + len(term) : idx_end]

    def _normalize_tel(text: str):
        for term in ["TEL:", "TEL;"]:
            idx = text.find(term)
            if idx > -1:
                break
        if idx == -1:
            return "111 222 333"
        idx_end = text.find("\n", idx)
        sub_text = text[idx + len(term) : idx_end]
        if sub_text.find(":") > -1:
            return sub_text.split(":")[-1]
        else:
            return "".join(re.findall("\d", sub_text))

    def _normalize_vcf(vcf: str):
        return vcf.encode('latin-1', errors='ignore').decode('latin-1')

    # Process the image and generate the ICS file
    vcf_data = await call_agent(agent, image_path, detail, location)
    vcf_data = vcf_data.encode("utf7", "ignore").decode("utf7")
    logger.debug(f"vcf_data: {vcf_data}")

    # Send the card (file) to the user
    if vcf_data:
        phone_number = _normalize_tel(vcf_data)
        first_name = _normalize_fn(vcf_data)
        if is_empty(phone_number) or is_empty(first_name):
            raise ValueError("No se pudo generar la tarjeta.")
        else:
            return phone_number, first_name, _normalize_vcf(vcf_data)
    else:
        raise ValueError("No se pudo generar la tarjeta.")


def delete_file(file_path: Path):
    if file_path.exists():
        logger.info(f"Deleting file: {file_path}")
        os.remove(file_path)

@app.post("/get_ics_card/")
async def get_ics_card(background_tasks: BackgroundTasks, 
                       # location: Optional[Location],
                       latitude: Optional[float] = None,
                       longitude: Optional[float] = None,
                       photo: UploadFile = File(...), 
                       # location: Optional[Location] = Depends(),
                       agent: CardAgent = Depends(build_agent)):
    # Save the uploaded image file using a temporary directory
    with tempfile.NamedTemporaryFile() as photo_file:
        photo_file.write(await photo.read())

        img = Image.open(photo_file)
        lat, lon = EXIFHelper.extract_coordinates(img)
        location = Location(latitude=lat or latitude, longitude=lon or longitude)
        _, first_name, vcf_data = await handle_image(agent, photo_file.name, location=location)

        # Create a new temporary directory
        vcf_file_name = f"{first_name or 'event'}.vcf"
        card_file = tempfile.NamedTemporaryFile(delete=False)
        vcf_file_path = Path(card_file.name)
        
        # Save the vcf_data to the file
        with open(vcf_file_path, "w") as vcf_file:
            vcf_file.write(vcf_data)        

        # Add the file deletion task to the background tasks
        background_tasks.add_task(delete_file, vcf_file_path)

        return FileResponse(str(vcf_file_path), media_type='text/calendar', filename=vcf_file_name)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
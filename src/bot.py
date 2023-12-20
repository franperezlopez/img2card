import html
import json
import re
import tempfile
import traceback
from enum import IntEnum
from typing import Optional

from loguru import logger
from PIL import Image
from telegram import Location, ReplyKeyboardRemove, Update
from telegram.constants import ChatAction, ParseMode
from telegram.ext import (ApplicationBuilder, CommandHandler, ContextTypes,
                          ConversationHandler, MessageHandler, filters)

from src.llm.agent import build_agent
from src.llm.places import EXIFHelper
from src.settings import get_settings

settings = get_settings()

class States(IntEnum):
    START = 1
    PHOTO = 2
    OK_GPS = 3
    NO_GPS = 4
    CARD = 5
    END = 6

PHOTO = 1
NO_GPS = 2

async def call_agent(image_url, detail: str, location: Optional[Location] = None):
    logger.info("Calling agent ...")
    agent = build_agent()
    kwargs = {}
    if location:
        kwargs["lat"] = location.latitude
        kwargs["lon"] = location.longitude
    event = await agent.create_card(image_url, detail, **kwargs)
    logger.info(event)
    return event


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info("Start command ...")
    await update.message.reply_text("Bienvenido! Para convertir una imagen en una tarjeta de contacto, envíame una imagen.", 
                                    reply_markup=ReplyKeyboardRemove())

    return PHOTO

async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info("Handling photo ...")

    if len(update.message.photo) > 0:
        # compressed image -> ask geolocation
        photo = await context.bot.get_file(update.message.photo[-1])
        if context.user_data.get("location"):
            await _handle_image(update, context, photo, detail="high", location=context.user_data["location"])
            return ConversationHandler.END
        context.chat_data["photo"] = photo
        await update.message.reply_text("¿Puedes enviarme tu ubicación?", 
                                        reply_markup=ReplyKeyboardRemove())
        return NO_GPS
    else:
        # uncompressed image -> do card
        # TODO: refactor creating TelegramImage class
        photo = await context.bot.get_file(update.message.document)
        img = Image.open(photo)
        lat, lon = EXIFHelper.extract_coordinates(img)
        if lat and lon:
            await _handle_image(update, context, photo, detail="low")
            return ConversationHandler.END
        elif context.user_data.get("location"):
            await _handle_image(update, context, photo, detail="low", location=context.user_data["location"])
            return ConversationHandler.END
        else:
            context.chat_data["photo"] = photo
            await update.message.reply_text("¿Puedes enviarme tu ubicación?", 
                                            reply_markup=ReplyKeyboardRemove())
            return NO_GPS


async def location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info("Handling location ...")

    if update.message.location:
        # location -> do card
        photo = context.chat_data["photo"]
        context.user_data["location"] = update.message.location
        await _handle_image(update, context, photo, detail="high", location=update.message.location)
        return ConversationHandler.END
    else:
        # no location -> ask for location
        await update.message.reply_text("¿Puedes enviarme tu ubicación?", 
                                        reply_markup=ReplyKeyboardRemove())
        return NO_GPS

# async def handle_image_compressed(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     logger.info("Handling image compressed ...")

#     photo = await context.bot.get_file(update.message.photo[-1])
#     await _handle_image(update, context, photo)


# async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     # Get the image file from the message
#     logger.info("Handling image ...")

#     # user = update.message.from_user
#     await update.message.reply_chat_action(action=ChatAction.UPLOAD_PHOTO)
#     photo = await context.bot.get_file(update.message.document)
#     await _handle_image(update, context, photo)


async def _handle_image(update, context, photo, detail: str, location: Optional[Location] = None):
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

    # Download the image file and save it to a temporary file
    with tempfile.NamedTemporaryFile(delete=True) as f:
        image_path = f.name
        await photo.download_to_drive(image_path)

        # Process the image and generate the ICS file
        await update.message.reply_chat_action(action=ChatAction.TYPING)
        vcf_data = await call_agent(image_path, detail, location)

    # Send the card (file) to the user
    if vcf_data:
        phone_number = _normalize_tel(vcf_data)
        first_name = _normalize_fn(vcf_data)
        await update.message.reply_contact(phone_number=phone_number, first_name=first_name, vcard=vcf_data)
    else:
        await update.message.reply_text("No se pudo generar la tarjeta.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    logger.info("Help command ...")
    await update.message.reply_text("Help for you ...")


async def echo_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    logger.info(f"Echo command ... {update.message.text}")
    await update.message.reply_text(update.message.text)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception(context.error)
    dev_chat_id = settings.TELEGRAM_DEV_CHAT_ID
    if dev_chat_id:
        update_str = update.to_dict() if isinstance(update, Update) else str(update)
        tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
        tb_string = "".join(tb_list)
        message = (
            f"An exception was raised while handling an update\n"
            f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
            "</pre>\n\n"
            f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
            f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
            f"<pre>{html.escape(tb_string)}</pre>"
        )
        await context.bot.send_message(chat_id=dev_chat_id, text=message, parse_mode=ParseMode.HTML)


async def cancel(update, context):
    """Cancel the current operation and end the conversation"""
    update.message.reply_text("Operación cancelada.")
    return ConversationHandler.END


def main():
    # Set up the Telegram bot
    app = ApplicationBuilder().token(settings.TELEGRAM_TOKEN).build()

    # Set up the message handler for images
    # app.add_handler(MessageHandler(filters.PHOTO, handle_image_compressed))
    # app.add_handler(MessageHandler(filters.Document.IMAGE, handle_image))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_command))
    # app.add_handler(CommandHandler("help", help_command))

        # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            # GENDER: [MessageHandler(filters.Regex("^(Boy|Girl|Other)$"), gender)],
            PHOTO: [MessageHandler(filters.PHOTO | filters.Document.IMAGE, photo)],
            # PHOTO: [MessageHandler(filters.ALL, photo)],
            NO_GPS: [MessageHandler(filters.LOCATION, location)],
            # BIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, bio)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)

    app.add_error_handler(error_handler)

    # Start the bot
    logger.info("Starting bot ...")
    logger.info(settings.model_dump())

    if settings.TELEGRAM_WEBHOOK_URL:
        # preferred method for production
        app.run_webhook(
            listen="0.0.0.0",
            webhook_url=settings.TELEGRAM_WEBHOOK_URL,
            port=80,
            allowed_updates=Update.ALL_TYPES,
            secret_token=settings.TELEGRAM_SECRET,
            drop_pending_updates=True,
        )
    else:
        # preferred method for development
        app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

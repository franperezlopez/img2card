import html
import io
import json
import tempfile
import traceback
import re

from loguru import logger
from telegram import InputFile, Update
from telegram.constants import ParseMode, ChatAction
from telegram.ext import (ApplicationBuilder, CallbackContext, CommandHandler,
                          ContextTypes, MessageHandler, Updater, filters)

from src.llm.agent import make_agent
from src.settings import get_settings


settings = get_settings()

async def call_agent(image_url):
    logger.info("Processing image ...")
    agent = make_agent()
    event = await agent.create_card(image_url)
    logger.info(event)
    return event

async def handle_image_compressed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Handling image2 ...")

    photo = await context.bot.get_file(update.message.photo[-1])
    await _handle_image(update, context, photo)


async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Get the image file from the message
    logger.info("Handling image ...")

    # user = update.message.from_user
    await update.message.reply_chat_action(action=ChatAction.UPLOAD_PHOTO)
    photo = await context.bot.get_file(update.message.document)
    await _handle_image(update, context, photo)

async def _handle_image(update, context, photo):
    # Download the image file and save it to a temporary file
    with tempfile.NamedTemporaryFile(delete=True) as f:
        image_path = f.name
        await photo.download_to_drive(image_path)

        # Process the image and generate the ICS file
        await update.message.reply_chat_action(action=ChatAction.TYPING)
        vcf_data = await call_agent(image_path)

    # Send the card (file) to the user
    if vcf_data:
        match = re.search(r'\b(\+\d{1,3}\s?)?(\()?(\d{3})(?(2)\))[-.]?\d{3}[-.]?\d{4}\b', vcf_data)
        if match:
            phone_number = match.group(0)
        else:
            phone_number = "111 222 333"
        await update.message.reply_contact(phone_number=phone_number, first_name="Test bot", vcard=vcf_data)
    else:
        await update.message.reply_text("No event found in image")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    logger.info("Help command ...")
    await update.message.reply_text("Help for you ...")


async def echo_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    logger.info("Echo command ...")
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
            f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}" "</pre>\n\n"
            f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
            f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
            f"<pre>{html.escape(tb_string)}</pre>"
        )
        await context.bot.send_message(chat_id=dev_chat_id, text=message, parse_mode=ParseMode.HTML)


def main():
    # Set up the Telegram bot
    app = ApplicationBuilder().token(settings.TELEGRAM_TOKEN).build()

    # Set up the message handler for images
    app.add_handler(MessageHandler(filters.PHOTO, handle_image_compressed))
    app.add_handler(MessageHandler(filters.Document.IMAGE, handle_image))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_command))
    app.add_handler(CommandHandler("help", help_command))

    app.add_error_handler(error_handler)

    # Start the bot
    logger.info("Starting bot ...")
    logger.info(settings.model_dump)
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
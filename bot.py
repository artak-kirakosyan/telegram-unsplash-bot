#!/usr/bin/env python
try:
    import os
    from datetime import datetime
    from uuid import uuid4

    from telegram import ParseMode
    from telegram import Update
    from telegram import InlineQueryResultArticle
    from telegram import InputTextMessageContent
    from telegram.ext import InlineQueryHandler
    from telegram.ext import Updater
    from telegram.ext import Filters
    from telegram.ext import CallbackContext
    from telegram.ext import MessageHandler
    from telegram.ext import CommandHandler
    from telegram.utils.request import Request
    from telegram.utils.helpers import escape_markdown
    from telegram import Bot

    from unsplash_client import UnsplashClient, UnsplashThread
    from common import get_logger
    
except ImportError as e:
    print(f'Error occured during import: {e}')
    print('Please install all necessary libraries and try again')
    exit(1)


logger = get_logger(
        logger_name="UNSPLASHBOT",
        file_name="logs/bot.log",
        )
unsplash_client = UnsplashClient("configuration.json")


def log_error(func):
    def inner(*args, **kwargs):
        try:
            logger.info(f"Calling function {func.__name__}")
            return func(*args, **kwargs)
            logger.info(f"Finished function {func.__name__}")
        except Exception as e:
            logger.exception(f"Exception during {func.__name__} call: {e}")
            raise e
    return inner


@log_error
def do_help(update: Update, context: CallbackContext):
    reply = "I am designed to send awesome pictures from Unsplash.\
            \nHit /random to get one image or /random n to get n images.\
            \nPlease note that I cant send more than 5 at once :/"
    update.message.reply_text(
            text=reply,
    )


@log_error
def do_start(update: Update, context: CallbackContext):
    reply = f"Hey {update.message.from_user.first_name}. Welcome onboard.\
            \nTo begin, type /help."
    update.message.reply_text(
            text=reply,
    )


@log_error
def get_random(update: Update, context: CallbackContext):
    if not hasattr(update, "message"):
        return
    if not hasattr(update.message, "text"):
        return
    if context.args:
        num = context.args[0]
        try:
            num = int(num)
        except ValueError as e:
            num = 1
        num = min(num, 5)
        num = max(num, 1)
    else:
        num = 1
    thr = UnsplashThread(
            unsplash_client=unsplash_client,
            bot=context.bot,
            chat_id=update.message.chat_id,
            num_of_images=num,
            )
    thr.start()


@log_error
def do_not_understand(update: Update, context: CallbackContext):
    if not hasattr(update, "message"):
        return
    if not hasattr(update.message, "text"):
        return

    reply = f"Hmm, not sure if I get you right :/\
            \nHit /random to get a random image."
    update.effective_message.reply_text(
            text=reply,
            )


@log_error
def inlinequery(update, context):
    """Handle the inline query."""
    results = []
    
    results = [
        InlineQueryResultArticle(
            id=0,
            title="Caps",
            input_message_content=InputTextMessageContent(
                query.upper())),
        InlineQueryResultArticle(
            id=1,
            title="Bold",
            input_message_content=InputTextMessageContent(
                "<b>{}</b>".format(escape_markdown(query)),
                parse_mode=ParseMode.HTML)),
        InlineQueryResultArticle(
            id=2,
            title="Italic",
            input_message_content=InputTextMessageContent(
                "<i>{}</i>".format(escape_markdown(query)),
                parse_mode=ParseMode.HTML))]

    update.inline_query.answer(results)


def setup_updater():
    __TG_TOKEN = os.getenv("TG_TOKEN")

    req = Request(
            connect_timeout=5,
            )
    bot = Bot(
            token=__TG_TOKEN,
            request=req,
            #base_url='https://telegg.ru/orig/bot',
            )
    updater = Updater(
            bot=bot,
            use_context=True,
            )
    bot_getme = updater.bot.get_me()
    dp = updater.dispatcher
    print(f"Bot {bot_getme.first_name} is live now") 

    random_handler = CommandHandler("random", get_random)
    help_handler = CommandHandler("help", do_help)
    start_handler = CommandHandler("start", do_start)
    dont_understand_handler = MessageHandler(Filters.all, do_not_understand) 
    inline_handler = InlineQueryHandler(inlinequery)

    dp.add_handler(random_handler)
    dp.add_handler(start_handler)
    dp.add_handler(help_handler)
    dp.add_handler(dont_understand_handler)
    dp.add_handler(inline_handler)

    return updater


def main():
    updater = setup_updater()
    updater.start_polling()
    updater.idle()
    print("Done, quitting")


if __name__ == "__main__":
    main()

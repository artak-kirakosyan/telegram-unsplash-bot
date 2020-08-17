#!/usr/bin/env python
try:
    import os
    from datetime import datetime

    from telegram import Update
    from telegram.ext import Updater
    from telegram.ext import Filters
    from telegram.ext import CallbackContext
    from telegram.ext import MessageHandler
    from telegram.ext import CommandHandler
    from telegram.utils.request import Request
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
PORT = int(os.environ.get('PORT', 5000))


def log_error(func):
    def inner(*args, **kwargs):
        try:
            logger.info(f"Calling function {func.__name__}")
            return func(*args, **kwargs)
            logger.info(f"Finished function {func.__name__}")
        except Exception as e:
            logger.exception("Exception during {func.__name__} call: {e}")
            raise e
    return inner


@log_error
def do_help(update: Update, context: CallbackContext):
    reply = "I am designed to send amazing pictures from Unsplash to you.\
            \nHit /random to get one or /random n to get n images.\
            \n Keep in mind tha the maximum is 5.\
            \nPlease ba patient and do not exhaust the bot :)."
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


def main():

    #__TG_TOKEN = os.getenv("TG_TOKEN")
    __TG_TOKEN = "1191619905:AAFPOxGzqiGRaCFwMu-sqg8KkjgZLP3Z4xo"
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

    print(f"Bot {bot_getme.first_name} is live now") 

    random_handler = CommandHandler("random", get_random)
    help_handler = CommandHandler("help", do_help)
    start_handler = CommandHandler("start", do_start)
    
    updater.dispatcher.add_handler(random_handler)
    updater.dispatcher.add_handler(start_handler)
    updater.dispatcher.add_handler(help_handler)

    #updater.start_polling()
    updater.start_webhook(listen="0.0.0.0",
            port=PORT,
            url_path=__TG_TOKEN,
            )
    updater.bot.setWebhook('https://unsplash-bot.herokuapp.com/' + __TG_TOKEN)
    updater.idle()
    print("Done, quitting")


if __name__ == "__main__":
    main()

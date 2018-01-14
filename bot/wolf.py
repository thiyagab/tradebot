#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Simple Bot to reply to Telegram messages.

This program is dedicated to the public domain under the CC0 license.

This Bot uses the Updater class to handle the bot.

First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging
import sys

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import ParseMode, Chat
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler,
                          ConversationHandler, CallbackQueryHandler)

from bot import db, data
from bot.schedulers import Scheduler
from alerts.twitter import fromtwitter

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

MAKECALL, SYMBOL, QUERY = range(3)
INVALIDSYNTAX, INVALIDSYMBOL, GENERALERROR = range(3)
VERSION = 'v0.0.6'

HELPTXT = 'The wolf (' + VERSION + ') is here to help you with your stock queries\n\n' \
          + 'Ask me anything here /q\n' \
          + '1.Give me a symbol, I will give you the quote\n' \
          + "2.Say 'Buy infy@9000 sl@990', i will add it in calls\n" \
          + "3.Say 'Calls', I will give you the last 4 calls in the group\n"

STARTCONV = 'How can I /help you?'

SYNTAX = "Make a call in this format\n" \
         "BUY|SELL 'symbol'@'pricerange' SL@'pricerange'\n" \
         "e.g BUY INFY@1000-1005 SL@995\n" \
         "For futures:\n" \
         "e.g BUY CGPOWER.JAN@92\n"

errormsgs = {INVALIDSYNTAX: "syntax oyunga kudra\n", INVALIDSYMBOL: "Symbol thappu.", GENERALERROR: "Unknown Error!"}


# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
def start(bot, update):
    """Send a message when the command /start is issued."""
    update.message.reply_text(HELPTXT)
    return QUERY


def help(bot, update):
    """Send a message when the command /help is issued."""
    update.message.reply_text(HELPTXT)
    return nextconversation(update)


def echo(bot, update):
    """Echo the user message."""
    update.message.reply_text(update.message.text)


def quote(bot, update):
    try:
        text = update.message.text
        if text.startswith("/q"):
            parttext = text.partition(' ')
            if parttext[2]:
                symbol = parttext[2].upper()
                return replyquote(symbol, update)
            else:
                if isgroup(update):
                    update.message.reply_text('nse symbol?\n(for futures, <symbol> <month>')
                else:
                    update.message.reply_text(STARTCONV)
                return QUERY
        else:
            return replyquote(text.upper(), update)
    except:
        logger.warning('quote error "%s"', error)
        update.message.reply_text("Invalid symbol or unknown error!")
        return nextconversation(update)


def nextconversation(update):
    if isgroup(update):
        return ConversationHandler.END
    else:
        return QUERY


def isgroup(update):
    type = update.effective_chat.type
    return (type == Chat.GROUP or type == Chat.SUPERGROUP)


def replyquote(symbol, update, chat_id=None, message_id=None, bot=None):
    # when called from refresh action, update object wont have chatid
    if update.message:
        chat_id = update.message.chat_id
    stock =data.fetchquote(symbol)
    if stock:
        message = str(stock)
    else:
        message= "Couldnt find symbol. Try different query\n"
    message += getcalls(chat_id, symbol)

    if isgroup(update):
        message += "\n Make a /q"

    url = data.geturl(stock.sym)
    keyboard = [[InlineKeyboardButton("Refresh", callback_data='3' + stock.querysymbol), InlineKeyboardButton("More", url=url)],
                # [InlineKeyboardButton("Buy", callback_data='1' + symbol),
                #  InlineKeyboardButton("Sell", callback_data='2' + symbol)]
                ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    if bot:
        bot.edit_message_text(text=message,
                              chat_id=chat_id,
                              message_id=message_id, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
    else:
        update.message.reply_text(text=message, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
    return nextconversation(update)


def getcalls(chat_id, symbol=None):
    callstxt = db.getcalls(str(chat_id), symbol)

    if callstxt:
        callstxt = "Calls Made:\n==========\n" + callstxt
    else:
        callstxt = "No calls\n"

    callstxt += "==========\n"

    return callstxt


def button(bot, update):
    query = update.callback_query
    # Refresh and edit the same message
    if query.data.startswith('3'):
        symbol = query.data[1:]
        replyquote(symbol, update, chat_id=query.message.chat_id, message_id=query.message.message_id, bot=bot)
    else:
        query.message.reply_text("Not implemented yet")


def calls(bot, update):
    try:
        update.message.reply_text(getcalls(update.message.chat_id), parse_mode=ParseMode.HTML)
        return nextconversation(update)
    except Exception as e:
        update.message.reply_text("Error", e)
        return nextconversation(update)

def ipo(bot, update):
    try:
        update.message.reply_text(data.getnseipo(), parse_mode=ParseMode.HTML)
        return nextconversation(update)
    except Exception as e:
        update.message.reply_text("Error", e)
        return nextconversation(update)

def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def done(bot, update, user_data=None):
    update.message.reply_text("Happy trading")
    return nextconversation(update)


def call(bot, update):
    update.message.reply_text(SYNTAX, parse_mode=ParseMode.HTML)
    return MAKECALL



def watchlist(bot, update):
    try:
        watchlist=db.getwatchlist(str(update.message.chat_id))
        syslist=[row.sym for row in watchlist]
        names = [row.misc for row in watchlist]
        displaytext = ''
        if len(watchlist)>0:
            # TODO the syslist will be the names here, so swapping it, change to make better
            stocklist=data.fetchquotelist(names,syslist)
            for stock,watch in zip(stocklist,watchlist):
                user=watch.user
                sym=watch.sym
                addedprice=watch.callrange
                ltp=stock.ltp
                hi=stock.h
                low=stock.l
                displaytext+="<b>"+sym+"</b>"\
                    +"<pre>"\
                    +"\nAT  : "+addedprice+"    LTP : "+ltp\
                    +"\nHI  : "+hi+"    LO  : "+low\
                    +"\nBY  : "+user\
                    +"</pre>\n\n"
        if not displaytext:
            displaytext="Empty watchlist"
        update.message.reply_text(displaytext,parse_mode=ParseMode.HTML)
    except Exception as e:
        update.message.reply_text("Error in watchlist")
    return nextconversation(update)



def watch(bot,update,user_data=None):
    try:
        text = update.message.text.upper()
        tokens=text.partition(' ')
        if tokens[2]:
            stock=data.fetchquote(tokens[2])
            # reusing the same calls db with type as watch and using the misc column for query symbol
            db.createcall(type=db.WATCH_TYPE, symbol=stock.sym, callrange=stock.ltp,
                           misc=stock.querysymbol, user=update.message.from_user.first_name, chatid=str(update.message.chat_id),
                           userid=str(update.message.from_user.id))
            update.message.reply_text(text="Added to watchlist\n" + str(stock), parse_mode=ParseMode.HTML)
            db.deleteoldwatchlist()
        else:
            update.message.reply_text("Nothing to add")
    except Exception as e:
        update.message.reply_text("Error adding to watchlist")
    return nextconversation(update)

def makecall(bot, update, user_data):
    try:
        text = update.message.text.upper()
        if text.startswith('SKIP'):
            return done(bot, update, user_data)
        if not validatecall(text):
            errorreplytocall(update, INVALIDSYNTAX)
            return MAKECALL

        type, symbol, callrange, desc = tokenizecallquery(text)

        quote = ''
        try:
            quote = str(data.fetchquote(symbol))
        except:
            errorreplytocall(update, INVALIDSYMBOL)
            return MAKECALL

        db.createcall(type=type, symbol= symbol, callrange= callrange, desc= desc, user=update.message.from_user.first_name, chatid=str(update.message.chat_id),
                       userid=str(update.message.from_user.id))
        update.message.reply_text(text="Call made\n" + quote, parse_mode=ParseMode.HTML)
        db.deleteoldcalls()

    except:
        print("Unexpected error:", sys.exc_info()[0])
        errorreplytocall(update, GENERALERROR)

    return nextconversation(update)


def tokenizecallquery(text):
    tokens = text.partition(' ')
    type = tokens[0]
    tokens = tokens[2].partition('@')
    symbol = tokens[0].strip()
    tokens = tokens[2].strip().partition(' ')
    callrange = tokens[0].strip()
    desc = tokens[2]
    return type, symbol, callrange, desc


def validatecall(text):
    tarr = text.split(' ')
    if not text.startswith('BUY') and not text.startswith('SELL') or \
            len(text) > 50 or len(tarr) < 2 or '@' not in text:
        return False

    return True


def errorreplytocall(update, errortype):
    message = "Hi " + getusername(
        update.message.from_user.first_name) + ",\n" + errormsgs[errortype] + "\nTry again or type 'skip' to cancel"
    update.message.reply_text(text=message, parse_mode=ParseMode.HTML)


def getusername(name):
    return name


def deletecall(symbol, update):
    userid = update.message.from_user.id
    chatid = update.message.chat_id
    rowcount = db.deletecall(symbol, userid, chatid)
    if rowcount > 0:
        update.message.reply_text("Call for " + symbol + " deleted")
    else:
        update.message.reply_text("No calls for symbol " + symbol)


def query(bot, update):
    command = update.message.text.upper().partition(' ')[2]
    if command:
        update.message.text = command
        return processquery(bot, update, None)
    else:
        update.message.reply_text(STARTCONV)
        return QUERY


def alerts(bot, update):
    replytxt = db.getalerts(str(update.message.chat_id))
    update.message.reply_text("Alerts:\n" + (replytxt if replytxt else 'None'))
    return nextconversation(update)


def alert(bot, update):
    commands = update.message.text.upper().partition(' ')[2]
    # split(r'(>+|<+)')
    if '>' in commands:
        commands = commands.split('>')
        operation = '>'
    elif '<' in commands:
        commands = commands.split('<')
        operation = '<'

    price = commands[1].strip()
    symbol = commands[0].strip()
    if symbol not in data.symbolmap.keys():
        update.message.reply_text(symbol + " not supported")
        return nextconversation(update)

    chat_id = update.message.chat_id
    update.message.reply_text('Alert set for ' + symbol + " " + price)
    db.createalert(symbol, operation, price, str(chat_id))
    return nextconversation(update)


def processquery(bot, update, user_data):
    logger.info("Query: "+update.message.text)
    text = update.message.text.upper()
    try:
        # query may contain commands again, so process the commands too
        if text.startswith('/'):
            # ppl may use /q alerts or /q infy in private chat itself, lets process same as in group
            if text.startswith('/Q '):
                text = text[3:]
            else:
                text = text[1:]
        if text.startswith(('BUY', 'SELL', 'SHORT')):
            return makecall(bot, update, user_data)
        elif text.startswith('CALLS'):
            return calls(bot, update)
        elif text.startswith("HELP"):
            return help(bot, update)
        elif text=="WATCHLIST":
            return watchlist(bot,update)
        elif text.startswith("WATCH"):
            return watch(bot,update)
        elif text=="IPO":
            return ipo(bot, update)
        elif text == "Q":
            return quote(bot, update)
        elif text.startswith('ALERTS'):
            return alerts(bot, update)
        elif text.startswith('DELETE'):
            symbol = text.partition(' ')[2]
            return deletecall(symbol, update)
        elif text.startswith('ALERT'):
            return alert(bot, update)
        elif len(text) < 50:
            return quote(bot, update)
        else:
            update.message.reply_text("Not ready to handle this query")
    except:
        logger.error("Error processing query",sys.exc_info()[0])
        update.message.reply_text("Error")

    return nextconversation(update)


def setupnewconvhandler():
    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start), CommandHandler('q', query),
                      CommandHandler('help', help),
                      CommandHandler('ipo', ipo),
                      CommandHandler('watchlist', watchlist),
                      CommandHandler('cancel', done)],

        states={
            QUERY: [MessageHandler(Filters.text,
                                   processquery,
                                   pass_user_data=True),

                    MessageHandler(Filters.command, processquery, pass_user_data=True)
                    ]
        },

        fallbacks=[RegexHandler('^Done$', done, pass_user_data=True)]
    )
    return conv_handler


# TODO the updater is declared as global object, which may leeds to issues
# Need to find best way to receive notifications without having this wolf reference
def notifyalert(chatid, text,disable_web_page_preview=None,parse_mode=None):
    if updater and updater.bot:
        updater.bot.send_message(chat_id=chatid, text=text,
                                 disable_web_page_preview=disable_web_page_preview,
                                 parse_mode=parse_mode)



def setupconvhandler():
    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start), CommandHandler('quote', quote), CommandHandler('call', call),
                      CommandHandler('calls', calls),
                      CommandHandler('done', done),
                      CommandHandler('ipo', ipo)],

        states={
            SYMBOL: [MessageHandler(Filters.text,
                                    quote,
                                    pass_user_data=False),
                     ],
            MAKECALL: [MessageHandler(Filters.text,
                                      makecall,
                                      pass_user_data=True),
                       ]
        },

        fallbacks=[RegexHandler('^Done$', done, pass_user_data=True)]
    )
    return conv_handler


updater = None

#def schedulejobs():
    # updater.

def main():

    db.initdb()

    """Start the bot."""
    # Create the EventHandler and pass it your bot's token.
    global updater
    # 535372141:AAEgx8VtahWGWWUYhFcYR0zonqIHycRMXi0   - dev token
    # 534849104:AAHGnCHl4Q3u-PauqDZ1tspUdoWzH702QQc   - live token

    # updater = Updater("535372141:AAEgx8VtahWGWWUYhFcYR0zonqIHycRMXi0")  #Dev
    updater = Updater("534849104:AAHGnCHl4Q3u-PauqDZ1tspUdoWzH702QQc")  # Live

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    dp.add_handler(setupnewconvhandler())

    dp.add_handler(CallbackQueryHandler(button))

    # on noncommand i.e message - echo the message on Telegram
    # dp.add_handler(MessageHandler(Filters.text, echo))

    # log all errors
    dp.add_error_handler(error)

    logger.info("Starting the bot...")

    # Start the Bot
    updater.start_polling()
    scheduler = Scheduler(bot=updater.bot)
    updater.job_queue.run_repeating(callback=scheduler.ipos,interval=12*60*60)

    fromtwitter.startstreaming(notifyalert)

    data.startstreaming(notifyalert)




    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    # updater.idle()


if __name__ == '__main__':
    main()

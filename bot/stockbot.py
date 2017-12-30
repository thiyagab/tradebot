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

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging
from web import quotefromnse
from telegram import ParseMode
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler,
                          ConversationHandler,CallbackQueryHandler)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

import sqlite3
from datetime import datetime
import sys
import webbrowser



# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

MAKECALL, SYMBOL = range(2)

dbname='calls.db'
equityurl='https://www.nseindia.com/live_market/dynaContent/live_watch/get_quote/GetQuote.jsp?symbol='
futureurl='https://www.nseindia.com/live_market/dynaContent/live_watch/get_quote/GetQuoteFO.jsp?instrument=FUTSTK&expiry=%s&underlying=%s'

conn = sqlite3.connect(dbname)
c=conn.cursor()
# Create table
c.execute('''CREATE TABLE IF NOT EXISTS calls
             (type text, symbol text, callrange text, slrange text, 
             user text,chatid text,userid text,time timestamp,
             PRIMARY KEY (symbol,chatid,userid))''')
c.close()


# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
def start(bot, update):
    """Send a message when the command /start is issued."""
    update.message.reply_text('Hi!')


def help(bot, update):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')


def echo(bot, update):
    """Echo the user message."""
    update.message.reply_text(update.message.text)


def quote(bot, update):
    try:
        print(update.message.text)
        text = update.message.text
        if text.startswith("/quote"):
            parttext=text.partition(' ')
            if parttext[2]:
                symbol = parttext[2].upper()
                return replyquote(symbol,update)
            else:
                update.message.reply_text('symbol?')
                return SYMBOL
        else:
            return replyquote(text.upper(), update)
    except:
        update.message.reply_text("Error!")
        return ConversationHandler.END


def replyquote(symbol,update):
    message=getcalls(update,symbol)
    message+=fetchquote(symbol)
    symbolandexpiry = symbol.partition(' ')
    url = equityurl+symbol
    if symbolandexpiry[2]:
        url=futureurl % (symbolandexpiry[2],symbolandexpiry[0])
    keyboard = [[InlineKeyboardButton("More", url=url)],
        [InlineKeyboardButton("Buy", callback_data='1'+symbol),
                 InlineKeyboardButton("Sell", callback_data='2'+symbol)]]

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(text=message, parse_mode=ParseMode.HTML,reply_markup=reply_markup)
    return ConversationHandler.END

def getcalls(update,symbol=None):
    chat_id=update.message.chat_id
    conn = sqlite3.connect(dbname,detect_types=sqlite3.PARSE_DECLTYPES)
    c = conn.cursor()
    sqlstr="SELECT * FROM calls where chatid='"+str(chat_id)+"'"
    if symbol:
        symbol = symbol.replace(" ", ".")
        sqlstr+="and symbol='"+symbol+"'"


    callstxt=''
    for row in c.execute(sqlstr):
        print(row)
        callstxt+=row[4]+" : "+row[0]+" "+row[1]+"@"+row[2]+" on <i>"+row[7].strftime('%b %d %H:%M')+ "</i>\n"

    if callstxt:
        callstxt="Calls Made:\n=================================\n"+callstxt
    else:
        callstxt="No calls\n"

    callstxt+="=================================\n"

    c.close()
    return callstxt


def button(bot, update):
    query = update.callback_query
    print(query.data)
    if query.data.startswith('3'):
        url=+query.data[1:]
        webbrowser.open(url)
    else:
        query.message.reply_text("Not implemented yet")

def calls(bot, update):
     # try:
        print(update.message.text)
        update.message.reply_text(getcalls(update),parse_mode=ParseMode.HTML)
        return ConversationHandler.END
     # except:
     #     update.message.reply_text("Error")
     #     return ConversationHandler.END


def fetchquote(symbol):
    symbolandexpiry=symbol.partition(' ')
    response = quotefromnse.fetchquote(symbol=symbolandexpiry[0],expiry=symbolandexpiry[2])
    quote = response['data'][0]
    pchange = quote['pChange']

    openkey='open'
    highkey='dayHigh'
    lowkey='dayLow'
    pclosekey='previousClose'

    if symbolandexpiry[2]:
        openkey='openPrice'
        highkey='highPrice'
        lowkey='lowPrice'
        pclosekey='prevClose'



    #changedir=':arrow_down:' if pChange.startswith('-') else ':arrow_up:'
    return '<b>'+symbol+'</b> @ <b>'+quote['lastPrice']+'</b> ( '+pchange+'% )\n'  \
            'open: '+quote[openkey]+'\n' \
            'high: '+quote[highkey]+'\n' \
            'low: '+quote[lowkey]+'\n' \
            'pClose: '+quote[pclosekey]


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def done(bot, update, user_data):
    update.message.reply_text("Happy trading")
    user_data.clear()
    return ConversationHandler.END

def call(bot, update):
    update.message.reply_text("Make a call in this format\nBUY|SELL <symbol>@<pricerange> SL@<pricerange>\ne.g BUY INFY@1000-1005 SL@995")
    return MAKECALL

def makecall(bot,update,user_data):
    try:
        text=update.message.text.upper()

        tarr=text.split(' ')
        type=tarr[0]
        symbol =tarr[1].split('@')[0]
        callrange = tarr[1].split('@')[1]
        slrange=''

        quote=fetchquote(symbol)

        if len(tarr) >2:
            slrange=tarr[2].split('@')[1]

        sqlstr='''INSERT OR REPLACE INTO calls VALUES (?,?,?,?,?,?,?,?)'''
        params= list()
        # (type text, symbol text, callrange text, slrange text, user text, chatid text, userid text
        params.append(type)
        params.append(symbol)
        params.append(callrange)
        params.append(slrange)
        params.append(update.message.from_user.first_name)
        params.append(update.message.chat_id)
        params.append(update.message.from_user.id)
        params.append(datetime.now())

        conn = sqlite3.connect(dbname)
        c = conn.cursor()
        c.execute(sqlstr,params)
        conn.commit()
        c.close()

        update.message.reply_text(text="Call made\n"+quote,parse_mode=ParseMode.HTML)
        deleteoldcalls()

    except:
        print("Unexpected error:", sys.exc_info()[0])
        message = "Hi "+update.message.from_user.first_name+",\n"+"Please try again with proper syntax or symbol from NSE\ne.g. BUY INFY@1010 SL@1005"
        update.message.reply_text(text=message, parse_mode=ParseMode.HTML)

    return ConversationHandler.END

def deleteoldcalls():
    conn = sqlite3.connect(dbname)
    c = conn.cursor()
    c.execute('delete from calls where time not in (select time from calls order by time desc limit 5)')
    conn.commit()
    c.close()


def main():
    """Start the bot."""
    # Create the EventHandler and pass it your bot's token.
    updater = Updater("534849104:AAHGnCHl4Q3u-PauqDZ1tspUdoWzH702QQc")

    print("Starting the bot...")

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
   # dp.add_handler(CommandHandler("start", start))
    #dp.add_handler(CommandHandler("help", help))

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('quote', quote),CommandHandler('call', call),CommandHandler('calls', calls)],

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

    dp.add_handler(conv_handler)
    dp.add_handler(CallbackQueryHandler(button))

    # on noncommand i.e message - echo the message on Telegram
   # dp.add_handler(MessageHandler(Filters.text, echo))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()

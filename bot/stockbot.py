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

MAKECALL, SYMBOL,QUERY = range(3)

dbname='calls.db'
equityurl='https://www.nseindia.com/live_market/dynaContent/live_watch/get_quote/GetQuote.jsp?symbol='
futureurl='https://www.nseindia.com/live_market/dynaContent/live_watch/get_quote/GetQuoteFO.jsp?instrument=FUTSTK&expiry=%s&underlying=%s'

INVALIDSYNTAX,INVALIDSYMBOL,GENERALERROR = range(3)

version ='v0.0.2'

helptext='The wolf ('+version+') is here to help you with your stock queries\n\n'\
                              +'Ask me anything here /q\n'\
                              +'1.Give me a symbol, I will give you the quote\n'\
                              +"2.Say 'Buy infy@9000 sl@990', i will add it in calls\n" \
                              +"3.Say 'Calls', I will give you the last 4 calls in the group\n"

SYNTAX="Make a call in this format\n" \
       "BUY|SELL 'symbol'@'pricerange' SL@'pricerange'\n" \
       "e.g BUY INFY@1000-1005 SL@995\n"\
        "For futures:\n"\
        "e.g BUY CGPOWER.JAN@92\n"

errormsgs={INVALIDSYNTAX:"syntax oyunga kudra\n",INVALIDSYMBOL:"Symbol thappu.",GENERALERROR:"Unknown Error!"}

FUTURES=('25JAN2018','22FEB2018','28MAR2018')

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
    update.message.reply_text(helptext)
    return ConversationHandler.END


def help(bot, update):
    """Send a message when the command /help is issued."""
    update.message.reply_text(helptext)
    return ConversationHandler.END


def echo(bot, update):
    """Echo the user message."""
    update.message.reply_text(update.message.text)


def quote(bot, update):
    try:
        print(update.message.text)
        text = update.message.text
        if text.startswith("/q"):
            parttext=text.partition(' ')
            if parttext[2]:
                symbol = parttext[2].upper()
                return replyquote(symbol,update)
            else:
                update.message.reply_text('nse symbol?\n(for futures, <symbol> <month>')
                return SYMBOL
        else:
            return replyquote(text.upper(), update)
    except:
        logger.warning('quote error "%s"', error)
        update.message.reply_text("Invalid symbol or unknown error!")
        return ConversationHandler.END


def replyquote(symbol,update,chat_id=None,message_id=None,bot=None):
    #when called from refresh action, update object wont have chatid
    if update.message:
        chat_id=update.message.chat_id

    message = fetchquote(symbol)
    message+=getcalls(chat_id,symbol)

    symbolandexpiry = symbol.partition(' ')
    url = equityurl+symbol
    if symbolandexpiry[2]:
        url=futureurl % (getexpiry(symbolandexpiry[2]),symbolandexpiry[0])
    keyboard = [[InlineKeyboardButton("Refresh", callback_data='3'+symbol),InlineKeyboardButton("More", url=url)],
        [InlineKeyboardButton("Buy", callback_data='1'+symbol),
                 InlineKeyboardButton("Sell", callback_data='2'+symbol)]]

    reply_markup = InlineKeyboardMarkup(keyboard)
    if bot:
        bot.edit_message_text(text=message,
                              chat_id=chat_id,
                              message_id=message_id,parse_mode=ParseMode.HTML,reply_markup=reply_markup)
    else:
        update.message.reply_text(text=message, parse_mode=ParseMode.HTML,reply_markup=reply_markup)
    return ConversationHandler.END

def getcalls(chat_id,symbol=None):

    conn = sqlite3.connect(dbname,detect_types=sqlite3.PARSE_DECLTYPES)
    c = conn.cursor()
    sqlstr="SELECT * FROM calls where chatid='"+str(chat_id)+"'"
    if symbol:
        sqlstr+="and symbol='"+symbol+"'"


    callstxt=''
    for row in c.execute(sqlstr):
        print(row)
        callstxt+=row[4]+" : "+row[0]+" "+row[1]+"@"+row[2]+\
                  " "+('SL@'+row[3] if row[3] else '') +\
                  " on <i>"+row[7].strftime('%b %d %H:%M')+ "</i>\n"

    if callstxt:
        callstxt="Calls Made:\n=============================\n"+callstxt
    else:
        callstxt="No calls\n"

    callstxt+="=============================\nmake a /q"

    c.close()
    return callstxt


def button(bot, update):
    query = update.callback_query
    print(query.data)
    # Refresh and edit the same message
    if query.data.startswith('3'):
        symbol=query.data[1:]
        replyquote(symbol,update,chat_id=query.message.chat_id,message_id=query.message.message_id,bot=bot)
    else:
        query.message.reply_text("Not implemented yet")

def calls(bot, update):
     try:
        print(update.message.text)
        update.message.reply_text(getcalls(update.message.chat_id),parse_mode=ParseMode.HTML)
        return ConversationHandler.END
     except:
         update.message.reply_text("Error")
         return ConversationHandler.END


def getexpiry(month):
    expiry=''
    # TODO HARDCODED FOR EXPIRY will change, find a better way
    if month:
        if 'JAN'in month:
            expiry=FUTURES[0]
        elif 'FEB'in month:
            expiry=FUTURES[1]
        elif 'MAR'in month:
            expiry=FUTURES[2]
    return expiry


def fetchquote(symbol):
    symbolandexpiry=symbol.partition(' ')

    expiry = getexpiry(symbolandexpiry[2])
    response = quotefromnse.fetchquote(symbol=symbolandexpiry[0],expiry=expiry)
    quote = response['data'][0]
    pchange = quote.get('pChange','-')

    openkey='open'
    highkey='dayHigh'
    lowkey='dayLow'
    pclosekey='previousClose'
    volumekey='totalTradedVolume'

    if symbolandexpiry[2]:
        openkey='openPrice'
        highkey='highPrice'
        lowkey='lowPrice'
        pclosekey='prevClose'
    #changedir=':arrow_down:' if pChange.startswith('-') else ':arrow_up:'
    return '<b>'+symbol+'@'+quote['lastPrice']+'</b> ( '+pchange+'% )\n\n'  \
            'o: '+quote[openkey]+ \
            '\th: '+quote[highkey]+'\n' \
            'l: '+quote[lowkey]+ \
            '\tc: '+quote[pclosekey]+'\n\n' \
            +'bestbid: '+quote['buyPrice1'] \
            +' bestoffer: '+quote['sellPrice1']+'\n' \
            +'buyqty: '+quote['totalBuyQuantity']\
            +' sellqty: '+quote['totalSellQuantity']+'\n'\
             +'<i>updated: ' + response.get('lastUpdateTime','-') + '</i>\n\n'

def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def done(bot, update, user_data=None):
    update.message.reply_text("Happy trading")
    return ConversationHandler.END

def call(bot, update):
    update.message.reply_text(SYNTAX,parse_mode=ParseMode.HTML)
    return MAKECALL


def makecall(bot,update,user_data):
    try:
        text=update.message.text.upper()
        tarr=text.split(' ')
        if text.startswith('SKIP'):
            return done(bot,update,user_data)
        if not validatecall(text):
            errorreplytocall(update,INVALIDSYNTAX)
            return MAKECALL
        type=tarr[0]
        symbol =tarr[1].split('@')[0]
        callrange = tarr[1].split('@')[1]
        slrange=''

        quote=''
        try:
            # for future the syntax is <symbol>.<month>, so replace by space
            symbol=symbol.replace('.',' ')
            quote=fetchquote(symbol)
        except:
            errorreplytocall(update,INVALIDSYMBOL)
            return MAKECALL

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
        errorreplytocall(update,GENERALERROR)

    return ConversationHandler.END

def validatecall(text):
    tarr= text.split(' ')
    if not text.startswith('BUY') and not text.startswith('SELL') or\
            len(text) > 50 or len(tarr) < 2 or '@' not in text:
        return False

    return True

def errorreplytocall(update,errortype):
    message = "Hi " + getusername(
        update.message.from_user.first_name) + ",\n" + errormsgs[errortype]+"\nTry again or type 'skip' to cancel"
    update.message.reply_text(text=message, parse_mode=ParseMode.HTML)

def getusername(name):
    return name

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




    dp.add_handler(setupnewconvhandler())
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


def query(bot, update):
    update.message.reply_text('How can I /help you?')
    return QUERY


def processquery(bot, update,user_data):
    print(update.message.text)
    text=update.message.text.upper()
    #query may contain commands again, so process the commands too
    if(text.startswith('/')):
        text=text[1:]
    if text.startswith(('BUY','SELL','SHORT')):
        return makecall(bot,update,user_data)
    elif text.startswith('CALLS'):
        return calls(bot,update)
    elif text=="HELP":
        return help(bot,update)
    elif text=="Q":
        return quote(bot,update)
    elif len(text) <50:
        return quote(bot,update)
    else:
        update.message.reply_text("Not ready to handle this query")
        return ConversationHandler.END




def setupnewconvhandler():
    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start), CommandHandler('q', query),
                      CommandHandler('help', help),
                      CommandHandler('cancel', done)],

        states={
            QUERY: [MessageHandler(Filters.text,
                                    processquery,
                                    pass_user_data=True),

                    MessageHandler(Filters.command,processquery,pass_user_data=True)
                     ]
        },

        fallbacks=[RegexHandler('^Done$', done, pass_user_data=True)]
    )
    return conv_handler


def setupconvhandler():
    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start), CommandHandler('quote', quote), CommandHandler('call', call),
                      CommandHandler('calls', calls),
                      CommandHandler('done', done)],

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

if __name__ == '__main__':
    main()

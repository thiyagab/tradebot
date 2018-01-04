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
from telegram import ParseMode,Chat
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler,
                          ConversationHandler,CallbackQueryHandler)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

import sys
from kiteconnect import WebSocket
from bot import dbhandler



# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

MAKECALL, SYMBOL,QUERY = range(3)

equityurl='https://www.nseindia.com/live_market/dynaContent/live_watch/get_quote/GetQuote.jsp?symbol='
futureurl='https://www.nseindia.com/live_market/dynaContent/live_watch/get_quote/GetQuoteFO.jsp?instrument=FUTSTK&expiry=%s&underlying=%s'

INVALIDSYNTAX,INVALIDSYMBOL,GENERALERROR = range(3)

version ='v0.0.4'

HELPTXT= 'The wolf (' + version + ') is here to help you with your stock queries\n\n' \
         +'Ask me anything here /q\n' \
         +'1.Give me a symbol, I will give you the quote\n' \
         +"2.Say 'Buy infy@9000 sl@990', i will add it in calls\n" \
         +"3.Say 'Calls', I will give you the last 4 calls in the group\n"

STARTCONV='How can I /help you?'

SYNTAX="Make a call in this format\n" \
       "BUY|SELL 'symbol'@'pricerange' SL@'pricerange'\n" \
       "e.g BUY INFY@1000-1005 SL@995\n"\
        "For futures:\n"\
        "e.g BUY CGPOWER.JAN@92\n"

errormsgs={INVALIDSYNTAX:"syntax oyunga kudra\n",INVALIDSYMBOL:"Symbol thappu.",GENERALERROR:"Unknown Error!"}

FUTURES=('25JAN2018','22FEB2018','28MAR2018')


# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
def start(bot, update):
    """Send a message when the command /start is issued."""
    update.message.reply_text(HELPTXT)
    return nextconversation(update)


def help(bot, update):
    """Send a message when the command /help is issued."""
    update.message.reply_text(HELPTXT)
    return nextconversation(update)


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


def replyquote(symbol,update,chat_id=None,message_id=None,bot=None):
    #when called from refresh action, update object wont have chatid
    if update.message:
        chat_id=update.message.chat_id

    message = fetchquote(symbol)
    message+=getcalls(chat_id,symbol)

    if isgroup(update):
        message+="\n Make a /q"

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
    return nextconversation(update)

def getcalls(chat_id,symbol=None):

    callstxt=getcalls(str(chat_id),symbol)

    if callstxt:
        callstxt="Calls Made:\n==========\n"+callstxt
    else:
        callstxt="No calls\n"

    callstxt+="==========\n"

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
        return nextconversation(update)
     except:
         update.message.reply_text("Error")
         return nextconversation(update)


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
    return '<b>'+symbol+'@'+quote['lastPrice']+'</b> ( '+pchange+'% )\n' \
           + '<i>updated: ' + response.get('lastUpdateTime', '-') + '</i>\n\n' \
           + 'o: '+quote[openkey]+ \
            '\th: '+quote[highkey]+'\n' \
            'l: '+quote[lowkey]+ \
            '\tc: '+quote[pclosekey]+'\n\n' \
            +'bestbid: '+quote['buyPrice1'] \
            +' bestoffer: '+quote['sellPrice1']+'\n' \
            +'buyqty: '+quote['totalBuyQuantity']\
            +' sellqty: '+quote['totalSellQuantity']+'\n\n'\


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def done(bot, update, user_data=None):
    update.message.reply_text("Happy trading")
    return nextconversation(update)

def call(bot, update):
    update.message.reply_text(SYNTAX,parse_mode=ParseMode.HTML)
    return MAKECALL


def makecall(bot,update,user_data):
    try:
        text=update.message.text.upper()
        if text.startswith('SKIP'):
            return done(bot,update,user_data)
        if not validatecall(text):
            errorreplytocall(update,INVALIDSYNTAX)
            return MAKECALL

        type,symbol,callrange,misc=tokenizecallquery(text)

        quote=''
        try:
            quote=fetchquote(symbol)
        except:
            errorreplytocall(update,INVALIDSYMBOL)
            return MAKECALL

        dbhandler.createcall(symbol,callrange,misc,update.message.from_user.first_name,update.message.chat_id,update.message.from_user.id)
        update.message.reply_text(text="Call made\n"+quote,parse_mode=ParseMode.HTML)
        dbhandler.deleteoldcalls()

    except:
        print("Unexpected error:", sys.exc_info()[0])
        errorreplytocall(update,GENERALERROR)

    return nextconversation(update)

def tokenizecallquery(text):
    tokens = text.partition(' ')
    type = tokens[0]
    tokens=tokens[2].partition('@')
    symbol=tokens[0].strip()
    tokens=tokens[2].strip().partition(' ')
    callrange=tokens[0].strip()
    addtext=tokens[2]
    return type, symbol, callrange,addtext

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




def deletecall(symbol,update):
    userid=update.message.from_user.id
    chatid=update.message.chat_id
    rowcount=dbhandler.deletecall(symbol,userid,chatid)
    if rowcount>0:
        update.message.reply_text("Call for " + symbol + " deleted")
    else:
        update.message.reply_text("No calls for symbol "+symbol)



updater=None
def main():

    dbhandler.initdb()

    """Start the bot."""
    # Create the EventHandler and pass it your bot's token.
    global updater
    #535372141:AAEgx8VtahWGWWUYhFcYR0zonqIHycRMXi0   - dev token
    #534849104:AAHGnCHl4Q3u-PauqDZ1tspUdoWzH702QQc   - live token

    updater = Updater("534849104:AAHGnCHl4Q3u-PauqDZ1tspUdoWzH702QQc")

    # Get the dispatcher to register handlers
    dp = updater.dispatcher




    dp.add_handler(setupnewconvhandler())

    dp.add_handler(CallbackQueryHandler(button))

    # on noncommand i.e message - echo the message on Telegram
   # dp.add_handler(MessageHandler(Filters.text, echo))

    # log all errors
    dp.add_error_handler(error)




    print("Starting the bot...")

    # Start the Bot
    updater.start_polling()

    startstreaming()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
   # updater.idle()


def query(bot, update):
    command=update.message.text.upper().partition(' ')[2]
    if command:
        update.message.text=command
        return processquery(bot,update,None)
    else:
        update.message.reply_text(STARTCONV)
        return QUERY

def alerts(bot,update):
    replytxt=dbhandler.getalerts(str(update.message.chat_id))
    update.message.reply_text("Alerts:\n"+(replytxt if replytxt else 'None'))
    return nextconversation(update)

def alert(bot,update):
    commands=update.message.text.upper().partition(' ')[2]
    #split(r'(>+|<+)')
    if '>' in commands:
        commands=commands.split('>')
        operation='>'
    elif '<' in commands:
        commands=commands.split('<')
        operation='<'

    price=commands[1].strip()
    symbol=commands[0].strip()
    if symbol not in symbolmap.keys():
        update.message.reply_text(symbol+" not supported")
        return nextconversation(update)

    chat_id=update.message.chat_id
    update.message.reply_text('Alert set for '+symbol+" "+price)
    dbhandler.createalert(symbol,operation,price,chat_id)
    return nextconversation(update)


def processquery(bot, update,user_data):
    print(update.message.text)
    text=update.message.text.upper()
    try:
        #query may contain commands again, so process the commands too
        if text.startswith('/'):
            #ppl may use /q alerts or /q infy in private chat itself, lets process same as in group
            if text.startswith('/Q '):
                text=text[3:]
            else:
                text=text[1:]
        if text.startswith(('BUY','SELL','SHORT')):
            return makecall(bot,update,user_data)
        elif text.startswith('CALLS'):
            return calls(bot,update)
        elif text.startswith("HELP"):
            return help(bot,update)
        elif text=="Q":
            return quote(bot,update)
        elif text.startswith('ALERTS'):
            return alerts(bot,update)
        elif text.startswith('DELETE'):
            symbol=text.partition(' ')[2]
            return deletecall(symbol,update)
        elif text.startswith('ALERT'):
            return alert(bot,update)
        elif len(text) <50:
            return quote(bot,update)
        else:
            update.message.reply_text("Not ready to handle this query")
    except:
        update.message.reply_text("Error")

    return nextconversation(update)




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

def notifyalert(chatid,text):
    if updater and updater.bot:
        updater.bot.send_message(chat_id=chatid,text=text)


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






kws = WebSocket(api_key="9oykkw4mc01lm5jf", public_token="V3mTjh6XbVQk3171IoWsn863qZsmBsDL", user_id="RT1384")
alertslist=list()



# Callback for tick reception.
def on_tick(ticks, ws):

    for tick in ticks:
        print(tick)
        ltp=tick['last_price']
        id=tick['instrument_token']
        for alert in alertslist:
            print(alert)
            alertprice=alert[2]
            text=''
            alertid= symbolmap.get(alert[0])
            if id==alertid:
                if '>' == alert[1]:
                    if ltp >= float(alertprice):
                        text="Alert: price greater than "+alertprice+" ltp: "+str(ltp)+" for "+alert[0]
                else:
                    if tick[0]['last_price'] <= float(alertprice):
                        text = "Alert: price lower than " + alertprice+" ltp: "+str(ltp)+" for "+alert[0]

                if text:
                    dbhandler.deletealert(alert[0],alert[3],alert[1])
                    notifyalert(int(alert[3]),text)

        # if tick[0]['last_price'] > alert[2]
        #     print('hi')
        # else:
        #     print('hello')






SUNTVJAN=12055042
CGPOWERFEB=14649602
CGPOWERJAN=11968258

symbolmap={"CGPOWER JAN":CGPOWERJAN,"CGPOWER FEB":CGPOWERFEB,"SUNTV JAN":SUNTVJAN}

# Callback for successful connection.
def on_connect(ws):
	# Subscribe to a list of instrument_tokens (RELIANCE and ACC here).
	ws.subscribe([CGPOWERJAN,CGPOWERFEB,SUNTVJAN])

	# Set RELIANCE to tick in `full` mode.
	ws.set_mode(ws.MODE_LTP, [CGPOWERJAN,CGPOWERFEB,SUNTVJAN])




def startstreaming():

	# Assign the callbacks.
	kws.on_tick = on_tick
	kws.on_connect = on_connect
	dbhandler.updatealerts()

	# To enable auto reconnect WebSocket connection in case of network failure
	# - First param is interval between reconnection attempts in seconds.
	# Callback `on_reconnect` is triggered on every reconnection attempt. (Default interval is 5 seconds)
	# - Second param is maximum number of retries before the program exits triggering `on_noreconnect` calback. (Defaults to 50 attempts)
	# Note that you can also enable auto reconnection	 while initialising websocket.
	# Example `kws = WebSocket("your_api_key", "your_public_token", "logged_in_user_id", reconnect=True, reconnect_interval=5, reconnect_tries=50)`
	kws.enable_reconnect(reconnect_interval=5, reconnect_tries=50)

	# Infinite loop on the main thread. Nothing after this will run.
	# You have to use the pre-defined callbacks to manage subscriptions.
	print('Starting streaming..')
	kws.connect()

def stop():
	if kws:
		kws.close()



if __name__ == '__main__':
    main()

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

import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram import ParseMode, Chat
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler,
                          ConversationHandler, CallbackQueryHandler)

from bot import db, data, schedulers, config, formatter
from bot.config import config
from alerts.twitter import fromtwitter
from alerts.rss import reader

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

MAKECALL, SYMBOL, QUERY,PORTFOLIO_DEL_QUERY,WATCHLIST_DEL_QUERY = range(5)
INVALIDSYNTAX, INVALIDSYMBOL, GENERALERROR = range(3)
VERSION = 'v0.0.8'

HELPTXT = 'Wolf the Stock BOT(' + VERSION + ')\n\n' \
          + 'Current version supports \n' \
          + '/quote \n' \
          + '/watchlist \n' \
          + '/portfolio \n' \
          + 'Many exciting new features like calls, news, alerts are planned\n'

STARTCONV = 'Give me the symbol? (e.g. TATA POWER)'

SYNTAX = "Make a call in this format\n" \
         "BUY|SELL 'symbol'@'pricerange' SL@'pricerange'\n" \
         "e.g BUY INFY@1000-1005 SL@995\n" \
         "For futures:\n" \
         "e.g BUY CGPOWER.JAN@92\n"

errormsgs = {INVALIDSYNTAX: "Usage: BUY|SELL 'symbol'@'pricerange' SL@'pricerange\n", INVALIDSYMBOL: "Invalid symbol.", GENERALERROR: "Unknown Error!"}


def reply(text,bot=None,update=None,parsemode=None,chatid=None,reply_markup=None,disable_web_page_preview=None):

    isgroupadmin=isadmin(bot,chat_id=update.effective_message.chat_id,user_id=update.effective_message.from_user.id)
    if bot and isgroup(update) and not isgroupadmin:
        if not chatid:
            chatid=update.effective_message.from_user.id
        bot.send_message(chat_id=chatid,text=text,
                         parse_mode=parsemode,
                         reply_markup=reply_markup,
                         disable_web_page_preview=disable_web_page_preview)
        update.effective_message.reply_text("Lets not spam the group, I replied you in private chat @btstockbot")
    elif update:
        update.effective_message.reply_text(text,
                                  parse_mode=parsemode,
                                  reply_markup=reply_markup,
                                  disable_web_page_preview=disable_web_page_preview)
    return isgroupadmin

# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
def start(bot, update):
    """Send a message when the command /start is issued."""
    isadmin=reply(HELPTXT,bot=bot,update=update)
    if not isgroup(update) or isadmin:
        return QUERY
    else:
        return ConversationHandler.END


def quote(bot, update):
    try:
        text = update.message.text
        if len(text)<3:
            update.message.reply_text('Please give atleast three characters. Try again /quote')
            return nextconversation(update)
        if text.startswith("/q"):
            parttext = text.partition(' ')
            if parttext[2]:
                symbol = parttext[2].upper()
                return replyquote(symbol, update=update,bot=bot)
            else:
                # if isgroup(update):
                #     update.message.reply_text('nse symbol?\n(for futures, <symbol> <month>')
                # else:
                isadmin=reply(STARTCONV, bot=bot, update=update)
                if not isgroup(update) or isadmin:
                    return QUERY
                else:
                    return ConversationHandler.END
        else:
            return replyquote(text.upper(), update=update,bot=bot)
    except Exception as e:
        logger.warning('quote error "%s"', e)
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

def isadmin(bot,chat_id,user_id):
    status=bot.get_chat_member(chat_id, user_id).status
    return status ==ChatMember.CREATOR or status == ChatMember.ADMINISTRATOR


def replyquote(symbol, update, chat_id=None, message_id=None, bot=None):
    # when called from refresh action, update object wont have chatid
    if update.message:
        chat_id = update.message.chat_id
    stock =data.fetchquote(symbol)
    if stock:
        message = str(stock)
    else:
        message= "Couldnt find symbol. Try different query\n"
    # message += getcalls(chat_id, symbol)

    if isgroup(update):
        message += "\n use /quote"

    url = data.geturl(stock.sym)
    keyboard = [[ InlineKeyboardButton("Add to Watchlist", callback_data='1'+stock.sym)],
                [InlineKeyboardButton("Add to Portfolio",callback_data='2'+stock.sym+'#'+stock.querysymbol)]
                # [InlineKeyboardButton("Buy", callback_data='1' + symbol),
                #  InlineKeyboardButton("Sell", callback_data='2' + symbol)
                # InlineKeyboardButton("Refresh", callback_data='3' + stock.sym),]
                ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    if bot and message_id:
        bot.edit_message_text(text=message,
                              chat_id=chat_id,
                              message_id=message_id, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
    else:
        reply(text=message,update=update,bot=bot,parsemode=ParseMode.HTML,reply_markup=reply_markup)
    return nextconversation(update)


def getcalls(chat_id, symbol=None):
    callstxt = db.getcalls(str(chat_id), symbol)

    if callstxt:
        callstxt = "Calls Made:\n==========\n" + callstxt
    else:
        callstxt = "No calls\n"

    callstxt += "==========\n"

    return callstxt


def buttoncallback(bot, update):
    query = update.callback_query
    # Refresh and edit the same message
    if query.data.startswith('3'):
        symbol = query.data[1:]
        replyquote(symbol, update, chat_id=query.message.chat_id, message_id=query.message.message_id, bot=bot)
    elif query.data.startswith('2'):
        symbol=query.data[1:]
        [symbol,querysymbol]=symbol.split('#')
        chatid=query.message.chat_id
        db.insertpendingportfolio(symbol=symbol,chatid=chatid,querysymbol=querysymbol)
        query.message.reply_text(
            "Give the _price_ and _quantity_  you bought "+symbol+" for?```"
            "\n\nUSAGE: +<qty><space><price> "
"\ne.g. +1000  1104.25```",parse_mode=ParseMode.MARKDOWN)
        # return PORTFOLIO_QUERY
    elif query.data.startswith('1'):
        symbol=query.data[1:]

        addtowatchlist(symbol=symbol,bot=bot,update=update)
    else:
        query.message.reply_text("Not implemented yet")
    return QUERY


def calls(bot, update):
    try:
        reply(text=getcalls(update.message.chat_id),update=update,bot=bot,parsemode=ParseMode.HTML)
        return nextconversation(update)
    except Exception as e:
        update.message.reply_text("Error", e)
        return nextconversation(update)

def ipo(bot, update):
    try:
        reply(text=data.getnseipo(), update=update, bot=bot, parsemode=ParseMode.HTML)
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
    reply(text=SYNTAX, update=update, bot=bot, parsemode=ParseMode.HTML)
    return MAKECALL



def watchlist(bot, update):
    try:
        watchlist=db.getwatchlist(str(update.message.chat_id))
        syslist=[row.sym for row in watchlist]
        names = [row.querysymbol for row in watchlist]
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
                cp="{:.2f}".format(((float(ltp)-float(addedprice))/float(addedprice))*100)
                displaytext+="<b>"+sym+' @ '+ltp+"</b>"\
                    +"<pre>"\
                    +"\nAT  : "+addedprice+"  CP  : "+cp+"%"\
                    +"\nHI  : "+hi+"  LO  : "+low\
                    +"</pre>\n\n"
        if not displaytext:
            displaytext="Empty watchlist"
        reply(text=displaytext, update=update, bot=bot, parsemode=ParseMode.HTML)
    except Exception as e:
        update.message.reply_text("Error in watchlist")
    return nextconversation(update)

def portfolio(bot, update):
    try:
        portfoliolist=db.getportfolio(str(update.message.chat_id))
        syslist=[row.sym for row in portfoliolist]
        names = [row.querysymbol for row in portfoliolist]
        displaytext = ''
        if len(portfoliolist)>0:
            # TODO the syslist will be the names here, so swapping it, change to make better
            stocklist=data.fetchquotelist(names,syslist)
            totalprofit=0
            for stock,portfolio in zip(stocklist,portfoliolist):
                sym=portfolio.sym
                addedprice=portfolio.callrange
                ltp=stock.ltp
                profit=(float(ltp)-float(addedprice))*float(portfolio.qty)
                totalprofit+=profit
                displaytext+="<b>"+sym+" @ "+ltp+"</b>"\
                    +"<pre>"\
                    +"\nPRICE   : "+addedprice+"  QTY : "+str(portfolio.qty)\
                    +"\nPROFIT  : "+"{:.2f}".format(profit)\
                    +"</pre>\n\n"
        if not displaytext:
            displaytext="Empty Portfolio"
        else:
            displaytext+="<b>Total Profit:  "+"{:.2f}".format(totalprofit)+"</b>"
        reply(text=displaytext, update=update, bot=bot, parsemode=ParseMode.HTML)
    except Exception as e:
        update.message.reply_text("Error in portfolio")
    return nextconversation(update)

def watch(bot,update,user_data=None):
    try:
        text = update.message.text.upper()
        tokens=text.partition(' ')
        symbol=tokens[2]
        if symbol.startswith('WATCH'):
            symbol=symbol.partition(' ')[2]
        if symbol:
           addtowatchlist(symbol=symbol,bot=bot,update=update)
        else:
            update.message.reply_text("Nothing to add")
    except Exception as e:
        update.message.reply_text("Error adding to watchlist")
    return nextconversation(update)

def addtowatchlist(symbol,bot,update):
    stock = data.fetchquote(symbol)
    try:
        if len(stock.sym)>0:
            db.createcall(type=db.WATCH_TYPE, symbol=stock.sym, callrange=stock.ltp,
                          querysymbol=stock.querysymbol, user=update.effective_message.from_user.first_name, chatid=str(update.effective_message.chat_id),
                          userid=str(update.effective_message.from_user.id))
            reply(text="Added to watchlist\n" + stock.shortview(), update=update, bot=bot, parsemode=ParseMode.HTML)
            db.deleteoldwatchlist()
        else:
            update.message.reply_text("Error adding to watchlist")
    except Exception as e:
        update.message.reply_text("Error adding to watchlist")



def addtoportfolio(bot,update):
    try:
        text=update.message.text
        [qty,price]=text.split(' ')
        call=db.lastupdatedportfolio(str(update.message.chat_id))
        if call:
            call=db.createorupdateportfolio(call.sym,db.PORTFOLIO_STATE_COMPLETE,update.message.chat_id,qty,call.querysymbol,price)

            if call:
                price=call.callrange
                qty=call.qty
            update.message.reply_text(call.sym+" added to portfolio at avg price: "+price+" total qty: "+str(qty))
        #else:
            #update.message.reply_text('Nothing to add')
    except Exception as e:
        update.message.reply_text("Error adding to portfolio. Check syntax")
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
        reply(text="Call made\n" + quote, update=update, bot=bot, parsemode=ParseMode.HTML)
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
    reply(text=message, update=update, parsemode=ParseMode.HTML)


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


def deletewatchlist(bot, update,user_data=None):
    chatid = update.message.chat_id
    symbol = update.message.text.upper()
    rowcount = db.deletewatchlist(symbol, chatid)
    if rowcount > 0:
        update.message.reply_text(symbol + " removed from watchlist")
    else:
        update.message.reply_text(symbol+" not in watchlist")
    return nextconversation(update)

def deleteportfolio(bot, update,user_data=None):
    chatid = update.message.chat_id
    symbol = update.message.text.upper()
    rowcount = db.deleteportfolio(symbol, chatid)
    if rowcount > 0:
        update.message.reply_text(symbol + " removed from portfolio")
    else:
        update.message.reply_text(symbol+" not in portfolio")
    return nextconversation(update)

def results(bot,update):
    replytxt=''
    eventsmap=db.getevents()
    for k,v in eventsmap.items():
        replytxt+='\n<b>'+k+":</b>\n"
        for event in v:
            replytxt+=event.name+", "
        replytxt+="\n\n"
    if replytxt:
        reply(text=replytxt, update=update, bot=bot,parsemode=ParseMode.HTML)
    else:
        reply(text="No results today", update=update, bot=bot, parsemode=ParseMode.HTML)

def news(bot,update):
    replytxt=reader.readnews()

    if replytxt:
        reply(text=replytxt, update=update, bot=bot, parsemode=ParseMode.HTML,disable_web_page_preview=True)
    else:
        reply(text="No News today", update=update, bot=bot, parsemode=ParseMode.HTML)

def query(bot, update):
    command = update.message.text.upper().partition(' ')[2]
    if command:
        update.message.text = command
        return processquery(bot, update, None)
    else:
        isadmin=reply(text=STARTCONV, update=update, bot=bot, parsemode=ParseMode.HTML)
        if not isgroup(update) or isadmin:
            return QUERY
        else:
            return ConversationHandler.END


def alerts(bot, update):
    replytxt = db.getalerts(str(update.message.chat_id))
    reply(text="Alerts:\n" + (replytxt if replytxt else 'None'), update=update, bot=bot, parsemode=ParseMode.HTML)
    return nextconversation(update)


def alert(bot, update):
    commands = update.message.text.upper().partition(' ')[2]

    if not commands[2]:
        reply(text="Usage: Alert INFY > 1000", update=update, bot=bot)
        return nextconversation(update)


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
    reply(text='Alert set for ' + symbol + " " + price, update=update, bot=bot)
    db.createalert(symbol, operation, price, str(chat_id))
    return nextconversation(update)

def delportfolioquery(bot,update):
    isadmin=reply(text="Give the symbol to delete from portfolio?",bot=bot,update=update)
    if not isgroup(update) or isadmin:
        return PORTFOLIO_DEL_QUERY


def delwatchlistquery(bot, update):
    isadmin = reply(text="Give the symbol to delete from watchlist?", bot=bot, update=update)
    if not isgroup(update) or isadmin:
        return WATCHLIST_DEL_QUERY

def processquery(bot, update, user_data=None):
    delay=datetime.datetime.now()-update.message.date
    # If the update received is delayed more than 5 mins, it may be due to server restart, so ignore the old queries
    if delay.seconds <300:
        logger.info("Query: "+update.message.text+' Date: '+str(delay))
        text = update.message.text.upper()
        try:
            # query may contain commands again, so process the commands too
            if text.startswith('/'):
                # ppl may use /q alerts or /q infy in private chat itself, lets process same as in group
                if text.startswith('/Q '):
                    text = text.partition(' ')[2]
                else:
                    text = text[1:]
            if text.startswith(('BUY', 'SELL', 'SHORT')):
                return makecall(bot, update, user_data)
            elif text.startswith('CALLS'):
                return calls(bot, update)
            elif text.startswith("HELP"):
                return start(bot, update)
            elif text=="START":
                return start(bot, update)
            elif text.startswith("CANCEL"):
                return done(bot, update)
            elif text == "RESULTS":
                return results(bot, update)
            elif text.startswith("WATCHLIST"):
                return watchlist(bot,update)
            elif text.startswith("WATCH"):
                return watch(bot,update)
            elif text=="IPO":
                return ipo(bot, update)
            elif text.startswith("PORTFOLIO"):
                return portfolio(bot, update)
            elif text == "Q":
                return quote(bot, update)
            elif text == "NEWS":
                return news(bot, update)
            elif text.startswith('ALERTS'):
                return alerts(bot, update)
            elif text.startswith('RESULT'):
                return results(bot, update)
            elif text.startswith('DELETE'):
                symbol = text.partition(' ')[2]
                return deletecall(symbol, update)
            elif text.startswith('ALERT'):
                return alert(bot, update)
            elif text.startswith(('+','-')):
                return addtoportfolio(bot,update)
            elif text.startswith('DELPORTFOLIO'):
                return delportfolioquery(bot, update)
            elif text.startswith('DELWATCHLIST'):
                return delwatchlistquery(bot,update)
            elif len(text) < 50:
                return quote(bot, update)
            else:
                reply(text="Not ready to handle this query", update=update, bot=bot)
        except:
            logger.error("Error processing query",str(sys.exc_info()[0]))
            reply(text="Error", update=update, bot=bot)

    return nextconversation(update)


def setupnewconvhandler():
    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', processquery), CommandHandler('quote', processquery),
                      CommandHandler('help', processquery),
                      CommandHandler('ipo', processquery),
                      CommandHandler('watchlist', processquery),
                      CommandHandler('portfolio', processquery),
                      CommandHandler('calls', processquery),
                      CommandHandler('results', processquery),
                      CommandHandler('news', processquery),
                      CommandHandler('cancel', processquery),
                      CommandHandler('delwatchlist', processquery),
                      CommandHandler('delportfolio', processquery)],

        states={
            QUERY: [MessageHandler(Filters.text,
                                   processquery,
                                   pass_user_data=True),

                    MessageHandler(Filters.command, processquery, pass_user_data=True)
                    ],
            WATCHLIST_DEL_QUERY: [MessageHandler(Filters.text,
                                   deletewatchlist,
                                   pass_user_data=True)],
            PORTFOLIO_DEL_QUERY: [MessageHandler(Filters.text,
                                   deleteportfolio,
                                   pass_user_data=True)],

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
        entry_points=[CommandHandler('start', processquery), CommandHandler('quote', processquery), CommandHandler('call', processquery),
                      CommandHandler('calls', processquery),
                      CommandHandler('done', processquery),
                      CommandHandler('ipo', processquery)],

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

def newmember(bot, update):
    # here you receive a list of new members (User Objects) in a single service message
    new_members = update.message.new_chat_members
    # do your stuff here:
    for member in new_members:
        # update.message.reply_text("Welcome "+member)
        print(member.name)
        bot.send_message(chat_id=member.id, text="Hi "+member.name+",\nWelcome to our group")


# This method should not be processed for private chat
# as it is already handled in processquery
def createportfolio(bot,update):
    if(isgroup(update)):
        addtoportfolio(bot,update)



def main():

    db.initdb()

    """Start the bot."""
    # Create the EventHandler and pass it your bot's token.
    global updater
    # 535372141:AAEgx8VtahWGWWUYhFcYR0zonqIHycRMXi0   - dev token
    # 534849104:AAHGnCHl4Q3u-PauqDZ1tspUdoWzH702QQc   - live token

    token_key='LIVE_TOKEN'
    if len(sys.argv )>1 and sys.argv[1].upper()=='DEV':
        token_key='DEV_TOKEN'




    # updater = Updater("535372141:AAEgx8VtahWGWWUYhFcYR0zonqIHycRMXi0")  #Dev

    updater = Updater(config['telegram'][token_key])  # Live

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    dp.add_handler(setupnewconvhandler())

    dp.add_handler(CallbackQueryHandler(buttoncallback))
    dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, newmember))
    dp.add_handler(RegexHandler('^[\+|\-][0-9.]+ [0-9.]+',
                                    createportfolio))

    # on noncommand i.e message - echo the message on Telegram
    # dp.add_handler(MessageHandler(Filters.text, echo))

    # log all errors
    dp.add_error_handler(error)

    logger.info("Starting the bot in "+("DEV" if token_key=="DEV_TOKEN" else "LIVE"))

    # Start the Bot
    updater.start_polling()



    schedulers.schedulejobs(updater.job_queue)
    fromtwitter.startstreaming(notifyalert)
    data.startstreaming(notifyalert)




    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    # updater.idle()


if __name__ == '__main__':
    main()

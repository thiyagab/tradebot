from bot.models import Calls,Alert,db
from bot.util import logger
from peewee import reduce,operator

alertslist = list()
WATCH_TYPE="WATCH"
LIMIT=5
def deleteoldcalls():
    calls=Calls.select(Calls.time).where(Calls.type!=WATCH_TYPE).order_by(Calls.time.desc()).limit(LIMIT)
    Calls.delete().where((Calls.type!=WATCH_TYPE) & (Calls.time.not_in(calls))).execute()


def deleteoldwatchlist():
    calls = Calls.select(Calls.time).where(Calls.type == WATCH_TYPE).order_by(Calls.time.desc()).limit(LIMIT)
    Calls.delete().where((Calls.type == WATCH_TYPE) & (Calls.time.not_in(calls))).execute()

def deletealert(symbol, chatid, operation):
    logger.info('Deleting... ', symbol, chatid, operation)
    Alert.delete().where((Alert.sym==symbol) and (Alert.op==operation) and (Alert.chatid==chatid)).execute()
    updatealerts()


def deletecall(symbol, userid, chatid):
    logger.info('Deleting call... '+ symbol)
    rowcount = Calls.delete().where((Calls.sym==symbol) & (Calls.userid==userid) & (Calls.chatid==chatid)).execute()
    return rowcount

#TODO this should be changed, obviously we cant stream multiple symbol to show alerts,
#but still keeping the alerts in list is not efficient
def updatealerts():
    alertslist.clear()
    for alert in Alert.select():
        alertslist.append(alert)



def getalerts(chatid):
    replytxt = ''
    for alert in Alert.select().where(Alert.chatid==chatid):
        replytxt += formatalert(alert) + "\n"
    return replytxt


def formatalert(alert):
    return alert.sym+ " " + alert.op + " " + alert.price


def createalert(symbol, operation, price, chat_id):
    Alert.insert(sym=symbol,op=operation,price=price,chatid=chat_id).upsert().execute()
    updatealerts()


def getcalls(chatid, symbol=None):
    clauses=[(Calls.chatid==chatid),
             (Calls.type!=WATCH_TYPE)]
    if symbol:
        clauses.append((Calls.sym==symbol))

    callstxt = ''
    for call in Calls.select().where(reduce(operator.and_,clauses)):
        callstxt += call.user + " : " + call.type + " " + call.sym + "@" + call.callrange + \
                    " " +(call.desc if call.desc else " ")+ \
                    " on <i>" + call.time.strftime('%b %d %H:%M') + "</i>\n"
    return callstxt


def getwatchlist(chatid):
    watchlist = list()
    for call in Calls.select().where((Calls.chatid==chatid) and Calls.type==WATCH_TYPE):
        watchlist.append(call)
    return watchlist

def createcall(type, symbol, user, chatid, userid,callrange=None, misc=None,desc=None):
    Calls.insert(sym=symbol, type=type, callrange=callrange, chatid=chatid,user=user,userid=userid,misc=misc,desc=desc).upsert().execute()

def initdb():
    db.connect()
    db.create_tables([Alert,Calls],safe=True)
    db.close()
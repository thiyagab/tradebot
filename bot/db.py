import datetime

from bot.models import Calls,Alert,Events,db
from bot.util import logger
from peewee import reduce, operator, DoesNotExist
from tinydb import TinyDB,JSONStorage

alertslist = list()
WATCH_TYPE="WATCH"
PORTFOLIO_TYPE="PORTFOLIO"
LIMIT=10
PORTFOLIO_STATE_PENDING=1
PORTFOLIO_STATE_COMPLETE=2

tdb=TinyDB('store.json',storage=JSONStorage)

def deleteoldcalls():
    calls=Calls.select(Calls.time).where((Calls.type.not_in([WATCH_TYPE,PORTFOLIO_TYPE]))).order_by(Calls.time.desc()).limit(LIMIT)
    Calls.delete().where((Calls.type.not_in([WATCH_TYPE,PORTFOLIO_TYPE])) & (Calls.time.not_in(calls))).execute()


def deleteoldwatchlist():
    calls = Calls.select(Calls.time).where(Calls.type == WATCH_TYPE).order_by(Calls.time.desc()).limit(LIMIT)
    Calls.delete().where((Calls.type == WATCH_TYPE) & (Calls.time.not_in(calls))).execute()

def deletealert(symbol, chatid, operation):
    logger.info('Deleting Alert... '+ symbol+" "+chatid+" "+operation)
    Alert.delete().where((Alert.sym==symbol) & (Alert.op==operation) & (Alert.chatid==chatid)).execute()
    updatealerts()


def deletecall(symbol, userid, chatid):
    logger.info('Deleting call... '+ symbol)
    rowcount = Calls.delete().where((Calls.sym==symbol)& (Calls.chatid==chatid)).execute()
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
             (Calls.type.not_in([WATCH_TYPE, PORTFOLIO_TYPE]))]
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
    for call in Calls.select().where((Calls.chatid==chatid) & (Calls.type==WATCH_TYPE) & (Calls.sym.is_null(False))):
        watchlist.append(call)
    return watchlist

def getportfolio(chatid):
    portfolio = list()
    for call in Calls.select().where((Calls.chatid==chatid) & (Calls.type==PORTFOLIO_TYPE) & (Calls.qty > 0)):
        portfolio.append(call)
    return portfolio

def lastupdatedportfolio(chatid):
    try:
        call=Calls.select()\
                .where((Calls.chatid==chatid) & (Calls.type==PORTFOLIO_TYPE) & (Calls.misc==str(PORTFOLIO_STATE_PENDING)))\
                .order_by(Calls.time.desc()).get()
    except DoesNotExist as de:
        pass
    return call


def createcall(type, symbol, user, chatid, userid,callrange=None, misc=None,desc=None,querysymbol=None):
    Calls.insert(sym=symbol, type=type, callrange=callrange,querysymbol=querysymbol, chatid=chatid,user=user,userid=userid,misc=misc,desc=desc).upsert().execute()


def insertipos(ipos):
    tdb.purge_table('ipos')
    ipotable = tdb.table('ipos')
    ipotable.insert_multiple(ipos)

def insertevents(events):
    for k,v in events.items():
        datetimeobj = datetime.datetime.strptime(k,'%Y-%m-%d')
        # companies=events[date]
        for company in v:
            if company:
                Events.insert(name=company,time=datetimeobj,type="RESULT").upsert().execute()


def deleteevents():
    Events.delete().where(Events.type=='RESULT').execute()

def getevents():
    nextthree = datetime.date.today() +datetime.timedelta(days=3)
    eventsmap={}
    for event in Events.select().where((Events.time >= datetime.date.today()) & (Events.time <= nextthree)):
        date= event.date.strftime('%Y-%m-%d')
        events=eventsmap.get(date)
        if not events:
            events =list()
        events.append(event)
        eventsmap[date]=events
    return eventsmap

def getipos():
    ipotable = tdb.table('ipos')
    return ipotable.all()

def createorupdateportfolio(sym,state,chatid,qty,querysymbol,price=None):
    call = getCall(sym,"PORTFOLIO",chatid)
    if call:
        oldprice = float(call.callrange) if call.callrange else '0'
        oldqty = call.qty
        qty = int(qty)
        if price:
            price=float(price)
            newqty = qty+oldqty
            newprice= (oldprice*oldqty+price*qty)/newqty
            call.callrange="{:.2f}".format(newprice)
            call.qty=newqty
        call.time=datetime.datetime.now()
        call.chatid=chatid
        call.misc=str(state)
        call.querysymbol=querysymbol
        call.save()
        return call
    else:
        Calls.insert(sym=sym,callrange=(str(price) if price else '0'),qty=int(qty),
                     chatid=chatid,type=PORTFOLIO_TYPE,querysymbol=querysymbol,
                     misc=str(state)).execute()



def getCall(sym,type,chatid):
    try:
        call= Calls.get(Calls.sym==sym,Calls.type==type,Calls.chatid==chatid)
        return call
    except DoesNotExist as de:
        logger.error("Not exists")

def initdb():
    db.connect()
    db.create_tables([Alert,Calls,Events],safe=True)
    db.close()
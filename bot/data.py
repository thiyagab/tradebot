from kiteconnect import WebSocket

from bot import db,util
from bot.util import logger
from web import nse,edelweiss

kws = WebSocket(api_key="9oykkw4mc01lm5jf", public_token="V3mTjh6XbVQk3171IoWsn863qZsmBsDL", user_id="RT1384")

SUNTVJAN = 12055042
CGPOWERFEB = 14649602
CGPOWERJAN = 11968258

FUTURES = ('25JAN2018', '22FEB2018', '28MAR2018')

symbolmap = {"CGPOWER JAN": CGPOWERJAN, "CGPOWER FEB": CGPOWERFEB, "SUNTV JAN": SUNTVJAN}

equityurl = 'https://www.nseindia.com/live_market/dynaContent/live_watch/get_quote/GetQuote.jsp?symbol='
futureurl = 'https://www.nseindia.com/live_market/dynaContent/live_watch/get_quote/GetQuoteFO.jsp?instrument=FUTSTK&expiry=%s&underlying=%s'


def geturl(symbol):
    symbolandexpiry = symbol.partition(' ')
    url = equityurl + symbol
    if symbolandexpiry[2]:
        url = futureurl % (getexpiry(symbolandexpiry[2]), symbolandexpiry[0])

    return url

def getnseipo():
    ipo= nse.getactiveipo()
    if not ipo:
        ipo= "No Active IPOs"
    return ipo


def fetchquote(symbol):
    symbolandexpiry = symbol.partition(' ')

    expiry = getexpiry(symbolandexpiry[2])
    # stock = quotefromnse.fetchquote(symbol=symbolandexpiry[0], expiry=expiry)
    stock = edelweiss.getquote(symbolandexpiry[0] + " " + expiry)
    return str(stock)

def getexpiry(month):
    expiry = ''
    # TODO HARDCODED FOR EXPIRY will change, find a better way
    if month:
        if 'JAN' in month:
            expiry = FUTURES[0]
        elif 'FEB' in month:
            expiry = FUTURES[1]
        elif 'MAR' in month:
            expiry = FUTURES[2]
    return expiry


# Callback for successful connection.
def on_connect(ws):
    # Subscribe to a list of instrument_tokens (RELIANCE and ACC here).
    ws.subscribe([CGPOWERJAN, CGPOWERFEB, SUNTVJAN])

    # Set RELIANCE to tick in `full` mode.
    ws.set_mode(ws.MODE_LTP, [CGPOWERJAN, CGPOWERFEB, SUNTVJAN])


fnnotifyalert = None


def startstreaming(notifyalert):
    global fnnotifyalert
    fnnotifyalert = notifyalert

    kws.on_tick = on_tick
    kws.on_connect = on_connect
    db.updatealerts()

    kws.enable_reconnect(reconnect_interval=5, reconnect_tries=50)
    logger.info('Started streaming..')
    kws.connect()


# Callback for tick reception.
def on_tick(ticks, ws):
    for tick in ticks:
        # print(tick)
        ltp = tick['last_price']
        id = tick['instrument_token']
        for alert in db.alertslist:
            # print(alert)
            alertprice = alert[2]
            text = ''
            alertid = symbolmap.get(alert[0])
            if id == alertid:
                if '>' == alert[1]:
                    if ltp >= float(alertprice):
                        text = "Alert: price greater than " + alertprice + " ltp: " + str(ltp) + " for " + alert[0]
                else:
                    if tick['last_price'] <= float(alertprice):
                        text = "Alert: price lower than " + alertprice + " ltp: " + str(ltp) + " for " + alert[0]

                if text:
                    db.deletealert(alert[0], alert[3], alert[1])
                    fnnotifyalert(int(alert[3]), text)

        # if tick[0]['last_price'] > alert[2]
        #     print('hi')
        # else:
        #     print('hello')


def stop():
    if kws:
        kws.close()

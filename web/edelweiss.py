import ujson
import timeit

import requests
import datetime

from web.stock import Stock


def getquote(sym):
    rsp = requests.post('https://ewmw.edelweiss.in/ewreports/api/search/gsa/suggestions',
                        {"SearchString": sym, "Cookie": ""})
    if rsp.status_code in (200,):
        respjson = ujson.loads(rsp.text)

        if respjson and len(respjson) > 0:
            # TODO filter out options here, once we have a proper feed, these dirty code will be unnecessary
            filteredlist=[x for x in respjson if not x['suggestion'].upper().endswith(('CE','PE'))]
            if len(filteredlist)>0:
                querysymbol = filteredlist[0]['NSEStreamingSymbol']

                name = filteredlist[0]['suggestion']
                sym=filteredlist[0]['nse_code']
                if not querysymbol:
                    querysymbol = filteredlist[0]['BSEStreamingSymbol']
                #print(streamingsymbol)
                stocklist = getstreamingdata([querysymbol], [name],[sym])
                if len(stocklist) > 0:
                    print(str(stocklist[0]))
                    return stocklist[0]


def getstreamingdata(querylist, names=None,symbols=None):
    stocklist = list()
    if querylist and len(querylist) > 0:
        payload = {'syLst': querylist}
        response = requests.request("POST", "https://ewmw.edelweiss.in/api/trade/getquote", data=payload)
        response = ujson.loads(response.text)['syLst']
        for idx, quotejson in enumerate(response):
            name=names[idx]
            sym=''
            if symbols:
                sym=symbols[idx]
            if not sym and quotejson['dpName']:
                sym = quotejson['dpName']
            stock = Stock(sym=sym, name=name, ltp=quotejson['ltp'], h=quotejson['h'], l=quotejson['l'], o=quotejson['o'],
                          cp=quotejson['chgP'], c=quotejson['c'], ltt=quotejson['ltt'], querysymbol=quotejson['sym'])
            stocklist.append(stock)
    return stocklist


def getevents():
    url = "https://ewmw.edelweiss.in/api/Market/MarketsModule/Events"
    time=datetime.datetime.now()
    # if the market is closed, then get results for next day
    if time.hour>15 and time.minute>0:
        time=time.replace(day=time.day+1)

    date=time.strftime('%Y-%m-%d')
    payload = {"dt":date}
    headers = {
        'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36",
        'Content-Type': "application/json;charset=UTF-8",
    }

    response = requests.request("POST", url, data=str(payload), headers=headers)
    return ujson.loads(ujson.loads(response.text))['JsonData']


if __name__ == '__main__':
    #print(timeit.timeit("getquote('INFY')", globals=globals(), number=1))
    getevents()

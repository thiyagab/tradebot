import json
import timeit

import requests

from web.stock import Stock


def getquote(sym):
    rsp = requests.post('https://ewmw.edelweiss.in/ewreports/api/search/gsa/suggestions',
                        {"SearchString": sym, "Cookie": ""})
    if rsp.status_code in (200,):
        respjson = json.loads(rsp.text)
        if respjson and len(respjson) > 0:
            streamingsymbol = respjson[0]['NSEStreamingSymbol']
            name = respjson[0]['suggestion']
            if not streamingsymbol:
                streamingsymbol = respjson[0]['BSEStreamingSymbol']
            #print(streamingsymbol)
            stocklist = getstreamingdata([streamingsymbol], [name])
            if len(stocklist) > 0:
                return stocklist[0]


def getstreamingdata(syslist, names=None):
    stocklist = list()
    if syslist and len(syslist) > 0:
        payload = {'syLst': syslist}
        response = requests.request("POST", "https://ewmw.edelweiss.in/api/trade/getquote", data=payload)
        response = json.loads(response.text)['syLst']
        for idx, quotejson in enumerate(response):
            name=names[idx]
            if quotejson['dpName']:
                name = quotejson['dpName']
            stock = Stock(sym=name, ltp=quotejson['ltp'], h=quotejson['h'], l=quotejson['l'], o=quotejson['o'],
                          cp=quotejson['chgP'], c=quotejson['c'], ltt=quotejson['ltt'], streamingsymbol=quotejson['sym'])
            stocklist.append(stock)
    return stocklist


if __name__ == '__main__':
    print(timeit.timeit("getquote('nifty')", globals=globals(), number=1))

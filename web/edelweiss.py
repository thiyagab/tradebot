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
        response = json.loads(response.text)['syLst']
        for idx, quotejson in enumerate(response):
            name=names[idx]
            sym=symbols[idx]
            if not sym and quotejson['dpName']:
                sym = quotejson['dpName']
            stock = Stock(sym=sym, name=name, ltp=quotejson['ltp'], h=quotejson['h'], l=quotejson['l'], o=quotejson['o'],
                          cp=quotejson['chgP'], c=quotejson['c'], ltt=quotejson['ltt'], querysymbol=quotejson['sym'])
            stocklist.append(stock)
    return stocklist


def getevents():
    import requests

    url = "https://ewmw.edelweiss.in/api/Market/MarketsModule/Events"

    payload = "{\"dt\":\"2018-01-16\"}"
    headers = {
        'Origin': "https://www.edelweiss.in",
        'Accept-Encoding': "gzip, deflate, br",
        'Accept-Language': "en-US,en;q=0.9,ta-IN;q=0.8,ta;q=0.7",
        'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36",
        'Content-Type': "application/json;charset=UTF-8",
        'Accept': "application/json, text/plain, */*",
        'Referer': "https://www.edelweiss.in/market/economic-and-company-events",
        'Connection': "keep-alive",
        'Cache-Control': "no-cache",
        'Postman-Token': "1b85f3cd-a7b9-59c4-9b6b-8d7f18e7af4b"
    }

    response = requests.request("POST", url, data=payload, headers=headers)

    print(json.loads(response.text))

if __name__ == '__main__':
    #print(timeit.timeit("getquote('INFY')", globals=globals(), number=1))
    getevents()

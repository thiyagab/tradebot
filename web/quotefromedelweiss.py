import json

import requests
import timeit
from web.stock import Stock



def getquote(sym):
    rsp = requests.post('https://ewmw.edelweiss.in/ewreports/api/search/gsa/suggestions',{"SearchString":sym,"Cookie":""})
    if rsp.status_code in (200,):
        # This magic here is to cut out various leading characters from the JSON
        # response, as well as trailing stuff (a terminating ']\n' sequence), and then
        # we decode the escape sequences in the response
        # This then allows you to load the resulting string
        # with the JSON module.
        respjson=json.loads(rsp.text)
        if respjson and len(respjson)>0:
            streamingsymbol=respjson[0]['NSEStreamingSymbol']
            name=respjson[0]['suggestion']
            if not streamingsymbol:
                streamingsymbol=respjson[0]['BSEStreamingSymbol']
            print(streamingsymbol)
            return getstreamingdata(streamingsymbol,name)


def getstreamingdata(streamingsymbol,name=None):
    if streamingsymbol and len(streamingsymbol) > 0:
        payload = {'syLst': [streamingsymbol]}
        response = requests.request("POST", "https://ewmw.edelweiss.in/api/trade/getquote", data=payload)
        quotejson = json.loads(response.text)['syLst'][0]
        if quotejson['dpName']:
            name = quotejson['dpName']
        stock = Stock(sym=name, ltp=quotejson['ltp'], h=quotejson['h'], l=quotejson['l'], o=quotejson['o'],
                      cp=quotejson['chgP'], c=quotejson['c'], ltt=quotejson['ltt'])
        print(stock)
        return stock

if __name__ == '__main__':
    print(timeit.timeit("getquote('suntv 25jan')",globals=globals(),number=1))
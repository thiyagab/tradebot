#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 19 08:57:58 2017

@author: thiyagab
"""
import sys,requests,lxml.html


from web import common
from web.stock import Stock



def fetchquote(symbol, expiry=None):

    quoteurl = "https://www.nseindia.com/live_market/dynaContent/live_watch/get_quote/ajaxGetQuoteJSON.jsp"
    futquoteurl = "https://www.nseindia.com/live_market/dynaContent/live_watch/get_quote/ajaxFOGetQuoteJSON.jsp"

    querystring = ''

    if expiry:
        querystring = {"underlying": symbol, "instrument": "FUTSTK", "expiry": expiry, "type": "SELECT",
                       "strike": "SELECT"}
        url = futquoteurl

    else:
        querystring = {"symbol": symbol}
        url = quoteurl

    response = common.sendrequest(url=url, querystring=querystring)
    return getstock(response,symbol,expiry)

def getstock(response,symbol,expiry=None):
    quote = response['data'][0]
    pchange = quote.get('pChange', '-')

    openkey = 'open'
    highkey = 'dayHigh'
    lowkey = 'dayLow'
    pclosekey = 'previousClose'
    volumekey = 'totalTradedVolume'

    if expiry:
        openkey = 'openPrice'
        highkey = 'highPrice'
        lowkey = 'lowPrice'
        pclosekey = 'prevClose'


    stock = Stock(sym=symbol,ltp=quote['lastPrice'],o=quote[openkey],h=quote[highkey],
                  l=quote[lowkey],c=quote[pclosekey],cp=pchange)
    return stock


def getactiveipo():
    url="https://www.nseindia.com/products/content/equities/ipos/ipo_current.htm"
    response=requests.request("GET", url)
    parser = lxml.html.fromstring(response.text)
    rowstag = parser.findall('tr')
    formattedtext=''
    if len(rowstag)>1:
        for idx,row in enumerate(rowstag):
            if idx>0:
              tds= row.findall('td')
              formattedtext+=formatipo(tds)

    return formattedtext


def formatipo(tds):
    formattedtext=''
    linktag=tds[0].getchildren()[0]
    link="https://www.nseindia.com"+linktag.attrib['href']
    formattedtext+='<a href="'+link+'">'+linktag.text+'</a>'
    formattedtext+="\n<pre>Start: "
    formattedtext+=tds[2].text
    formattedtext += "\nEnd: "
    formattedtext+=tds[3].text
    formattedtext+="</pre>\n\n"
    # print(formattedtext)
    return formattedtext

def main():
    if len(sys.argv) < 2:
        print("Usage: \n", "python quotefromnse <symbol>\n", "or\n", "python quotefromnse <symbol> <expiry>")
        sys.exit(1)

    symbol = sys.argv[1].upper()
    expiry = ''
    if len(sys.argv) == 3:
        expiry = sys.argv[2].upper()

    response = fetchquote(symbol, expiry)
    print(response['data'][0]['lastPrice'])


if __name__ == '__main__':
    # main()
    getactiveipo()

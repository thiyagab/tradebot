#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 19 08:57:58 2017

@author: thiyagab
"""
import sys

from web import common


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
    return response


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
    main()

import json

import requests


rsp = requests.get('https://finance.google.com/finance?q=NSE:INFY&output=json')
if rsp.status_code in (200,):
    # This magic here is to cut out various leading characters from the JSON
    # response, as well as trailing stuff (a terminating ']\n' sequence), and then
    # we decode the escape sequences in the response
    # This then allows you to load the resulting string
    # with the JSON module.
    # print(rsp.text)
    fin_data = json.loads(rsp.content[6:-2].decode('unicode_escape'))
    print(fin_data)
    # print out some quote data
    print('Price: {}'.format(fin_data['l']))
    print('Change percentage: {}'.format(fin_data['cp']))
    print('Opening Price: {}'.format(fin_data['op']))
    print('High Price: {}'.format(fin_data['hi']))
    print('Low Price: {}'.format(fin_data['lo']))
    print('Price/Earnings Ratio: {}'.format(fin_data['pe']))
    print('52-week high: {}'.format(fin_data['hi52']))
    print('52-week low: {}'.format(fin_data['lo52']))

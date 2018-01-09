import json

import requests
import timeit



def getquote():
    rsp = requests.get('https://ewmw.edelweiss.in/api/Market/Process/EquityDetailsMarketBySymbol/INFY')
    if rsp.status_code in (200,):
        # This magic here is to cut out various leading characters from the JSON
        # response, as well as trailing stuff (a terminating ']\n' sequence), and then
        # we decode the escape sequences in the response
        # This then allows you to load the resulting string
        # with the JSON module.
        print(rsp.text[1:-1])
        fin_data = json.loads(rsp.content[4:-1].decode('unicode_escape'))
        # print(fin_data)
        print(len(fin_data))
        # print out some quote data
        print('Price:',fin_data['JsonData']['companyMarketPrice']['LTP'])
# # print out some quote data
# print('Price: {}'.format(fin_data['l']))
# print('change percentage: {}'.format(fin_data['l']))
# print('Opening Price: {}'.format(fin_data['op']))
# print('Price/Earnings Ratio: {}'.format(fin_data['pe']))
# print('52-week high: {}'.format(fin_data['hi52']))
# print('52-week low: {}'.format(fin_data['lo52']))


# rsp = requests.post("https://ewmw.edelweiss.in/api/Market/Process/GetDerivativeMultiSymbolDetails",
#                     json=[{"schStr": "CGPOWER", "aTyp": "FUTSTK", "exp": ["25 Jan 2018"], "opTyp": ""}])
#
# fin_data = json.loads(rsp.text)
# print(fin_data)

if __name__ == '__main__':
    print(timeit.timeit("getquote()",globals=globals(),number=1))
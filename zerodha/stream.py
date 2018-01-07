import sqlite3

from kiteconnect import WebSocket

# Initialise.
# paste the api and public token here

dbname = "calls.db"

kws = WebSocket(api_key="9oykkw4mc01lm5jf", public_token="V3mTjh6XbVQk3171IoWsn863qZsmBsDL", user_id="RT1384")
#114968505

# Callback for tick reception.
def on_tick(tick, ws):
    print(tick[0])
    for alert in alertslist:
        print(alert)
    # if '>' == str(alert[1]).strip():
    # if(tick[0]['last_price'])> float(alert[2]):


alertslist = list()


def updatealerts():
    conn = sqlite3.connect(dbname)
    c = conn.cursor()
    sqlstr = "SELECT * FROM alerts"
    alertslist.clear()
    for row in c.execute(sqlstr):
        alertslist.append(row)

    c.close();


# Callback for successful connection.
def on_connect(ws):
    # Subscribe to a list of instrument_tokens (RELIANCE and ACC here).
    ws.subscribe([11968258])

    # Set RELIANCE to tick in `full` mode.
    ws.set_mode(ws.MODE_LTP, [11968258])


def start():
    # Assign the callbacks.
    kws.on_tick = on_tick
    kws.on_connect = on_connect
    updatealerts()

    # To enable auto reconnect WebSocket connection in case of network failure
    # - First param is interval between reconnection attempts in seconds.
    # Callback `on_reconnect` is triggered on every reconnection attempt. (Default interval is 5 seconds)
    # - Second param is maximum number of retries before the program exits triggering `on_noreconnect` calback. (Defaults to 50 attempts)
    # Note that you can also enable auto reconnection	 while initialising websocket.
    # Example `kws = WebSocket("your_api_key", "your_public_token", "logged_in_user_id", reconnect=True, reconnect_interval=5, reconnect_tries=50)`
    kws.enable_reconnect(reconnect_interval=5, reconnect_tries=50)

    # Infinite loop on the main thread. Nothing after this will run.
    # You have to use the pre-defined callbacks to manage subscriptions.
    print('Starting streaming..')
    kws.connect()


def stop():
    if kws:
        kws.close()

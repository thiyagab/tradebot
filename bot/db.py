import sqlite3
from datetime import datetime

DBNAME = "wolfca.db"

# TODO this may not work with multiple threads updating and reading
# from this list, need to find efficient way
alertslist = list()


def initdb():
    conn = sqlite3.connect(DBNAME)
    c = conn.cursor()
    # Create table
    c.execute('''CREATE TABLE IF NOT EXISTS calls
                 (type text, symbol text, callrange text, misc text, 
                 user text,chatid text,userid text,time timestamp,
                 PRIMARY KEY (symbol,chatid,userid))''')

    c.execute('''CREATE TABLE IF NOT EXISTS alerts
                 (symbol text,operation text, price text, chatid text,time timestamp,
                 PRIMARY KEY (symbol,operation,chatid))''')
    c.close()


def deleteoldcalls():
    conn = sqlite3.connect(DBNAME)
    c = conn.cursor()
    c.execute('delete from calls where time not in (select time from calls order by time desc limit 5)')
    conn.commit()
    c.close()


def deletealert(symbol, chatid, operation):
    print('Deleting... ', symbol, chatid, operation)
    conn = sqlite3.connect(DBNAME)
    c = conn.cursor()
    c.execute(
        "delete from alerts where symbol='" + symbol + "' and operation='" + operation + "'" + " and chatid='" + chatid + "'")
    conn.commit()
    c.close()
    updatealerts()


def deletecall(symbol, userid, chatid):
    print('Deleting call... ', symbol, chatid)
    conn = sqlite3.connect(DBNAME)
    c = conn.cursor()
    c.execute(
        "delete from calls where symbol='" + symbol + "' and userid='" + str(userid) + "'" + " and chatid='" + str(
            chatid) + "'")
    rowcount = c.rowcount
    conn.commit()
    c.close()
    return rowcount


def updatealerts():
    conn = sqlite3.connect(DBNAME)
    c = conn.cursor()
    sqlstr = "SELECT * FROM alerts"
    alertslist.clear()
    for row in c.execute(sqlstr):
        alertslist.append(row)
    c.close()


def getalerts(chatid):
    conn = sqlite3.connect(DBNAME, detect_types=sqlite3.PARSE_DECLTYPES)
    c = conn.cursor()
    sqlstr = "SELECT * FROM alerts where chatid='" + chatid + "'"
    replytxt = ''
    for row in c.execute(sqlstr):
        replytxt += formatalert(row) + "\n"
        print(row)
    return replytxt


def formatalert(row):
    return row[0] + " " + row[1] + " " + row[2]


def createalert(symbol, operation, price, chat_id):
    sqlstr = '''INSERT OR REPLACE INTO alerts VALUES (?,?,?,?,?)'''
    params = list()
    # (symbol text,operation text, price text, chatid text,time timestamp
    params.append(symbol)
    params.append(operation)
    params.append(price)
    params.append(chat_id)
    params.append(datetime.now())

    conn = sqlite3.connect(DBNAME)
    c = conn.cursor()
    c.execute(sqlstr, params)
    conn.commit()
    c.close()
    updatealerts()


def getcalls(chatid, symbol):
    conn = sqlite3.connect(DBNAME, detect_types=sqlite3.PARSE_DECLTYPES)
    c = conn.cursor()
    sqlstr = "SELECT * FROM calls where chatid='" + chatid + "'"
    if symbol:
        sqlstr += "and symbol='" + symbol + "'"

    callstxt = ''
    for row in c.execute(sqlstr):
        print(row)
        callstxt += row[4] + " : " + row[0] + " " + row[1] + "@" + row[2] + \
                    " " + row[3] + \
                    " on <i>" + row[7].strftime('%b %d %H:%M') + "</i>\n"
    return callstxt


def createcall(type, symbol, callrange, misc, user, chatid, userid):
    sqlstr = '''INSERT OR REPLACE INTO calls VALUES (?,?,?,?,?,?,?,?)'''
    params = list()
    # (type text, symbol text, callrange text, slrange text, user text, chatid text, userid text
    params.append(type)
    params.append(symbol)
    params.append(callrange)
    params.append(misc)
    params.append(user)
    params.append(chatid)
    params.append(userid)
    params.append(datetime.now())

    conn = sqlite3.connect(DBNAME)
    c = conn.cursor()
    c.execute(sqlstr, params)
    conn.commit()
    c.close()

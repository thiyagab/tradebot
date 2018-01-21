from peewee import *
from peewee import reduce,operator
from playhouse.sqlite_ext import SqliteExtDatabase
import datetime


db = SqliteExtDatabase('wolfca.db')

class BaseModel(Model):
    class Meta:
        database = db

#(type text, symbol text, callrange text, misc text,
 #                user text,chatid text,userid text,time timestamp

class Calls(BaseModel):
    sym=CharField()
    type=CharField()
    callrange=CharField()
    desc=CharField(null=True)
    user=CharField(null=True)
    chatid=CharField()
    userid=CharField(null=True)
    time=DateTimeField(default=datetime.datetime.now)
    misc=CharField(null=True)

    # def updateorreplace(self):
    #     self.insert(self).upsert().execute()

    class Meta:
        indexes = ((('sym', 'type','chatid'), True),)


#(symbol text,operation text, price text, chatid text,time timestamp,
#                 PRIMARY KEY (symbol,operation,chatid))''')

class Alert(BaseModel):
    sym=CharField()
    op=CharField()
    price=CharField()
    chatid=CharField()
    time=DateTimeField(default=datetime.datetime.now)
    misc=CharField(null=True)

    class Meta:
        indexes=((('sym','op','chatid'), True), )

class Events(BaseModel):
    name=CharField()
    date=DateTimeField()
    sym=CharField(null=True)
    type=CharField(null=True)



# db.connect()
# db.create_tables([Alert,Calls],safe=True)

def test():
    db.connect()
    db.create_tables([Alert,Calls],safe=True)
    alert = Alert(sym='INFY',type='BUY',price='1001')
    # alert.save(force_insert=False)

    Calls.insert(sym='ASHAPUR',type='BUY',callrange='1003',chatid='12345',userid='123').upsert().execute()
    Calls.insert(sym='INFY', type='BUY', callrange='1003', chatid='12345',userid='123').upsert().execute()
    Calls.insert(sym='watcccd', type='BUY', callrange='1003', chatid='12345',userid='123').upsert().execute()
    Calls.insert(sym='watcbin', type='BUY', callrange='1003', chatid='12345',userid='123').upsert().execute()
    Calls.insert(sym='watci', type='SELL', callrange='1003', chatid='12345',userid='123').upsert().execute()
    #
    # Alert.insert
    # #
    # #
    # print(Alert.insert(sym='INFY').upsert().execute())
    # deleteoldcalls()
    # for call in Calls.select():
    #     print(call.id,call.sym,call.type,call.callrange,call.time)

    for call in Calls.select().where(Calls.type!='WATCH'):
        print(call.sym,call.type,call.time)
    # print(Alert.get(Alert.sym=='INFY').price)

def deleteoldcalls():
    rowcount = Calls.delete().where(
        (Calls.sym == 'INFY') & (Calls.userid == '123') & (Calls.chatid == '12345')).execute()
    print(rowcount)
    for call in Calls.select():
        print(call.sym, call.type, call.time)



def getcalls(chatid, symbol=None):
    clauses=[(Calls.chatid==chatid),
             (Calls.type!='WATCH')]
    if symbol:
        clauses.append((Calls.sym==symbol))

    callstxt = ''

    for call in Calls.select().where(reduce(operator.and_,clauses)):
        print("Time: "+call.time.strftime('%b %d %H:%M'))
        callstxt +=  call.type + " " + call.sym + "@" + call.callrange \
                    +" on <i>" + call.time.strftime('%b %d %H:%M') + "</i>\n"
    return callstxt

if __name__ == '__main__':
    # test()
    # print(getcalls('12345'))
    deleteoldcalls()


from peewee import *
from playhouse.sqlite_ext import SqliteExtDatabase
import datetime

db = SqliteExtDatabase('test.db')

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

    def updateorreplace(self):
        self.insert(self).upsert().execute()

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

def test():
    db.connect()
    db.create_tables([Alert,Calls],safe=True)
    alert = Alert(sym='INFY',type='BUY',price='1001')
    # alert.save(force_insert=False)

    Calls.insert(sym='dsgdsg',type='BUY',callrange='1003',chatid='12345').upsert().execute()
    Calls.insert(sym='watcc', type='BUY', callrange='1003', chatid='12345').upsert().execute()
    Calls.insert(sym='watcccd', type='BUY', callrange='1003', chatid='12345').upsert().execute()
    Calls.insert(sym='watcbin', type='BUY', callrange='1003', chatid='12345').upsert().execute()
    Calls.insert(sym='watci', type='SELL', callrange='1003', chatid='12345').upsert().execute()
    #
    # Alert.insert
    # #
    # #
    # print(Alert.insert(sym='INFY').upsert().execute())
    deleteoldcalls()
    for call in Calls.select():
        print(call.id,call.sym,call.type,call.callrange,call.time)

    # for call in Calls.select().where(Calls.type!='WATCH'):
    #     print(call.type,call.time)
    # print(Alert.get(Alert.sym=='INFY').price)

def deleteoldcalls():
    calls=Calls.select(Calls.time).where(Calls.type!='WATCH').order_by(Calls.time.desc()).limit(2)
    print(Calls.delete().where((Calls.type!='WATCH') & (Calls.time.not_in(calls))).execute())

if __name__ == '__main__':
    test()


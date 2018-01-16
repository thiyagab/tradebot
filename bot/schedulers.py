import datetime

from web import nse,edelweiss
from bot import db

def ipos(bot,job):
    ipodetails=nse.getactiveipo()
    db.insertipos(ipodetails)

def events(bot,job):
    events=edelweiss.getevents()
    db.insertevents(events)


def schedulejobs(job_queue):
    job_queue.run_repeating(callback=ipos, interval=12 * 60 * 60, first=datetime.datetime.now())
    job_queue.run_repeating(callback=events, interval=12 * 60 * 60, first=datetime.datetime.now())

    return None
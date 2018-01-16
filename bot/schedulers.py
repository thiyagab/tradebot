import datetime

from web import nse,edelweiss
from bot import db
from bot.util import logger

def ipos(bot,job):
    ipodetails=nse.getactiveipo()
    db.insertipos(ipodetails)

def events(bot=None,job=None):
    events=edelweiss.getevents()
    db.insertevents(events)


def schedulejobs(job_queue):
    logger.info("Scheduling jobs..")
    job_queue.run_repeating(callback=ipos, interval=12 * 60 * 60, first=datetime.datetime.now())
    job_queue.run_repeating(callback=events, interval=12 * 60 * 60, first=datetime.datetime.now())

    return None

def main():
    events()
    print(db.getevents())


if __name__ == '__main__':
    main()

from web import nse
from bot import db

def ipos(bot,job):
    ipodetails=nse.getactiveipo()
    db.insertipos(ipodetails)


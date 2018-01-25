

def formatportfolio(portfoliolist):
    displaytext='Empty portfolio'
    if portfoliolist and len(portfoliolist)>0:
        displaytext=''
        for portfolio in portfoliolist:
            displaytext+=portfolio.sym
            displaytext+"\n"
    return displaytext

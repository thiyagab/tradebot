import feedparser


def readnews():
    parser=feedparser.parse('http://www.moneycontrol.com/rss/latestnews.xml')
    idx=0
    replytext=''
    for item in parser['entries']:
        title=item['title']
        link=item['link']
        title=title.replace('#39;',"'")
        idx+=1
        # print(idx,title)
        if idx<=10:
            replytext+='<a href="'+link+'">'+title+"</a>\n\n"
    return replytext



if __name__ == '__main__':
    readnews()

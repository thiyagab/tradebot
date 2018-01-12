import feedparser
import re


def cleanhtml(raw_html):
  cleanr = re.compile('<.*?>')
  cleantext = re.sub(cleanr, '', raw_html)
  return cleantext

parser=feedparser.parse('http://www.moneycontrol.com/rss/latestnews.xml')

for item in parser['entries']:
    title=item['title']
    link=item['link']
    print(link)




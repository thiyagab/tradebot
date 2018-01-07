import html
import re

import telegram
from telegram import TelegramError
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream,API
from alerts.twitter.util import escape_markdown,prepare_tweet_text


# Variables that contains yours credentials to access Twitter API
access_token = "83812829-L0Myd620u1IPoNfD0hQMtsjotbYNN9TlQGr3GK2rA"
access_token_secret = "rBjM7OThWglsYwOauXZmBXHywiP4eVeeccVKksEr7QgsG"
consumer_key = "ZIYZlTLiXBZnWbAzo45G38apc"
consumer_secret = "fDEz1QkietFosqJGY7xpRF0jYCWYuzGIIwEuPWosdETn3Od0FG"



# This is a basic listener that just prints received tweets to stdout.
class StdOutListener(StreamListener):

    # def on_data(self, data):
    #     print(data)
    #     return True

    def on_status(self, status):
        """Called when a new status arrives"""
        if not status.retweeted:
            tweet = gettweet(status)
            # print(tweet['user'])
            send_tweet(tweet)
        return


def gettweet(tweet):
        extensions = ('.jpg', '.jpeg', '.png', '.gif')
        pattern = '[(%s)]$' % ')('.join(extensions)
        photo_url = ''
        tweet_text = html.unescape(tweet.text)
        if 'media' in tweet.entities:
            photo_url = tweet.entities['media'][0]['media_url_https']
        else:
            for url_entity in tweet.entities['urls']:
                expanded_url = url_entity['expanded_url']
                if re.search(pattern, expanded_url):
                    photo_url = expanded_url
                    break
        # if photo_url:
            #self.logger.debug("- - Found media URL in tweet: " + photo_url)

        for url_entity in tweet.entities['urls']:
            expanded_url = url_entity['expanded_url']
            indices = url_entity['indices']
            display_url = tweet.text[indices[0]:indices[1]]
            tweet_text = tweet_text.replace(display_url, expanded_url)

        tw_data = {
            'tw_id': tweet.id,
            'text': tweet_text,
            'created_at': tweet.created_at,
            'user': tweet.user.name,
            'screen_name':tweet.user.screen_name,
            'photo_url': photo_url,
        }
        return tw_data




def send_tweet(tweet):
    try:
        '''
        Use a soft-hyphen to put an invisible link to the first
        image in the tweet, which will then be displayed as preview
        '''
        photo_url = ''
        if tweet['photo_url']:
            photo_url = '[\xad](%s)' % tweet['photo_url']

        # created_dt = utc.localize(tweet['created_at'])
        # if chat.timezone_name is not None:
        #     tz = timezone(chat.timezone_name)
        #     created_dt = created_dt.astimezone(tz)
        # created_at = created_dt.strftime('%Y-%m-%d %H:%M:%S %Z')
        fnnotifyalert(
            chatid='@stocktweets',
            text="""
{link_preview}*{name}* ([@{screen_name}](https://twitter.com/{screen_name})) at {created_at}:
{text}
-- [Link to this Tweet](https://twitter.com/{screen_name}/status/{tw_id})
"""
                .format(
                link_preview=photo_url,
                text=prepare_tweet_text(tweet['text']),
                name=escape_markdown(tweet['user']),
                screen_name=tweet['screen_name'],
                created_at=tweet['created_at'],
                tw_id=tweet['tw_id'],
            ),
            parse_mode=telegram.ParseMode.MARKDOWN)

    except TelegramError as e:
        print("Error",e)

fnnotifyalert = None
def startstreaming(notifyalert=None):
    global fnnotifyalert
    fnnotifyalert = notifyalert
    print('Listening to twitter..')
    l = StdOutListener()
    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    # api = API(auth)
    #
    # users=api.lookup_users(screen_names=['in_tradingview','Brainandmoney'])
    # for user in users:
    #     print(user.id,user.name )

    stream = Stream(auth, l)

    # This line filter tweets from the words.
    stream.filter(follow=['114968505','760853978837942272'], languages=['en'],async=True)

if __name__ == '__main__':
    # This handles Twitter authetification and the connection to Twitter Streaming API
    startstreaming()


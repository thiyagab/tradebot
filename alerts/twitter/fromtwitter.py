from pytz import utc, timezone
from telegram import TelegramError
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler,Stream
from bot.util import escape_markdown,prepare_tweet_text,logger
from bot.config import config
import sys,telegram,html,re

# Variables that contains yours credentials to access Twitter API
access_token = config['twitter']['ACCESS_TOKEN']
access_token_secret = config['twitter']['ACCESS_SECRET']
consumer_key = config['twitter']['CONSUMER_KEY']
consumer_secret = config['twitter']['CONSUMER_SECRET']



class TweetListener(StreamListener):

    # def on_data(self, data):
    #     print(data)
    #     return True

    def on_status(self, status):
        """Called when a new status arrives"""
        # print(status)
        try:
            if not hasattr(status, 'retweeted_status') and not status.in_reply_to_status_id:
                tweet = gettweet(status)
                # print(tweet['user'])
                send_tweet(tweet)
            else:
                logger.info('Not sending.. ')
        except :
            logger.error("Error handling status",sys.exc_info()[0])

        return


def gettweet(tweet):
        extensions = ('.jpg', '.jpeg', '.png', '.gif')
        pattern = '[(%s)]$' % ')('.join(extensions)
        media_url = ''
        tweet_text = html.unescape(tweet.text)
        if 'media' in tweet.entities:
            media_url = tweet.entities['media'][0]['media_url_https']
        else:
            for url_entity in tweet.entities['urls']:
                expanded_url = url_entity['expanded_url']
                if re.search(pattern, expanded_url):
                    media_url = expanded_url
                    break
        # if photo_url:
            #self.logger.debug("- - Found media URL in tweet: " + photo_url)

        # for url_entity in tweet.entities['urls']:
        #     expanded_url = url_entity['expanded_url']
        #     indices = url_entity['indices']
        #     display_url = tweet.text[indices[0]:indices[1]]
        #     tweet_text = tweet_text.replace(display_url, expanded_url)

        if hasattr(tweet,'extended_tweet'):
            # print('Extended text: ',tweet.extended_tweet["full_text"])
            tweet_text=tweet.extended_tweet["full_text"]

        tw_data = {
            'tw_id': tweet.id,
            'text': tweet_text,
            'created_at': tweet.created_at,
            'user': tweet.user.name,
            'screen_name':tweet.user.screen_name,
            'media_url': media_url,
        }
        return tw_data




def send_tweet(tweet):
    try:
        '''
        Use a soft-hyphen to put an invisible link to the first
        image in the tweet, which will then be displayed as preview
        '''
        media_url = ''
        if tweet['media_url']:
            media_url = '[\xad](%s)' % tweet['media_url']

        created_dt = utc.localize(tweet['created_at'])
        tz = timezone('Asia/Kolkata')
        created_dt = created_dt.astimezone(tz)
        created_at = created_dt.strftime('%b %d %H:%M')
        channel = config['telegram']['channel']
        if channel:
            if fnnotifyalert:
                fnnotifyalert(
                    chatid=channel,
                    text="""
        {link_preview}*{name}* ([@{screen_name}](https://twitter.com/{screen_name})) 
    
    {text}
        """
                        .format(
                        link_preview=media_url,
                        text=prepare_tweet_text(tweet['text']),
                        name=escape_markdown(tweet['user']),
                        screen_name=tweet['screen_name'],
                        created_at=created_at,
                    ),
                    disable_web_page_preview=not media_url,
                    parse_mode=telegram.ParseMode.MARKDOWN)

    except Exception as e:
        logger.error("Error",str(e))

fnnotifyalert = None
def startstreaming(notifyalert=None):
    if config['telegram']['channel']:
        global fnnotifyalert
        fnnotifyalert = notifyalert
        logger.info('Listening to twitter..')
        l = TweetListener()
        auth = OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        # api = API(auth)
        #

        # users=api.lookup_users(screen_names=['in_tradingview','Brainandmoney'])
        # for user in users:
        #     print(user.id,user.name )

        stream = Stream(auth, l)

        # This line filter tweets from the words.
        stream.filter(follow=['114968505'], languages=['en'],async=True)
        # stream.filter(track=['android'], languages=['en'], async=False)

if __name__ == '__main__':
    # This handles Twitter authetification and the connection to Twitter Streaming API
    startstreaming()


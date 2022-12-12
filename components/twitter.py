import tweepy
import tweepy.asynchronous
import html

# ----------------------------------------------------------------------------------------------------------------
# Twitter Component
# ----------------------------------------------------------------------------------------------------------------
# Improve the bot features using Twitter
# Tokens must be set in config.json
# ----------------------------------------------------------------------------------------------------------------

class Twitter():
    def __init__(self, bot):
        self.bot = bot
        self.data = None
        self.client = None

    def init(self):
        self.data = self.bot.data
        self.login()

    """login()
    Login to Twitter
    
    Returns
    --------
    bool: True if success, False if not
    """
    def login(self):
        try:
            self.client = tweepy.Client(bearer_token=self.bot.data.config['twitter']['bearer'])
            self.client.get_user(username='granblue_en', user_fields=['description', 'profile_image_url', 'pinned_tweet_id'])
            return True
        except:
            self.client = None # disable if error
            return False

    """user()
    Return a Twitter user
    
    Parameters
    ----------
    screen_name: Twitter user screen name
    
    Returns
    --------
    unknwon: None if error or the user if not
    """
    def user(self, screen_name : str):
        try: return self.client.get_user(username=screen_name, user_fields=['description', 'profile_image_url', 'pinned_tweet_id'])
        except: return None

    """timeline()
    Return a Twitter user timeline
    
    Parameters
    ----------
    screen_name: Twitter user screen name
    
    Returns
    --------
    unknwon: None if error or the user timeline if not
    """
    def timeline(self, screen_name, token=None):
        try: 
            user = self.user(screen_name)
            if token is None:
                return self.client.get_users_tweets(id=user.data.id, tweet_fields=['context_annotations', 'created_at', 'entities', 'public_metrics'], user_fields=['profile_image_url'], media_fields=['preview_image_url', 'url'], expansions=['author_id', 'attachments.media_keys', 'entities.mentions.username', 'referenced_tweets.id', 'referenced_tweets.id.author_id'], max_results=10)
            else:
                return self.client.get_users_tweets(id=user.data.id, tweet_fields=['context_annotations', 'created_at', 'entities', 'public_metrics'], user_fields=['profile_image_url'], media_fields=['preview_image_url', 'url'], expansions=['author_id', 'attachments.media_keys', 'entities.mentions.username', 'referenced_tweets.id', 'referenced_tweets.id.author_id'], pagination_token=token, max_results=10)
        except:
            return None

    """pinned()
    Return a Twitter user's pinned tweet.
    Note: it's mostly to access the tweet text. If you are interested in attachments and such, you better use user() and tweet() on your own.
    
    Parameters
    ----------
    screen_name: Twitter user screen name
    
    Returns
    --------
    unknwon: None if error or the user's pinned tweet
    """
    def pinned(self, screen_name):
        try: 
            user = self.user(screen_name)
            tweets = self.tweet([user.data.pinned_tweet_id])
            return tweets.data[0]
        except:
            return None

    """tweet()
    Return a list of tweets
    
    Parameters
    ----------
    ids: List of tweet ids to retrieve
    
    Returns
    --------
    unknwon: None if error or the tweet list dict otherwise
    """
    def tweet(self, ids):
        try: 
            return self.client.get_tweets(ids=ids, tweet_fields=['context_annotations', 'created_at', 'entities', 'public_metrics'], user_fields=['profile_image_url'], media_fields=['preview_image_url', 'url'], expansions=['author_id', 'attachments.media_keys', 'entities.mentions.username', 'referenced_tweets.id', 'referenced_tweets.id.author_id'])
        except:
            return None

    """user_last_tweet()
    Return a list of tweets from an user
    
    Parameters
    ----------
    screen_name: Twitter user screen name
    
    Returns
    --------
    unknwon: An object containing tweets of the user, None if error
    """
    def user_last_tweet(self, screen_name):
        try: 
            user = self.client.get_user(username=screen_name, user_fields=['description', 'profile_image_url', 'pinned_tweet_id']).data
            return self.client.get_users_tweets(id=user.id, tweet_fields=['context_annotations', 'created_at', 'entities', 'public_metrics'], user_fields=['profile_image_url'], media_fields=['preview_image_url', 'url'], expansions=['author_id', 'attachments.media_keys', 'entities.mentions.username', 'referenced_tweets.id', 'referenced_tweets.id.author_id'], max_results=10)
        except:
            return None

    """get_schedule_from_granblue_en()
    Get the pinned schedule tweet from @Granblue_EN to make a schedule list usable by the bot
    
    Returns
    --------
    tuple:
        - str: Title/Month
        - list: Schedule
        - time: tweet.created_at
    """
    def get_schedule_from_granblue_en(self):
        tw = self.pinned('granblue_en')
        month = None
        schedule = None
        created_at = None
        if tw is not None:
            txt = html.unescape(tw.text)
            if txt.find(" = ") != -1 and txt.find("chedule") != -1:
                created_at = tw.created_at
                s = txt.find("https://t.co/")
                if s != -1: txt = txt[:s]
                lines = txt.split('\n')
                month = lines[0]
                schedule = []
                for i in range(1, len(lines)):
                    if lines[i] != "":
                        schedule += lines[i].split(" = ")
        return month, schedule, created_at
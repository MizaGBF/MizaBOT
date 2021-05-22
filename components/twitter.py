import tweepy

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
        self.api = None

    def init(self):
        self.data = self.bot.data
        self.login()

    def login(self):
        try:
            auth = tweepy.OAuthHandler(self.data.config['twitter']['key'], self.data.config['twitter']['secret'])
            auth.set_access_token(self.data.config['twitter']['access'], self.data.config['twitter']['access_secret'])
            self.api = tweepy.API(auth)
            if self.api.verify_credentials() is None: raise Exception()
            return True
        except:
            self.api = None # disable if error
            return False

    def user(self, screen_name : str):
        try: return self.api.get_user(screen_name)
        except: return None

    def timeline(self, screen_name):
        try: return self.api.user_timeline(screen_name, tweet_mode='extended')
        except: return None
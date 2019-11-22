import logging
import traceback
import tweepy

from src.twitter.secret import CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_SECRET

logger = logging.getLogger("pycurser")


def init_twitter_handler() -> tweepy.API:

    api = None
    try:

        # create OAuthHandler object and set access
        auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
        auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)

        # create tweepy API object to fetch tweets
        api = tweepy.API(auth)

    except:
        logger.error("Error: Authentication Failed\n{}".format(traceback.format_exc()))

    return api


def send_tweet(api: tweepy.API, msg: str):
    response = api.update_status(msg)
    return response


def follow_back(api):
    logger.info("Retrieving and following followers")
    for follower in tweepy.Cursor(api.followers).items():
        if not follower.following:
            logger.info(f"Following {follower.name}")
            follower.follow()

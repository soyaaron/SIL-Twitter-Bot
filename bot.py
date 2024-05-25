import tweepy

# Authenticate to Twitter
api_key = "lM6aYeIuIOkmeaNqM3uGXt4FA"
api_secret_key = "9VW9Ho8w301SByP0pR6NMeRS9oE9adPGed4xbP3FExK0scNbZB"
bearer_token = "AAAAAAAAAAAAAAAAAAAAAKzatwEAAAAAqfec2s6OxZwiPzGDY%2BJ4ZgX52ns%3DX3uaBlKVzUeGSDNomHEJW3IF5tY2UdWwpvHgPZ9lguxJFx0jAl"
access_token = "1794203537653497856-IXws9tg5fL7le9pt69SBZcBPVDrciE"
access_token_secret = "Bo7HDaKpdKLqXY66urEOdTe1ed8iuA83TJpubEhURSj6N"

auth = tweepy.OAuthHandler(api_key, api_secret_key)
auth.set_access_token(access_token, access_token_secret)

api = tweepy.API(auth)

try:
    api.update_status("Hola mundo :)")
    print("Tweet posted successfully")
except Exception as e:
    print(f"An error occurred: {e}")
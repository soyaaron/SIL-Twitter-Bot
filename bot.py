import tweepy
#bearer_token = "AAAAAAAAAAAAAAAAAAAAAKzatwEAAAAAqfec2s6OxZwiPzGDY%2BJ4ZgX52ns%3DX3uaBlKVzUeGSDNomHEJW3IF5tY2UdWwpvHgPZ9lguxJFx0jAl",

client = tweepy.Client(
# Authenticate to Twitter
consumer_key = "lM6aYeIuIOkmeaNqM3uGXt4FA",
consumer_secret = "9VW9Ho8w301SByP0pR6NMeRS9oE9adPGed4xbP3FExK0scNbZB",
access_token = "1794203537653497856-IXws9tg5fL7le9pt69SBZcBPVDrciE",
access_token_secret = "Bo7HDaKpdKLqXY66urEOdTe1ed8iuA83TJpubEhURSj6N",
)

response = client.create_tweet(text='vienen cosas 😎')
print(response)

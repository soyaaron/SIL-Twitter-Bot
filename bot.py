import datetime
import configparser
import tweepy
import json
from azure.cosmos import CosmosClient, PartitionKey, exceptions

config = configparser.ConfigParser()
config.read('config.ini')

# Azure setup
endpoint = config.get('Database', 'endpoint')
key = config.get('Database', 'key')
database_name = config.get('Database', 'database_name')
container_name = config.get('Database', 'container_name')
container_aztweets = 'LastestTweet'

# Initialize the Cosmos client
clientAZ = CosmosClient(endpoint, key)
database = clientAZ.get_database_client(database_name)
container = database.get_container_client(container_name)
containerTW = database.get_container_client(container_aztweets)

# Twitter API v2 access
clientTW = tweepy.Client(
    consumer_key=config.get('Twitter', 'consumer_key'),
    consumer_secret=config.get('Twitter', 'consumer_secret'),
    access_token=config.get('Twitter', 'access_token'),
    access_token_secret=config.get('Twitter', 'access_token_secret')
)

# Twitter API v1 access
auth = tweepy.OAuthHandler(config.get('Twitter', 'consumer_key'), config.get('Twitter', 'consumer_secret'))
auth.set_access_token(config.get('Twitter', 'access_token'), config.get('Twitter', 'access_token_secret'))
api = tweepy.API(auth, wait_on_rate_limit=True)

# Function to query the latest session data
queryLatestSesion = f"""
SELECT top 1
    rs,
    (SELECT VALUE COUNT(1) 
     FROM a IN c.sesion.asistencia 
     WHERE a.presente = false and a.excusa = false) AS cantidadAusentesCount,
    (SELECT VALUE COUNT(1) 
     FROM a IN c.sesion.asistencia 
     WHERE a.excusa = true) AS cantidadExcusasCount
FROM c
JOIN rs IN c.sesion.resumen_sesion
ORDER BY c.sesion.resumen_sesion[0].id_sesion DESC
"""
queryLastestTweet = "SELECT TOP 1 c.id, c.fecha FROM c ORDER BY c.id DESC"

items = list(container.query_items(
    query=queryLatestSesion,
    enable_cross_partition_query=True
))

itemsLatestTweet = list(containerTW.query_items(
    query=queryLastestTweet,
    enable_cross_partition_query=True
))
resultsLatestTweet = itemsLatestTweet

for item in resultsLatestTweet:
    latestTweetId = item['id']

results = items
for item in results:
    rs = item['rs']
    cantidadAusentesCount = item['cantidadAusentesCount']
    cantidadExcusasCount = item['cantidadExcusasCount']
    cantidadPresentes = rs['cantidadPresentes']
    totalLegisladores = rs['totalLegisladores']
    numero = rs['numero']
    fecha = rs['fecha']
    source = rs['source']
    lugar = rs['lugar']
    idSesion = str(rs['id_sesion'])
    print(idSesion, latestTweetId)


    if idSesion != latestTweetId:
        tweet = f"""🏛️ {lugar}
Sesión: {numero}
Fecha: {fecha[:10]}
\nAsistencia:
🔴 AUSENTES SIN EXCUSA: {cantidadAusentesCount}
🟡 AUSENTES CON EXCUSA: {cantidadExcusasCount}
⚫ TOTAL AUSENTES: {cantidadAusentesCount + cantidadExcusasCount}
🟢 PRESENTES: {cantidadPresentes}/{totalLegisladores}
\nℹ️ Fuente: {source}
\n🧵 1/3"""

        #tweer 1
        response = clientTW.create_tweet(text=tweet)
        response_data = response.data  # Access the 'data' attribute
        tweet_id = response_data['id']
        #tweet 2
        media_id = api.media_upload(filename="ausente_sin_excusa.png").media_id_string
        response2 = clientTW.create_tweet(text="🔴 Ausencias sin excusa \n🧵 2/3", media_ids=[media_id], in_reply_to_tweet_id=tweet_id)
        response_data2 = response2.data
        tweet_id = response_data2['id']
        #tweet 3
        media_id2 = api.media_upload(filename="ausente_con_excusa.png").media_id_string
        clientTW.create_tweet(text="🟡 Ausencias con excusa \n🧵 3/3", media_ids=[media_id2], in_reply_to_tweet_id=tweet_id)
        print(response)

        # Upload latest tweet to the database
        latestTweet = {
            'id': str(133317),  # Ensure this is a string
            'fecha': datetime.datetime.now().isoformat()
        }
        containerTW.create_item(body=latestTweet)
    else:
        print("No se encontraron resultados para la sesión especificada.")

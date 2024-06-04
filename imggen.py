import datetime
import configparser
import tweepy
import json
from azure.cosmos import CosmosClient, PartitionKey, exceptions
from PIL import Image, ImageDraw, ImageFont

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

# Function to query the latest session data
queryLatestSesion = "select top 1 c.sesion.resumen_sesion[0].id_sesion from c order by c.sesion.resumen_sesion[0].id_sesion desc"
items = list(container.query_items(
    query=queryLatestSesion,
    enable_cross_partition_query=True
))
latestSesion = items[0]['id_sesion']

queryLastestTweet = "SELECT TOP 1 c.id, c.fecha FROM c ORDER BY c.id DESC"
itemsLatestTweet = list(containerTW.query_items(
    query=queryLastestTweet,
    enable_cross_partition_query=True
))
latestTweetId = itemsLatestTweet[0]['id']

print(latestTweetId, latestSesion)

for idSesion in range(int(latestTweetId)+1, int(latestSesion) + 1):  # Ensure the range includes the latest session
    print("Processing session ID:", idSesion)
    querySesion = f"""
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
        WHERE c.sesion.resumen_sesion[0].id_sesion = {idSesion}
    """
    items = list(container.query_items(
        query=querySesion,
        enable_cross_partition_query=True
    ))
    if items:
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
            print(f"Session {idSesion} processed with data.")
    else:
        print(f"No data found for session ID: {idSesion}")

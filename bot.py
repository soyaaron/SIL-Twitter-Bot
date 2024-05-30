import configparser
import tweepy
from azure.cosmos import CosmosClient, exceptions

config = configparser.ConfigParser()
config.read('config.ini')

#azure setup 
endpoint = config.get('Database','endpoint')
key = config.get('Database','key')
database_name = config.get('Database','database_name')
container_name = config.get('Database','container_name')
# Inicializar el cliente de Cosmos
clientAZ = CosmosClient(endpoint, key)
database = clientAZ.get_database_client(database_name)
container = database.get_container_client(container_name)

#  Twitter setup
clientTW = tweepy.Client(
    consumer_key= config.get('Twitter','consumer_key'),
    consumer_secret=config.get('Twitter','consumer_secret'),
    access_token=config.get('Twitter','access_token'),
    access_token_secret=config.get('Twitter','access_token_secret')
)
auth = tweepy.OAuthHandler(config.get('Twitter','consumer_key'), config.get('Twitter','consumer_secret'))
auth.set_access_token(config.get('Twitter','access_token'), config.get('Twitter','access_token_secret'))
api = tweepy.API(auth, wait_on_rate_limit=True)




# Función para consultar los datos por id_sesion
query = f"""SELECT top 1
        rs,
        (SELECT VALUE COUNT(1) 
         FROM a IN c.sesion.asistencia 
         WHERE a.presente = false and a.excusa = false) AS cantidadAusentesCount,
        (SELECT VALUE COUNT(1) 
         FROM a IN c.sesion.asistencia 
         WHERE a.excusa = true) AS cantidadExcusasCount
        FROM c
        JOIN rs IN c.sesion.resumen_sesion
        order by c.sesion.resumen_sesion[0].id_sesion desc"""
items = list(container.query_items(
        query=query,
        enable_cross_partition_query=True
    ))

results = items
if results:
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
            
            tweet = f"""🏛️ {lugar}
Sesión: {numero}
Fecha: {fecha[:10]}
\nAsistencia:
🔴 AUSENTES SIN EXCUSA: {cantidadAusentesCount}
🟡 AUSENTES CON EXCUSA: {cantidadExcusasCount}
⚫ TOTAL AUSENTES: {cantidadAusentesCount + cantidadExcusasCount}
🟢 PRESENTES: {cantidadPresentes}/{totalLegisladores}
\nℹ️ Fuente: {source}"""

        response= clientTW.create_tweet(text=tweet) 
        response_data = response[0]
        tweet_id = response_data['id'] 
        

        media_id = api.media_upload(filename="ausente_sin_excusa.png").media_id_string
        response2 = clientTW.create_tweet(text="🔴 Ausencias sin excusa",media_ids=[media_id], in_reply_to_tweet_id=tweet_id)
        response_data2 = response2[0]      
        tweet_id = response_data2['id']

        media_id2 = api.media_upload(filename="ausente_con_excusa.png").media_id_string
        clientTW.create_tweet(text="🟡 Ausencias con excusa",media_ids=[media_id2] ,in_reply_to_tweet_id=tweet_id)
        print(response)
            
    
else:
        print("No se encontraron resultados para la sesión especificada.")


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


#  Twitter setup
clientTW = tweepy.Client(
    consumer_key= config.get('Twitter','consumer_key'),
    consumer_secret=config.get('Twitter','consumer_secret'),
    access_token=config.get('Twitter','access_token'),
    access_token_secret=config.get('Twitter','access_token_secret')
)


# Inicializar el cliente de Cosmos
clientAZ = CosmosClient(endpoint, key)
database = clientAZ.get_database_client(database_name)
container = database.get_container_client(container_name)

# Función para consultar los datos por id_sesion
def query_by_id_sesion(id_sesion):
    query = f"""SELECT 
        rs,
        (SELECT VALUE COUNT(1) 
         FROM a IN c.sesion.asistencia 
         WHERE a.presente = false and a.excusa = false) AS cantidadAusentesCount,
        (SELECT VALUE COUNT(1) 
         FROM a IN c.sesion.asistencia 
         WHERE a.excusa = true) AS cantidadExcusasCount
        FROM c
        JOIN rs IN c.sesion.resumen_sesion
        WHERE rs.id_sesion = {id_sesion}"""
    items = list(container.query_items(
        query=query,
        enable_cross_partition_query=True
    ))
    return items

# Función para formatear y publicar el tweet
def publicar_tweet(id_sesion):
    results = query_by_id_sesion(id_sesion)
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

            response = clientTW.create_tweet(text=tweet)
            print(response)
    else:
        print("No se encontraron resultados para la sesión especificada.")

# Ejemplo de uso
#id_sesion = 133299
#publicar_tweet(id_sesion)
def publicar_tweets_en_rango(id_sesion_inicio, id_sesion_fin):
    for id_sesion in range(id_sesion_inicio, id_sesion_fin + 1):
        publicar_tweet(id_sesion)

# Ejemplo de uso: publicar tweets desde id_sesion 133299 hasta 133316
publicar_tweets_en_rango(133300 , 133316)
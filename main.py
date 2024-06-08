import datetime
import os
import configparser
import tweepy
import json
from azure.cosmos import CosmosClient, PartitionKey, exceptions
from PIL import Image, ImageDraw, ImageFont

config = configparser.ConfigParser()
config.read('config.ini')

# Azure setup
#endpoint = config.get('Database', 'endpoint')
#key = config.get('Database', 'key')
#database_name = config.get('Database', 'database_name')
#container_name = config.get('Database', 'container_name')
endpoint = os.getenv("ENDPOINT")
key = os.getenv("KEY")
database_name = os.getenv("DATABASE_NAME")
container_name = os.getenv("CONTAINER_NAME")
container_aztweets = 'LastestTweet'

# Initialize the Cosmos client
clientAZ = CosmosClient(endpoint, key)
database = clientAZ.get_database_client(database_name)
container = database.get_container_client(container_name)
containerTW = database.get_container_client(container_aztweets)

# Twitter API v2 access
clientTW = tweepy.Client(
    #consumer_key=config.get('Twitter', 'consumer_key'),
    #consumer_secret=config.get('Twitter', 'consumer_secret'),
    #access_token=config.get('Twitter', 'access_token'),
    #access_token_secret=config.get('Twitter', 'access_token_secret')
    
    consumer_key=os.getenv('consumer_key'),
    consumer_secret=os.getenv('consumer_secret'),
    access_token=os.getenv('access_token'),
    access_token_secret=os.getenv('access_token_secret')
)

# Twitter API v1 access
#auth = tweepy.OAuthHandler(config.get('Twitter', 'consumer_key'), config.get('Twitter', 'consumer_secret'))
#auth.set_access_token(config.get('Twitter', 'access_token'), config.get('Twitter', 'access_token_secret'))
auth = tweepy.OAuthHandler(os.getenv('consumer_key'), os.getenv('consumer_secret'))
auth.set_access_token(os.getenv('access_token'), os.getenv('access_token_secret'))
api = tweepy.API(auth, wait_on_rate_limit=True)

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

for idSesion in range(int(latestTweetId)+1, int(latestSesion) + 1): 
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
        
        queryLatestAsistencia = """SELECT top 1 c.sesion.asistencia FROM c ORDER BY c.sesion.resumen_sesion[0].id_sesion DESC"""
        items = list(container.query_items(
            query=queryLatestAsistencia,
            enable_cross_partition_query=True
        ))

        results = items

        result_no_excusa = [item for item in results[0]['asistencia'] if not item['presente'] and not item['excusa']]
        result_excusa = [item for item in results[0]['asistencia'] if not item['presente'] and item['excusa']]
        
                # Function to create image
                 # Function to create image with photos
        def create_image_with_photos(legislators, folder_path, file_name,asistenciaType):
            photos_per_row = 5
            photo_size = 150  # Assuming each photo is 150x150 pixels
            spacing = 20
            font_path = "OpenSans-Regular.ttf"
            font_size = 14
            font = ImageFont.truetype(font_path, font_size)
            
            # Calculate dimensions for the image
            rows = (len(legislators) + photos_per_row - 1) // photos_per_row
            image_width = photos_per_row * (photo_size + spacing) + spacing
            image_height = rows * (photo_size + spacing) + spacing + 100  # Extra space for title and names
            
            # Create a new blank image with white background
            background_color = (255, 255, 255)
            image = Image.new("RGB", (image_width, image_height), background_color)
            draw = ImageDraw.Draw(image)
            
            y_position = 20  # Initial y position for the title
            draw.text((image_width // 2, y_position), asistenciaType, fill=(0, 0, 0), font=font, anchor="mm")
            y_position += 30  # Adjust y position to start adding photos
            
            for index, legislator in enumerate(legislators):
                legislator_id = legislator['legisladorId']
                nombre_completo = legislator['nombreCompleto']
                
                # Find the photo matching the legislator_id
                photo_path = None
                for file_names in os.listdir(folder_path):
                    if file_names.startswith(f"{legislator_id}_") and file_names.endswith(".png"):
                        photo_path = os.path.join(folder_path, file_names)
                        break
                    
                x_position = spacing + (index % photos_per_row) * (photo_size + spacing)
                y_photo_position = y_position + (index // photos_per_row) * (photo_size + spacing)
                
                if photo_path and os.path.exists(photo_path):
                    photo = Image.open(photo_path).resize((photo_size, photo_size))
                    image.paste(photo, (x_position, y_photo_position))
                else:
                    draw.rectangle([(x_position, y_photo_position), 
                                    (x_position + photo_size, y_photo_position + photo_size)], 
                                   outline="black", width=1)
                    text_position = (x_position + photo_size // 2, y_photo_position + photo_size // 2)
                    draw.text(text_position, nombre_completo, fill="black", font=font, anchor="mm")
            
            # Save the image
            image.save(file_name)
        
        # Define the path to the folder with photos
        folder_path = 'newphotos'
        
        # Create images
        create_image_with_photos(result_no_excusa, folder_path, "ausente_sin_excusa.png","Ausencias Sin Excusa")
        create_image_with_photos(result_excusa, folder_path, "ausente_con_excusa.png","Ausencias Con Excusa")

#        font_path = "OpenSans-Regular.ttf"
#        font_size = 18
#        font = ImageFont.truetype(font_path, font_size)
#
#        def create_image(legislators, file_name):
#            max_width = 800
#            line_spacing = 30
#
#            # Calculate the height required for the content and add padding
#            image_height = len(legislators) * line_spacing + 100 
#
#            # Create a new blank image with white background
#            image_width = max_width + 100  
#            background_color = (255, 255, 255)
#            image = Image.new("RGB", (image_width, image_height), background_color)
#
#            draw = ImageDraw.Draw(image)
#            y_position = 50
#
#            for legislador in legislators:
#                nombre_completo = legislador['nombreCompleto']
#                draw.text((50, y_position), f"• {nombre_completo}", fill=(0, 0, 0), font=font)
#                y_position += line_spacing
#
#            image.save(file_name)
#
#        create_image(result_no_excusa, "ausente_sin_excusa.png")
#        create_image(result_excusa, "ausente_con_excusa.png")

        #tweet 1
        response = clientTW.create_tweet(text=tweet)
        response_data = response.data  
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
            'id': str(latestSesion),
            'fecha': datetime.datetime.now().isoformat()
        }
        containerTW.create_item(body=latestTweet)
    else:
        print("No se encontraron resultados para la sesión especificada.")

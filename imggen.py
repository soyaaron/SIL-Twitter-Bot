# Import necessary libraries
import datetime
import os
import configparser
import tweepy
import json
from azure.cosmos import CosmosClient, PartitionKey, exceptions
from PIL import Image, ImageDraw, ImageFont

# Read configuration
config = configparser.ConfigParser()
config.read('config.ini')

# Set up CosmosDB client
endpoint = 'https://sil-bot-db.documents.azure.com:443/'
key = 'o5YF7FZfkqIJWAG8vqh5LciXwPst5IwloqPqszb4LMB9gkFQXo73MMFWuzeCjF5pw9ggHpP9FYJxACDbtbdGHw=='
database_name = 'ToDoList'
container_name = 'Sesiones'
container_aztweets = 'LastestTweet'

clientAZ = CosmosClient(endpoint, key)
database = clientAZ.get_database_client(database_name)
container = database.get_container_client(container_name)
containerTW = database.get_container_client(container_aztweets)

# Query latest attendance
queryLatestAsistencia = """SELECT top 1 c.sesion.asistencia FROM c ORDER BY c.sesion.resumen_sesion[0].id_sesion DESC"""
items = list(container.query_items(
    query=queryLatestAsistencia,
    enable_cross_partition_query=True
))

results = items
#print(results)

# Filter attendance results
result_no_excusa = [item for item in results[0]['asistencia'] if not item['presente'] and not item['excusa']]
result_excusa = [item for item in results[0]['asistencia'] if not item['presente'] and item['excusa']]

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

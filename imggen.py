import configparser
import tweepy
from azure.cosmos import CosmosClient, exceptions
from PIL import Image, ImageDraw, ImageFont

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

# Función para consultar los datos por id_sesion
query = f"""SELECT top 1 c.sesion.asistencia  FROM c order by c.sesion.resumen_sesion[0].id_sesion desc"""
items = list(container.query_items(
        query=query,
        enable_cross_partition_query=True
    ))

results = items

result_no_excusa = [item for item in results[0]['asistencia'] if not item['presente'] and not item['excusa']]
result_excusa = [item for item in results[0]['asistencia'] if not item['presente'] and item['excusa']]


# Load a default font
font_path = "arial.ttf"
font_size = 18
font = ImageFont.truetype(font_path, font_size)

# Define bullet point character
bullet = "•"

# Initialize variables
max_width = 800
line_spacing = 30



# Calculate the height required for the content
image_height = len(result_no_excusa) * line_spacing + 100  # Adding some padding

# Create a new blank image with white background
image_width = max_width + 100  # Adding some padding
background_color = (255, 255, 255)
image = Image.new("RGB", (image_width, image_height), background_color)

# Initialize drawing context
draw = ImageDraw.Draw(image)

# Set initial position for drawing text
y_position = 50

# Draw the names on the image with bullet points
for legislador in result_no_excusa:
    nombre_completo = legislador['nombreCompleto']
    draw.text((50, y_position), f"{bullet} {nombre_completo}", fill=(0, 0, 0), font=font)
    y_position += line_spacing

# Save the image
image.save("ausente_sin_excusa.png")

from call_api import call_4_images
from PIL import Image

path = '/Users/alkalisk/Downloads/04.png'
img = Image.open(path)
call_4_images('/Users/alkalisk/Downloads/',img)
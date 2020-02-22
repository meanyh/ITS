import os
import io, re
from PIL import Image
from array import array
import numpy as np

def readimage(path):
    count = os.stat(path).st_size / 2
    with open(path, "rb") as f:
        return bytearray(f.read())

def pil_grid(images):
    rows = 7
    columns = 7
    height = 18
    width = 32
    full = []
    k = 0
    full = Image.new( 'RGB', (  columns * width, rows * height ) )
    for j in range( 0, rows * height, height ):
        for i in range( 0, columns * width, width ):
            # paste the image at location i,j:
            full.paste( images[k], (i,j) )
            # Select next image and text
            k = k + 1
    full.save("savepath.jpg")

path = "img/split/"
files = []
for file in sorted(os.listdir( path ), key=lambda x: (int(re.sub('\D','',x)),x)):
    print(file)
    bytes = readimage(path+file)
    print(bytes)
    image = Image.open(io.BytesIO(bytes))
    files.append(image)
pil_grid(files)
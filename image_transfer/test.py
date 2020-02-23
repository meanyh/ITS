import os
import io, re
from PIL import Image
from array import array
import numpy as np
import math
import datetime, time

crop_h = 18
crop_w = 32
height = 94
width = 168

def readimage(path):
    count = os.stat(path).st_size / 2
    with open(path, "rb") as f:
        return bytearray(f.read())

def pil_grid(images):
    rows = math.ceil(height / crop_h)
    columns = math.ceil(width / crop_w)
    full = []
    k = 0
    full = Image.new( 'RGB', (  width, height ) )
    for j in range( 0, rows * crop_h, crop_h ):
        if (k >= len(images)):
            break
        for i in range( 0, columns * crop_w, crop_w ):
            # paste the image at location i,j:
            print(i, j, k, len(images))
            if (k >= len(images)):
                break
            full.paste( images[k], (i,j) )
            # Select next image and text
            k = k + 1
    full.save("img/IMG-4k.jpg")

# path = "img/split/"
# files = []
# for file in sorted(os.listdir( path ), key=lambda x: (int(re.sub('\D','',x)),x)):
#     # print(file)
#     bytes = readimage(path+file)
#     # print(bytes)
#     image = Image.open(io.BytesIO(bytes))
#     files.append(image)
# pil_grid(files)

now = str(datetime.datetime.utcnow())
time.sleep(5)
next = str(datetime.datetime.utcnow())
print(datetime.datetime.strptime(next, '%Y-%m-%d %H:%M:%S.%f') - datetime.datetime.strptime(now, '%Y-%m-%d %H:%M:%S.%f'))
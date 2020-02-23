import subprocess as sp
import numpy as np
from PIL import Image, ImageFile
import os
import re
import serial
import time, datetime
import json
import io
import shutil
import math

dest_path = ""
crop_h = 18
crop_w = 32

def clear(path):
    for filename in os.listdir(path):
        file_path = os.path.join(path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

def clean_one_img(byte_array):
    delete_list = [b"Receive: ", b"656E64", b"\r\n", b"Sent", b"end", b".jpg"]
    try:
        first = byte_array.index(b"IMG-")
        last = byte_array.index(b":", first)
        name = byte_array[first:last].decode()
        byte_array = byte_array[:first] + byte_array[last+1:]
        while 1:
            if b"Size: " in byte_array:
                first = byte_array.index(b"Size")
                last = byte_array.index(b"\r\n", first)
                byte_array = byte_array[:first] + byte_array[last:]
            else:
                break
        for word in delete_list:
            byte_array = byte_array.replace(word, b"")
        return bytearray(byte_array), name
    except Exception as e:
            print('Failed to clean. Reason: %s' % e)

def save_img(image_data):
    split_path = dest_path + "split/"
    image_data, imgname = clean_one_img(image_data)
    ImageFile.LOAD_TRUNCATED_IMAGES = True
    try:
        image = Image.open(io.BytesIO(image_data))
        image.save(split_path + imgname + ".jpg")
        print("Save Image %s" % imgname)
    except Exception as e:
        print("Cannot Open Image %s: %s" % (imgname, e))

def check_img(image_data):
    if image_data.count(b"IMG-") > 1:
        index = image_data.index(b"IMG-", 5)
        save_img(image_data[:index])
        save_img(image_data[index:])
    else:
        save_img(image_data)

def readimage(path):
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
            if (k >= len(images)):
                break
            full.paste( images[k], (i,j) )
            # Select next image and text
            k = k + 1
    full.save(dest_path + img_name)

def merge_img():
    files = []
    path = dest_path + "split/"
    k = 0
    for file in sorted(os.listdir( path ), key=lambda x: (int(re.sub('\D','',x)),x)):
        while str(k) not in file:
            image = Image.new('RGB', (crop_w, crop_h))
            files.append(image)
            k+=1
        bytes = readimage(path+file)
        image = Image.open(io.BytesIO(bytes))
        files.append(image)
        k+=1
    pil_grid(files)
    clear(path)

def read_description(ser, read):
    while True:
        if ser.in_waiting:
            tmp = ser.read()
            read += tmp
            if b"Sent" in read:
                ser.write(b"get Data")
                global img_name, height, width, time
                read = read[len("Description: ") - 1:read.index(b"Size: ")]
                img_name = read.split(b", ")[0].decode()
                height = int(read.split(b", ")[1].decode())
                width = int(read.split(b", ")[2].decode())
                time = str(read.split(b", ")[3].decode())
                break

def recieve_part(ser):
    receive = b""
    read = b""
    tmp = b""
    end = False
    while True:
        if ser.in_waiting:
            tmp = ser.read()
            read += tmp
            if b"Description: " in read:
                read_description(ser, read)
                read = b""
            if b"Sent" in read:
                ser.write(b"get Data")
                receive += read
                if b".jpg" in read:
                    ser.write(b"end Data")
                    check_img(receive)
                    receive = b""
                if b"656E64\r\n" in read or b"end" in read:
                    end = True
                    break
                read = b"" 
    if end:
        merge_img()
        read_time()

def read_time():
    now = datetime.datetime.utcnow()
    print(time)
    print(now)
    print(now - datetime.datetime.strptime(time, '%Y-%m-%d %H:%M:%S.%f'))

def main():
    with open('./config.json','r') as f:
        config = json.load(f)

    port = config['PORT']
    global dest_path
    dest_path = config["DEST_PATH"]
    
    ser = serial.Serial(port[0],115200)
    recieve_part(ser)

if __name__ == "__main__":
	main()
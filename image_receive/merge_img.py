import subprocess as sp
import numpy as np
from PIL import Image
import os
import re
import serial
import time
import json
import io

def clean_one_img(byte_array):
    delete_list = [b"Receive: ", b"656E64", b"\r\n", b"Sent", b"end", b".jpg"]
    print(byte_array)
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

def save_img(image_data):
    split_path = "img/split/"
    image_data, imgname = clean_one_img(image_data)
    try:
        image = Image.open(io.BytesIO(image_data))
        image.save(split_path + imgname + ".jpg")
    except:
        print("Cannot Open Image")

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

def merge_img(image_data):
    split_path = "img/"
    image_data, imgname = clean_one_img(image_data)
    try:
        image = Image.open(io.BytesIO(image_data))
        image.save(split_path + imgname + ".jpg")
    except:
        print("Cannot Open Image")

def recieve_part(ser):
    receive = b""
    read = b""
    tmp = b""
    end = False
    while True:
        if ser.in_waiting:
            tmp = ser.read()
            read += tmp
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

def main():
    with open('./config.json','r') as f:
        config = json.load(f)

    port = config['PORT']
    imgname = config['IMAGE_NAME']
    
    ser = serial.Serial(port[0],115200)
    recieve_part(ser)
    # with open(recFile,"w+") as txt:
    #     txt.write(receive)
    
    # toImg(cleanned(receive),imgname)
	
    

if __name__ == "__main__":
	main()
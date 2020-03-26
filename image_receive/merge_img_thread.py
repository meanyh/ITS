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
from threading import Thread

dest_path = ""
crop_h = 16
crop_w = 32
end = False
count_all = 0
time_out = 0
height = 0
width = 0


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
    global count_all
    delete_list = [b"Receive: ", b"656E64", b"\r\n", b"Sent", b"end", b".jpg"]
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
    count_all+=len(byte_array)
    print(len(byte_array))
    return bytearray(byte_array), name

def save_img(image_data):
    split_path = dest_path + "split/"
    try:
        image_data, imgname = clean_one_img(image_data)
        ImageFile.LOAD_TRUNCATED_IMAGES = True
        try:
            image = Image.open(io.BytesIO(image_data))
            image.save(split_path + imgname + ".jpg")
            print("Save Image %s" % imgname)
        except Exception as e:
            print("Cannot Open Image %s: %s" % (imgname, e))
    except:
        print("Cannot Find Image name")

def check_img(image_data):
    global count_all
    if image_data.count(b"IMG-") > 1:
        index = image_data.index(b"IMG-", 5)
        save_img(image_data[:index])
        save_img(image_data[index:])
    elif image_data.count(b"IMG-") < 1:
        count_all+=len(image_data)
        print(len(image_data))
        print("Cannot find IMG name")
        pass
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
        # print(file)
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
            if b"Sent\r\n" in read:
                print(read)
                global img_name, height, width, sent_time
                read = read[len("Description: ") - 1:read.index(b"Size: ")]
                img_name = read.split(b", ")[0].decode()
                height = int(read.split(b", ")[1].decode())
                width = int(read.split(b", ")[2].decode())
                sent_time = str(read.split(b", ")[3].decode())
                break

def recieve_part(ser, ser_inused):
    receive = b""
    read = b""
    tmp = b""
    global end
    global count_all
    ser_inused.set(True)
    print(ser.name)
    while True:
        if ser.in_waiting > 0:
            tmp = ser.read()
            read += tmp
            if b"Description: " in read:
                read_description(ser, read)
                read = b""
                count_all = 0
                break
            if b"Sent\r\n" in read:
                # print(read)
                receive += read
                if b"656E64\r\n" in read or b"end" in read:
                    end = True
                if b".jpg" in read:
                    check_img(receive)
                    receive = b""
                    break
                read = b"" 
    if end:
        merge_img()
        read_time()
        end = False
        print(count_all)
        count_all = 0
    ser_inused.set(False)

def read_time():
    now = datetime.datetime.utcnow()
    print(sent_time)
    print(now)
    print(now - datetime.datetime.strptime(sent_time, '%Y-%m-%d %H:%M:%S.%f'))

class check_ser:
    def __init__(self, obj): self.obj = obj
    def get(self):    return self.obj
    def set(self, obj):      self.obj = obj

def main():
    with open('./config.json','r') as f:
        config = json.load(f)

    port = config['PORT']
    global dest_path, time_out, count_all
    time_out = time.time()
    dest_path = config["DEST_PATH"]

    ser1_inused = check_ser(False)
    ser2_inused = check_ser(False)
    ser3_inused = check_ser(False)
    ser4_inused = check_ser(False)
    
    ser1 = serial.Serial(port[0], 115200, timeout = 2)
    ser2 = serial.Serial(port[1], 115200, timeout = 2)
    ser3 = serial.Serial(port[2], 115200, timeout = 2)
    ser4 = serial.Serial(port[3], 115200, timeout = 2)
    # ser5 = serial.Serial(port[4], 115200, timeout = 2)
    while 1:
        if ser1.in_waiting > 0 and not(ser1_inused.get()):
            Thread(target = recieve_part, args=(ser1,ser1_inused,)).start()
        if ser2.in_waiting > 0 and not(ser2_inused.get()):
            Thread(target = recieve_part, args=(ser2,ser2_inused,)).start()
        if ser3.in_waiting > 0 and not(ser3_inused.get()):
            Thread(target = recieve_part, args=(ser3,ser3_inused,)).start()
        if ser4.in_waiting > 0 and not(ser4_inused.get()):
            Thread(target = recieve_part, args=(ser4,ser4_inused,)).start()
        # if ser5.in_waiting > 0:
        #     Thread(target = recieve_part, args=(ser5,)).start()

if __name__ == "__main__":
	main()
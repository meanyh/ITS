import subprocess as sp
from PIL import Image
import os, shutil, io
import serial
import time
import json
import sys
import datetime

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

def splitImage(path, im, h, w):
    im_w, im_h = im.size
    count = 0
    clear(path)
    for i in range(0, im_h, h):
        for j in range(0, im_w, w):
            box = (j, i, j + w, i + h)
            crop_img = im.crop(box)
            crop_img.save(os.path.join(path, "IMG-%s.jpg" % count))
            count += 1
    return count

def sendImg(dest_path, ser, i, last):
    f = open(dest_path + "IMG-%s.jpg" % i, 'rb')
    image = f.read()
    f.close()

    byte_array = b"IMG-" + b"%d" % i + b":" + bytearray(image) + b".jpg"
    if last:
       byte_array += b"end"
    n = len(byte_array)
    ser.write(b"%d" % n)
    print(n)
    print(b"%d" % n)
    
    print ("Python value sent: ")
    print("IMG-%s.jpg" % i)
    print("SerName: %s" % ser.name)
    i=0
    
    string = ''.join('{:02x}'.format(x) for x in byte_array)
    print(byte_array)
    ser.write(b"%d" % 250 + byte_array[:250])
    ser.flush()
    rec = b""
    i=1
    while 1:
        if (ser.in_waiting):
            rec += ser.read()
            print(rec)
            if b"Done" in rec:
                rec = b""
                if i < n//250:
                    ser.write(b"%d" % 250 + byte_array[i*250:2*i*250])
                else:
                    ser.write(b"%d" % byte_array[2*i*250:] + byte_array[2*i*250:])
                    break
                i += 1


def main():
    f = open('./config.json', 'r')
    config = json.load(f)

    port = config['PORT']
    img_name = config['IMAGE_NAME']
    source = config['SOURCE_PATH']
    dest_path = config['DEST_PATH']

    image = Image.open(source + img_name)

    k = splitImage(dest_path, image, crop_h, crop_w)
    n = int(k)-1
    
    im_w, im_h = image.size
    desciption = b"Description: " + bytearray(img_name) + b", " + b"%d" % im_h + b", " + b"%d" % im_w
    
    
    ser = serial.Serial(port[0], 115200)

    ser.write(desciption)
    last = False
    for i in range(n):
        if i == n-1:
            last = True
        sendImg(dest_path, ser, i, last)



if __name__ == "__main__":
    main()

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
count_all = 0
max_frame = 250

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

def split_image(path, im, h, w):
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

def send_img(dest_path, ser, i, last):
    f = open(dest_path + "IMG-%s.jpg" % i, 'rb')
    image = f.read()
    f.close()
    global count_all
    count_all+=len(bytearray(image))
    byte_array = b"IMG-" + b"%d" % i + b":" + bytearray(image) + b".jpg"
    if last:
       byte_array += b"end"
    n = len(byte_array)
    
    print("IMG-%s.jpg" % i)
    print("Size: %d" % n)
    print("SerName: %s" % ser.name)

    tmp = byte_array[:max_frame]
    print(len(tmp))
    ser.write(b"%d" % len(tmp))
    print(tmp)
    ser.write(tmp)
    rec = b""
    j = 1
    end = False
    while 1:
        if (ser.in_waiting):
            rec += ser.read()
            if b"Done" in rec:
                rec = b""
                if end:
                    break
                if j < n//max_frame:
                    tmp = byte_array[j*max_frame:(j+1)*max_frame]
                    print(len(tmp))
                    ser.write(b"%d" % len(tmp))
                    print(tmp)
                    ser.write(tmp)
                else:
                    end = True
                    if n % max_frame == 0:
                        break
                    tmp = byte_array[j*max_frame:]
                    print(len(tmp))
                    ser.write(b"%d" % len(tmp))
                    print(tmp)
                    ser.write(tmp)
                j += 1

def sent_description(ser, img_name, im_w, im_h, time):
    desciption = b"Description: " + bytearray(img_name, 'utf8') + b", " + b"%d" % im_h + b", " + b"%d" % im_w + b", " + bytearray(str(time), 'utf8')
    n = len(desciption)
    ser.write(b"%d" % n)
    ser.write(desciption)
    print(desciption)
    rec = b""
    while 1:
        if (ser.in_waiting):
            rec += ser.read()
            if b"Done" in rec:
                break

def main():
    f = open('./config.json', 'r')
    config = json.load(f)

    port = config['PORT']
    img_name = config['IMAGE_NAME']
    source = config['SOURCE_PATH']
    dest_path = config['DEST_PATH']

    image = Image.open(source + img_name)
    time = datetime.datetime.utcnow()
    k = split_image(dest_path, image, crop_h, crop_w)
    n = int(k)-1
    global count_all
    im_w, im_h = image.size
    
    ser1 = serial.Serial(port[0], 115200)
    
    sent_description(ser1, img_name, im_w, im_h, time)

    last = False
    for i in range(n):
        if i == n-1:
            last = True
        while ser1.out_waiting > 0:
            print(ser1.out_waiting)
            continue
        if ser1.out_waiting <= 0:
            send_img(dest_path, ser1, i, last)
    print(count_all)

if __name__ == "__main__":
    main()

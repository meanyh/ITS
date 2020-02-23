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

    byte_array = b"IMG-" + b"%d" % i + b":" + bytearray(image) + b".jpg"
    if last:
       byte_array += b"end"
    n = len(byte_array)
    ser.write(b"%d" % n)
    print(n)
    
    print("IMG-%s.jpg" % i)
    print("SerName: %s" % ser.name)

    ser.write(byte_array)
    ser.flush()
    print(ser.out_waiting)


def sent_description(ser, img_name, im_w, im_h, time):
    desciption = b"Description: " + bytearray(img_name, 'utf8') + b", " + b"%d" % im_h + b", " + b"%d" % im_w + b", " + bytearray(str(time), 'utf8')
    n = len(desciption)
    ser.write(b"%d" % n)
    # time.sleep(0.5)
    ser.write(desciption)
    print(desciption)

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
    
    im_w, im_h = image.size
    
    ser1 = serial.Serial(port[0], 115200)
    ser2 = serial.Serial(port[1], 115200)
    # ser3 = serial.Serial(port[2], 115200)
    # ser4 = serial.Serial(port[3], 115200)
    
    sent_description(ser1, img_name, im_w, im_h, time)
        
    last = False
    for i in range(n):
        if i == n-1:
            last = True
        print(i)
        # ser1 = serial.Serial(port[0], 115200)
        # ser2 = serial.Serial(port[1], 115200)
        # ser3 = serial.Serial(port[2], 115200)
        # ser4 = serial.Serial(port[3], 115200)  
        while ser1.out_waiting > 0 and ser2.out_waiting > 0:
        # while ser1.out_waiting and ser2.out_waiting and ser3.out_waiting and ser4.out_waiting:
            print(ser1.out_waiting, ser2.out_waiting)
            continue
        if ser2.out_waiting <= 0:
            send_img(dest_path, ser1, i, last)
        if ser2.out_waiting <= 0:
            send_img(dest_path, ser2, i, last)
        # elif not ser3.out_waiting:
        #     send_img(ser3, i)
        # elif not ser4.out_waiting:
        #     send_img(ser4, i)

if __name__ == "__main__":
    main()

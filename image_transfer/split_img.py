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

def split_image(path, im):
    im_w, im_h = im.size
    count = 0
    clear(path)
    for i in range(0, im_h, crop_h):
        for j in range(0, im_w, crop_w):
            box = (j, i, j + crop_w, i + crop_h)
            crop_img = im.crop(box)
            crop_img.save(os.path.join(path, "IMG-%s.jpg" % count))
            count += 1
    return count

def send_img(dest_path, ser, i, last):
    f = open(dest_path + "IMG-%s.jpg" % i, 'rb')
    image = f.read()
    f.close()

    byte_array = b"IMG-" + bytes(i) + ":" + bytearray(image) + b".jpg"
    if last:
       byte_array += b"end"
    n = len(byte_array)
    print(n)

    print ("Python value sent: ")
    print("IMG-%s.jpg" % i)
    print("SerName: %s" % ser.name)
    i=0
    
    str = ''.join('{:02x}'.format(x) for x in byte_array)
    print(str)
    ser.write(byte_array)
    rec = b""
    while 1:
        if (ser.in_waiting):
            rec += ser.read(ser.in_waiting)
            if b"Done" in rec and b"get" in rec:
                print(rec)
                break

def main():
    f = open('./config.json', 'r')
    config = json.load(f)

    port = config['PORT']
    img_name = config['IMAGE_NAME']
    source = config['SOURCE_PATH']
    dest_path = config['DEST_PATH']

    image = Image.open(source + img_name)

    k = split_image(dest_path, image)
    n = int(k)-1
    
    
    last = False
    for i in range(n):
        if i == n-1:
            last = True
        ser1 = serial.Serial(port[0], 115200)
        ser2 = serial.Serial(port[1], 115200)
        # ser3 = serial.Serial(port[2], 115200)
        # ser4 = serial.Serial(port[3], 115200)
        while ser1.out_waiting and ser2.out_waiting:
        # while ser1.in_waiting and ser2.in_waiting and ser3.in_waiting and ser4.in_waiting:
            # print(ser1.in_waiting, ser2.in_waiting)
            continue
        if not ser1.out_waiting:
            send_img(dest_path, ser1, i, last)
        elif not ser2.out_waiting:
            send_img(dest_path, ser2, i, last)
        # elif not ser3.in_waiting:
        #     send_img(ser3, i)
        # elif not ser4.in_waiting:
        #     send_img(ser4, i)

            # if time1 == 0:
            #     time1 = datetime.datetime.utcnow()
            # time2 = datetime.datetime.utcnow()
            # print("Time")
            # print(time2-time1)

            #     time2 = datetime.datetime.utcnow()
            #     total_time = time2-time1
            #     print("TimeEnd")
            #     print(total_time)
            #     break


if __name__ == "__main__":
    main()

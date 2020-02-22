import subprocess as sp
from PIL import Image
import os, shutil
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
    data = ""

    for i in range(n):
        f = open(dest_path + "IMG-%s.jpg" % i, 'rb')
        image = f.read()
        f.close()

        txt = list(image)
        byte_array = bytearray(image)
        n = len(byte_array)
        byte_array.append(0x2D)
        ser = serial.Serial(port[0], 115200)

        count = 1
        exit = False
        time1 = 0

        while True:

            rec = ser.read(1000)
            print ("Received : ")
            print(rec)
            if "sent" in rec:
                print ("Python value sent: ")
                # ser.write(byte_array)
                print("IMG-%s.jpg" % i)

            # if time1 == 0:
            #     time1 = datetime.datetime.utcnow()
            # time2 = datetime.datetime.utcnow()
            # print("Time")
            # print(time2-time1)

            # if exit:
            #     ser.write("end")
            #     print("end")

            #     time2 = datetime.datetime.utcnow()
            #     total_time = time2-time1
            #     print("TimeEnd")
            #     print(total_time)
            #     break


if __name__ == "__main__":
    main()

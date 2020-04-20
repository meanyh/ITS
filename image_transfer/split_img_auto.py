import subprocess as sp
from PIL import Image
import os, shutil, io
import serial
import time
import json
import sys
import datetime
from threading import Thread

crop_h = 16
crop_w = 32
count_all = 0
max_frame = 250

def clear(path):
    for filename in os.listdir(path):
        file_path = os.path.join(path, filename)
        delete(file_path)

def delete(file_path):
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
            crop_img.save(os.path.join(path, "IMG-%s.jpg" % count), optimize=True)
            count += 1
    return count

def send_img(dest_path, ser, ser_inused, i, last):
    ser_inused.set(True)
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
    print("IMG-%s.jpg" % i)
    print(len(tmp))
    ser.write(b"%d" % len(tmp))
    # print(tmp)
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
                    print("IMG-%s.jpg" % i)
                    print(len(tmp))
                    ser.write(b"%d" % len(tmp))
                    # print(tmp)
                    ser.write(tmp)
                else:
                    end = True
                    if n % max_frame == 0:
                        break
                    tmp = byte_array[j*max_frame:]
                    print("IMG-%s.jpg" % i)
                    print(len(tmp))
                    ser.write(b"%d" % len(tmp))
                    # print(tmp)
                    ser.write(tmp)
                j += 1
    ser_inused.set(False)

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

class check_ser:
    def __init__(self, obj): self.obj = obj
    def get(self):    return self.obj
    def set(self, obj):      self.obj = obj


def main():
    f = open('./config.json', 'r')
    config = json.load(f)

    port = config['PORT']
    img_name = config['IMAGE_NAME']
    source = config['SOURCE_PATH']
    dest_path = config['DEST_PATH']

    for file in sorted(os.listdir( source )):
        img_path = source + file
        image = Image.open(img_path)
        time = datetime.datetime.utcnow()
        k = split_image(dest_path, image, crop_h, crop_w)
        n = int(k)-1
        global count_all
        im_w, im_h = image.size
        
        ser1 = serial.Serial(port[0], 115200)
        ser2 = serial.Serial(port[1], 115200)
        ser3 = serial.Serial(port[2], 115200)
        ser4 = serial.Serial(port[3], 115200)
        ser5 = serial.Serial(port[4], 115200)

        ser1_inused = check_ser(False)
        ser2_inused = check_ser(False)
        ser3_inused = check_ser(False)
        ser4_inused = check_ser(False)
        ser5_inused = check_ser(False)
        
        sent_description(ser1, img_name, im_w, im_h, time)
            
        last = False
        for i in range(n):
            if i == n-1:
                last = True
            while ser1_inused.get() and ser2_inused.get() and ser3_inused.get() and ser4_inused.get() and ser5_inused.get():
                continue

            if ser1.out_waiting <= 0 and not(ser1_inused.get()):
                Thread(target = send_img, args=(dest_path,ser1,ser1_inused, i, last,)).start()
            elif ser2.out_waiting <= 0 and not(ser2_inused.get()):
                Thread(target = send_img, args=(dest_path,ser2,ser2_inused, i, last,)).start()
            elif ser3.out_waiting <= 0 and not(ser3_inused.get()):
                Thread(target = send_img, args=(dest_path,ser3,ser3_inused, i, last,)).start()
            elif ser4.out_waiting <= 0 and not(ser4_inused.get()):
                Thread(target = send_img, args=(dest_path,ser4,ser4_inused, i, last,)).start()
            elif ser5.out_waiting <= 0 and not(ser5_inused.get()):
                Thread(target = send_img, args=(dest_path,ser5,ser5_inused, i, last,)).start()
        print(count_all)
        delete(img_path)

if __name__ == "__main__":
    main()

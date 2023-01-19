from PIL import Image
import os

PATH = "/home/royann/dataset/VOCdevkit/VOC2012/JPEGImages"
SAVED_PATH = "/home/royann/gray_dataset/VOCdevkit/VOC2012/JPEGImages"
os.chdir(PATH)

for file in os.listdir():    
    image = Image.open(PATH+"/"+file)
    grayscale = image.convert('L')
    grayscale.save(SAVED_PATH+"/"+file)

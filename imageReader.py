import pytesseract as tess
import os
import re
import cv2
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict
from datetime import date

#! Modify line 6 to the directory where `tesseract.exe` is stored
tess.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

#! Modify `boss` to the folder where the images are stored
directory_img = r'boss'
directory_names = r'defined_names.txt'


# -- Functions --
def get_image_files(directory):
    files = []
    for file in os.listdir(directory):
        if file.endswith('.png') or file.endswith('.jpg') or file.endswith('.jpeg'):
            files.append(file)
    return files

def read_defined_file(directory):
    item_names = []
    item_categories = []

    with open(directory, 'r', encoding='utf-8') as file:
        lines = file.readlines()

        for line in lines:
            text_only_line = line.strip().lower()
            if text_only_line.startswith('#'):
                item_categories.append(text_only_line.split('#')[1])
            elif text_only_line != '':
                item_names.append(text_only_line)

        return item_names, item_categories


# Directory and files
image_files = get_image_files(directory_img)
item_names, item_categories = read_defined_file(directory_names)

# Regex
name_quantity_pattern = re.compile(r'\b(?:got|gat)\s+(.*)')
name_pattern = re.compile(r'^(.*?)(?:\s*x\d+|\.\.)')
quantity_pattern = re.compile(r'\bx(\d+)\b')

# Create empty folder using current date
creation_date = date.today().strftime("%d-%m-%Y")
if not os.path.exists(creation_date):
    os.makedirs(creation_date)

desired_width = 1000
    
for file in image_files:
    try:
        file_without_extension = re.sub(r'\.png|\.jpg|\.jpeg', '', file)
        img = cv2.imread(os.path.join("boss/", file))
        aspect_ratio = desired_width / img.shape[1]
        new_dimensions = (desired_width, int(img.shape[0] * aspect_ratio))

        # Up-sample (since the image is too small), then convert to HSV. Get binary mask and perform OCR
        img = cv2.resize(img, (0, 0), fx=2.1, fy=2.1)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        # hsv = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        msk = cv2.inRange(hsv, np.array([0, 0, 123]), np.array([179, 255, 255]))
        extracted_text = tess.image_to_string(msk, lang='eng', config='--psm 6').split('\n')

        #* Display the mask
        # plt.figure(figsize=(10, 10))
        # plt.subplot(1, 2, 1)
        # plt.title('Mask')
        # plt.imshow(msk)
        # plt.axis('off')
        # plt.show()

        print(f"\n\n---Reading file: {file}---")
        item_quantity_map = defaultdict(int)

        #* Extracting Text
        for line in extracted_text:
            match = name_quantity_pattern.search(line)

            if match:              
                formatted_text = match.group(1).strip()

                obtained_item_match = name_pattern.search(formatted_text)
                obtained_quantity_match = quantity_pattern.search(formatted_text)

                # Check if the obtained_item is a substring to item_names
                if obtained_item_match:
                    obtained_item = obtained_item_match.group(1).lower()
                    for item in item_names:
                        if obtained_item in item:
                            obtained_quantity = int(obtained_quantity_match.group(1)) if obtained_quantity_match else 0
                            
                            print(f"Item read: {item}; Quantity: {obtained_quantity}")
                            item_quantity_map[item] += obtained_quantity
                            break
                else:
                    print(f"Not matching with any item: {formatted_text}")
            elif line.strip() != '':
                print(f"Could not extract text from line: {line}")

            # Write the output in text file and store into the folder created
            with open(os.path.join(creation_date, f"{file_without_extension}.txt"), 'w', encoding='utf-8') as output_file:
                for item, quantity in item_quantity_map.items():
                    output_file.write(f"{item}: {quantity}\n")

    except Exception as e:
        print(f"Error processing file {file}: {e}")
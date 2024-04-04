from fastapi import FastAPI, HTTPException, Body
from PIL import Image
import os
import logging
from pydantic import BaseModel, Field
import csv  # For CSV file parsing
import json  # For JSON file parsing
 
app = FastAPI()
logger = logging.getLogger("uvicorn.error")
 
class ImageDir(BaseModel):
    image_dir: str = Field(..., title="Image Directory", description="The directory containing the images to analyze.", strict=True)
 
def count_images_in_class(class_dir):
    num_files = 0
    for root, dirs, files in os.walk(class_dir):
        for filename in files:
            num_files += 1
    return num_files
 
def count_classes(dataset_path, class_mapping=None):
    if class_mapping:
        return len(set(class_mapping.values()))
    else:
        return len([d for d in os.listdir(dataset_path) if os.path.isdir(os.path.join(dataset_path, d))])
 
def count_images_per_class(data_dir, class_mapping=None):
    if class_mapping:
        class_counts = {}
        for class_label in set(class_mapping.values()):
            class_counts[class_label] = sum(1 for label in class_mapping.values() if label == class_label)
        return class_counts
    else:
        class_dirs = [d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d))]
        class_counts = {}
        for class_dir in class_dirs:
            class_counts[class_dir] = count_images_in_class(os.path.join(data_dir, class_dir))
        return class_counts
 
def check_image_format(image_dir):
    num_files = 0
    num_invalid_images = 0
    invalid_images = []
    class_mapping = {}
 
    # Check if there's a CSV or JSON file present in the directory
    csv_file = None
    json_file = None
    for file in os.listdir(image_dir):
        if file.endswith('.csv'):
            csv_file = os.path.join(image_dir, file)
        elif file.endswith('.json'):
            json_file = os.path.join(image_dir, file)
   
    # If both CSV and JSON files exist, prefer CSV
    if csv_file:
        # Assuming CSV file format: 'image_filename,class_label'
        with open(csv_file, 'r') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header if present
            for row in reader:
                if len(row) == 2:
                    filename, class_label = row
                    class_mapping[filename] = class_label
    elif json_file:
     # Assuming JSON file format: [{"patientId": "id1", "Target": "target1"}, ...]
     with open(json_file, 'r') as f:
        data = json.load(f)
        for entry in data:
            patient_id = entry.get('patientId')
            target = entry.get('Target')
            if patient_id and target:
                class_mapping[patient_id] = target
 
    # If no CSV or JSON file found, assume each subfolder represents a class and count images in each subfolder
    if not class_mapping:
        class_dirs = [d for d in os.listdir(image_dir) if os.path.isdir(os.path.join(image_dir, d))]
        for class_dir in class_dirs:
            class_mapping.update({filename: class_dir for filename in os.listdir(os.path.join(image_dir, class_dir))})
 
    for root, dirs, files in os.walk(image_dir):
        for filename in files:
            if filename.endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif')):
                filepath = os.path.join(root, filename)
                num_files += 1
                try:
                    img = Image.open(filepath)
                    img.verify()
                    img.close()
                except Exception as e:
                    print(f"Error reading {filename}: {e}")
                    num_invalid_images += 1
                    invalid_images.append(filename)
            else:
                print(f"{filename}: Format error - Not a JPG, JPEG, PNG, BMP, TIFF, or GIF")
                num_invalid_images += 1
                invalid_images.append(filename)
 
    if num_invalid_images == 0:
        image_format_message = f"All {num_files} images are in the correct format."
    else:
        image_format_message = f"{num_invalid_images} out of {num_files} images are in incorrect format."
 
    return image_format_message, count_classes(image_dir, class_mapping), count_images_per_class(image_dir, class_mapping), invalid_images, class_mapping
 
@app.get("/")
def home():
    return {"message": "The app is running"}
 
@app.post("/analyze/")
def analyze(image_dir: ImageDir):
    if not os.path.exists(image_dir.image_dir):
        raise HTTPException(status_code=404, detail="Directory not found")
 
    image_format_message, classes_count, images_per_class, invalid_images, class_mapping = check_image_format(image_dir.image_dir)
    return {
        "image_format_message": image_format_message,
        "invalid_images": invalid_images,
        "classes_count": {"Number of classes": classes_count},
        "images_per_class": images_per_class
    }
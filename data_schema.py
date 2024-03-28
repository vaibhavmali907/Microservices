from fastapi import FastAPI, HTTPException, Body
from PIL import Image
import os
import logging
from pydantic import BaseModel, Field

app = FastAPI()

logger = logging.getLogger("uvicorn.error")

class ImageDir(BaseModel):
    image_dir: str = Field(..., title="Image Directory", description="The directory containing the images to analyze.", strict=True)

def check_image_format(image_dir):
    num_files = 0
    num_corrupted = 0
    corrupted_images = []
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
                    num_corrupted += 1
                    corrupted_images.append(filename)
            else:
                print(f"{filename}: Format error - Not a JPG, JPEG, PNG, BMP, TIFF, or GIF")
                num_corrupted += 1
                corrupted_images.append(filename)
    if num_corrupted == 0:
        image_format_message = f"All {num_files} images are in the correct format."
    else:
        image_format_message = f"{num_corrupted} out of {num_files} images are corrupted or in the wrong format."

    return image_format_message, count_classes(image_dir), count_images_per_class(image_dir), corrupted_images

def count_classes(dataset_path):
    return len(set(os.listdir(dataset_path)))

def count_images_in_class(class_dir):
    num_files = 0
    for root, dirs, files in os.walk(class_dir):
        for filename in files:
                num_files += 1
    return num_files

def count_images_per_class(data_dir):
    class_dirs = [d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d))]
    class_counts = {}
    for class_dir in class_dirs:
        class_counts[class_dir] = count_images_in_class(os.path.join(data_dir, class_dir))
    return class_counts

@app.get("/")
def home():
    return {"message": "The app is running"}

@app.post("/analyze/")
def analyze(image_dir: ImageDir):
    if not os.path.exists(image_dir.image_dir):
        raise HTTPException(status_code=404, detail="Directory not found")
    
    image_format_message, classes_count, images_per_class, corrupted_images = check_image_format(image_dir.image_dir)
    return {
        "image_format_message": image_format_message,
        "corrupted_images": corrupted_images,
        "classes_count": {"Number of classes": classes_count},
        "images_per_class": images_per_class

    }
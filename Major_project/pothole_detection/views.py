from posixpath import splitext
import re
from django.shortcuts import render
import os
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from PIL import Image
from pathlib import Path
from ultralytics import YOLO
import pytesseract
import pandas as pd
import folium
import geocoder


BASE_DIR = Path(__file__).resolve().parent.parent

pytesseract.pytesseract.tesseract_cmd=r"C:\Program Files\Tesseract-OCR\tesseract.exe"

model_path=os.path.join(BASE_DIR, 'best.pt')

ALLOWED_EXTENSIONS = ['.jpg']

# Create your views here.
def main(request):
    return render(request,"home.html")

def is_allowed_file(filename):
    return splitext(filename)[1].lower() in ALLOWED_EXTENSIONS
# Create your views here.

def upload_image(request):
    upload_success = False
    upload_error = None
    pothole_detected=False
    saved_result=[]
    if request.method == 'POST' and request.FILES.get('image'): #check for post request and image file
        image = request.FILES['image']  # Extract the uploaded image from the request
        if is_allowed_file(image.name):  # Check if the file has an allowed extension
            save_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')  # Define the directory where the file will be saved
            os.makedirs(save_dir, exist_ok=True)

            _, extension = os.path.splitext(image.name) # retriving original extension

            default_filename = "default_image" + extension   
            file_path = os.path.join(settings.MEDIA_ROOT, 'uploads', default_filename) #uploading image with default_image name

            
            if default_storage.exists(file_path): # Check if the file already exists and delete it
                default_storage.delete(file_path)
              
            default_storage.save(file_path, ContentFile(image.read())) # Save the new file using Django's default storage backend  
           
            upload_success = "File is uploaded"

            ocr_result = pytesseract.image_to_string(file_path, lang='eng')

            # Extract latitude and longitude using regular expressions
            latitude_match = re.search(r'Lat (\d+\.\d+)', ocr_result)
            longitude_match = re.search(r'Long (\d+\.\d+)', ocr_result)
            latitude_value = None
            longitude_value = None

            # Check if matches were found and extract values
            if latitude_match:
                latitude_value = latitude_match.group(1)
            if longitude_match:
                longitude_value = longitude_match.group(1)

            # Print or use the extracted values
            print("Latitude:", latitude_value)
            print("Longitude:", longitude_value)
            model = YOLO(model_path)
            input_image = Image.open(file_path)
            results = model(input_image)    
            for result in results:
                name = result.names
                saved_result.extend(name.values())
            print(saved_result)

            if latitude_value is not None and longitude_value is not None:
                if any(keyword in saved_result for keyword in ["potholes", "pothole", "Potholes", "Pothole"]):
                    print("Potholes detected")
                    pothole_detected="Potholes detected"
                    csv_file_path = os.path.join(settings.MEDIA_ROOT, 'uploads', 'coordinates.csv')

                    # Check if the CSV file already exists
                    csv_exists = os.path.exists(csv_file_path)

                    # Create a CSV string with the latitude and longitude
                    csv_data = f"{latitude_value},{longitude_value}\n"

                    # If the CSV file exists, append new coordinates
                    mode = 'a' if csv_exists else 'w'
                    with open(csv_file_path, mode, newline='') as csvfile:
                        # Write the header if the file is newly created
                        if not csv_exists:
                            csvfile.write("latitude,longitude\n")

                        # Write the new coordinates
                        csvfile.write(csv_data)
                    


                else:
                        print(" Potholes not detected") 

            else:
                upload_error = 'Invalid image. Latitude or Longitude not found.'
  
        else: 
            upload_error = 'Invalid file format. Please upload a valid image.'
     
    return render(request, 'uploadimage.html', {'pothole_detected':pothole_detected,'upload_success': upload_success, 'upload_error': upload_error})  # Render the template with the upload status  


def display_map(request):
    # Step 2: Load Your CSV Data
    csv_file_path = os.path.join(settings.MEDIA_ROOT, 'uploads', 'coordinates.csv')  # Update with the correct path to your CSV file
    df = pd.read_csv(csv_file_path)

    # Step 3: Get Current Location
    current_location = geocoder.ip('me')
    initial_center = [current_location.latlng[0], current_location.latlng[1]]

    # Step 4: Create a Folium Map
    m = folium.Map(location=initial_center, zoom_start=10)

    # Step 5: Add Markers to the Map
    for index, row in df.iterrows():
        location = [row['latitude'], row['longitude']]
        folium.Marker(location).add_to(m)

    # Step 6: Save or Display the Map
    map_html = m.get_root().render()
    return render(request, 'map_display.html', {'map_html': map_html})

def about_us (request):
    return render(request, 'aboutus.html')
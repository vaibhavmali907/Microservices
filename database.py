import mysql.connector
import boto3
from PIL import Image
from io import BytesIO
import os
import pydicom
 
# Function to connect to MySQL database
def connect_to_mysql(host, port, user, password, database):
    try:
        connection = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        return connection
    except mysql.connector.Error as err:
        print("Error: ", err)
        raise
 
# Function to connect to AWS S3
def connect_to_s3(access_key, secret_key, region):
    try:
        s3 = boto3.client('s3',
                          aws_access_key_id=access_key,
                          aws_secret_access_key=secret_key,
                          region_name=region)
        return s3
    except Exception as e:
        print("Error: ", e)
        raise
 
# Function to retrieve image locations from MySQL database
def get_image_locations_from_db(connection):
    cursor = connection.cursor()
    cursor.execute("SELECT image_location FROM images")
    image_locations = cursor.fetchall()
    return image_locations
 
# Function to convert image to TIFF format
def convert_to_tiff(image_data):
    image = Image.open(BytesIO(image_data))
    # Convert to RGB (for PNG images with transparency)
    if image.mode != "RGB":
        image = image.convert("RGB")
    # Save as TIFF
    output = BytesIO()
    image.save(output, format="TIFF")
    output.seek(0)
    return output.getvalue()
 
# Function to process images and upload to S3
def process_and_upload_images(s3, image_locations, connection):
    for location in image_locations:
        image_location = location[0]
        # Download image from S3
        s3_object = s3.get_object(Bucket='your-bucket-name', Key=image_location)
        image_data = s3_object['Body'].read()
        # Determine file extension
        _, ext = os.path.splitext(image_location)
        ext = ext.lower()
        # Convert image to TIFF if not already TIFF
        if ext != ".tiff":
            if ext == ".dcm":
                # Convert DICOM to TIFF
                tiff_data = convert_dicom_to_tiff(image_data)
            else:
                # Convert other formats to TIFF
                tiff_data = convert_to_tiff(image_data)
            # Upload processed image to S3
            processed_key = 'processed/' + image_location.split('/')[-1].split('.')[0] + '.tiff'
            s3.put_object(Bucket='your-bucket-name', Key=processed_key, Body=tiff_data)
            # Update image location in database
            update_image_location(connection, image_location, processed_key)
 
# Function to convert DICOM image to TIFF
def convert_dicom_to_tiff(dicom_data):
    dicom_data = pydicom.dcmread(BytesIO(dicom_data))
    pixel_data = dicom_data.pixel_array
    image = Image.fromarray(pixel_data)
    return convert_to_tiff(image.tobytes())
 
# Function to update image location in the database
def update_image_location(connection, original_location, processed_location):
    cursor = connection.cursor()
    query = "UPDATE images SET image_location = %s WHERE image_location = %s"
    cursor.execute(query, (processed_location, original_location))
    connection.commit()
 
def main():
    # MySQL Database Configuration
    mysql_host = ''
    mysql_port =   # Specify the port number here
    mysql_user = ''
    mysql_password = ''
    mysql_database = ''
 
    # AWS S3 Configuration
    aws_access_key = ''
    aws_secret_key = ''
    aws_region = ''
 
    try:
        # Connect to MySQL Database
        mysql_connection = connect_to_mysql(mysql_host, mysql_port, mysql_user, mysql_password, mysql_database)
        print("Connected to MySQL database.")
    except Exception as e:
        print("Failed to connect to the MySQL database:", e)
        return
 
    try:
        # Connect to AWS S3
        s3_client = connect_to_s3(aws_access_key, aws_secret_key, aws_region)
        print("Connected to S3 bucket.")
    except Exception as e:
        print("Failed to connect to the S3 bucket:", e)
        mysql_connection.close()
        return
 
    try:
        # Get image locations from MySQL database
        image_locations = get_image_locations_from_db(mysql_connection)
 
        # Process and upload images to S3
        process_and_upload_images(s3_client, image_locations, mysql_connection)
 
        print("Image processing and upload completed successfully.")
 
    except Exception as e:
        print("An error occurred during image processing and upload:", e)
 
    finally:
        # Close MySQL connection
        mysql_connection.close()
 
if __name__ == "__main__":
    main()

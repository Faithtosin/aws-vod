import boto3
import os
import sys
import uuid
from urllib.parse import unquote_plus
from PIL import Image
import PIL.Image
import logging




logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')
destBucket= "filmabonito-vod-destination-mgbq4jb0jip0"
logo_key= "LOGO-NEW.png"
#destBucket= os.environ['DEST_BUCKET']

control_key = "/"

def resize_image(image_path, resized_path,ratio):
    with Image.open(image_path) as image:
        
        image.thumbnail(tuple((x / ratio) for x in image.size))
        image.save(resized_path)
        
def set_key(key,file_prefix):
    control_split = "."
    
    if ".jpg" in key or ".jpeg" in key : control_split =".jp"
    elif ".png" in key : control_split =".png"
    else: control_split = "."
    
    if key.find(control_key) > 0: 
        folder = key.split("/", 1)
        subfolder= folder[1].split(control_split,1)
        new_key = folder[0] + "/"+ subfolder[0] +"/" +file_prefix + folder[1]
    else:
        subfolder= key.split(control_split,1)
        destBucket= str(destBucket+ "/" +subfolder[0] + "/")
        new_key = file_prefix +str(key)
    
    return new_key

def watermark(image_path, resized_path, bucket):
    
    logo_key= "LOGO-NEW.png"
    s3_client.download_file(bucket, logo_key, '/tmp/LOGO-NEW.png')
    
    logo=Image.open('/tmp/LOGO-NEW.png')
    image=Image.open(image_path)
    image_copy=image.copy()
    
    position1=(int((image_copy.width - logo.width)/ 2), int((image_copy.height - logo.height)/2))
    image_copy.paste(logo, position1, logo)
    image_copy.save(resized_path)
    
    position2=(int(image_copy.width - logo.width), int(image_copy.height - logo.height))
    image_copy.paste(logo, position2, logo)
    image_copy.save(resized_path)
    
    image_copy.paste(logo, logo)
    image_copy.save(resized_path)
        

def lambda_handler(event, context):
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = unquote_plus(record['s3']['object']['key'])
        tmpkey = key.replace('/', '')
        download_path = '/tmp/{}{}'.format(uuid.uuid4(), tmpkey)
        upload_path = '/tmp/resized-{}'.format(tmpkey)
        s3_client.download_file(bucket, key, download_path)
        ratio = 1
        logger.info("Try 3--------------key")
        logger.info(key)
        logger.info("Try 4-----bucket")
        logger.info(bucket)
        
        #Original image
        ratio = 1
        resize_image(download_path, upload_path, ratio)
        file_prefix = "XL-"
        new_key= set_key(key,file_prefix )
        
        
        s3_client.upload_file(upload_path, destBucket, new_key, ExtraArgs= {'ContentDisposition': 'attachment'})
        logger.info("Original image uploaded")
        
        #0.66 RESOLUTION
        ratio = 0.66
        resize_image(download_path, upload_path, ratio)
        file_prefix = "L-"
        new_key= set_key(key,file_prefix )
        s3_client.upload_file(upload_path, destBucket, new_key, ExtraArgs= {'ContentDisposition': 'attachment'})
        logger.info("0.66 RESOLUTION image uploaded")
        
        # RESOLUTION/3
        ratio = 3
        resize_image(download_path, upload_path, ratio)
        file_prefix = "M-"
        new_key= set_key(key,file_prefix )
        
        s3_client.upload_file(upload_path, destBucket, new_key, ExtraArgs= {'ContentDisposition': 'attachment'})
        logger.info("RESOLUTION/3 image uploaded")
        
        # RESOLUTION/6
        ratio = 6
        resize_image(download_path, upload_path, ratio)
        file_prefix = "S-"
        new_key= set_key(key,file_prefix )
        
        s3_client.upload_file(upload_path, destBucket, new_key, ExtraArgs= {'ContentDisposition': 'attachment'})
        logger.info("RESOLUTION/6 image uploaded")
        
        
        # Demo
        ratio = 2
        resize_image(download_path, upload_path, ratio)
        watermark(download_path, upload_path, bucket)
        file_prefix = "DEMO-"
        new_key= set_key(key,file_prefix )
        
        s3_client.upload_file(upload_path, destBucket, new_key, ExtraArgs= {'ContentDisposition': 'attachment'})
        logger.info("Demo image uploaded")
        
        #PREVIEW
        ratio = 6
        resize_image(download_path, upload_path, ratio)
        file_prefix = "PREVIEW-"
        new_key= set_key(key,file_prefix )
        
        s3_client.upload_file(upload_path, destBucket, new_key, ExtraArgs= {'ContentType': 'image/jpeg'}) 
        logger.info("Preview image uploaded")
        
    return
        

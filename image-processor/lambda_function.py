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
destBucket= "vodstack-1-destination-1gxvgnrwvxg6i"
control_key = "/"

def resize_image(image_path, resized_path,ratio):
    with Image.open(image_path) as image:
        
        image.thumbnail(tuple(x / ratio for x in image.size))
        image.save(resized_path)
        
def set_key(key,file_prefix):
    if key.find(control_key) > 0:
        folder = key.split("/", 1)
        new_key = folder[0] + "/" +file_prefix +folder[1]
    else:
        new_key = "file_prefix"+str(key)
    
    return new_key

def lambda_handler(event, context):
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = unquote_plus(record['s3']['object']['key'])
        tmpkey = key.replace('/', '')
        download_path = '/tmp/{}{}'.format(uuid.uuid4(), tmpkey)
        upload_path = '/tmp/resized-{}'.format(tmpkey)
        s3_client.download_file(bucket, key, download_path)
        ratio = 1
        #logger.info("Try 3--------------key")
        #logger.info(key)
        #logger.info("Try 4-----bucket")
        #logger.info(bucket)
        
        #Original image
        ratio = 1
        resize_image(download_path, upload_path, ratio)
        file_prefix = "XL-"
        new_key= set_key(key,file_prefix )
        s3_client.upload_file(upload_path, destBucket, new_key)
        
        #1/1.5 RESOLUTION
        ratio = 0.66
        resize_image(download_path, upload_path, ratio)
        file_prefix = "L-"
        new_key= set_key(key,file_prefix )
        s3_client.upload_file(upload_path, destBucket, new_key)
        
        # RESOLUTION/3
        ratio = 3
        resize_image(download_path, upload_path, ratio)
        file_prefix = "M-"
        new_key= set_key(key,file_prefix )
        s3_client.upload_file(upload_path, destBucket, new_key)
        
        # RESOLUTION/6
        ratio = 6
        resize_image(download_path, upload_path, ratio)
        file_prefix = "S-"
        new_key= set_key(key,file_prefix )
        s3_client.upload_file(upload_path, destBucket, new_key)
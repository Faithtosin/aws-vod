import boto3
import os
import sys
import uuid
from urllib.parse import unquote_plus

import logging




logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')
destBucket= os.environ['DEST_BUCKET']

control_key = "/"


        

def lambda_handler(event, context):
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = unquote_plus(record['s3']['object']['key'])
        tmpkey = key.replace('/', '')
        download_path = '/tmp/{}{}'.format(uuid.uuid4(), tmpkey)
        upload_path = '/tmp/resized-{}'.format(tmpkey)
        
        
        logger.info(str(key) + " download from " + str(bucket) + " beginging--------------")
        s3_client.download_file(bucket, key, download_path)
       
        logger.info(str(key) +" download from " + str(bucket) + " completed --------------")
        
        #Reupload video with correct metadata
     
        
        logger.info( str(key) + " re-upload to " + str(destBucket) + " beginging--------------")
        
        if "preview" in key.lower():
            s3_client.upload_file(download_path, destBucket, key, ExtraArgs= {'ContentType': 'video/mp4'})
        else:
            s3_client.upload_file(download_path, destBucket, key, ExtraArgs= {'ContentDisposition': 'attachment'})

        
        logger.info(str(key) + " re-upload to "+ str(destBucket) + " completed --------------")
        
    return
        
        

import json
import pprint
import logging
import boto3
import botocore
import subprocess
import os
from urllib.parse import unquote_plus
from botocore.config import Config


SIGNED_URL_EXPIRATION = 300     # The number of seconds that the Signed URL is valid
region = os.environ['AWS_REGION']


logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """

    :param event:
    :param context:
    """
    # Loop through records provided by S3 Event trigger
    for s3_record in event['Records']:
        logger.info("Working on new s3_record...")
        # Extract the Key and Bucket names for the asset uploaded to S3
        key = unquote_plus(s3_record['s3']['object']['key'])
        bucket = s3_record['s3']['bucket']['name']
        destBucket= os.environ['DEST_BUCKET']
        logger.info("Bucket: {} \t Key: {}".format(bucket, key))

        # Generate a signed URL for the uploaded asset
        signed_url = get_signed_url(SIGNED_URL_EXPIRATION, bucket, key)
        #logger.info("Signed URL: {}".format(signed_url))
        # Launch MediaInfo
        json_output = subprocess.check_output(["/opt/mediainfo", "--full", "--output=JSON", signed_url])
        #media_info = subprocess.check_output(["./mediainfo", signed_url])

        #logger.info("Output: {}".format(json_output))
        logger.info("Try 1--------------------------")
        logger.info(json_output)
        logger.info("Try 2--------------------------")
        logger.info(json.loads(json_output))
        # Finish the Lambda function with an HTTP 200 status code:
        json_output = json.loads(json_output)
        
        
        #Template selection
        control_mp4 = ".mp4"
        control_mov = ".mov"
        control_4k = ["2160", "2304"]
        control_HD = ["720", "1080"]
        control_key = "/"
        
        jobTemplate = [
                        "MediaConvert_Template_4k_MP4_H264",
                        "MediaConvert_Template_4k_MOV_PRORES",
                        "MediaConvert_Template_4k_MOV_H264",
                        "MediaConvert_Template_HD_MP4_H264",
                        "MediaConvert_Template_HD_MOV_PRORES",
                        "MediaConvert_Template_HD_MOV_H264",
                        
                        "MediaConvert_Template_4k_MP4_H265",
                        "MediaConvert_Template_4k_MOV_H265",
                        "MediaConvert_Template_HD_MP4_H265",
                        "MediaConvert_Template_HD_MOV_H265",
                        "MediaConvert_Template_4k_MOV_PRORES_422HQ",
                        "MediaConvert_Template_HD_MOV_PRORES_422HQ"
                        ]
                        
        srcVideo = key
        
        
        for i in json_output["media"]["track"]:
            if i['@type'] == "General":
                FileNameExtension = i["FileNameExtension"]
                Video_Codec_List = i["Video_Codec_List"]
            if i['@type'] == "Video":
                Height = i["Height"]
                Format_Profile = i["Format_Profile"]
                
        #Determine template for different resolution
        if  Height in control_4k:
            if control_mp4 in key.lower() : 
                if "hevc" in Video_Codec_List.lower() : jobTemplate = jobTemplate[6]
                else: jobTemplate = jobTemplate[0]
            elif control_mov in key.lower() :
                if "prores" in Video_Codec_List.lower() : 
                    if "422" in Format_Profile: jobTemplate = jobTemplate[10]
                    else:    jobTemplate = jobTemplate[1]
                elif "hevc" in Video_Codec_List.lower() : jobTemplate = jobTemplate[2]
                else: jobTemplate = jobTemplate[2]
            else: jobTemplate = jobTemplate[0]
        elif Height in control_HD:
            if control_mp4 in key.lower() : 
                if "hevc" in Video_Codec_List.lower() : jobTemplate = jobTemplate[8]
                else: jobTemplate = jobTemplate[3]
            elif control_mov in key.lower() :
                if "prores" in Video_Codec_List.lower() :
                    if "422" in Format_Profile: jobTemplate = jobTemplate[11]
                    else: jobTemplate = jobTemplate[4]
                elif "hevc" in Video_Codec_List.lower() : jobTemplate = jobTemplate[5]
                else: jobTemplate = jobTemplate[5]
            else: jobTemplate = jobTemplate[3]
        else :
            jobTemplate = jobTemplate[3]
            #pprint.pprint(i["Count"])
        
        
        
        if key.find(control_key) > 0:
            folder = key.split("/", 1)
            key = folder[0] + "/" + "metadata.json"
            subfolder= folder[1].split(".m",1)
            destBucket= str(destBucket+ "/" + folder[0] + "/" +subfolder[0] + "/")
        else:
            subfolder= key.split(".m",1)
            destBucket= str(destBucket+ "/" +subfolder[0] + "/")
            key = "metadata.json"
        
         
        metadata_json= {
            "srcVideo": srcVideo,
            "frameCapture": False,
            "enableSqs": False ,
            "enableSns": False ,
            "destBucket": destBucket ,
            "jobTemplate": jobTemplate

        } 
        
        Body = json.dumps(metadata_json, indent=4)
        
        s3 = boto3.resource('s3')
        s3.Bucket(bucket).put_object(Key=key, Body=Body)
        return Body
        
        
        


def get_signed_url(expires_in, bucket, obj):
    """
    Generate a signed URL
    :param expires_in:  URL Expiration time in seconds
    :param bucket:
    :param obj:         S3 Key name
    :return:            Signed URL
    """
    s3_cli = boto3.client("s3", region_name=region, config = Config(signature_version = 's3v4', s3={'addressing_style': 'virtual'}))
    presigned_url = s3_cli.generate_presigned_url('get_object', Params={'Bucket': bucket, 'Key': obj}, ExpiresIn=expires_in)
    return presigned_url
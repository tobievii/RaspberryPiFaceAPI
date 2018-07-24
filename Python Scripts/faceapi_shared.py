import http.client, urllib.request, urllib.parse, urllib.error
#import base64
import json
import os, uuid, sys
from azure.storage.blob import BlockBlobService, PublicAccess, ContentSettings
import pyodbc
import picamera
#import time

subscription_key = "[subscription_key]"
endpoint_mscs = "northeurope.api.cognitive.microsoft.com"
blob_account_name = '[account_name]'
blob_account_key = '[account_key]'
blob_container_name = '[container_name]'

def group_train(person_group_id):
    
    headers = {'Ocp-Apim-Subscription-Key': subscription_key,}

    try:
        conn = http.client.HTTPSConnection(endpoint_mscs)
        conn.request("POST", "/face/v1.0/persongroups/{0}/train".format(person_group_id), None, headers)
        response = conn.getresponse()
        data = response.read()
        print("Person Group (",person_group_id,") trained")
        return(data)
        conn.close()
    except Exception as e:
        return("[Errno {0}] {1}".format(e.errno, e.strerror))


def person_create(person_group_id, person_name, user_data):
    
    headers = {
        'Ocp-Apim-Subscription-Key': subscription_key,
    }

    body = json.dumps({"name": person_name, "userData" : user_data,},indent=2)

    try:
        conn = http.client.HTTPSConnection(endpoint_mscs)
        conn.request("POST", "/face/v1.0/persongroups/{0}/persons".format(person_group_id), body, headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        return(data)
    except Exception as e:
        print("[Errno {0}] {1}".format(e.errno, e.strerror))


# gets details of one person in a group
def person_get(person_group_id, person_id):

    headers = {
        'Ocp-Apim-Subscription-Key': subscription_key,
    }

    try:
        conn = http.client.HTTPSConnection(endpoint_mscs)
        conn.request("GET", "/face/v1.0/persongroups/{0}/persons/{1}".format(person_group_id,person_id), None, headers)
        response = conn.getresponse()
        data = response.read()
        #print(data)
        conn.close()
        return(data)
    except Exception as e:
        print("[Errno {0}] {1}".format(e.errno, e.strerror))

# deletes ther person from the group
def person_delete(person_group_id, person_id):
    
    headers = {
        'Ocp-Apim-Subscription-Key': subscription_key,
        }

    try:
        conn = http.client.HTTPSConnection(endpoint_mscs)
        conn.request("DELETE", "/face/v1.0/persongroups/{0}/persons/{1}".format(person_group_id,person_id), None, headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        return(data)
    except Exception as e:
        print("[Errno {0}] {1}".format(e.errno, e.strerror))


def person_face_add(person_group_id, person_id, file_location):

    headers = {
        'Content-Type': 'application/octet-stream',
        'Ocp-Apim-Subscription-Key': subscription_key,
    }

    with open(file_location, mode='rb') as file:
        fileContent = file.read()
    try:
        conn = http.client.HTTPSConnection(endpoint_mscs)
        conn.request("POST", "/face/v1.0/persongroups/{0}/persons/{1}/persistedFaces".format(person_group_id,person_id), fileContent, headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        #print(data)
        return(data)
    except Exception as e:
        print("[Errno {0}] {1}".format(e.errno, e.strerror))

# loads an image and creates a temporary face_id, returning gender & face attributes.
# this does not detect matches in the person-group, need to use face_identfy
def person_face_detect(file_location):

    headers = {
        'Content-Type': 'application/octet-stream',
        'Ocp-Apim-Subscription-Key': subscription_key,
    }

    params = urllib.parse.urlencode({
        'returnFaceId': 'true',
        'returnFaceLandmarks': 'false',
        'returnFaceAttributes': 'age,gender,emotion',
    })


    with open(file_location, mode='rb') as file:
        fileContent = file.read()
    try:
        conn = http.client.HTTPSConnection(endpoint_mscs)
        conn.request("POST", "/face/v1.0/detect?%s" % params, fileContent, headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        
        #print(data)
        return(data)
    except Exception as e:
        print("[Errno {0}] {1}".format(e.errno, e.strerror))


# matches a face_id to stored faces in a person group
def face_identify(person_group_id,face_id):

    headers = {
    'Ocp-Apim-Subscription-Key': subscription_key,
    }


    body = json.dumps({
    "personGroupId": person_group_id,
    "faceIds" : [face_id], ## converts the face_id parameter to a list, by adding square brackets
    "maxNumOfCandidatesReturned" : 1,
    "confidenceThreshold" : 0.5,
    },indent=2)
    
    try:
        conn = http.client.HTTPSConnection(endpoint_mscs)
        conn.request("POST", "/face/v1.0/identify", body, headers)
        response = conn.getresponse()
        data = response.read()
        #print(data)
        conn.close()
        return(data)
    except Exception as e:
        print("[Errno {0}] {1}".format(e.errno, e.strerror))


# create a person group
def group_create(person_group_id, name, user_data):

    headers = {
        # Request headers
        'Ocp-Apim-Subscription-Key': subscription_key,
    }

    params = urllib.parse.urlencode({
        # Request parameters
        'personGroupId': person_group_id,
    })

    body = json.dumps({
    "name": name,
    "userData" : user_data,
    },indent=2)
    
    try:
        conn = http.client.HTTPSConnection(endpoint_mscs)
        conn.request("PUT", "/face/v1.0/persongroups/{0}?%s".format(person_group_id) % params, body, headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        return(data)
    except Exception as e:
        print("[Errno {0}] {1}".format(e.errno, e.strerror))

# delete a person group
def group_delete(person_group_id):

    headers = {
        # Request headers
        'Ocp-Apim-Subscription-Key': subscription_key,
    }

    params = urllib.parse.urlencode({
        # Request parameters
        'personGroupId': person_group_id,
    })
 
    try:
        conn = http.client.HTTPSConnection(endpoint_mscs)
        conn.request("DELETE", "/face/v1.0/persongroups/{0}".format(person_group_id), None, headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        return(data)
    except Exception as e:
        print("[Errno {0}] {1}".format(e.errno, e.strerror))


# - lists all of the groups in the subscription
def group_list():

    headers = {
        'Ocp-Apim-Subscription-Key': subscription_key,
    }

    try:
        conn = http.client.HTTPSConnection(endpoint_mscs)
        conn.request("GET", "/face/v1.0/persongroups", None, headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        return(data)
    except Exception as e:
        print("[Errno {0}] {1}".format(e.errno, e.strerror))

# - lists the details of one group in the subscription
def group_get(person_group_id):

    headers = {
        'Ocp-Apim-Subscription-Key': subscription_key,
    }

    try:
        conn = http.client.HTTPSConnection(endpoint_mscs)
        conn.request("GET", "/face/v1.0/persongroups/{0}".format(person_group_id), None, headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        return(data)
    except Exception as e:
        print("[Errno {0}] {1}".format(e.errno, e.strerror))

# lists the persons in the person group
def person_group_get(person_group_id):

    headers = {
        'Ocp-Apim-Subscription-Key': subscription_key,
    }

    try:
        conn = http.client.HTTPSConnection(endpoint_mscs)
        conn.request("GET", "/face/v1.0/persongroups/{0}/persons".format(person_group_id), None, headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        return(data)
    except Exception as e:
        print("[Errno {0}] {1}".format(e.errno, e.strerror))

def capture_image(file_name):
    camera = picamera.PiCamera()
    camera.resolution = (1200, 1200)
    #camera.start_preview()
    camera.capture(file_name)
    #time.sleep(2)
    #camera.stop_preview()
    camera.close()



# ---------------------------------------------
# Readable print of JSON
# ---------------------------------------------

def json_print(json_text):
    json_text = json_text.decode("utf-8")
    print(json.dumps(json.loads(json_text),indent=2))


# ---------------------------------------------
# File copy component
# ---------------------------------------------

# - this is specific to the Azure blob created for the demo
def copy_to_blob (file_long_name, file_name):
    block_blob_service = BlockBlobService(account_name=blob_account_name, account_key=blob_account_key)
    block_blob_service.create_blob_from_path(
        blob_container_name,
        file_name,
        file_long_name,
        content_settings=ContentSettings(content_type='image/png')
        )

# ---------------------------------------------
# Insert SQL component
# ---------------------------------------------

def insert_to_sql (tsql):

    dsn = '[DSN_NAME]' 
    username = '[username@database]' 
    password = '[password]' 
    database = '[database]'
    connection_string = 'DSN={0};UID={1};PWD={2};DATABASE={3};'.format(dsn,username,password,database)

    cnxn = pyodbc.connect(connection_string)
    cursor = cnxn.cursor()
    cursor.execute(tsql)
    cnxn.commit()
    cnxn.close()




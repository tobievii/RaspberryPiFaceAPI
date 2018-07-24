print("Home Monitor is starting...")

# -------------------------------------------
# import required modules
# -------------------------------------------

import time
import grovepi
import faceapi
import datetime
import json
import operator
import os, uuid, sys
from azure.storage.blob import BlockBlobService, PublicAccess, ContentSettings
import uuid

# -------------------------------------------
# Connect the Grove Button to digital port D3
# -------------------------------------------
button = 3
grovepi.pinMode(button,"INPUT")

# -------------------------------------------
# local variables
# -------------------------------------------
image_folder = r"/home/pi/Pictures/HomeMonitor" # where images are saved
person_group_id ="mygroup" # name of the faces database for the Face API
blob_account_name = 'raspberrypi'
blob_container_name = 'houseguest'
blob_account_key = '/MhmKNM0/wjtP4LvnmgDo21XtBwGOdfWSWxnqOZvSGVFBkWKrcXRRGVNK11YDuVGHvNfC49ji1gZbGok82t1Xw=='
face_identity_count = 0
program_version = '1.0.0'

print("Home Monitor is running...")

# -------------------------------------------
# Enter the while loop to constantly monitor for the button press
# -------------------------------------------

while True:
    try:
        # -------------------------------------------
        # if the button is pressed
        # -------------------------------------------
        if grovepi.digitalRead(button) == 1:
            print("image captured, processing...")
            # -------------------------------------------
            # Capture the image
            # -------------------------------------------
            now = datetime.datetime.now()
            image_file_name = "image_"+now.strftime("%Y%m%d_%H%M%S")+".jpg"
            image_full_name = image_folder+"/"+image_file_name
            faceapi.capture_image(image_full_name)
            screen_message = ""

            # set initial SQL variables, more after the recognition loop
            visit_id = uuid.uuid4()
            visit_datetime = now.strftime("%Y-%m-%d %H:%M:%S")
            visit_image_url = 'https://raspberrypi.blob.core.windows.net/houseguest/'+image_file_name
            
            # -------------------------------------------
            # Send the image to Microsoft Face API to Detect
            # -------------------------------------------
            print("Performing Facial recognition algorithms...")
            detect_json = faceapi.person_face_detect(image_full_name)
            detect_py = json.loads(detect_json.decode("utf-8"))
            if "error" in detect_py:
                print("Error found:",detect_py["error"]["message"])
                break
            
            # -------------------------------------------
            # Second loop: 
            # For every face it detects in the image, grab the details & check if they are in the database
            # -------------------------------------------
            for x in detect_py:
                face_identity_count +=1
                # Get the facial detection attributes
                age = x["faceAttributes"]["age"]
                gender = x["faceAttributes"]["gender"]
                emotion = x["faceAttributes"]["emotion"]
                emotion_sorted = sorted(emotion.items(), key=operator.itemgetter(1),reverse=True)
                expression = emotion_sorted[0][0]
                expression_confidence = emotion_sorted[0][1]

                # Look up the face to identify
                identify_json = faceapi.face_identify(person_group_id, x["faceId"])
                identify_py = json.loads(identify_json.decode("utf-8"))
                if "error" in identify_py:
                    print("Error found:",identify_py["error"]["message"])
                    break

                # if the identify found candidates, grab their details-
                if len(identify_py[0]["candidates"]) > 0:
                    #print(identify_py)
                    person_get_json = faceapi.person_get(person_group_id, identify_py[0]["candidates"][0]["personId"])
                    person_get_py = json.loads(person_get_json.decode("utf-8"))
                    if "error" in person_get_py:
                        print("Error found:",person_get_py["error"]["message"])
                        break
                    person_name = person_get_py["name"]
                    identify_confidence = identify_py[0]["candidates"][0]["confidence"]
                else:
                    person_name = "Unknown"
                    identify_confidence = 0

                # ----------------------------------------
                # Output the results to the screen
                # ----------------------------------------
                #screen_message = ">>> I see "+person_name+" who is a "+gender+" aged "+age+", with facial expression of "+str("{0:.1%}".format(expression_confidence))+" "+expression
                print(">>> I see ",person_name," who is a ",gender," aged ",age,", with facial expression of ","{0:.1%}".format(expression_confidence),expression)

                # ----------------------------------------
                # Insert the identity row to SQL Server
                # ----------------------------------------
                print("Inserting to SQL VisitFaces table...")
                visitfaces_tsql = "insert rpi.VisitFaces ( VisitGUID, PersonName, PersonConfidence, Age, Gender, Expression, ExpressionConfidence) values ('{0}','{1}',{2},{3},'{4}','{5}',{6})".format(visit_id, person_name, identify_confidence, age, gender, expression, expression_confidence)
                #print(visitfaces_tsql)
                faceapi.insert_to_sql(visitfaces_tsql)
                
            # -------------------------------------------
            # Copy to Azure Blob Storage
            # -------------------------------------------
            print("copying to Azure blob storage...")
            block_blob_service = BlockBlobService(account_name=blob_account_name, account_key=blob_account_key)

            out = block_blob_service.create_blob_from_path(
                blob_container_name,
                image_file_name,
                image_full_name,
                content_settings=ContentSettings(content_type='image/png')
                )

            # --------------------------------------------
            # Insert the photo visit row to SQL Azure
            # --------------------------------------------
            print("Inserting to SQL Visit table...")
            visit_tsql = "insert rpi.Visit ( VisitGUID, VisitDateTime, ProgramVersion, VisitImageURL, FaceCount ) values ('{0}', '{1}', '{2}', '{3}', {4})".format(visit_id, visit_datetime, program_version, visit_image_url,face_identity_count)
            #print(visit_tsql)
            faceapi.insert_to_sql(visit_tsql)

            # ----------------------------------------
            # Finished processing the image, return to monitoring
            # ----------------------------------------
            face_identity_count = 0
            print("\n")
            #print(screen_message)
            print("Done. Back to monitoring mode...")
                
        time.sleep(.5)

    except IOError:
        print ("Error")
    except KeyboardInterrupt:
        print("Goodbye")
        break


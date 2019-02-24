import http.client, urllib.request, urllib.parse, urllib.error
import json


prediction_key = '7a4eff85e7c84d4c8bb9c8ae2b4ccda1'
project_id = 'cebe9fde-6e61-406e-b495-ce4f1d859cf8'
iteration_id = '4dfe854e-24ec-4cdd-8779-517deacf92f6'
endpoint_mscv = 'southcentralus.api.cognitive.microsoft.com'

def custom_vision_mouse(image_file):
    print('before headers')
    
    headers = {
        'Prediction-Key': prediction_key,
        'Content-Type':'application/octet-stream',
    }

    print('before params')
    params = urllib.parse.urlencode({
        'iterationId':iteration_id,
    })

    #body = {"url":"http://example.com/images/test.jpg"}

    print('before body')
    with open(image_file, mode='rb') as file:
        fileContent = file.read()
    print('before try')    
    try:
        conn = http.client.HTTPSConnection(endpoint_mscv)
        conn.request('POST', '/customvision/v2.0/Prediction/{0}/image?%s'.format(project_id) % params, fileContent, headers)
        response = conn.getresponse()
        data = response.read()
        #print("Person Group (",person_group_id,") trained")
        return(data)
        conn.close()
    except Exception as e:
        return("[Errno {0}] {1}".format(e.errno, e.strerror))

image_file =  r'C:\Users\benwa\Pictures\temp2\IMG_20190203_142100.jpg'

print('here')

json_out = custom_vision_mouse(image_file)

json_py = json.loads(json_out)

for x in json_py["predictions"]:
    probability = x["probability"]
    if probability > 0.8:
        print(x)


#print(json.dumps(json.loads(json_out),indent=2))



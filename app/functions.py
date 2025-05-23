import time
import jwt
from django.http import HttpResponse
import requests
# from dropdown_to_subitems.values import token
import monday_code
import os 
from dotenv import load_dotenv


def get_auth(request):
    
    # global token
    
    authorization = request.headers.get('Authorization')
    load_dotenv()
    SIGNING_SECRET = os.getenv('SIGNING_SECRET')
    
    try:
        payload = jwt.decode(authorization, SIGNING_SECRET, algorithms=['HS256', 'SHA256', 'RSASSA', 'HMAC'], options={'verify_aud': False})
        
        
        return payload['shortLivedToken']
        
    except jwt.ExpiredSignatureError:
        return HttpResponse('Token ha expirado', status=401)
    except jwt.InvalidTokenError:
        return HttpResponse('Token inválido', status=401)

def trigger_monday_webhook(webhook_url, output_fields):
    SIGNING_SECRET = os.getenv("SIGNING_SECRET")
    APP_ISSUER = os.getenv("APP_ID")  # opcional, si prefieres meterlo en .env

    if not SIGNING_SECRET:
        raise ValueError("Falta SIGNING_SECRET en las variables de entorno")

    payload = {
        "iat": int(time.time()),
        "iss": APP_ISSUER or "f864ca3026e4ae0f32fcf492838a6976"
    }

    token = jwt.encode(payload, SIGNING_SECRET, algorithm="HS256")
    if isinstance(token, bytes):
        token = token.decode("utf-8")

    headers = {
        "Authorization": token,
        "Content-Type": "application/json"
    }

    body = {
        "trigger": {
            "outputFields": output_fields
        }
    }

    response = requests.post(webhook_url, json=body, headers=headers)
    return response

def monday_request(query, token):
    
    apiUrl = "https://api.monday.com/v2"
    headers = {"Authorization" : token, "API-Version" : "2023-10"}
    data = {"query" : query}
    #print(f"query en monday_request = {query}")
    r = requests.post(url=apiUrl, json=data, headers=headers)
    # print(f"r en monday_request = {r}")

    # print(f"resultado consulta en monday_request = {r.json()}")
    if "errors" in r.json():
        try:
            print(f"entro en error_code")
            # int(error_message.split()[-2]) + 1
            if r.json()["error_code"] == 'ComplexityException':
                print(f"entro en complexity error")
                seconds_to_wait = int(r.json()["errors"][0].split()[-2])+1
                print(f"Complexity budget exhausted, waiting {seconds_to_wait}seg")
                
                time.sleep(seconds_to_wait+1)
                # print(f"query en return Complexity budget exhausted = {query}")
                return monday_request(query,token)
            else:
                print(f"ERROR EN MONDAY REQUEST = {r.json()}")
                return f"ERROR{r.json()}"
            
            
        except:
            print(f"ERROR EN MONDAY REQUEST = {r.json()}")
            return f"ERROR{r.json()}"
    # print(f"r.json() despues condiciones errores= {r.json()}")
    
    return r.json()
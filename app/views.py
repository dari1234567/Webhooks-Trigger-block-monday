import json

from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from .functions import get_auth, monday_request

@csrf_exempt
def test(request):
    try:
        if request.method == "POST" and request.body:
            body = json.loads(request.body)
        
        else:
            body= {}
            
        headers = dict(request.headers)
        print(f"Headers: {json.dumps(headers, indent=2)}")
        
        if 'challenge' in body:
            print("Respuesta al challenge de verificación")
            return HttpResponse(
                json.dumps({'challenge': body['challenge']}),
                content_type='application/json'
            )
        
        print("\n--- WEBHOOK RECIBIDO ---")
        print("Headers:", json.dumps(headers, indent=2))
        print("Body:", json.dumps(body, indent=2))
        print("Método:", request.method)
        print("--------------------------------\n")
        
    except Exception as e:
        print("\n--- ERROR EN TEST ---")
        print("Error:", str(e))
        print("Body crudo:", request.body)
        print("--------------------------\n")
    
    return HttpResponse("OK")




@csrf_exempt
def subscribe(request):
    body = json.loads(request.body)
    print(f"Body_subscribe: {body}")
    webhook_url = body["payload"]["webhookUrl"]
    subscription_id = body["payload"]["subscriptionId"]
    input_fields = body["payload"]["inputFields"]
    
    headers = request.headers
    print(f"Headers: {headers}")

    
    print(f"Suscripción recibida: {subscription_id}, webhook: {webhook_url}, inputs: {input_fields}")
    
    config_json = json.dumps({"columnId": "date_mkr481k2"}).replace('"', '\\"')  
    webhook_url = request.build_absolute_uri('/app/test')
    
    mutation = '''
    mutation {
        create_webhook (
            board_id: 1908603295,
            url: "%s",
            event: change_specific_column_value,
            config: "%s"
        ) {
            id
            board_id
        }
    }
    ''' % (webhook_url, config_json)

        
    print(f"Mutation: {mutation}")
    token = get_auth(request)
    print (f"Token: {token}")
    
    result= monday_request(mutation, token)
    print(f"Resultado: {result}")
    
    
    
    return HttpResponse(json.dumps({"webhookId": subscription_id}), content_type="application/json")
    
    
    
    
    
    
    
    
    
@csrf_exempt
def unsubscribe(request):
    body = json.loads(request.body)
    webhook_id = body["payload"]["webhookId"] or body["payload"].get("subscriptionId")

    
    print(f"Cancelando suscripción {webhook_id}")

    return HttpResponse(status=200)

@csrf_exempt
def health(request):
    return HttpResponse("OK")

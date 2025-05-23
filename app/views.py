import json
import os
import time
import jwt
import requests
import traceback

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from dotenv import load_dotenv

from .functions import get_auth, monday_request, trigger_monday_webhook

load_dotenv()


@csrf_exempt
def test(request):
    try:
        if request.method == "POST" and request.body:
            body = json.loads(request.body)
        else:
            body = {}

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

        event = body["event"] if "event" in body else body.get("payload", {}).get("event", {})
        board_id = event["boardId"]
        item_id = event["pulseId"]
        column_id = event["columnId"]

        print(f"[DEBUG] Evento detectado - Board: {board_id}, Item: {item_id}, Column: {column_id}")

        subscription_ids = cache.get("subscription_ids", [])

        SIGNING_SECRET = os.getenv("SIGNING_SECRET")
        if not SIGNING_SECRET:
            raise ValueError("SIGNING_SECRET no configurado")

        for subscription_id in subscription_ids:
            webhook_url = cache.get(f"subscription:{subscription_id}")
            if not webhook_url:
                continue

            print(f"Disparando trigger para suscripción {subscription_id} en {webhook_url}")

            payload_jwt = {
                "iat": int(time.time()),
                "iss": os.getenv("MONDAY_APP_ID", "default-app-id")
            }
            token = jwt.encode(payload_jwt, SIGNING_SECRET, algorithm="HS256")
            if isinstance(token, bytes):
                token = token.decode("utf-8")

            trigger_payload = {
                "trigger": {
                    "outputFields": {
                        "board": board_id,
                        "item": item_id,
                        "column": column_id
                    }
                }
            }

            response = requests.post(webhook_url, headers={
                "Authorization": token,
                "Content-Type": "application/json"
            }, json=trigger_payload)

            print(f"Trigger disparado: status {response.status_code}, response: {response.text}")

    except Exception as e:
        print("\n--- ERROR EN /app/test ---")
        print(str(e))
        print(traceback.format_exc())
        print(f"Body recibido crudo: {request.body}")

    return HttpResponse("OK")


@csrf_exempt
def subscribe(request):
    try:
        body = json.loads(request.body)
        print(f"Body_subscribe: {json.dumps(body, indent=2)}")

        webhook_url = body["payload"]["webhookUrl"]
        subscription_id = body["payload"]["subscriptionId"]
        input_fields = body["payload"]["inputFields"]
        board_id = body["payload"]["inputFields"]["boardId"]


        print(f"Suscripción recibida: {subscription_id}, webhook: {webhook_url}, inputs: {input_fields}")

        # Guardar la suscripción
        cache.set(f"subscription:{subscription_id}", webhook_url, timeout=None)
        subscription_ids = cache.get("subscription_ids", [])
        if subscription_id not in subscription_ids:
            subscription_ids.append(subscription_id)
            cache.set("subscription_ids", subscription_ids)

        # Crear webhook en Monday
        config_json = json.dumps({"columnId": input_fields["columnId"]}).replace('"', '\\"')
        webhook_callback_url = request.build_absolute_uri('/app/test')

        mutation = '''
        mutation {
            create_webhook (
                board_id: %s,
                url: "%s",
                event: change_specific_column_value,
                config: "%s"
            ) {
                id
                board_id
            }
        }
        ''' % (board_id,webhook_callback_url,config_json)

        token = get_auth(request)
        result = monday_request(mutation, token)
        print(f"Resultado mutation: {result}")

        return HttpResponse(json.dumps({"webhookId": subscription_id}), content_type="application/json")

    except Exception as e:
        print("Error en /subscribe:", str(e))
        print(traceback.format_exc())
        return HttpResponse("Error en subscribe", status=500)


@csrf_exempt
def unsubscribe(request):
    try:
        body = json.loads(request.body)
        webhook_id = body["payload"]["webhookId"]

        cache.delete(f"subscription:{webhook_id}")
        subscription_ids = cache.get("subscription_ids", [])
        if webhook_id in subscription_ids:
            subscription_ids.remove(webhook_id)
            cache.set("subscription_ids", subscription_ids)

        print(f"Cancelando suscripción {webhook_id}")
        return HttpResponse(status=200)

    except Exception as e:
        print("Error en /unsubscribe:", str(e))
        print(traceback.format_exc())
        return HttpResponse("Error en unsubscribe", status=500)


@csrf_exempt
def health(request):
    return HttpResponse("OK")

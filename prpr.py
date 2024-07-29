import json
import requests
from flask import Flask, request, jsonify
import base64
from flasgger import Swagger, swag_from

app = Flask(__name__)

# Custom Swagger configuration
swagger_template = {
    'components': {
        'securitySchemes': {
            'bearerAuth': {
                'type': 'http',
                'scheme': 'bearer',
                'bearerFormat': 'JWT'
            }
        },
        'security': {
            'bearerAuth': []
        }
    }
}
app.config['SWAGGER'] = {
    'title': 'Receipt API',
    'version': '3.0.0',
    'swagger_version': '2.0',
    'description':'API для смены форматов чеков Атол',
    'hide_flask_swagger': True,  # Hide "Powered by Flasgger"
    'swagger_ui': True,
    'specs_route': '/swagger/',
    "termsOfService": "",
    "template": swagger_template,
    'ui_settings': {
        'defaultModelsExpandDepth': -1,  # Hide models section
        'docExpansion': 'none',  # Collapse all sections
        'operationsSorter': 'alpha',  # Sort operations alphabetically
        'tagsSorter': 'alpha',  # Sort tags alphabetically
        'requestSnippetsEnabled': True,  # Enable request snippets
    },
    'auth': {
        'type': 'basic',
        'basic_auth_ui': True
    }
}

swagger = Swagger(app)

TOKEN_URL = "https://api.stage.vdpaybox.ru/api/atol/login"
RECEIPT_URL = "https://api.stage.vdpaybox.ru/api/receipt"

def get_nested(data, *keys, default=None):
    for key in keys:
        data = data.get(key, default)
        if data is default:
            break
    return data

def remove_empty_fields(data):
    def empty(x):
            return x is None or x == {} or x == []
    
    if not isinstance(data, (dict, list)):
            return data
    elif isinstance(data, list):
            return [v for v in (remove_empty_fields(v) for v in data) if not empty(v)]
    else:
            return {k: v for k, v in ((k, remove_empty_fields(v)) for k, v in data.items()) if not empty(v)}

def transform_electr(item):
    return item.get("electronically") != "false"

def transform_marking_code(item):
    mark_code = item.get("mark_code", {})
    if mark_code:
        if "egais20" in mark_code:
            mark_type = "egais20"
        elif "egais30" in mark_code:
            mark_type = "egais30"
        else:
            mark_type = "other"
        return {
            "type": mark_type,
            "mark": mark_code[list(mark_code.keys())[0]]
        }
    return {
        "type": "other",
        "mark": mark_code
    }

def transform_payment_object(item):
    payment_object = item.get("payment_object")
    tr_list = {
        1: "commodity",
        2: "excise",
        3: "job",
        4: "service",
        5: "gamblingBet",
        6: "gamblingPrize",
        7: "lottery",
        8: "lotteryPrize",
        9: "intellectualActivity",
        10: "payment",
        11: "agentCommission",
        12: "pay",
        13: "another",
        14: "proprietaryLaw",
        15: "nonOperatingIncome",
        16: "otherContributions",
        17: "merchantTax",
        18: "resortFee",
        19: "deposit",
        20: "consumption",
        21: "soleProprietorCPIContributions",
        22: "cpiContributions",
        23: "soleProprietorCMIContributions",
        24: "cmiContributions",
        25: "csiContributions",
        26: "casinoPayment",
        27: "bankAgentPayment",
        30: "markedExciseNoCode",
        31: "markedExciseWithCode",
        32: "markedCommodityNoCode",
        33: "markedCommodityWithCode"
    }
    return tr_list.get(payment_object, "unknown")

def transform_payment_method(item):
    payment_method = item.get("payment_method")
    pm_list = {
        "full_prepayment": "fullPrepayment",
        "prepayment": "prepayment",
        "advance": "advance",
        "full_payment": "fullPayment",
        "partial_payment": "partialPayment",
        "credit": "credit",
        "credit_payment": "creditPayment"
    }
    return pm_list.get(payment_method, "unknown")

def transform_agent(items):
    agents = items.get("agent_info",{})
    if agents:
        return ["another"]
    else:
        return None

def transform_measure(item):
    measurement_unit = item.get("measure")
    units_list = {
        0: "шт",
        10: "Грамм",
        11: "Килограмм",
        12: "Тонна",
        20: "Сантиметр",
        21: "Дециметр",
        22: "Метр",
        30: "Квадратный сантиметр",
        31: "Квадратный дециметр",
        32: "Квадратный метр",
        40: "Миллилитр",
        41: "Литр",
        42: "Кубический метр",
        50: "Киловатт час",
        51: "Гигакалория",
        70: "Сутки (день)",
        71: "Час",
        72: "Минута",
        73: "Секунда",
        80: "Килобайт",
        81: "Мегабайт",
        82: "Гигабайт",
        83: "Терабайт",
        255: "иное"
    }
    return units_list.get(measurement_unit, "unknown")

@app.route('/process', methods=['POST'])
@swag_from({
    'responses': {
        200: {
            'description': 'Success',
            'content': {
                'application/json': {
                    'example': {
                        'message': 'Success',
                        'data': {}
                    }
                }
            }
        },
        400: {
            'description': 'Bad Request',
            'content': {
                'application/json': {
                    'example': {
                        'error': 'Authorization header is required and should be Basic'
                    }
                }
            }
        },
        500: {
            'description': 'Internal Server Error',
            'content': {
                'application/json': {
                    'example': {
                        'error': 'Failed to send receipt data'
                    }
                }
            }
        }
    }
})
def process():
    """
    Process the receipt
    ---
    tags:
      - Receipt
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Basic authorization header
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            external_id:
              type: string
              example: "892924433534522515289444"
            receipt:
              type: object
              properties:
                client:
                  type: object
                  properties:
                    email:
                      type: string
                      example: "client@client.ru"
                    phone:
                      type: string
                      example: "+70002410085"
                    name:
                      type: string
                      example: "Иванов Иван Иванович"
                    inn:
                      type: string
                      example: "516974792202"
                    birthdate:
                      type: string
                      example: "18.11.1990"
                    citizenship:
                      type: string
                      example: "643"
                    document_code:
                      type: string
                      example: "21"
                    document_data:
                      type: string
                      example: "4507 443564"
                    address:
                      type: string
                      example: "г.Москва, Ленинский проспект д.1 кв 43"
                company:
                  type: object
                  properties:
                    email:
                      type: string
                      example: "email@ofd.ru"
                    sno:
                      type: string
                      example: "osn"
                    inn:
                      type: string
                      example: "5010051677"
                    payment_address:
                      type: string
                      example: "shop-url.ru"
                items:
                  type: array
                  items:
                    type: object
                    properties:
                      name:
                        type: string
                        example: "Ваш любимый товар1"
                      price:
                        type: number
                        example: 120
                      quantity:
                        type: number
                        example: 1.0
                      measure:
                        type: integer
                        example: 0
                      sum:
                        type: number
                        example: 120
                      payment_method:
                        type: string
                        example: "full_payment"
                      payment_object:
                        type: integer
                        example: 1
                      vat:
                        type: object
                        properties:
                          type:
                            type: string
                            example: "vat20"
                          sum:
                            type: number
                            example: 20.0
                      user_data:
                        type: string
                        example: "Дополнительный реквизит предмета расчета"
                      excise:
                        type: number
                        example: 10.0
                      country_code:
                        type: string
                        example: "056"
                      declaration_number:
                        type: string
                        example: "12332234533"
                      mark_quantity:
                        type: object
                        properties:
                          numerator:
                            type: number
                            example: 1
                          denominator:
                            type: number
                            example: 2
                      mark_processing_mode:
                        type: string
                        example: "0"
                      sectoral_item_props:
                        type: array
                        items:
                          type: object
                          properties:
                            federal_id:
                              type: string
                              example: "001"
                            date:
                              type: string
                              example: "18.11.2020"
                            number:
                              type: string
                              example: "123/43"
                            value:
                              type: string
                              example: "Ид1=Знач1&Ид2=Знач2&Ид3=Знач3"
                      mark_code:
                        type: object
                        properties:
                          egais20:
                            type: string
                            example: "MDEwNDYwNzQyODY3OTA5MDIxNmVKSWpvV0g1NERkVSA5MWZmZDAgOTJzejZrU1BpckFwZk1CZnR2TGJvRTFkbFdDLzU4aEV4UVVxdjdCQmtabWs0PQ="
                      agent_info:
                        type: object
                        properties:
                          type:
                            type: string
                            example: "another"
                          paying_agent:
                            type: object
                            properties:
                              operation:
                                type: string
                                example: "Операция 1"
                              phones:
                                type: array
                                items:
                                  type: string
                                  example: "+79998887766"
                          receive_payments_operator:
                            type: object
                            properties:
                              phones:
                                type: array
                                items:
                                  type: string
                                  example: "+79998887766"
                          money_transfer_operator:
                            type: object
                            properties:
                              phones:
                                type: array
                                items:
                                  type: string
                                  example: "+79998887766"
                              name:
                                type: string
                                example: "Оператор перевода"
                              address:
                                type: string
                                example: "г. Москва, ул. Складочная д.3"
                              inn:
                                type: string
                                example: "8634330204"
                      supplier_info:
                        type: object
                        properties:
                          phones:
                            type: array
                            items:
                              type: string
                              example: "+79998887766"
                          name:
                            type: string
                            example: "Название поставщика"
                          inn:
                            type: string
                            example: "287381373424"
                payments:
                  type: array
                  items:
                    type: object
                    properties:
                      type:
                        type: integer
                        example: 1
                      sum:
                        type: number
                        example: 120.0
                vats:
                  type: array
                  items:
                    type: object
                    properties:
                      type:
                        type: string
                        example: "vat20"
                      sum:
                        type: number
                        example: 20.0
                cashier:
                  type: string
                  example: "кассир"
                cashier_inn:
                  type: string
                  example: "887405485310"
                additional_check_props:
                  type: string
                  example: "445334544"
                total:
                  type: number
                  example: 120.0
                additional_user_props:
                  type: object
                  properties:
                    name:
                      type: string
                      example: "название доп реквизита"
                    value:
                      type: string
                      example: "значение доп реквизита"
                operating_check_props:
                  type: object
                  properties:
                    name:
                      type: string
                      example: "0"
                    value:
                      type: string
                      example: "данные операции"
                    timestamp:
                      type: string
                      example: "03.11.2020 12:05:31"
                sectoral_check_props:
                  type: array
                  items:
                    type: object
                    properties:
                      federal_id:
                        type: string
                        example: "001"
                      date:
                        type: string
                        example: "18.11.2020"
                      number:
                        type: string
                        example: "123/43"
                      value:
                        type: string
                        example: "Ид1=Знач1&Ид2=Знач2&Ид3=Знач3"
    """
    input_data = request.json
    auth_header = request.headers.get('Authorization')
    
    if not auth_header or not auth_header.startswith('Basic '):
        return jsonify({"error": "Authorization header is required and should be Basic"}), 400
    
    auth_encoded = auth_header.split(' ')[1]
    auth_decoded = base64.b64decode(auth_encoded).decode('utf-8')
    username, password = auth_decoded.split(':')
    
    if not password:
        print(request.headers)
        return jsonify({"error": "Password is required"}), 400
    
    response = requests.get(TOKEN_URL, headers={"Authorization": auth_header})
    
    if response.status_code != 200:
        print(username, "\n", password)
        return jsonify(response.json()), response.status_code
    
    token = response.json().get('token')
    orgid = response.json().get('orgId')
    data = response.content
    print(data)
    if not token:
        return jsonify({"error": "Token not found in response"}), 400
    
    target_data = {
        "externId": input_data.get("external_id"),
        "externDeviceId": input_data.get("device_number"),
        "recreatePayment": None,  # Not found
        "orgId": orgid,
        "cashboxId": None,  # Not found
        "receiptBody": {
            "externId": input_data.get("external_id"),
            "type": "sell",  # E
            "taxationType": get_nested(input_data, "receipt", "company", "sno"),
            "electronically": transform_electr(input_data),
            "paymentsPlace": get_nested(input_data, "receipt", "client", "address"),
            "operator": {
                "name": get_nested(input_data, "receipt", "client", "name"),
                "vatin": get_nested(input_data, "receipt", "client", "inn")
            },
            "clientInfo": {
                "emailOrPhone": get_nested(input_data, "receipt", "client", "email"),
                "vatin": get_nested(input_data, "receipt", "client", "inn"),
                "name": get_nested(input_data, "receipt", "client", "name")
            },
            "items": [
                {
                    "type": "position",
                    "name": item.get("name"),
                    "price": item.get("price"),
                    "quantity": item.get("quantity"),
                    "amount": item.get("sum"),
                    "measurementUnit": transform_measure(item),
                    "paymentMethod": transform_payment_method(item),
                    "paymentObject": transform_payment_object(item),
                                        "supplierInfo": {
                        "phones": item.get("supplier_info", {}).get("phones"),
                        "name": item.get("supplier_info", {}).get("name"),
                        "vatin": item.get("supplier_info", {}).get("inn")
                    },
                    "tax": {
                        "type": item.get("vat", {}).get("type"),
                        "sum": item.get("vat", {}).get("sum")
                    },
                    "markingCode": transform_marking_code(item),

                    "agentInfo": {
                        "agents": transform_agent(item),
                        "payingAgent": {
                            "operation": item.get("agent_info", {}).get("paying_agent", {}).get("operation"),
                            "phones": item.get("agent_info", {}).get("paying_agent", {}).get("phones")
                        },
                        "receivePaymentsOperator": {
                            "phones": item.get("agent_info", {}).get("receive_payments_operator", {}).get("phones")
                        },
                        "moneyTransferOperator": {
                            "phones": item.get("agent_info", {}).get("money_transfer_operator", {}).get("phones"),
                            "name": item.get("agent_info", {}).get("money_transfer_operator", {}).get("name"),
                            "address": item.get("agent_info", {}).get("money_transfer_operator", {}).get("address"),
                            "vatin": item.get("agent_info", {}).get("money_transfer_operator", {}).get("inn")
                        }
                    }
                } for item in get_nested(input_data, "receipt", "items", default=[])
            ],
            "payments": [
                {
                    "sum": payment.get("sum"),
                    "type": "electronically"
                } for payment in get_nested(input_data, "receipt", "payments", default=[])
            ],
            "taxes": [
                {
                    "type": tax.get("type"),
                    "sum": tax.get("sum")
                } for tax in get_nested(input_data, "receipt", "vats", default=[])
            ]
        }
    }

    cleaned_target_data = remove_empty_fields(target_data)
    clear_data = target_data

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(RECEIPT_URL, json=cleaned_target_data, headers=headers)
    
    if response.status_code != 200:
        print(cleaned_target_data)
        return jsonify(response.json()), response.status_code

    return jsonify(response.json()), 200

if __name__ == '__main__':
    app.run(debug=True)

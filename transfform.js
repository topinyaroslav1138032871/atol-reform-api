function transform(input) {
    var request = input.request[0];
    var transformedItems = request.items
        .filter(function (item) { return item.type === 'position'; })
        .map(function (item) { return ({
        type: item.type,
        name: item.name,
        price: item.price,
        quantity: item.quantity,
        amount: item.amount,
        paymentMethod: item.paymentMethod,
        paymentObject: item.paymentObject,
        tax: item.tax ? { type: item.tax.type } : undefined,
    }); });
    console.log(transformedItems);
    var transformedPayments = request.payments.map(function (payment) { return ({
        type: payment.type,
        sum: payment.sum,
    }); });
    var output = {
        receiptBody: {
            type: request.type,
            electronically: true,
            operator: {
                name: request.operator.name,
            },
            clientInfo: {
                emailOrPhone: "1",
            },
            items: transformedItems,
            payments: transformedPayments,
            total: request.total,
        },
    };
    return output;
}
var inputJSON = {
    "uuid": "0ba40014-5fa5-11ea-b5e9-037d4786a49d",
    "callbacks": {
        "resultUrl": "http://myapp.domain.ru/task_ready?myid=receipt1"
    },
    "request": [
        {
            "type": "sell",
            "taxationType": "osn",
            "ignoreNonFiscalPrintErrors": false,
            "operator": {
                "name": "Иванов",
                "vatin": 123654789507
            },
            "items": [
                {
                    "type": "position",
                    "name": "Кефир",
                    "price": 48.45,
                    "quantity": 1,
                    "amount": 48.45,
                    "department": 1,
                    "measurementUnit": "шт.",
                    "paymentMethod": "fullPrepayment",
                    "paymentObject": "excise",
                    "additionalAttribute": "ID:iASDv3w45",
                    "tax": {
                        "type": "vat0"
                    }
                },
                {
                    "type": "barcode",
                    "barcode": 123456789012,
                    "barcodeType": "EAN13",
                    "scale": 2
                }
            ],
            "payments": [
                {
                    "type": "cash",
                    "sum": 2000
                }
            ],
            "total": 224
        }
    ]
};
var outputJSON = transform(inputJSON);
console.log(JSON.stringify(outputJSON, null, 2));

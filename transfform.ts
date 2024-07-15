interface InputJSON {
    uuid: string;
    callbacks: {
      resultUrl: string;
    };
    request: RequestItem[];
  }
  
  interface RequestItem {
    type: string;
    taxationType: string;
    ignoreNonFiscalPrintErrors: boolean;
    operator: {
      name: string;
      vatin?: number;
    };
    items: Item[];
    payments: Payment[];
    total: number;
  }
  
  interface Item {
    type: string;
    name?: string;
    price?: number;
    quantity?: number;
    amount?: number;
    department?: number;
    measurementUnit?: string;
    paymentMethod?: string;
    paymentObject?: string;
    tax?: {
      type: string;
    };
    scale?: number;
  }
  
  interface Payment {
    type: string;
    sum: number;
  }
  
  interface OutputJSON {
    receiptBody: {
      type: string;
      electronically: boolean;
      operator: {
        name: string;
      };
      clientInfo: {
        emailOrPhone: string;
      };
      items: OutputItem[];
      payments: OutputPayment[];
      total: number;
    };
  }
  
  interface OutputItem {
    type: string;
    name?: string;
    price?: number;
    quantity?: number;
    amount?: number;
    paymentMethod?: string;
    paymentObject?: string;
    tax?: {
      type: string;
    };
  }
  
  interface OutputPayment {
    type: string;
    sum: number;
  }
  
  function transform(input: InputJSON): OutputJSON {
    const request = input.request[0];
  
    const transformedItems: OutputItem[] = request.items
    .filter(item=>item.type === 'position')
    .map(item => ({
      type: item.type,
      name: item.name,
      price: item.price,
      quantity: item.quantity,
      amount: item.amount,
      paymentMethod: item.paymentMethod,
      paymentObject: item.paymentObject,
      tax: item.tax ? { type: item.tax.type } : undefined,
    }));
  console.log(transformedItems)
    const transformedPayments: OutputPayment[] = request.payments.map(payment => ({
      type: payment.type,
      sum: payment.sum,
    }));
  
    const output: OutputJSON = {
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
  
  const inputJSON: InputJSON = {

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
      }
  
  const outputJSON = transform(inputJSON);
  console.log(JSON.stringify(outputJSON, null, 2));
  
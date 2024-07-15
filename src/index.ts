import express, { Request, Response } from 'express';
import axios from 'axios';

const app = express();
const port = 7676;

app.use(express.json());

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
  orgId: number,
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

interface serverAnswer {
  token: string,
  orgId: number
}

function transform(input: InputJSON): OutputJSON {
  const request = input.request[0];

  const transformedItems: OutputItem[] = request.items
    .filter(item => item.type === 'position')
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

  const transformedPayments: OutputPayment[] = request.payments.map(payment => ({
    type: payment.type,
    sum: payment.sum,
  }));

  const output: OutputJSON = {
    orgId: -1,
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

app.post('/process', async (req: Request, res: Response) => {
  try {
    const inputData: InputJSON = req.body;
    const header = req.headers['authorization'];
    const outputData = transform(inputData);
    if(!header){
      return res.status(400).json({error:req.headers})
    }
    const base64header = header.split(' ')[1];
    const cr = Buffer.from(base64header,'base64').toString('ascii');
    const [login,password] = cr.split(':');
    const tokenResponse = await axios.get('https://api.stage.vdpaybox.ru/api/atol/login', { headers: {
      Authorization: `Basic ${base64header}`
    }});

    const token: string = await tokenResponse.data['token'];
    outputData.orgId = await tokenResponse.data['orgId'];

    const receiptResponse = await axios.post('https://api.stage.vdpaybox.ru/api/receipt', outputData, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });

    res.json(receiptResponse.data);
  } catch (error) {
    console.error('Error processing request:', error);
    res.status(500).json({ error: 'Internal Server Error' });
  }
});

app.listen(port, () => {
  console.log(`Server is running at http://localhost:${port}`);
});

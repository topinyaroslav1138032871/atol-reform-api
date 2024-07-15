"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = __importDefault(require("express"));
const axios_1 = __importDefault(require("axios"));
const app = (0, express_1.default)();
const port = 3000;
app.use(express_1.default.json());
function transform(input) {
    const request = input.request[0];
    const transformedItems = request.items
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
    const transformedPayments = request.payments.map(payment => ({
        type: payment.type,
        sum: payment.sum,
    }));
    const output = {
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
app.post('/process', (req, res) => __awaiter(void 0, void 0, void 0, function* () {
    try {
        const inputData = req.body;
        const login = req.headers['username'];
        const password = req.headers['password'];
        const emailOrPhone = '1';
        const outputData = transform(inputData);
        if (!login || !password) {
            return res.status(400).json({ error: 'no login/password' });
        }
        const tokenResponse = yield axios_1.default.post('http://127.0.0.1:3000/generate-token', {
            login: login,
            password: password
        });
        const token = tokenResponse.data.token;
        const receiptResponse = yield axios_1.default.post('https://api.stage.vdpaybox.ru/api/receipt', outputData, {
            headers: {
                Authorization: `Bearer ${token}`
            }
        });
        res.json(receiptResponse.data);
    }
    catch (error) {
        console.error('Error processing request:', error);
        res.status(500).json({ error: 'Internal Server Error' });
    }
}));
app.listen(port, () => {
    console.log(`Server is running at http://localhost:${port}`);
});

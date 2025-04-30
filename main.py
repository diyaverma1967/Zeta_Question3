
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict
import uuid
import threading
import logging
from collections import defaultdict

class AccountKeys:
    ID = "id"
    BALANCE = "balance"
    CURRENCY = "currency"

class ErrorMessages:
    ACCOUNT_NOT_FOUND = "Account {account_id} not found"
    INVALID_AMOUNT = "Amount must be greater than 0"
    INSUFFICIENT_FUNDS = "Insufficient funds. Current balance: {current_balance}, Required: {required_amount}"

class LogOperations:
    ACCOUNT_CREATED = "ACCOUNT_CREATED"
    DEBIT_SUCCESS = "DEBIT_SUCCESS"
    CREDIT_SUCCESS = "CREDIT_SUCCESS"
    BALANCE_UPDATED = "BALANCE_UPDATED"
    ACCOUNT_DELETED = "ACCOUNT_DELETED"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Mock Account API")

accounts: Dict[str, Dict] = {
    "1001": {
        AccountKeys.ID: "1001",
        AccountKeys.BALANCE: 100000.0,
        AccountKeys.CURRENCY: "INR"
    },
    "1002": {
        AccountKeys.ID: "1002",
        AccountKeys.BALANCE: 50000.0,
        AccountKeys.CURRENCY: "INR"
    },
    "1003": {
        AccountKeys.ID: "1003",
        AccountKeys.BALANCE: 200.0,
        AccountKeys.CURRENCY: "INR"
    }
}
account_locks = defaultdict(threading.Lock)

class AccountCreate(BaseModel):
    balance: float
    currency: str = "INR"

class DebitCreditRequest(BaseModel):
    amount: float

def log_operation(operation: str, account_id: str, metadata: dict = None):
    """Standardized logging format"""
    message = f"{operation} - Account: {account_id}"
    if metadata:
        message += f" | Metadata: {metadata}"
    logger.info(message)

@app.post("/accounts", status_code=201)
async def create_account(account: AccountCreate):
    new_id = str(uuid.uuid4())
    with account_locks[new_id]:
        accounts[new_id] = {
            AccountKeys.ID: new_id,
            AccountKeys.BALANCE: account.balance,
            AccountKeys.CURRENCY: account.currency
        }
        log_operation(
            LogOperations.ACCOUNT_CREATED,
            new_id,
            {
                "initial_balance": account.balance,
                "currency": account.currency
            }
        )
    return accounts[new_id]

@app.get("/accounts/{account_id}")
async def get_account(account_id: str):
    if account_id not in accounts:
        logger.error(ErrorMessages.ACCOUNT_NOT_FOUND.format(account_id=account_id))
        raise HTTPException(404, ErrorMessages.ACCOUNT_NOT_FOUND.format(account_id=account_id))
    return accounts[account_id]

@app.post("/accounts/{account_id}/debit")
async def debit_account(account_id: str, request: DebitCreditRequest):
    logger.info(f"Debit request - Account: {account_id}, Amount: {request.amount}")
    
    if request.amount <= 0:
        logger.error(ErrorMessages.INVALID_AMOUNT)
        raise HTTPException(400, ErrorMessages.INVALID_AMOUNT)

    with account_locks[account_id]:
        if account_id not in accounts:
            logger.error(ErrorMessages.ACCOUNT_NOT_FOUND.format(account_id=account_id))
            raise HTTPException(404, ErrorMessages.ACCOUNT_NOT_FOUND.format(account_id=account_id))

        account = accounts[account_id]
        if account[AccountKeys.BALANCE] < request.amount:
            logger.error(ErrorMessages.INSUFFICIENT_FUNDS.format(
                current_balance=account[AccountKeys.BALANCE],
                required_amount=request.amount
            ))
            raise HTTPException(400, ErrorMessages.INSUFFICIENT_FUNDS.format(
                current_balance=account[AccountKeys.BALANCE],
                required_amount=request.amount
            ))

        account[AccountKeys.BALANCE] -= request.amount
        log_operation(
            LogOperations.DEBIT_SUCCESS,
            account_id,
            {
                "amount": request.amount,
                "new_balance": account[AccountKeys.BALANCE]
            }
        )
        return {
            "message": "Debit successful",
            "new_balance": account[AccountKeys.BALANCE]
        }

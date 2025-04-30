
#1###############1##########################1
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict
import uuid
import threading
import logging
from collections import defaultdict

# --------------------------
# Global Constants
# --------------------------
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

# --------------------------
# Configuration
# --------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Mock Account API")

# --------------------------
# In-Memory Database
# --------------------------
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

# --------------------------
# Models & Helpers
# --------------------------
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

# --------------------------
# API Endpoints
# --------------------------
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

# Similarly update credit, update_balance, and delete endpoints
# ... (remaining endpoints follow same pattern)
#2###############2##########################2
# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel
# from typing import Dict
# import uuid
# import threading
# import logging
# from collections import defaultdict

# # Configure logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# )
# logger = logging.getLogger(__name__)

# app = FastAPI(title="Mock Account API")

# # In-memory database with sample data
# accounts: Dict[str, Dict] = {
#     "1001": {"id": "1001", "balance": 100000.0, "currency": "INR"},
#     "1002": {"id": "1002", "balance": 50000.0, "currency": "INR"},
#     "1003": {"id": "1003", "balance": 200.0, "currency": "INR"}
# }
# account_locks = defaultdict(threading.Lock)

# class AccountCreate(BaseModel):
#     balance: float
#     currency: str = "INR"  # Default to INR

# class DebitCreditRequest(BaseModel):
#     amount: float

# # --------------------------
# # Helper Functions
# # --------------------------
# def log_operation(operation: str, account_id: str, metadata: dict = None):
#     """Log API operations with context"""
#     message = f"{operation} - Account: {account_id}"
#     if metadata:
#         message += f" | Metadata: {metadata}"
#     logger.info(message)

# # --------------------------
# # API Endpoints
# # --------------------------
# @app.post("/accounts", status_code=201)
# async def create_account(account: AccountCreate):
#     new_id = str(uuid.uuid4())
#     with account_locks[new_id]:
#         accounts[new_id] = {
#             "id": new_id,
#             "balance": account.balance,
#             "currency": account.currency
#         }
#         log_operation("ACCOUNT_CREATED", new_id, {
#             "initial_balance": account.balance,
#             "currency": account.currency
#         })
#     return accounts[new_id]

# @app.get("/accounts/{account_id}")
# async def get_account(account_id: str):
#     if account_id not in accounts:
#         logger.error(f"Account {account_id} not found")
#         raise HTTPException(404, f"Account {account_id} does not exist")
#     return accounts[account_id]

# @app.post("/accounts/{account_id}/debit")
# async def debit_account(account_id: str, request: DebitCreditRequest):
#     logger.info(f"Debit request for {account_id} - Amount: {request.amount}")
    
#     if request.amount <= 0:
#         logger.error(f"Invalid debit amount: {request.amount}")
#         raise HTTPException(400, "Debit amount must be greater than 0")

#     with account_locks[account_id]:
#         if account_id not in accounts:
#             logger.error(f"Debit failed - Account {account_id} not found")
#             raise HTTPException(404, f"Account {account_id} not found")

#         account = accounts[account_id]
#         if account["balance"] < request.amount:
#             logger.error(f"Insufficient funds in {account_id} | Current: {account['balance']} | Required: {request.amount}")
#             raise HTTPException(400, 
#                 f"Insufficient funds. Current balance: {account['balance']}, Required: {request.amount}"
#             )

#         account["balance"] -= request.amount
#         log_operation("DEBIT_SUCCESS", account_id, {
#             "amount": request.amount,
#             "new_balance": account["balance"]
#         })
#         return {"message": "Debit successful", "new_balance": account["balance"]}

# @app.post("/accounts/{account_id}/credit")
# async def credit_account(account_id: str, request: DebitCreditRequest):
#     logger.info(f"Credit request for {account_id} - Amount: {request.amount}")
    
#     if request.amount <= 0:
#         logger.error(f"Invalid credit amount: {request.amount}")
#         raise HTTPException(400, "Credit amount must be greater than 0")

#     with account_locks[account_id]:
#         if account_id not in accounts:
#             logger.error(f"Credit failed - Account {account_id} not found")
#             raise HTTPException(404, f"Account {account_id} not found")

#         account = accounts[account_id]
#         account["balance"] += request.amount
#         log_operation("CREDIT_SUCCESS", account_id, {
#             "amount": request.amount,
#             "new_balance": account["balance"]
#         })
#         return {"message": "Credit successful", "new_balance": account["balance"]}

# @app.put("/accounts/{account_id}")
# async def update_balance(account_id: str, new_balance: float):
#     logger.info(f"Balance update for {account_id} - New balance: {new_balance}")
    
#     with account_locks[account_id]:
#         if account_id not in accounts:
#             logger.error(f"Update failed - Account {account_id} not found")
#             raise HTTPException(404, f"Account {account_id} not found")

#         accounts[account_id]["balance"] = new_balance
#         log_operation("BALANCE_UPDATED", account_id, {"new_balance": new_balance})
#         return {"message": "Balance updated", "new_balance": new_balance}

# @app.delete("/accounts/{account_id}")
# async def delete_account(account_id: str):
#     logger.warning(f"Account deletion requested: {account_id}")
    
#     with account_locks[account_id]:
#         if account_id not in accounts:
#             logger.error(f"Delete failed - Account {account_id} not found")
#             raise HTTPException(404, f"Account {account_id} not found")

#         del accounts[account_id]
#         log_operation("ACCOUNT_DELETED", account_id)
#         return {"message": "Account deleted"}
#3###############3##########################3
# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel
# from typing import Dict
# import uuid
# import threading
# from collections import defaultdict

# app = FastAPI(title="Mock Account API")

# # In-memory database with sample data
# accounts: Dict[str, Dict] = {
#     "1001": {"id": "1001", "balance": 100000.0, "currency": "INR"},
#     "1002": {"id": "1002", "balance": 50000.0, "currency": "INR"},
#     "1003": {"id": "1003", "balance": 200.0, "currency": "INR"}
# }
# account_locks = defaultdict(threading.Lock)

# class AccountCreate(BaseModel):
#     balance: float
#     currency: str = "USD"

# class DebitCreditRequest(BaseModel):
#     amount: float

# # Create new account
# @app.post("/accounts", status_code=201)
# async def create_account(account: AccountCreate):
#     new_id = str(uuid.uuid4())
#     with account_locks[new_id]:
#         accounts[new_id] = {
#             "id": new_id,
#             "balance": account.balance,
#             "currency": account.currency
#         }
#     return accounts[new_id]

# # Get account balance
# @app.get("/accounts/{account_id}")
# async def get_account(account_id: str):
#     if account_id not in accounts:
#         raise HTTPException(404, "Account not found")
#     return accounts[account_id]

# # Debit account
# @app.post("/accounts/{account_id}/debit")
# async def debit_account(account_id: str, request: DebitCreditRequest):
#     if request.amount <= 0:
#         raise HTTPException(400, "Amount must be positive")
    
#     with account_locks[account_id]:
#         if account_id not in accounts:
#             raise HTTPException(404, "Account not found")
        
#         if accounts[account_id]["balance"] < request.amount:
#             raise HTTPException(400, "Insufficient funds")
        
#         accounts[account_id]["balance"] -= request.amount
#         return {"message": "Debit successful", "new_balance": accounts[account_id]["balance"]}

# # Credit account
# @app.post("/accounts/{account_id}/credit")
# async def credit_account(account_id: str, request: DebitCreditRequest):
#     if request.amount <= 0:
#         raise HTTPException(400, "Amount must be positive")
    
#     with account_locks[account_id]:
#         if account_id not in accounts:
#             raise HTTPException(404, "Account not found")
        
#         accounts[account_id]["balance"] += request.amount
#         return {"message": "Credit successful", "new_balance": accounts[account_id]["balance"]}

# # Update balance directly
# @app.put("/accounts/{account_id}")
# async def update_balance(account_id: str, new_balance: float):
#     if account_id not in accounts:
#         raise HTTPException(404, "Account not found")
    
#     with account_locks[account_id]:
#         accounts[account_id]["balance"] = new_balance
#         return {"message": "Balance updated", "new_balance": new_balance}

# # Delete account
# @app.delete("/accounts/{account_id}")
# async def delete_account(account_id: str):
#     if account_id not in accounts:
#         raise HTTPException(404, "Account not found")
    
#     with account_locks[account_id]:
#         del accounts[account_id]
#         return {"message": "Account deleted"}
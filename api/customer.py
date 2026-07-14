from fastapi import APIRouter, Depends, HTTPException
from api.schemas import TransactionSchema, TransferSchema
from api.dependencies import bank_instance, verify_customer_access

router = APIRouter(prefix="/customer", tags=["Customer Menu"])

@router.get("/{account_num}/details")
def view_account_details(account_num: int):
    account = bank_instance.get_account(account_num)
    return {"account_number": account.account_num, "customer_name": account.name, "balance": f"${account.balance}"}

@router.post("/{account_num}/deposit")
def process_deposit(payload: TransactionSchema, account_num: int):
    account = bank_instance.get_account(account_num)
    account.deposit(payload.amount)
    return {"message": f"Deposit processed. Current balance: ${account.balance}"}

@router.post("/{account_num}/withdraw")
def process_withdrawal(payload: TransactionSchema, account_num: int):
    account = bank_instance.get_account(account_num)
    old_balance = float(account.balance)
    account.withdraw(payload.amount)
    if old_balance == float(account.balance):
        raise HTTPException(status_code=400, detail="Withdrawal rejected.")
    return {"message": f"Withdrawal complete. Current balance: ${account.balance}"}

@router.post("/{account_num}/transfer")
def process_funds_transfer(payload: TransferSchema, account_num: int):
    if account_num == payload.dest_account_num:
        raise HTTPException(status_code=400, detail="Source and destination accounts cannot match.")
    bank_instance.transfer_funds(account_num, payload.dest_account_num, payload.amount)
    return {"message": f"Successfully transferred ${payload.amount:.2f} to Account {payload.dest_account_num}."}

@router.get("/{account_num}/transactions")
def view_transaction_history(account_num: int):
    account = bank_instance.get_account(account_num)
    return {"account_number": account_num, "history": account.transactions}
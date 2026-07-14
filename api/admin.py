from fastapi import APIRouter, HTTPException, status
from api.schemas import AccountCreateSchema
from api.dependencies import bank_instance

# Prefixes all routes in this file with /admin and tags them in /docs automatically
router = APIRouter(prefix="/admin", tags=["Admin Menu"])

@router.post("/accounts", status_code=status.HTTP_201_CREATED)
def create_new_account(payload: AccountCreateSchema):
    account_num = bank_instance._generate_unique_account_num()
    bank_instance.add_account(
        account_num = account_num,
        name=payload.name, 
        street_name=payload.street_name, zip_code=payload.zip_code, 
        start_balance=payload.start_balance
    )
    return {"message": f"Account for {payload.name} created successfully.", "account_number": account_num}

@router.delete("/accounts/{account_num}")
def terminate_account(account_num: str):
    account = bank_instance.get_account(account_num)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found.")
    bank_instance.delete_account(account_num)
    return {"message": f"Account {account_num} has been successfully closed."}

@router.get("/accounts")
def list_all_system_accounts():
    summary_list = [{
        "account_number": num, "owner": acc.name, "current_balance": f"${acc.balance}"
    } for num, acc in bank_instance.accounts.items()]
    return {"total_accounts": len(summary_list), "records": summary_list}
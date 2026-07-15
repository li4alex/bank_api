from datetime import datetime, timezone
import random
import uuid
from fastapi import APIRouter, HTTPException, status
from api.schemas import AccountCreateSchema
from database import account_collection, database

# Prefixes all routes in this file with /admin and tags them in /docs automatically
router = APIRouter(prefix="/admin", tags=["Admin Menu"])

async def _generate_unique_account_num() -> int:
    """Generates a unique 6-digit random account number in MongoDB."""
    while True:
        account_num = random.randint(100000, 999999)
        # Check if the generated ID already exists in MongoDB
        existing = await account_collection.find_one({"_id": account_num})
        if not existing:
            return account_num

@router.post("/accounts", status_code=status.HTTP_201_CREATED)
async def create_new_account(payload: AccountCreateSchema):
    account_num = await _generate_unique_account_num()
    
    # Construct the document following the Schema setup
    new_account_document = {
        "_id": account_num,
        "name": payload.name,
        "street_name": payload.street_name,
        "zip_code": payload.zip_code,
        "balance": float(payload.start_balance)
    }
    
    # Insert safely into MongoDB
    await account_collection.insert_one(new_account_document)

    initial_transaction = {
        "_id": str(uuid.uuid4()), # Generates a clean, unique transaction ID
        "account_id": account_num,
        "type": "DEPOSIT",
        "amount": float(payload.start_balance),
        "description": "Initial account opening balance deposit",
        "timestamp": datetime.now(timezone.utc)
    }
    await database.get_collection("transactions").insert_one(initial_transaction)

    return {
        "message": f"Account for {payload.name} created successfully.", 
        "account_number": account_num
    }

@router.delete("/accounts/{account_num}")
async def terminate_account(account_num: int):  # Type hinted to int to prevent string conversions
    # Attempt to delete the account by ID
    delete_result = await account_collection.delete_one({"_id": account_num})
    
    if delete_result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Account not found."
        )
        
    # Clean up associated transaction history for this account
    await database.get_collection("transactions").delete_many({"account_id": account_num})
        
    return {"message": f"Account {account_num} has been successfully closed."}

@router.get("/accounts")
async def list_all_system_accounts():
    summary_list = []
    
    # Retrieve all accounts in MongoDB using an async cursor
    cursor = account_collection.find()
    async for account in cursor:
        # 1. Safely extract balance (default to 0.0 if missing)
        raw_balance = account.get("balance", 0.0)
        
        # 2. Clean and convert the balance if it's accidentally a string
        if isinstance(raw_balance, str):
            # Strip out dollar signs or commas if any exist, then convert to float
            clean_balance = raw_balance.replace("$", "").replace(",", "").strip()
            try:
                balance_val = float(clean_balance)
            except ValueError:
                balance_val = 0.0
        else:
            balance_val = float(raw_balance)

        summary_list.append({
            "account_number": account["_id"],
            "owner": account.get("name", "Unknown"),
            "current_balance": f"${balance_val:.2f}"
        })
        
    return {
        "total_accounts": len(summary_list), 
        "records": summary_list
    }
from pydantic import BaseModel, Field

class AccountCreateSchema(BaseModel):
    name: str
    street_name: str
    zip_code: str
    start_balance: float = Field(0.0, ge=0.0)

class AccountModel(BaseModel):
    # Map MongoDB's string-converted structural IDs cleanly to responses
    account_num: int = Field(..., alias="_id")
    name: str
    street_name: str
    zip_code: str
    balance: float = 0.0

    class Config:
        populate_by_name = True

class TransactionSchema(BaseModel):
    amount: float = Field(..., gt=0.0)

class TransferSchema(BaseModel):
    dest_account_num: int
    amount: float = Field(..., gt=0.0)
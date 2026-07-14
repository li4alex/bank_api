from pydantic import BaseModel, Field

class AccountCreateSchema(BaseModel):
    account_num: int
    name: str
    street_name: str
    zip_code: str
    start_balance: float = Field(0.0, ge=0.0)

class TransactionSchema(BaseModel):
    amount: float = Field(..., gt=0.0)

class TransferSchema(BaseModel):
    dest_account_num: str
    amount: float = Field(..., gt=0.0)
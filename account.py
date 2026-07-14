class Account:
    """
    Represents a specific bank account. Handles financial transactions, 
    account details, and a transaction list for an individual account holder.
    """
    def __init__(self, account_num, name, street_name, zip_code, start_balance = 0):
        """Class properties are private for encapsulation."""
        self.__account_num = account_num
        self.__name = name
        self.__street_name = street_name
        self.__zip_code = zip_code
        self.__balance = float(start_balance)
        self.__transactions = [f"Account created with starting balance: ${start_balance:.2f}"]

    @property
    def account_num(self):
        """Getter property to access the account number safely."""
        return self.__account_num
    
    @property
    def name(self):
        """Getter property to access the account holder's name safely."""
        return self.__name

    @property
    def balance(self):
        """Getter property to access the balance safely as a formatted string."""
        return f"{self.__balance:.2f}"
    
    @property
    def transactions(self):
        """Getter property to access the transaction history safely."""
        return self.__transactions

    def details(self):
        """Prints all account details."""
        print(f"""
        Account Number: {self.__account_num}
        Customer Name: {self.__name}
        Street Address: {self.__street_name}
        Zip Code: {self.__zip_code}
        Balance: ${self.balance}
        """)

    def deposit(self, amount):
        """Adds a positive dollar amount to the account balance and records it."""
        if amount > 0:
            self.__balance += amount
            print(f"Deposited ${amount:.2f}. New balance is ${self.balance}.")
            self.__transactions.append(f"Deposited ${amount:.2f}. New balance: ${self.balance}")
        else:
            print("Deposit amount must be positive.")

    def withdraw(self, amount):
        """Deducts a dollar amount from the balance if funds are available and amount is valid."""
        if 0 < amount <= self.__balance:
            self.__balance -= amount
            print(f"Withdrew ${amount:.2f}. New balance is ${self.balance}.")
            self.__transactions.append(f"Withdrew ${amount:.2f}. New balance: ${self.balance}")
        else:
            print("Invalid withdrawal amount.")

    def transfer_destination(self, amount, source_account_num):
        """Adds a positive dollar amount to the account balance from a transfer and records it."""
        self.__balance += amount
        self.__transactions.append(f"Transferred ${amount:.2f} from {source_account_num}. New balance: ${self.balance}")

    def transfer_source(self, amount, destination_account_num):
        """Deducts a dollar amount from the balance if funds are available and amount is valid for a transfer."""
        if 0 < amount <= self.__balance:
            self.__balance -= amount
            self.__transactions.append(f"Transferred ${amount:.2f} to account number {destination_account_num}. New balance: ${self.balance}")
        else:
            print("Invalid transfer amount.")

    def get_transaction_history(self):
        """Prints out the transaction history for this account."""
        print("Transaction History:")
        for transaction in self.__transactions:
            print(transaction)
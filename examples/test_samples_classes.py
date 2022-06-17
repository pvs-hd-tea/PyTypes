import pytest


class Bank:
    def __init__(self):
        pass

    def create_new_account(self, starting_balance = 0):
        return BankAccount(self, starting_balance)


class BankAccount:
    def __init__(self, bank: Bank, base_balance: int = 0):
        self._balance = base_balance
        self.bank = bank

    def get_balance(self):
        return self._balance

    def deposit(self, additional_value):
        if additional_value < 0:
            raise ValueError
        self._balance += additional_value

    def withdraw(self, requested_value: int) -> int:
        if requested_value < 0 or self._balance < requested_value:
            raise ValueError

        self._balance -= requested_value
        return requested_value

    def withdraw_all(self) -> int:
        prev_balance = self._balance
        self._balance = 0
        return prev_balance


class Human:
    def __init__(self, name: str):
        if not isinstance(name, str):
            raise TypeError

        self.name = name


class Customer(Human):
    def __init__(self, name, account: BankAccount = None):
        super().__init__(name)
        self._account = account

    def has_positive_balance(self):
        return self._account.get_balance() > 0

    def update_balance_by(self, amount):
        if amount > 0:
            self._account.deposit(amount)
        else:
            self._account.withdraw(-amount)

    def have_accounts_in_same_bank(self, customer2) -> bool:
        if not isinstance(customer2, Customer):
            raise TypeError

        if not self._account or not customer2._account:
            return False
        return self._account.bank == customer2._account.bank


class Worker(Human):
    def __init__(self, name, bank):
        super().__init__(name)

        if bank is None:
            raise TypeError

        self.bank = bank

    def are_working_in_same_bank(self, worker2) -> bool:
        if not isinstance(worker2, Worker):
            raise TypeError()

        return self.bank == worker2.bank


# Since the sample files do not contain real unit tests and are only used to generate trace data files,
# non-unit tests are implemented which do not cover every possible case.
def test_all_potential_errors_in_this_file():
    with pytest.raises(ValueError):
        BankAccount(Bank()).deposit(-1)
        BankAccount(Bank()).withdraw(-1)
    with pytest.raises(TypeError):
        BankAccount(None)
        Human(None)
        Customer(None)
        Customer("a").have_accounts_in_same_bank(None)
        Worker(None)
        Worker("a").are_working_in_same_bank(None)


def test_1():
    bank1 = Bank()
    bank2 = Bank()

    account1 = bank1.create_new_account(100)
    account2 = bank2.create_new_account(0)

    worker1 = Worker("a", bank1)
    worker2 = Worker("b", bank1)

    assert worker1.are_working_in_same_bank(worker2)

    customer1 = Customer("a", account1)
    customer2 = Customer("b", account2)

    assert not customer1.have_accounts_in_same_bank(customer2)

    count = 0
    while customer1.has_positive_balance():
        customer1.update_balance_by(-10)
        count += 1

    assert count == 10








from eth_account.account import Account

class ETHAccount(object):
    def send_eth_to(self, to, amount):
        to.fallback(self, amount)

class Author(object):
    """
    The author of the book
    """
    balance = 0
    def __init__(self, eth_pk_bytes):
        self.account = Account.create(eth_pk_bytes)


class Book(object):
    def __init__(self, author):
        self.author = author


class BookStoreEthContract(object):
    """
    The contract receiving the rewards and selling the books
    """
    def __init__(self, book, author, price):
        self.book = book
        self.rewardee = author
        self.price = price

    def fallback(self, sender, amount):
        print("Received %s ETH from %s" % (amount, sender))


class Buyer(ETHAccount):
    """
    The person who pays for the book and receives content
    """
    balance = 100
    def __init__(self, eth_pk_bytes):
        self.account = Account.create(eth_pk_bytes)


author = Author(b"Author's ETH account")
book = Book(author)
first_buyer = Buyer(b"First Buyer's ETH account")
second_buyer = Buyer(b"Second Buyer's ETH account")
book_store = BookStoreEthContract(book, author, 10)
first_buyer.send_eth_to(book_store, 1)


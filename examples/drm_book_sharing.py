from eth_account.account import Account
from nucypher.characters.lawful import Alice, Bob, Ursula
from nucypher.network.middleware import RestMiddleware
from nucypher.data_sources import DataSource
from umbral.keys import UmbralPublicKey
import sys
import os
import binascii
import shutil
import maya
import datetime

teacher_rest_port = 3501
m = 2
n = 3
with open("examples-runtime-cruft/node-metadata-{}".format(teacher_rest_port), "r") as f:
    f.seek(0)
    teacher_bytes = binascii.unhexlify(f.read())
URSULA = Ursula.from_bytes(teacher_bytes, federated_only=True)
print("Will learn from {}".format(URSULA))
SHARED_CRUFTSPACE = "{}/examples-runtime-cruft".format(os.path.dirname(os.path.abspath(__file__)))
CRUFTSPACE = "{}/drm".format(SHARED_CRUFTSPACE)
CERTIFICATE_DIR = "{}/certs".format(CRUFTSPACE)
shutil.rmtree(CRUFTSPACE, ignore_errors=True)
os.mkdir(CRUFTSPACE)
os.mkdir(CERTIFICATE_DIR)
URSULA.save_certificate_to_disk(CERTIFICATE_DIR)

class ETHAccount(object):
    def send_eth_to(self, to, amount):
        return(to.fallback(self, amount))

class Author(object):
    """
    The author of the book
    """
    balance = 0
    def __init__(self, eth_pk_bytes, character):
        self.account = Account.create(eth_pk_bytes)
        self.character = character


class Book(object):
    def __init__(self, author):
        self.author = author
        self.content = b"PlainText of the book"
        self.label = b"book"


class BookStoreEthContract(object):
    """
    The contract receiving the rewards and selling the books
    """
    def __init__(self, book, author, price, purchase_event_hook):
        self.book = book
        self.rewardee = author
        self.price = price
        self.purchase_event_hook = purchase_event_hook

    def fallback(self, sender, amount):
        print("Received %s ETH from %s" % (amount, sender.account.address))
        if amount == self.price:
            sender.balance -= amount
            self.rewardee.balance += amount
            return(self.purchase_event_hook(sender))

class BookStoreDelivery(object):
    def __init__(self, book):
        self.book = book
        self.author = book.author

    def deliver_purchase(self, to):
        policy_end_datetime = maya.now() + datetime.timedelta(days=5)
        policy = author.character.grant(first_buyer.character, self.book.label, m=m, n=n,
                             expiration=policy_end_datetime)
        author_pubkey = bytes(self.author.character.stamp)
        data_source = DataSource(policy_pubkey_enc=policy.public_key)
        message_kit, _signature = data_source.encapsulate_single_message(self.book.content)
        data_source_public_key = bytes(data_source.stamp)
        return (author_pubkey, policy.public_key, data_source_public_key, self.book.label, message_kit)




class Buyer(ETHAccount):
    """
    The person who pays for the book and receives content
    """
    balance = 100
    def __init__(self, eth_pk_bytes, character):
        self.account = Account.create(eth_pk_bytes)
        self.character = character


author = Author(b"Author's ETH account", Alice(network_middleware=RestMiddleware(),
              known_nodes=(URSULA,),
              federated_only=True,
              known_certificates_dir=CERTIFICATE_DIR,))
author.character.start_learning_loop(now=True)

book = Book(author)
first_buyer = Buyer(b"First Buyer's ETH account", Bob(known_nodes=(URSULA,),
          federated_only=True,
          known_certificates_dir=CERTIFICATE_DIR))
book_store_delivery = BookStoreDelivery(book)
book_store_contract = BookStoreEthContract(book, author, 10, book_store_delivery.deliver_purchase)
author_public_key, policy_public_key, data_source_public_key, label, kit = first_buyer.send_eth_to(book_store_contract, 10)
first_buyer.character.join_policy(label,  # The label - he needs to know what data he's after.
                bytes(author.character.stamp),  # To verify the signature, he'll need Alice's public key.
                # He can also bootstrap himself onto the network more quickly
                # by providing a list of known nodes at this time.
                node_list=[("localhost", 3601)]
                )
datasource_as_understood_by_bob = DataSource.from_public_keys(
        policy_public_key=policy_public_key,
        datasource_public_key=data_source_public_key,
        label=label
    )
alice_pubkey_restored_from_ancient_scroll = UmbralPublicKey.from_bytes(author_public_key)
delivered_cleartexts = first_buyer.character.retrieve(message_kit=kit,
                                        data_source=datasource_as_understood_by_bob,
                                        alice_verifying_key=alice_pubkey_restored_from_ancient_scroll)
print(delivered_cleartexts)



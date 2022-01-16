import sys
from enum import Enum, IntEnum
import json
import sys


def get2Pow(x):
    powers = []
    i = 1
    while i <= x:
        if i & x:
            powers.append(i)
        i <<= 1
    return powers


class Type(IntEnum):
    INVALID = 0
    EMPTY = 1 << 1
    CHECK = 1 << 2
    OTHER_TX_CHECK = 1 << 3  # TX_CHECK, CHECK
    EXTERNAL_CHECK = 1 << 4  # CHECK
    EXECUTION = 1 << 5
    TX_CHECK = 1 << 6  # CHECK


type_crp = {
    "CHECK": Type.CHECK,
    "TX_CHECK": Type.TX_CHECK,
    "OTHER_TX_CHECK": Type.OTHER_TX_CHECK,
    "EXTERNAL_CHECK": Type.EXTERNAL_CHECK,
    "EXECUTION": Type.EXECUTION
}


class BinIdxDict(dict):
    def __init__(self, d):
        super().__init__()
        self.d = d

    def __get__(self, item):
        to_get = get2Pow(item)
        res = [self.d[i] for i in to_get]
        if len(res) == 1:
            return res[0]
        print(f"Warning: BinIdxDict return {len(res)} different results")
        return res  # Is not supposed to happen


class SmartContract:
    requirements = BinIdxDict({
        Type.OTHER_TX_CHECK: ['recipient', 'sender', 'amount', 'token'],
    })

    def __init__(self, blockchain, Txs, raw_contract):
        # For contract execution purpose
        self.blockchain = blockchain
        self.Txs = Txs
        # Content
        self.raw_contract = raw_contract
        if self.contractType == Type.INVALID:
            print("Invalid contract sent to SmartContract class __init__()", file=sys.stderr)
        if self.contractType != Type.EMPTY and self.contractType != Type.INVALID:
            self.smartContract = json.load(raw_contract)

    def run(self):
        if self.contractType == Type.INVALID:
            print('ERROR This contract should not be run', file=sys.stderr)
        if self.contractType & Type.EMPTY:
            return True
        if self.contractType & Type.EXECUTION:
            return self.execute()
        if self.contractType & Type.CHECK:
            return self.check()
        return False

    def checkTXs(self):
        for waitingTx in self.Txs:  # Search the corresponding transaction
            if all([waitingTx[i] == self.smartContract[i] for i in SmartContract.requirements[self.contractType]])\
               and waitingTx['sc'].run():
                return True

    def check(self):
        if self.contractType & Type.TX_CHECK:
            return self.checkTXs()
        else:
            print("Not implemented")
        return False

    def execute(self):
        raise NotImplementedError
        # return True

    def __str__(self):
        return self.raw_contract or ""

    @property
    def __dict__(self):
        return self.raw_contract or {}

    @property
    def contractType(self):
        """
        check if smart contract is valid

        ======= TEMPLATE =======
            type: str that match one of the type
            IF TYPE IS <CHECK>
                IF TYPE IS <OTHER_TX_CHECK>
                    recipient: str
                    sender: str
                    amount: double
                    token: str
        ========================

        :return: True if contract is valid, false otherwise
        """

        if self.raw_contract is None:
            return Type.EMPTY
        try:
            result = json.load(self.raw_contract)
        except json.decoder.JSONDecodeError:
            return Type.INVALID
        if 'type' not in result:
            return Type.INVALID
        if result['type'].upper().replace(' ', '_') == 'OTHER_TX_CHECK':
            type_ = Type.OTHER_TX_CHECK | Type.CHECK | Type.TX_CHECK
            if any([i not in result for i in SmartContract.requirements[type_]]):  # Check if all requirements fields are present
                return Type.INVALID
            return type_

        return Type.INVALID

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

    def __getitem__(self, item):
        to_get = get2Pow(item)
        res = [self.d[i] for i in to_get if i in self.d]
        if len(res) == 1:
            return res[0]
        print(f"Warning: BinIdxDict return {len(res)} different results")
        return res  # Is not supposed to happen

    def __str__(self):
        return self.d.__str__()

    def __repr__(self):
        return self.__str__()


class SmartContract:
    requirements = BinIdxDict({
        Type.OTHER_TX_CHECK: ['recipient', 'sender', 'amount', 'token'],
    })

    def __init__(self, contract, related_tx_id):
        self.txs = None
        # Content
        self.smartContract = contract
        if self.contractType == Type.INVALID:
            print("Invalid contract sent to SmartContract class __init__()", file=sys.stderr)
        self.related_tx_id = related_tx_id

    def run(self, txs, prevent_self_check_id=None):  # TODO add timeout to transaction never confirmed
        self.txs = txs
        if self.contractType == Type.INVALID:
            print('ERROR This contract should not be run', file=sys.stderr)
        if self.contractType & Type.EMPTY:
            return True
        if self.contractType & Type.EXECUTION:
            return self.execute()
        if self.contractType & Type.CHECK:
            return self.check(prevent_self_check_id)
        return False

    def checkTXs(self, prevent_self_check_id):  # TODO this system might validate multiple transactions wanting the same thing although there is only one of "the other thing"
        for tx in self.txs.all(except_id=self.related_tx_id):  # Search the corresponding transaction
            if all([str(tx[i]) == str(self.smartContract[i]) for i in SmartContract.requirements[self.contractType]]) \
                    and (prevent_self_check_id == tx.smart_contract.related_tx_id or tx.smart_contract.run(txs=self.txs, prevent_self_check_id=self.related_tx_id)):
                # FIXME this check may validate with transaction not used in this block because of timestamp
                return True
        return False

    def check(self, prevent_self_check_id):
        if self.contractType & Type.TX_CHECK:
            return self.checkTXs(prevent_self_check_id)
        else:
            print("Not implemented")
        return False

    def execute(self):
        raise NotImplementedError
        # return True

    def __str__(self):
        return self.smartContract.__str__() if self.smartContract is not None else ""

    def __dict__(self):
        return self.smartContract or {}

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

        # print("parse contract", self.smartContract)
        if self.smartContract is None or self.smartContract == {}:
            return Type.EMPTY
        if 'type' not in self.smartContract:
            return Type.INVALID
        if self.smartContract['type'].upper().replace(' ', '_') == 'OTHER_TX_CHECK':
            type_ = Type.OTHER_TX_CHECK | Type.CHECK | Type.TX_CHECK
            # print('type_', type_)
            # print("SmartContract.requirements[type_]", SmartContract.requirements[type_])
            if any([i not in self.smartContract for i in SmartContract.requirements[type_]]):  # Check if all requirements fields are present
                return Type.INVALID
            return type_

        return Type.INVALID

    @classmethod
    def from_dict(cls, dictionary):
        sc = cls(contract=dictionary['contract'],
                 related_tx_id=dictionary['related_tx_id']
                 )
        if sc.contractType == Type.INVALID:
            return None, 'Invalid contract type'
        return sc






import sys
from enum import Enum, IntEnum
import json
import sys
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


if __name__ != "__main__":
    gunicorn_logger = logging.getLogger("gunicorn.error")
    gunicorn_logger.setLevel(logging.DEBUG)
    logger.handlers = gunicorn_logger.handlers
    logger.setLevel(gunicorn_logger.level)


def get_2_pow(x):
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
    "EXECUTION": Type.EXECUTION,
}


class BinIdxDict(dict):
    def __init__(self, d):
        super().__init__()
        self.d = d

    def __getitem__(self, item):
        to_get = get_2_pow(item)
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
    requirements = BinIdxDict(
        {
            Type.OTHER_TX_CHECK: ["recipient", "sender", "amount", "token"],
        }
    )

    def __init__(self, contract, related_tx):
        self.txs = None
        # Content
        self.smartContract = contract
        if self.contract_type == Type.INVALID:
            print(
                "Invalid contract sent to SmartContract class __init__()",
                file=sys.stderr,
            )
        self.related_tx = related_tx
        self.related_tx_id = related_tx.id
        self._is_validated = False

    def run(self, txs, prevent_self_check_id=None) -> bool:
        """
        Run the smart contract
        :param txs: Transactions to check against the smart contract
        :param prevent_self_check_id: Transaction id not to check
        :return: True if the smart contract is validated else False
        """
        self.txs = txs
        if not self.related_tx.does_not_violate_the_portfolio():
            return False
        if self.contract_type == Type.INVALID:
            print(
                'ERROR This contract should not be run because it has type "INVALID"',
                file=sys.stderr,
            )
        if self.contract_type & Type.EMPTY:
            return True
        if self.contract_type & Type.EXECUTION:
            return self.__execute()
        if self.contract_type & Type.CHECK:
            return self.__check(prevent_self_check_id)
        return False

    def __does_validate(self, tx, prevent_self_check_id):
        """
        Check if fields match
        Then check you back check the same transactions that requested the check, or the smart contract is valid
        :param tx:
        :param prevent_self_check_id:
        :return:
        """
        return (
            not tx.is_used_to_validate_smart_contract()
            and all(
                [
                    str(tx[i]) == str(self.smartContract[i])
                    for i in SmartContract.requirements[self.contract_type]
                ]
            )
            and (
                prevent_self_check_id == tx.smart_contract.related_tx_id
                or tx.smart_contract.run(
                    txs=self.txs, prevent_self_check_id=self.related_tx_id
                )
            )
        )

    def __check_txs(self, prevent_self_check_id: list) -> bool:
        """
        For type: Type.TX_CHECK
        Check if one of the transactions satisfies the smart contract requirements
        :param prevent_self_check_id: transaction id not to check
        :return: True if one of the transactions satisfies the smart contract requirements else False
        """
        for tx in self.txs.all(
            except_id=self.related_tx_id
        ):  # Search the corresponding transaction
            if self.__does_validate(tx, prevent_self_check_id):
                tx.use_to_validate_smart_contract()
                self._is_validated = True
                return True
        return False

    def reset_state(self):
        """ Reset the state of the smart contract. i.e. set is_validated to False """
        self._is_validated = False

    def is_validated(self):
        """ Check if the smart contract is validated """
        return self._is_validated

    def __check(self, prevent_self_check_id):
        """
        For contract type: Type.CHECK
        :param prevent_self_check_id:
        :return:
        """
        if self.contract_type & Type.TX_CHECK:
            return self.__check_txs(prevent_self_check_id)
        else:
            logger.warning("Not implemented")
        return False

    def __execute(self):
        """
        For contract type: Type.EXECUTION
        :return:
        """
        raise NotImplementedError
        # return True

    def __str__(self):
        return self.smartContract.__str__() if self.smartContract is not None else ""

    def __dict__(self):
        return self.smartContract or {}

    @property
    def contract_type(self) -> Type:
        """
        Assign a type to the contract if it is valid

        :return: Type of the smart contract
        """

        # print("parse contract", self.smartContract)
        if self.smartContract is None or self.smartContract == {}:
            return Type.EMPTY
        if "type" not in self.smartContract:
            return Type.INVALID
        if self.smartContract["type"].upper().replace(" ", "_") == "OTHER_TX_CHECK":
            """
            IF TYPE IS <CHECK>
                IF TYPE IS <OTHER_TX_CHECK>
                    recipient: str
                    sender: str
                    amount: double
                    token: str
            """
            type_ = Type.OTHER_TX_CHECK | Type.CHECK | Type.TX_CHECK
            if any(
                [i not in self.smartContract for i in SmartContract.requirements[type_]]
            ):  # Check if all requirements fields are present
                return Type.INVALID
            return type_

        return Type.INVALID

    # @classmethod
    # def from_dict(cls, dictionary):
    #     sc = cls(
    #         contract=dictionary['contract'],
    #         related_tx=None,  # FIXME
    #     )
    #     if sc.contract_type == Type.INVALID:
    #         return None, 'Invalid contract type'
    #     return sc

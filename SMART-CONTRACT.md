

## OTHER_TX_CHECK
types: TX_CHECK - CHECK

#### Security

To validate Smart Contract you need to match the following requirements

- Transaction not already used to validate another smart contract
    ````python
    not tx.is_used_to_validate_smart_contract() and
    ````
- Transaction details match what smart contract needs
    ````python
    all([str(tx[i]) == str(self.smartContract[i]) for i in SmartContract.requirements[self.contractType]]) and
    ````
- If the transaction used to validate the smart contract also contains a smart contract. This one has to run:
    1. The transaction used to validate the smart contract contains the smart contract that called the validation of the current smart contract
        ````python
        (prevent_self_check_id == tx.smart_contract.related_tx_id or
        ````
    2. The related smart contract has to run
        ````python
        tx.smart_contract.run(txs=self.txs, prevent_self_check_id=self.related_tx_id))
        ````
- Transaction related to smart contract has to be valid
    ````python
    not self.related_tx.does_not_violate_the_portfolio()
    ````
<br>
<br>
<br>
If 2 transactions relies on each other such as 

TX A :
````json
{
    "sender": "{{PBKEY_BERNARD}}",
    "recipient": "{{PBKEY_HENRI}}",
    "amount": 50,
    "private_key": "{{PVKEY_BERNARD}}",
    "token": "snowy",
    "smart_contract": {
        "type": "OTHER_TX_CHECK",
        "recipient": "{{PBKEY_BERNARD}}",
        "sender": "{{PBKEY_HENRI}}",
        "amount": 10,
        "token": "snowy"
    }
}
````
TX B : 
````json
{
    "sender": "{{PBKEY_HENRI}}",
    "recipient": "{{PBKEY_BERNARD}}",
    "amount": 10,
    "private_key": "{{PVKEY_HENRI}}",
    "token": "snowy",
    "smart_contract": {
        "type": "OTHER_TX_CHECK",
        "recipient": "{{PBKEY_HENRI}}",
        "sender": "{{PBKEY_BERNARD}}",
        "amount": 50,
        "token": "snowy"
    }
}
````

We can write these dependencies as *A<->B* (*A ->(needs to validate) B*) and (*B ->(needs to validate) A*)
Although we can imagine that *A->C* and *C->D* <br>
- If D does not exist
  - then C can't be validated
  - So we need to ensure that A is validated by B and not by C
    - Otherwise A would validate C and be used. such that B can't be validated. Later A won't validated because C is not. Therefore nothing would be validated while A and B could

To ensure this not happens, the code is organized this way :
1. Try to validate A
2. Find B transaction
3. Try to Validate B
4. Put transaction A as priority to validate B



## EXECUTION

*TODO*











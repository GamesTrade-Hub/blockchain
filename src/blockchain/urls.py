from src.blockchain.tcp_protocol_routes import *


routes = {
    "/get_new_private_key": GetNewPrivateKey,
    "/get_new_public_key_casual": GetNewPublicKeyCasual,
    "/get_new_public_key_admin": GetNewPublicKeyAdmin,
    "/get_new_public_key_miner": GetNewPublicKeyMiner,
    "/get_node_public_key": GetNodePublicKey,
    "/start": Start,
    "/status": Status,
    "/transactions/new": TransactionNew,
    "/create_nft": CreateNFT,
    "/create_item": CreateItem,
    "/transaction/add": TransactionAdd,
    "/chain": Chain,
    "/ping": Ping,
    "/nodes/register": NodesRegister,
    "/nodes/unregister": NodesUnregister,
    "/get_type": GetType,
    "/nodes/resolve": NodesResolve,
    "/nodes/list": NodesList,
    "/block/new": BlockNew,
    "/chain_found": ChainFound,
    "/get_balance": GetBalance,
}
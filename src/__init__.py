# TODO reward for fastest miner
# TODO Fix the trouble that can happen if two miners finish at the same time
#   - Maybe by choosing the chain the most popular among all others
# TODO check transactions real validity when a node propose the same chain as yours with one new block (meaning he found it faster that you did)
# TODO fix api return code to make them match the good practices
# TODO when a node is removed it should send a signal to others
# TODO POA
# TODO GUI configuration
# TODO Other smart contract types
# TODO Setup update without loosing current state (dump saved transactions?)
#   - update nodes one after the other, at each node restart, one another send him the current transactions to confirm
#   - node dump its state, update, restart, reload (can be bad if the update takes some time)

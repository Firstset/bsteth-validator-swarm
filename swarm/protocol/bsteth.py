from .csm import CSM
from .. import util
import os
from web3 import Web3, exceptions
from ..connection.connection import NodeWSConnection
from ..exception import CSMSubmissionException, KeyExistsException, TransactionRejectedException, ExecutionLayerRPCException
from ..local_sign import local_sign


class Bsteth(CSM):
    def __init__(self, config: dict) -> None:
        # Call parent's __init__ with bsteth config
        super().__init__(config)
        
        # Add BstETH contract to existing contracts
        self.contracts['BstETH'] = {
            'abi': util.load_json_file(os.path.join(os.getcwd(), 'abis', 'bsteth', 'BstETH.json')),
            'address': config['bsteth']
        }
    
    async def submit_keys_local_sign(self, deposit_data: dict) -> None:

        if self.have_repeated_keys(deposit_data):
            print("Error: one or more keys are already uploaded to the protocol")
            raise KeyExistsException()

        bond = await self.get_eth_bond(len(deposit_data))
        
        print('Submitting keys....')

        async with NodeWSConnection(self.rpc) as con:
            contract = con.get_contract(**self.contracts['BstETH'])
            pubkeys = [Web3.to_bytes(hexstr=(x['pubkey'])) for x in deposit_data]
            pubkeys_bytes = b''.join(pubkeys)
            sigs = [Web3.to_bytes(hexstr=(x['signature'])) for x in deposit_data]
            sigs_bytes = b''.join(sigs)
            if self.node_operator_id == None:
                print('Creating node operator id...')
                if len(deposit_data) > 1:
                    raise ValueError("Only one validator is supported for BstETH")
                
                function = contract.functions['createNodeOperatorId']
                contract_call = function(
                    pubkeys_bytes,
                    sigs_bytes
                )
                value = hex(bond)
            else:
                print('Bonding validators...')
                function = contract.functions['bondValidators']
                contract_call = function(
                    len(deposit_data), 
                    pubkeys_bytes,
                    sigs_bytes
                )
                value = 0
            tx = {'value': value, 'from': self.eth_base}
            try:
                complete_tx = await contract_call.build_transaction(tx)
                resp = await local_sign(8000, complete_tx)
                print('Tx hash: ', resp)

            except exceptions.ContractCustomError as e:
                print(e.data)
                print('Error returnerd by contract call', e.message)
                raise CSMSubmissionException(e)
            except TransactionRejectedException as e:
                print('Transaction was rejected by signer.')
                raise CSMSubmissionException(e)
        
        print('Uploaded keys and sent ETH to BstETH sucessfully')

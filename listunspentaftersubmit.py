from test_framework.mininode import *
from test_framework.script import *
from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import *
from test_framework.blocktools import create_confirmed_utxos

class ListUnspentAfterSubmitTest(BitcoinTestFramework):

    def set_test_params(self):
        self.num_nodes = 2
        self.setup_clean_chain = False

    def setup_network(self):
        # Need a bit of extra time for the nodes to start up for this test
        self.add_nodes(self.num_nodes, timewait=600)
        self.start_nodes()
        # Leave them unconnected, we'll use submitblock directly in this test

    def sync_blocks(self, block_hashes):
        node1_utxo_hash = self.nodes[1].gettxoutsetinfo()['hash_serialized']

        # Retrieve all the blocks from node1
        blocks = []
        for block_hash in block_hashes:
            blocks.append(
                [block_hash, self.nodes[1].getblock(block_hash, False)])

        self.log.debug("Syncing blocks to node 0")
        for bi, (block_hash, block) in enumerate(blocks):
            self.log.debug("submitting block %s", block_hash)
            self.nodes[0].submitblock(block)


    def run_test(self):

        node1_initial_height = self.nodes[1].getblockcount()
        node1_initial_uxto_set_hash = self.nodes[1].gettxoutsetinfo()['hash_serialized']

        node0_initial_height = self.nodes[0].getblockcount()
        node0_initial_uxto_set_hash = self.nodes[0].gettxoutsetinfo()['hash_serialized']

        self.log.debug(f'node1 initial height: {node1_initial_height}, initial utxo set hash: {node1_initial_uxto_set_hash}')
        self.log.debug(f'node1 initial height: {node0_initial_height}, initial utxo set hash: {node0_initial_uxto_set_hash}')

        assert node1_initial_height == node0_initial_height
        assert node1_initial_uxto_set_hash == node0_initial_uxto_set_hash

        utxo_list = create_confirmed_utxos(self.nodes[1], 5000)
        self.log.info("Prepped %d utxo entries", len(utxo_list))
        node1_utxo_set_hash = self.nodes[1].gettxoutsetinfo()['hash_serialized']

        block_hashes_to_sync = []
        for height in range(node1_initial_height + 1, self.nodes[1].getblockcount() + 1):
            block_hashes_to_sync.append(self.nodes[1].getblockhash(height))

        self.log.debug("Syncing %d blocks with other nodes", len(block_hashes_to_sync))

        self.sync_blocks(block_hashes_to_sync)

        node0_unspent_count = len(self.nodes[0].listunspent())
        node1_unspent_count = len(self.nodes[1].listunspent())


        assert self.nodes[0].gettxoutsetinfo()['txouts'] == self.nodes[1].gettxoutsetinfo()['txouts']
        assert self.nodes[0].gettxoutsetinfo()['hash_serialized'] == self.nodes[1].gettxoutsetinfo()['hash_serialized']

        self.log.debug(f'node0 unspent count:{node0_unspent_count}')
        self.log.debug(f'node1 unspent count:{node1_unspent_count}')

        assert node0_unspent_count == node1_unspent_count





if __name__ == '__main__':
    pass
    #ListUnspentAfterSubmitTest().main()

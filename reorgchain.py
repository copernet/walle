#!/usr/bin/env python3
# Copyright (c) 2014-2016 The Bitcoin Core developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

# Exercise the getchaintips API.  We introduce a network split, work
# on chains of different lengths, and join the network together again.
# This gives us two tips, verify that it works.

from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import (
    assert_equal,
    connect_nodes,
    disconnect_nodes,
)


class ActiveBestChainTest(BitcoinTestFramework):
    def set_test_params(self):
        self.num_nodes = 2
        self.setup_clean_chain = True

    def run_test(self):
        self.nodes[0].generate(100)
        connect_nodes(self.nodes[0], 1)
        self.sync_all()
        disconnect_nodes(self.nodes[0], 1)

        block_hash = self.nodes[0].generate(1)[0]
        tx_hash = self.nodes[0].getblock(block_hash)['tx'][0]
        self.nodes[0].generate(100)
        self.log.info("#1. node0 create tx cost coinbase from 101 height  ======")
        inputs = [{'txid': tx_hash, 'vout': 0}]
        outputs = {"mhVHh1nLNsRooRdL5oHzrXV7troxRi9xGP": 3.33}
        rawtx = self.nodes[0].createrawtransaction(inputs, outputs)
        sigedtx = self.nodes[0].signrawtransaction(rawtx)
        self.nodes[0].sendrawtransaction(sigedtx['hex'])
        self.log.info("#2. node0 generate block of 202 height            =======")
        self.nodes[0].generate(1)

        block_hash = self.nodes[1].generate(1)[0]
        tx_hash = self.nodes[1].getblock(block_hash)['tx'][0]
        self.nodes[1].generate(100)
        self.log.info("#3. node1 create tx cost coinbase from 101 height =======")
        inputs = [{'txid': tx_hash, 'vout': 0}]
        outputs = {"mhVHh1nLNsRooRdL5oHzrXV7troxRi9xGP": 3.0}
        rawtx = self.nodes[1].createrawtransaction(inputs, outputs)
        sigedtx = self.nodes[1].signrawtransaction(rawtx)
        self.nodes[1].sendrawtransaction(sigedtx['hex'])
        self.log.info("#4. node0 generate block of height 202-203        ========")
        self.nodes[1].generate(2)

        block_node1 = self.nodes[1].getbestblockhash()
        txout_node1 = self.nodes[1].gettxoutsetinfo()
        work_node1 = self.nodes[1].getblockheader(block_node1)

        self.log.info("#5. connect node0 and node1,wait node0 reorg to 203======")
        connect_nodes(self.nodes[0], 1)
        self.sync_all()

        # check chain status
        block_node0 = self.nodes[0].getblockhash(203)
        assert_equal(block_node0, block_node1)
        txout_node0 = self.nodes[0].gettxoutsetinfo()
        assert_equal(txout_node0['height'], txout_node1['height'])
        assert_equal(txout_node0['bestblock'], txout_node1['bestblock'])
        assert_equal(txout_node0['transactions'], txout_node1['transactions'])
        assert_equal(txout_node0['txouts'], txout_node1['txouts'])
        assert_equal(txout_node0['total_amount'], txout_node1['total_amount'])
        work_node0 = self.nodes[1].getblockheader(block_node0)
        assert_equal(work_node0, work_node1)


if __name__ == '__main__':
    ActiveBestChainTest().main()

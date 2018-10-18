#!/usr/bin/env python3
# Copyright (c) 2017 The Bitcoin Core developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

# Avoid wildcard * imports if possible
import time

from test_framework.blocktools import (create_coinbase, create_transaction, create_block_with_txns)
from test_framework.mininode import (
    NetworkThread,
    NodeConn,
    NodeConnCB,
    msg_block,
)
from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import (
    p2p_port,
)


class ExampleTest(BitcoinTestFramework):
    def set_test_params(self):
        self.setup_clean_chain = True
        self.num_nodes = 1

    def setup_network(self):
        self.setup_nodes()

    def run_test(self):
        node0 = NodeConnCB()
        node0.add_connection(NodeConn('127.0.0.1', p2p_port(0), self.nodes[0], node0))

        NetworkThread().start()
        node0.wait_for_verack()

        self.log.info("#1. generate 1 block by node0")
        self.nodes[0].generate(nblocks=1)
        self.tip = int(self.nodes[0].getbestblockhash(), 16)
        self.block_time = self.nodes[0].getblock(self.nodes[0].getbestblockhash())['time'] + 1

        self.height = 1
        self.coinbase_txs = []

        self.log.info("#2. create 100 blocks and send to node0")
        for i in range(100):
            coinbase_tx = create_coinbase(self.height)
            self.coinbase_txs.append(coinbase_tx)
            self.create_block_and_send([coinbase_tx], node0)

        self.nodes[0].waitforblockheight(101)

        self.fork_point_hash = self.tip
        self.fork_height = self.height

        self.log.info("#3. create one fork chain with one block")
        for i in range(1):
            input_txn = self.coinbase_txs[i]
            outputValue = int(input_txn.vout[0].nValue / 5)
            txn = create_transaction(input_txn, 0, b'', outputValue)

            self.create_block_and_send([create_coinbase(self.height), txn], node0)

        self.nodes[0].waitforblockheight(102)

        self.log.info("#4. create another fork chain with two blocks")
        self.tip = self.fork_point_hash
        self.height = self.fork_height
        for i in range(1):
            input_txn = self.coinbase_txs[i]
            outputValue = int(input_txn.vout[0].nValue / 5)
            txn = create_transaction(input_txn, 0, b'', outputValue)

            self.create_block_and_send([create_coinbase(self.height), txn], node0)

        self.log.info("#5. expect node0 switch to new chain")
        time.sleep(20)
        self.nodes[0].waitforblockheight(102)

    def create_block_and_send(self, txs, node):
        block = create_block_with_txns(self.tip, txs, self.block_time)
        block.solve()
        node.send_message(msg_block(block))
        self.tip = block.sha256
        self.log.info("height %d, hash: %s", self.height, self.tip)
        self.block_time += 1
        self.height += 1

if __name__ == '__main__':
    ExampleTest().main()

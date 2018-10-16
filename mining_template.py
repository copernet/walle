#!/usr/bin/env python3
# Copyright (c) 2018-2019 The Copernicus developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
"""Test mining RPCs

- getblocktemplate template mode
- submitblock"""

from binascii import b2a_hex
import copy

from test_framework.blocktools import create_coinbase
from test_framework.test_framework import BitcoinTestFramework
from test_framework.mininode import CBlock
from test_framework.util import *


def b2x(b):
    return b2a_hex(b).decode('ascii')

class MiningTest(BitcoinTestFramework):
    def set_test_params(self):
        self.num_nodes = 2
        self.setup_clean_chain = False

    def run_test(self):
        node = self.nodes[0]
        # Mine a block to leave initial block download
        node.generate(1)

        prevblk = node.getblock(node.getbestblockhash())

        tmpl = node.getblocktemplate()
        self.log.info("getblocktemplate: Test capability advertised")

        assert 'rules' in tmpl
        assert 'vbavailable' in tmpl
        assert 'transactions' in tmpl
        assert 'coinbaseaux' in tmpl
        assert 'coinbasetxn' not in tmpl
        assert 'mutable' in tmpl
        assert isinstance(tmpl['version'], int)
        assert isinstance(tmpl['curtime'], int)
        assert isinstance(tmpl['vbrequired'], int)
        assert isinstance(tmpl['coinbasevalue'], int)
        assert_is_hex_string(tmpl['bits'])
        assert_is_hash_string(tmpl['target'])
        assert_is_hash_string(tmpl['previousblockhash'])
        assert_equal(tmpl['sizelimit'], 32000000)
        assert_equal(tmpl['sigoplimit'], 640000)
        assert_equal(tmpl['mintime'], prevblk['mediantime'] + 1)
        assert_equal(tmpl['height'], prevblk['height'] + 1)
        assert_equal(tmpl['noncerange'], "00000000ffffffff")

        coinbase_tx = create_coinbase(height=int(tmpl["height"]) + 1)
        # sequence numbers must not be max for nLockTime to have effect
        coinbase_tx.vin[0].nSequence = 2 ** 32 - 2
        coinbase_tx.rehash()

        block = CBlock()
        block.nVersion = tmpl["version"]
        block.hashPrevBlock = int(tmpl["previousblockhash"], 16)
        block.nTime = tmpl["curtime"]
        block.nBits = int(tmpl["bits"], 16)
        block.nNonce = 0
        block.vtx = [coinbase_tx]

        self.log.info("getblocktemplate: Test valid block")
        #assert_template(node, block, None)

        self.log.info("submitblock: Test block decode failure")
        assert_raises_rpc_error(-22, "Block decode failed",
                                node.submitblock, b2x(block.serialize()[:-15]))

        block.hashMerkleRoot = block.calc_merkle_root()
        node.submitblock(b2x(block.serialize()[:]))

if __name__ == '__main__':
    MiningTest().main()

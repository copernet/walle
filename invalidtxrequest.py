#!/usr/bin/env python3
# Copyright (c) 2015-2016 The Bitcoin Core developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from test_framework.test_framework import ComparisonTestFramework
from test_framework.comptool import TestManager, TestInstance, RejectResult, RejectInvalid, RejectNonstandard
from test_framework.blocktools import *
import time


'''
In this test we connect to one node over p2p, and test tx requests.
'''

# Use the ComparisonTestFramework with 1 node: only use --testbinary.


class InvalidTxRequestTest(ComparisonTestFramework):

    ''' Can either run this test as 1 node with expected answers, or two and compare them. 
        Change the "outcome" variable from each TestInstance object to only do the comparison. '''

    def set_test_params(self):
        self.num_nodes = 1
        self.setup_clean_chain = True

    def run_test(self):
        test = TestManager(self, self.options.tmpdir)
        test.add_all_connections(self.nodes)
        self.tip = None
        self.block_time = None
        NetworkThread().start()  # Start up network handling in another thread
        test.run()

    def get_tests(self):
        if self.tip is None:
            self.tip = int("0x" + self.nodes[0].getbestblockhash(), 0)
        self.block_time = int(time.time()) + 1

        '''
        Create a new block with an anyone-can-spend coinbase
        '''
        height = 1
        block = create_block(
            self.tip, create_coinbase(height), self.block_time)
        self.block_time += 1
        block.solve()
        # Save the coinbase for later
        self.block1 = block
        self.tip = block.sha256
        height += 1
        yield TestInstance([[block, True]])

        '''
        Now we need that block to mature so we can spend the coinbase.
        '''
        test = TestInstance(sync_every_block=False)
        for i in range(100):
            block = create_block(
                self.tip, create_coinbase(height), self.block_time)
            block.solve()
            self.tip = block.sha256
            self.block_time += 1
            test.blocks_and_transactions.append([block, True])
            height += 1
        yield test

        # b'\x64' is OP_NOTIF
        # Transaction will be rejected with code 16 (REJECT_INVALID)
        tx1 = create_transaction(
            self.block1.vtx[0], 0, b'\x64', 50 * COIN - 12000)
        yield TestInstance([[tx1, RejectResult(RejectInvalid, b'mandatory-script-verify-flag-failed')]])

        self.log.debug("[tx_check 001] should reject coinbase tx -----------------------------------------------------")
        # Transaction will be rejected with code 16 (REJECT_INVALID)
        tx1 = create_coinbase(0)
        yield TestInstance([[tx1, RejectResult(RejectInvalid, b'bad-tx-coinbase')]])

        self.log.debug("[tx_check 002] should reject non final tx ----------------------------------------------------")
        # Transaction will be rejected with code 16 (REJECT_INVALID)
        tx1 = create_transaction(self.block1.vtx[0], 0, b'', 50 * COIN - 200)
        tx1.nLockTime = 5000000     #high lock height
        tx1.vin[0].nSequence = 0    #not final sequence
        tx1.rehash()
        yield TestInstance([[tx1, RejectResult(RejectInvalid, b'bad-txns-nonfinal')]])

        self.log.debug("[tx_check 003] should reject tx whose input has already spent in mempool ---------------------")
        # Transaction will be rejected with code 16 (REJECT_INVALID)
        tx1 = create_transaction(self.block1.vtx[0], 0, b'\x51', 50 * COIN - 300)
        yield TestInstance([[tx1, RejectResult(RejectNonstandard, b'non-mandatory-script-verify-flag (Script did not clean its stack)')]])

        self.log.debug("[tx_check 004-0] should reject tx whose input has already spent in mempool ---------------------")
        self.log.debug("          004-1 --------------------- create a transaction tx1 with output")
        tx1 = create_transaction(self.block1.vtx[0], 0, b'', 50 * COIN - 300, CScript([OP_TRUE]))
        yield TestInstance([[tx1, True]])
        self.log.debug("          004-2 --------------------- spend output of tx1")
        tx2 = create_transaction(tx1, 0, b'', 50 * COIN - 300 - 100)
        yield TestInstance([[tx2, True]])
        self.log.debug("          004-3 --------------------- try spend output of tx1 again")
        tx3 = create_transaction(tx1, 0, b'', 50 * COIN - 300 - 200)
        yield TestInstance([[tx3, False]])

        self.log.debug("[tx_check finished] --------------------------------------------------------------------------")
        # TODO: test further transactions...

if __name__ == '__main__':
    InvalidTxRequestTest().main()

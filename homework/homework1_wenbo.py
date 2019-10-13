#! /usr/bin/env python2
# coding: utf-8

import logging
import Queue
import random
import time
import thread

logger = logging.getLogger(__name__)

result = []

read_timeout = 0.5


class Acceptor(object):

    def __init__(self, connections, index):

        self.MaxN = None
        self.AcceptN = None
        self.AcceptV = None

        self.connections = connections
        self.index = index

        for conn in self.connections:
            logger.info('A{i} connection: {i_conn}'.format(i=self.index, i_conn=conn.index))

    def run(self):

        while True:

            random.shuffle(self.connections)

            for conn in self.connections:
                try:
                    msg = conn._input.get(timeout=read_timeout)
                except Queue.Empty:
                    logger.info('connection {i} request timeout'.format(i=conn.index))
                    continue

                assert msg.get('Type') in ('prepare', 'accept'), 'wrong msg type'

                if msg.get('Type') == 'prepare':
                    self.get_prepare(msg, conn._output)

                elif msg.get('Type') == 'accept':
                    self.get_accept(msg, conn._output)

    def get_prepare(self, msg, _output):

        assert isinstance(msg.get('RoundN'), int), 'wrong round number, not int'

        if self.MaxN is None:
            self.MaxN = msg['RoundN']
            _output.put({
                'Status': 'ok',
                'AcceptN': None,
                'AcceptV': None,
                'Type': 'prepare',
            })

            return

        if self.MaxN > msg['RoundN']:
            _output.put({
                'Status': 'error',
                'AcceptN': None,
                'AcceptV': None,
                'Type': 'prepare',
            })

            return

        assert self.MaxN != msg['RoundN'], 'wrong round number, duplicate'

        self.MaxN = msg['RoundN']
        _output.put({
            'Status': 'ok',
            'AcceptN': self.AcceptN,
            'AcceptV': self.AcceptV,
            'Type': 'prepare',
        })

    def get_accept(self, msg, _output):

        assert isinstance(msg.get('RoundN'), int), 'wrong round number, not int'

        if self.MaxN is None or self.MaxN > msg['RoundN']:
            _output.put({
                'Status': 'error',
                'AcceptN': None,
                'AcceptV': None,
                'Type': 'accept',
            })

            return

        self.AcceptN = msg['RoundN']
        self.AcceptV = msg['Value']
        self.MaxN = msg['RoundN']

        _output.put({
            'Status': 'ok',
            'AcceptN': self.AcceptN,
            'AcceptV': self.AcceptV,
            'Type': 'accept',
        })


class Proposer(object):

    def __init__(self, value, connections, round_keeper, index):

        self.value = value
        self.connections = connections
        self.round_keeper = round_keeper

        self.index = index

        for conn in self.connections:
            logger.info('P{i} connection: {i_conn}'.format(i=self.index, i_conn=conn.index))

    def run(self):

        while True:
            self.roundN = self.round_keeper.get_roundN()

            logger.info('{i}, roundN: {roundN}'.format(i=self.index, roundN=self.roundN))

            value = self.do_prepare()

            logger.info('{i}, value: {value}'.format(i=self.index, value=value))

            if value is None:
                continue

            rst = self.do_submit(value)

            logger.info('{i}, rst: {rst}'.format(i=self.index, rst=rst))

            if rst is None:
                continue

            self.out(rst)
            break

    def do_prepare(self):

        msg = {
            'Type': 'prepare',
            'RoundN': self.roundN,
        }

        random.shuffle(self.connections)

        for conn in self.connections:

            # make a empty connection
            conn.clear()

            if self.lost():
                logger.info('{i_prop} connection {i_conn} submit lost'.format(i_prop=self.index, i_conn=conn.index))
                continue

            conn._input.put(msg)

        pre_replies = []

        for conn in self.connections:
            try:
                reply = conn._output.get(timeout=read_timeout)
                if self.lost():
                    logger.info('{i_prop} connection {i_conn} pre reply lost'.format(i_prop=self.index, i_conn=conn.index))
                else:
                    pre_replies.append(reply)
            except Queue.Empty:
                logger.info('{i_prop} connection {i_conn} pre read timeout'.format(i_prop=self.index, i_conn=conn.index))

        logger.info('{i} got pre reply: {n}'.format(i=self.index, n=len(pre_replies)))

        return self.resolve_pre_replies(pre_replies)

    def do_submit(self, value):

        msg = {
            'Type': 'accept',
            'RoundN': self.roundN,
            'Value': value,
        }

        random.shuffle(self.connections)

        for conn in self.connections:

            conn.clear()

            if self.lost():
                logger.info('{i_prop} connection {i_conn} submit lost'.format(i_prop=self.index, i_conn=conn.index))
                continue

            conn._input.put(msg)

        acc_replies = []

        for conn in self.connections:
            try:
                reply = conn._output.get(timeout=read_timeout)
                if self.lost():
                    logger.info('{i_prop} connection {i_conn} acc reply lost'.format(i_prop=self.index, i_conn=conn.index))
                else:
                    acc_replies.append(reply)
            except Queue.Empty:
                logger.info('{i_prop} connection {i_conn} acc read timeout'.format(i_prop=self.index, i_conn=conn.index))

        logger.info('{i} got submit reply: {n}'.format(i=self.index, n=len(acc_replies)))

        return self.resolve_acc_replies(acc_replies, value)

    def resolve_pre_replies(self, replies):

        n_ok = 0
        max_n = None
        value = None

        for rply in replies:

            assert rply['Type'] == 'prepare', 'recieve wrong type msg: {t}'.format(t=rply['Type'])

            if rply['Status'] == 'ok':
                n_ok += 1

                if rply['AcceptN'] is not None:
                    if max_n is None or max_n < rply['AcceptN']:
                        max_n = rply['AcceptN']
                        value = rply['AcceptV']

        logger.info('{i} pre n_ok {n_ok}'.format(i=self.index, n_ok=n_ok))

        if n_ok > len(self.connections)/2:
            if value is None:
                return self.value

            return value

        return None

    def resolve_acc_replies(self, replies, value):

        n_ok = 0

        for rply in replies:

            assert rply['Type'] == 'accept', 'recieve wrong type msg: {t}'.format(t=rply['Type'])

            if rply['Status'] == 'ok':
                n_ok += 1

                assert rply['AcceptV'] == value, 'accept a wrong number, {w} {g}'.format(w=value, g=rply['AcceptV'])

        logger.info('{i} acc n_ok {n_ok}'.format(i=self.index, n_ok=n_ok))

        if n_ok > len(self.connections)/2:
            return value

        return None

    def out(self, value):

        result.append(value)

    def lost(self):

        i = random.randint(0, 100)

        if i % 8 == 0:
            return True

        return False


class RoundKeeper(object):

    def __init__(self):

        self.num_list = Queue.Queue(1024)
        self.next_num = 1024

        for i in range(0, 1024):
            self.num_list.put(i)

    def get_roundN(self):

        return self.num_list.get()

    def run(self):

        while True:

            if self.num_list.empty():
                for i in range(self.next_num, self.next_num+1024):
                    self.num_list.put(i)

                self.next_num += 1024

            time.sleep(3)


class Connection(object):

    def __init__(self, index):
        self._input = Queue.Queue(1)
        self._output = Queue.Queue(1)

        self.index = index

    def clear(self):
        self._input.queue.clear()
        self._output.queue.clear()


def paxos(acceptor_num, proposer_values):

    round_keeper = RoundKeeper()
    thread.start_new_thread(round_keeper.run, ())

    proposer_num = len(proposer_values)

    acc_conns = [[None for j in range(proposer_num)] for i in range(acceptor_num)]
    prop_conns = [[None for i in range(acceptor_num)] for j in range(proposer_num)]

    for i in range(acceptor_num):
        for j in range(proposer_num):
            c = Connection(str(i)+str(j))

            acc_conns[i][j] = c
            prop_conns[j][i] = c

    for i in range(acceptor_num):
        acceptor = Acceptor(acc_conns[i], i)
        thread.start_new_thread(acceptor.run, ())

    random.shuffle(proposer_values)

    for i, value in enumerate(proposer_values):

        proposer = Proposer(value, prop_conns[i], round_keeper, i)
        thread.start_new_thread(proposer.run, ())

    while len(result) != 3:
        print result
        time.sleep(1)

    print result


if __name__ == '__main__':

    logging.basicConfig(level=logging.INFO, filename='wenbo-paxos-test.log')
    paxos(9, [1, 2, 3])

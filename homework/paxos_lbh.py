#!/usr/bin/env python2
# coding: utf-8

import threading
import Queue
import random

proposer_session = {'id': 0}
pps_lock = threading.RLock()
result = []
res_lock = threading.RLock()


class AcceptNotEnough(Exception):
    pass


def start_thread(target, name=None, args=None, kwargs=None, daemon=True):
    args = args or ()
    kwargs = kwargs or {}

    t = threading.Thread(target=target, name=name, args=args, kwargs=kwargs)
    t.daemon = daemon
    t.start()

    return t


def get_proposer_id():
    with pps_lock:
        proposer_session['id'] += 1

        return proposer_session['id']


class Acceptor(object):

    def __init__(self):
        self.p2a = Queue.Queue(1)
        self.max_n = 0
        self.accept_n = 0
        self.accept_v = None
        self.lock = threading.RLock()

    def run(self):
        while True:
            msg = self.p2a.get()

            handle = getattr(self, msg['type'], None)
            if handle is None:
                continue

            handle(msg)

    def prepare(self, msg):
        response = {'type': 'prepare'}

        with self.lock:
            if self.max_n >= msg['n']:
                response['ok'] = False

            else:
                self.max_n = msg['n']
                response['ok'] = True
                response['accept_n'] = self.accept_n
                response['accept_v'] = self.accept_v

        msg['a2p'].put(response)

    def accept(self, msg):
        response = {'type': 'accept'}

        with self.lock:
            if self.max_n > msg['n']:
                response['ok'] = False

            else:
                self.accept_n = msg['n']
                self.accept_v = msg['value']
                self.max_n = msg['n']

                response['ok'] = True

        msg['a2p'].put(response)


class Proposer(object):

    def __init__(self, value, acceptors):
        self.a2p = Queue.Queue(1)
        self.value = value
        self.acceptors = acceptors
        self.quorum = len(self.acceptors) / 2 + 1

    def submit(self):
        while True:
            try:
                value = self.prepare()
                self.accept(value)
            except AcceptNotEnough:
                continue

            with res_lock:
                result.append(value)

            break

    def prepare(self):
        self.n = get_proposer_id()

        msg = {'type': 'prepare', 'n': self.n, 'a2p': self.a2p}
        for acp in self.acceptors:
            if self.lost():
                continue

            acp.p2a.put(msg)

        ok_count = 0
        value = self.value
        max_n = 0
        for _ in self.acceptors:
            try:
                res = self.a2p.get(timeout=0.1)
            except Queue.Empty:
                continue

            if not res['ok'] or res['type'] != 'prepare' or self.lost():
                continue

            ok_count += 1
            if res['accept_n'] > max_n:
                max_n = res['accept_n']
                value = res['accept_v']

        if ok_count < self.quorum:
            raise AcceptNotEnough

        return value

    def accept(self, value):
        msg = {'type': 'accept', 'n': self.n, 'value': value, 'a2p': self.a2p}
        for acp in self.acceptors:
            if self.lost():
                continue

            acp.p2a.put(msg)

        ok_count = 0
        for _ in self.acceptors:
            try:
                res = self.a2p.get(timeout=0.1)
            except Queue.Empty:
                continue

            if not res['ok'] or res['type'] != 'accept' or self.lost():
                continue

            ok_count += 1

        if ok_count < self.quorum:
            raise AcceptNotEnough

    def lost(self):
        return random.randint(0, 100) < 20


def run():
    acceptors = []
    for _ in range(5):
        a = Acceptor()
        acceptors.append(a)
        start_thread(a.run)

    p_threads = []
    for v in range(3):
        p = Proposer(v, acceptors)
        t = start_thread(p.submit)
        p_threads.append(t)

    for t in p_threads:
        t.join()

    assert len(result) == 3
    print result


if __name__ == '__main__':
    run()

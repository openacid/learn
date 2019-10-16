# -*- coding: utf-8 -*-

import cluster
import message

import time
import random
import logging


random.seed(time.time())
logger = logging.getLogger(__name__)


class Proposer(cluster.Node):
    def __init__(self, ident):
        super(Proposer, self).__init__(ident, cluster.Role.PROPOSER)
        self.register()

        self.round_num = None

    def makeRoundNum(self):
        self.round_num = "{tm}-{ident}".format(tm=int(time.time()*1000*1000), ident=self.ident)

    def unstable_send(self, msg, rato=0.1):
        rnd = random.randint(1, 10)
        if rnd < int(rato*10):
            ''' ignore sending '''
            return

        self.send(msg)

    def unstable_receive(self, rato=0.1):
        timeout = False

        msg = self.receive(timeout=0.1)
        if msg is None:
            timeout = True

        rnd = random.randint(1, 10)
        if rnd < int(rato*10):
            ''' ignore received msg '''
            msg = None

        return msg, timeout

    def send_reqs(self, acceptors, category, m_type, round_num, value=None):
        for ident in acceptors.keys():
            msg = message.Message(self.ident,
                                  ident,
                                  round_num,
                                  value,
                                  category,
                                  m_type)
            self.unstable_send(msg)

        received = []
        for ident in acceptors.keys():
            msg, timeout = self.unstable_receive()
            if timeout:
                logger.error("some acceptor not response")
                break

            if msg is not None:
                received.append(msg)

        return received

    def prepare_reqs(self, acceptors, round_num):
        return self.send_reqs(acceptors,
                              message.Category.PREPATR_REQUEST,
                              message.MessageType.REQUEST,
                              round_num)

    def accept_reqs(self, round_num, value, acceptors):
        return self.send_reqs(acceptors,
                              message.Category.ACCEPT_REQUEST,
                              message.MessageType.REQUEST,
                              round_num,
                              value)

    def do_propose(self, value):
        '''
        return:
            whether accepted by majority and accepted value
        '''
        self.makeRoundNum()

        all_acceptors = cluster.getRandomNodesByRoleList(cluster.Role.ACCEPTOR)
        logger.info("{who} sees acceptors: {a}".format(who=self.ident, a=all_acceptors))

        majority = {}
        quorum = len(all_acceptors)/2 + 1

        logger.info("{who} quorum: {q}".format(who=self.ident, q=quorum))

        for acptor in all_acceptors:
            majority[acptor["ident"]] = acptor["channel"]

            if len(majority) >= quorum:
                break

        ''' send prepare requests '''
        received_msg = self.prepare_reqs(majority, self.round_num)
        if len(received_msg) < quorum:
            return False, None

        logger.info("{who} receives {n} prepare reponses".format(who=self.ident, n=len(received_msg)))

        acceptors = {}
        max_rnd = None
        max_rnd_value = None
        for msg in received_msg:
            acceptors[msg.sender] = self.getNodeChannel(msg.sender)

            if msg.round_num is None:
                continue

            if max_rnd is None or msg.round_num > max_rnd:
                max_rnd = msg.round_num
                max_rnd_value = msg.value

        propose_value = value
        if max_rnd_value is not None:
            propose_value = max_rnd_value

        if max_rnd is not None and max_rnd > self.round_num:
            logger.info("{who} finds greater round num: {g} > {s}, "
                        "increase self round number".format(who=self.ident, g=max_rnd, s=self.round_num))
            return False, None

        ''' accept request '''
        received_msg = self.accept_reqs(self.round_num, propose_value, acceptors)
        if len(received_msg) < quorum:
            return False, None

        return True, propose_value

    def propose(self, value):
        while True:
            accepted, acpt_val = self.do_propose(value)
            if accepted:
                logger.info("{who}: value {v} accepted".format(who=self.ident, v=acpt_val))
                break

            time.sleep((random.random()+0.1)/100)

        logger.info("{who} quits".format(who=self.ident))

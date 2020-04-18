# -*- coding: utf-8 -*-
'''
nodes info in cluster
'''

import copy
import Queue
import logging
import random
import time


class Role(object):
    PROPOSER = "proposer"
    ACCEPTOR = "acceptor"


random.seed(time.time())
logger = logging.getLogger(__name__)
CLUSTER_NODES_BY_IDENT = {}
CLUSTER_NODES_BY_ROLE = {
    Role.PROPOSER: {},
    Role.ACCEPTOR: {},
}


class Node(object):
    def __init__(self, ident, role):
        self.role = role
        self.ident = ident
        self.channel = {
            # TODO(lsl): one queue may enough
            "send": Queue.Queue(),
            "recv": Queue.Queue(),
        }

    def receive(self, timeout=None):
        msg = None
        try:
            msg = self.channel["recv"].get(timeout=timeout)
            return msg
        except Queue.Empty as err:
            logger.info("timeout before receive any messages, {e}".format(e=err))
            return None


    def send(self, msg):
        rece_chan = self.getNodeChannel(msg.receiver)
        rece_chan["recv"].put(msg)

    def register(self):
        CLUSTER_NODES_BY_IDENT[self.ident] = self.channel
        CLUSTER_NODES_BY_ROLE[self.role][self.ident] = self.channel

    def getNodeChannel(self, ident):
        return CLUSTER_NODES_BY_IDENT[ident]


def getRandomNodesByRoleList(role):
    idents = CLUSTER_NODES_BY_ROLE[role].keys()
    random.seed(time.time())
    random.shuffle(idents)

    ret = []
    for ident in idents:
        ret.append({
            "ident": ident,
            "channel": CLUSTER_NODES_BY_IDENT[ident],
        })

    return ret


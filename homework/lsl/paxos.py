# -*- coding: utf-8 -*-
"""
main entry of paxos demo
"""

import cluster
import proposer
import acceptor

import time
import threading
import logging


logger = logging.getLogger(__name__)


def make_nodes(num, role):
    ret= []
    for idx in range(num):
        if role == cluster.Role.PROPOSER:
            node = proposer.Proposer("proposer-{idx}".format(idx=idx))

        elif role == cluster.Role.ACCEPTOR:
            node = acceptor.Acceptor("acceptor-{idx}".format(idx=idx))

        else:
            raise Exception("unknown role: {r}".format(r=role))

        ret.append(node)

    return ret

def main():
    acceptors = make_nodes(5, cluster.Role.ACCEPTOR)
    proposers = make_nodes(3, cluster.Role.PROPOSER)

    logger.info("cluster: {nodes}".format(nodes=cluster.CLUSTER_NODES_BY_IDENT))

    ''' start acceptors '''
    for acptor in acceptors:
        threading.Thread(target=acptor.run).start()

    logger.info("acceptors started")
    time.sleep(0.1)
    
    proposer_ths = []
    value = 0
    ''' start proposers '''
    for pro in proposers:
        th = threading.Thread(target=pro.propose, args=(value,))
        th.start()
        proposer_ths.append(th)
        value += 1

    logger.info("proposers started")

    for th in proposer_ths:
        th.join()

    logger.info("propose finished")
    for acptor in acceptors:
        logger.info("{who}: rnd: {rnd}, value: {val}".format(who=acptor.ident,
                                                             rnd=acptor.round_num,
                                                             val=acptor.value))


def init_log():
    log_format = '%(asctime)s:%(levelname)s:%(filename)s:' \
                 '%(funcName)s:%(lineno)s:%(message)s'
    datefmt = '%a, %d %b %Y %H:%M:%S'
    level = logging.DEBUG

    logging.basicConfig(format=log_format, datefmt=datefmt, level=level)

if __name__ == "__main__":
    init_log()
    main()

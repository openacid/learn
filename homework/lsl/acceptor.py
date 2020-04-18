# -*- coding: utf-8 -*-

import cluster
import message

import Queue
import logging


logger = logging.getLogger(__name__)


class Acceptor(cluster.Node):
    def __init__(self, ident):
        super(Acceptor, self).__init__(ident, cluster.Role.ACCEPTOR)
        self.register()

        ''' pre_round_num is None means never receives msg '''
        self.pre_round_num = None

        ''' round_num and value accepted '''
        self.round_num = None
        self.value = None

    def stable_store(self, round_num, value=None, accepted=False): 
        ''' simulate store info on stable storage '''
        self.pre_round_num = round_num

        if accepted:
            self.round_num = round_num
            self.value = value

    def handle_msg(self):
        send_msg = None
        recv_msg = self.receive()

        logger.info("{who} receives msg: {msg}".format(who=self.ident, msg=recv_msg))

        if recv_msg.category == message.Category.PREPATR_REQUEST:
            round_num = recv_msg.round_num

            if self.pre_round_num is None or round_num > self.pre_round_num:
                send_msg = message.Message(self.ident,
                                           recv_msg.sender,
                                           self.round_num,
                                           self.value,
                                           message.Category.PREPATR_REQUEST,
                                           message.MessageType.RESPONSE)

                self.stable_store(round_num)
                logger.info("{who} accept prepare request: {m}".format(who=self.ident, m=recv_msg))
            else:
                logger.info("{who} reject prepare request: {m}".format(who=self.ident, m=recv_msg))

        elif recv_msg.category == message.Category.ACCEPT_REQUEST:
            round_num = recv_msg.round_num
            if self.pre_round_num is None or round_num >= self.pre_round_num:
                send_msg = message.Message(self.ident,
                                           recv_msg.sender,
                                           round_num,
                                           recv_msg.value,
                                           message.Category.ACCEPT_REQUEST,
                                           message.MessageType.RESPONSE)
                self.stable_store(round_num, recv_msg.value, True)
                logger.info("{who} accept accept request: {m}".format(who=self.ident, m=recv_msg))
            else:
                logger.info("{who} reject accept request: {m}".format(who=self.ident, m=recv_msg))

        else:
            ''' ignore unkonwn msg '''
            logger.warn("received unknoen message: {msg}".format(msg=recv_msg))
            pass

        if send_msg is not None:
            self.send(send_msg)

    def run(self):
        while True:
            self.handle_msg()

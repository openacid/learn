# -*- coding: utf-8 -*-


class Category(object):
    ACCEPT_REQUEST = "accept"
    PREPATR_REQUEST = "prepare"


class MessageType(object):
    REQUEST = "request"
    RESPONSE = "response"


class Message(object):
    def __init__(self, sender, receiver, round_num, value, category, m_type):
        self.sender = sender
        self.receiver = receiver

        ''' round_num is None and value is None means never receives msg '''
        self.round_num = round_num
        self.value = value

        ''' prepare request or accept request '''
        self.category = category
        ''' request or response which is not a must '''
        self.m_type = m_type

    def __repr__(self):
        return "<sender: {s}, recevier: {r}, "\
               "round:{n}, value: {v}, {c}-{m}>"\
               "".format(s=self.sender, r=self.receiver,
                         n=self.round_num, v=self.value,
                         c=self.category, m=self.m_type)

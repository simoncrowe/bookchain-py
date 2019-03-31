#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Simple periodical process removes unused queues."""

import sched
import time

from bookchain import Bookchain, config

DEQUEUE_INTERVAL = config['BOOKCHAIN']['dequeue_interval']


bookchain = Bookchain()
scheduler = sched.scheduler(time.time, time.sleep)


def consume_queue(_scheduler):
    bookchain.consume_queue()
    _scheduler.enter(
        delay=DEQUEUE_INTERVAL,
        priority=1,
        action=consume_queue,
        argument=(_scheduler,)
    )


scheduler.enter(
    delay=DEQUEUE_INTERVAL,
    priority=1,
    action=consume_queue,
    argument=(scheduler,)
)
scheduler.run()

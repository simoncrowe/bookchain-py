#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Runs a 'dumb' Bookchain node backed by a database.
This effectively acts as a server."""

import sched
import time

from bookchain.core import config
from bookchain.database import DatabaseBackedBookchain

DEQUEUE_INTERVAL = float(config['BOOKCHAIN']['dequeue_interval'])


bookchain = DatabaseBackedBookchain()
bookchain.start()
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

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Runs a bookchain node, outputting blocks to a USB ESC-POS printer."""

import sched
import time

from bookchain.usb_printer import UsbEscposBookchain
from bookchain.core import config

DEQUEUE_INTERVAL = float(config['BOOKCHAIN']['dequeue_interval'])

USB_PRODUCT_ID = int(config['ESCPOS']['usb_product_id'], base=16)
USB_VENDOR_ID = int(config['ESCPOS']['usb_vendor_id'], base=16)
IMAGE_PATHS = config['ESCPOS']['image_paths'].split(',')

bookchain = UsbEscposBookchain(
    usb_product_id=USB_PRODUCT_ID,
    usb_vendor_id=USB_VENDOR_ID,
    image_paths=IMAGE_PATHS,
)
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

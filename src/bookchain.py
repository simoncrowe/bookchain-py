# -*- coding: utf-8 -*-
"""Basic Bookchain client used for data storage."""

import configparser
from hashlib import sha256
import logging
import os

import requests


MODULE_PARENT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))

config = configparser.ConfigParser()
config.read(os.path.join(MODULE_PARENT_DIRECTORY, 'config.ini'))

logger = logging.getLogger()

QUEUE_ROUTER_HOST = config['QUEUE_ROUTER']['host']
QUEUE_ROUTER_PORT = config['QUEUE_ROUTER']['port']


class Bookchain:
    """Basic consume-only bookchain node."""

    identity = None
    token = None
    blocks = []

    _auth_dict = None

    def __init__(self, save_new_block=None, get_all_blocks=None):
        if save_new_block:
            self.save_block = save_new_block

        if get_all_blocks:
            self.get_all_blocks = get_all_blocks

    def register(self):
        response = requests.get(
            '{host}:{port}/register'.format(
                host=QUEUE_ROUTER_HOST,
                port=QUEUE_ROUTER_PORT
            )
        )
        self.identity = response.json()['identity']
        self.token = self._generate_token(**response.json())

    def consume_queue(self):
        response = requests.get(
            '{host}:{port}/dequeue?identity={id}&token{token}'.format(
                host=QUEUE_ROUTER_HOST,
                port=QUEUE_ROUTER_PORT,
                id=self.identity,
                token=self.token,
            )
        )
        if response.status_code == 200:
            message = response.json()

            if message['type'] == 'ADD_BLOCK':
                self.save_block(message['block'])

            elif message['type'] == 'RESPOND_BLOCKS':
                self.send_all_blocks(message['sender_address'])

        elif response.status_code == 404:
            logger.info(
                'No data to dequeue Status code: {code}'.format(
                    code=response.status_code
                )
            )

        else:
            logger.error(
                '/dequeue request failed. Status code: {code}'.format(
                    code=response.status_code
                )
            )

    def send_all_blocks(self, address):
        post_data = self.get_auth_dict()
        post_data.update(
            address=address,
            data=self.get_all_blocks()
        )
        response = requests.post(
            '{host}:{port}/enqueue'.format(
                host=QUEUE_ROUTER_HOST,
                port=QUEUE_ROUTER_PORT
            ),
            data=post_data
        )
        if not response.status_code == 200:
            logger.error(
                '/enqueue request failed. Status code: {code}'.format(
                    code=response.status_code
                )
            )

    def get_auth_dict(self):
        if not self._auth_dict:
            self._auth_dict = {
                'identity': self.identity,
                'token': self.token,
            }

        return self._auth_dict

    def save_block(self, block):
        self.blocks.append(block)

    def get_all_blocks(self):
        return self.blocks

    @staticmethod
    def _generate_token(identity, epoch):
        return sha256(
            '{id}-{timestamp}'.format(
                id=identity,
                timestamp=epoch
            ).encode('utf-8')
        ).hexdigest()

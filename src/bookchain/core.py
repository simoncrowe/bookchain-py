# -*- coding: utf-8 -*-
"""Basic Bookchain client used for data storage."""

import configparser
from hashlib import sha256
import json
import logging
import os

import requests

MODULE_PARENT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))

config = configparser.ConfigParser()
config.read(os.path.join(MODULE_PARENT_DIRECTORY, 'settings.ini'))

logger = logging.getLogger()

QUEUE_ROUTER_HOST = config['QUEUE_ROUTER']['host']


class Bookchain:
    """Basic consume-only bookchain node."""

    validate_hashes = False

    identity = None
    token = None
    blocks = []

    _auth_dict = None

    def start(self):
        self.register()

    def register(self):
        print('Attempting to register...')
        response = requests.get(
            'http://{host}/register'.format(
                host=QUEUE_ROUTER_HOST,
            ),
            timeout=3
        )

        response_data = response.json()
        self.identity = response_data.get('identity')
        self.token = self._generate_token(**response_data)

        if response.status_code == 200:
            message = '/register request succeded. Identity: {identity}'.format(
                identity=self.identity
            )
            print(message)  # For ease of debugging
            logger.info(message)
        else:
            message = '/register request failed. Status code: {code}'.format(
                code=response.status_code
            )
            logger.error(message)

    def consume_queue(self):
        response = requests.get(
            'http://{host}/dequeue?identity={id}&token={token}'.format(
                host=QUEUE_ROUTER_HOST,
                id=self.identity,
                token=self.token,
            )
        )
        if response.status_code == 200:
            message = response.json()

            if message['type'] == 'ADD_BLOCK':
                block = message['block']
                if self.validate_hashes:
                    if (
                            not self.blocks or
                            self._get_block_hash(self.blocks[-1]) == block['hash']
                    ):
                        self.save_block(message['block'])
                    else:
                        message = 'Hash mismatch! Block ignored: {block}'.format(
                            block=block
                        )
                        print(message)  # For ease of debugging
                        logger.info(message)
                else:
                    self.save_block(message['block'])

            elif message['type'] == 'REQUEST_BLOCKS':
                self.send_all_blocks(message['sender_address'])

        elif response.status_code == 404:
            message = 'No data to dequeue Status code: {code}'.format(
                code=response.status_code
            )
            print(message)  # For ease of debugging
            logger.info(message)

        else:
            message = '/dequeue request failed. Status code: {code}'.format(
                code=response.status_code
            )
            print(message)  # For ease of debugging
            logger.info(message)

    def send_all_blocks(self, address):
        post_data = self.get_auth_dict()
        post_data.update(
            address=address,
            data=json.dumps(
                {
                    'type': 'RESPOND_BLOCKS',
                    'sender_address': self.identity,
                    'blocks': self.get_all_blocks(),
                }
            ),
        )
        response = requests.post(
            'http://{host}/enqueue'.format(
                host=QUEUE_ROUTER_HOST,
            ),
            data=post_data
        )
        if response.status_code == 200:

            message = '/enqueue request succeded. JSON payload: {data}'.format(
                data=post_data
            )
            print(message)  # For ease of debugging
            logger.info(message)

        else:
            message = '/enqueue request failed. Status code: {code}'.format(
                code=response.status_code
            )
            logger.error(message)

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

    @staticmethod
    def _get_block_hash(block):
        return sha256('{hash}{text}{timestamp}'.format(
                hash=block['hash'] if block['hash'] else 'null',
                text=block['text'],
                timestamp=block['timestamp']
            ).encode()
        ).hexdigest()

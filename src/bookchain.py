# -*- coding: utf-8 -*-
"""Basic Bookchain client used for data storage."""

import configparser
from hashlib import sha256
import json
import logging
import os

import requests
from sqlalchemy.orm import sessionmaker

from models import Block, DATABASE_ENGINE

Session = sessionmaker(bind=DATABASE_ENGINE)

MODULE_PARENT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))

config = configparser.ConfigParser()
config.read(os.path.join(MODULE_PARENT_DIRECTORY, 'settings.ini'))

logger = logging.getLogger()

QUEUE_ROUTER_HOST = config['QUEUE_ROUTER']['host']
QUEUE_ROUTER_PORT = config['QUEUE_ROUTER']['port']


class Bookchain:
    """Basic consume-only bookchain node."""

    identity = None
    token = None
    blocks = []

    _auth_dict = None

    def start(self):
        self.register()

    def register(self):
        response = requests.get(
            'http://{host}:{port}/register'.format(
                host=QUEUE_ROUTER_HOST,
                port=QUEUE_ROUTER_PORT
            )
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
            'http://{host}:{port}/dequeue?identity={id}&token={token}'.format(
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
            'http://{host}:{port}/enqueue'.format(
                host=QUEUE_ROUTER_HOST,
                port=QUEUE_ROUTER_PORT
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


class DatabaseBackedBookchain(Bookchain):

    def save_block(self, block):
        session = Session()
        block = Block(**block)
        session.add(block)
        session.commit()

    def get_all_blocks(self):
        session = Session()
        blocks = session.query(Block).order_by(Block.id)
        return [
            {
                'hash': block.hash,
                'timestamp': block.timestamp,
                'text': block.text,
            }
            for block in blocks
        ]

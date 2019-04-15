

from sqlalchemy.orm import sessionmaker

from .models import Block, DATABASE_ENGINE
from .core import Bookchain

Session = sessionmaker(bind=DATABASE_ENGINE)


class DatabaseBackedBookchain(Bookchain):

    validate_hashes = True

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

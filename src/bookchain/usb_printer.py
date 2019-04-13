from collections import deque

from escpos import printer

from .core import Bookchain


class UsbEscposBookchain(Bookchain):

    def __init__(
            self,
            usb_product_id,
            usb_vendor_id,
            chars_per_line=42,
            minimum_text_lines=27,
            image_paths=None
    ):
        self.printer = printer.Usb(usb_product_id, usb_vendor_id)
        self.printer.codepage = 'utf-8'
        self.chars_per_line = chars_per_line
        self.minimum_text_lines = minimum_text_lines
        self.image_paths = image_paths or []
        super().__init__()

    def save_block(self, block):
        self.print_block(
            text=block['text'],
            hash=block['hash'],
            timestamp=block['timestamp']
        )
        super().save_block(block)

    def print_block(self, text, hash, timestamp):
        self.printer.text(
            '{text}'
            '\n\n'
            'HASH:\n'
            '{hash}'
            '\n\n'
            'TIMESTAMP:\n'
            '{timestamp}'
            '\n\n'.format(
                text=self.word_wrap(text),
                hash=hash,
                timestamp=timestamp,
            )
        )

        for image_path in self.image_paths:
            self.printer.image(image_path)

        self.printer.cut()

    def word_wrap(self, text):
        words = deque(text.split())
        lines = []
        current_line = ''
        while words:
            if len(current_line) + len(words[0]) + 1 <= self.chars_per_line:
                current_line += ' ' + words.popleft()
            elif len(words[0]) > self.chars_per_line:
                lines.append(words.popleft())
            else:
                lines.append(current_line)
                current_line = ''
        else:
            if current_line:
                lines.append(current_line)

        while len(lines) < self.minimum_text_lines:
            lines.append('')

        return '\n'.join(lines)

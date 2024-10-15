"mfbatch tests"

import unittest
from unittest.mock import MagicMock
from typing import cast

from mfbatch.commands import BatchfileParser


class BatchfileParserTests(unittest.TestCase):
    """
    Tests the BatchfileParser class
    """

    def setUp(self):
        self.command_parser = BatchfileParser()
        self.command_parser.dry_run = False
        self.command_parser.write_metadata_f = MagicMock()

    def tearDown(self):
        pass

    def test_set_without_write(self):
        "Test setting a key without writing"
        self.command_parser.set(['TYPE', 'Everything'])
        self.assertFalse(cast(MagicMock,
                              self.command_parser.write_metadata_f).called)
        self.assertEqual(self.command_parser.env.metadatums['TYPE'],
                         'Everything')

    def test_set_command(self):
        "Test set command"
        self.command_parser.set(['X', 'Y'])
        self.command_parser._eval("./testfile.flac", lineno=1,
                                 interactive=False)
        self.assertTrue(cast(MagicMock,
                             self.command_parser.write_metadata_f).called)
        self.assertEqual(cast(MagicMock,
                              self.command_parser.write_metadata_f).call_args.args,
                         ('./testfile.flac', {'X': 'Y'}))

    def test_unset_command(self):
        "Test unset command"
        self.command_parser.set(['A', '1'])
        self.assertEqual(self.command_parser.env.metadatums['A'], '1')
        self.command_parser.unset(['A'])
        self.assertNotIn('A', self.command_parser.env.metadatums.keys())

    def test_setp(self):
        "Test setp command"
        self.command_parser.set(['VAL', 'ABC123'])
        self.command_parser.setp(['DONE', 'VAL', r"([A-Z]+)123", r"X\1"])
        self.command_parser._eval("./testfile.flac", lineno=1,
                                 interactive=False)

        self.assertTrue(cast(MagicMock,
                             self.command_parser.write_metadata_f).called)
        self.assertEqual(cast(MagicMock,
                              self.command_parser.write_metadata_f).call_args.args,
                         ("./testfile.flac", {'VAL': 'ABC123', 'DONE': 'XABC'}))

    def test_eval(self):
        "Test eval"
        self.command_parser._eval(":set A 1", 1, False)
        self.assertEqual(self.command_parser.env.metadatums['A'], '1')

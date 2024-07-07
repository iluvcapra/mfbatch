"mfbatch tests"

import unittest
from unittest.mock import MagicMock
from typing import cast

from mfbatch.commands import BatchfileParser

class CommandTests(unittest.TestCase):
    def setUp(self):
        self.command_parser = BatchfileParser()
        self.command_parser.dry_run = False
        self.command_parser.write_metadata_f = MagicMock()       

    def tearDown(self):
        pass

    def testSetWithoutWrite(self):
        self.command_parser.set(['TYPE', 'Everything'])
        self.assertFalse(cast(MagicMock, 
                             self.command_parser.write_metadata_f).called)
        self.assertEqual(self.command_parser.env.metadatums['TYPE'],
                         'Everything')

    def testSetCommand(self):
        self.command_parser.set(['X', 'Y'])
        self.command_parser.eval("./testfile.flac", lineno=1,
                                 interactive=False)
        self.assertTrue(cast(MagicMock, 
                             self.command_parser.write_metadata_f).called)
        self.assertEqual(cast(MagicMock, 
                             self.command_parser.write_metadata_f).call_args.args,
                         ('./testfile.flac', {'X': 'Y'}))

    def testUnsetCommand(self):
        self.command_parser.set(['A', '1'])
        self.assertEqual(self.command_parser.env.metadatums['A'], '1')
        self.command_parser.unset(['A'])
        self.assertNotIn('A', self.command_parser.env.metadatums.keys())

    def testSetP(self):
        pass 

    def testEval(self):
        self.command_parser.eval(":set A 1", 1, False)
        self.assertEqual(self.command_parser.env.metadatums['A'], '1')


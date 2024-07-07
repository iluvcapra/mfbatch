"mfbatch tests"

import unittest

from mfbatch.commands import BatchfileParser 

class CommandTests(unittest.TestCase):
    def setUp(self):
        self.command_parser = BatchfileParser()

    def tearDown(self):
        pass

    def testSetCommand(self):
        self.command_parser.set(['X', 'Y'])
        self.assertEqual(self.command_parser.env.metadatums['X'], 'Y')

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


import unittest

from aiojsonrpc.cleaner import Cleaner


class TestMultiCast(unittest.TestCase):

    def test_cleaner(self):
        a = Cleaner(clear_timeout=0)
        a.data['a'] = dict()
        a.try_clear()
        self.assertEquals(len(a.data), 1)
        a.try_clear()
        self.assertEquals(len(a.data), 1)
        a.try_clear()
        self.assertEquals(len(a.data), 0)
        a.try_clear()
        self.assertEquals(len(a.data), 0)

from io import StringIO
import unittest
buffer = StringIO()

from custom_log import get_logger, log

class CusttomLogTest(unittest.TestCase):
    def test_get_logger(self):
        logger = get_logger()
        with self.assertLogs() as cm:
            logger.info("info message")
            print("print", cm.output)
            print("print", cm.records[0].getMessage())




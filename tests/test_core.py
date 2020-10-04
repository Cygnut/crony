from datetime import datetime
import unittest
import shlex

from parameterized import parameterized, param

from crony import core
from tests.util import write_temp_crontab

simple_filepath = write_temp_crontab("* * * * * woof")

class CoreTest(unittest.TestCase):
    # TODO: thorough tests here
    @parameterized.expand([
        param("simple", { "file": simple_filepath, "begin": "2020-01-01 00:00:00", "end": "2020-02-01 01:23:45" })
    ])
    def test_core_doesnt_die(self, _, kwargs):
        core.run(**kwargs)
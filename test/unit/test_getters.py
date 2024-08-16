"""Tests for getters."""

from napalm.base.test.getters import BaseTestGetters
from napalm.base.utils import py23_compat
from napalm_vyos import vyos
import re

import pytest


@pytest.mark.usefixtures("set_device_parameters")
class TestGetter(BaseTestGetters):
    """Test get_* methods."""
    @classmethod
    def setUpClass(cls):
        """Executed when the class is instantiated."""
        cls.mock = True

        username = 'vyos'
        ip_addr = '192.168.0.20'
        password = 'vyos'
        cls.vendor = 'vyos'

        cls.device = vyos.VyosDriver(ip_addr, username, password)

        if cls.mock:
            cls.device.device = FakeVyosDevice()
        else:
            cls.device.open()

    def test_get_facts(self):
        pass


class FakeVyosDevice:
    """Class to fake a Vyos Device."""

    @staticmethod
    def read_txt_file(filename):
        """Read a txt file and return its content."""
        with open(filename) as data_file:
            return data_file.read()

    def send_command_expect(self, command, **kwargs):
        """Fake execute a command in the device by just returning the content of a file."""
        cmd = re.sub(r'[\[\]\*\^\+\s\|]', '_', command)
        output = self.read_txt_file('ios/mock_data/{}.txt'.format(cmd))
        return py23_compat.text_type(output)

    def send_command(self, command, **kwargs):
        """Fake execute a command in the device by just returning the content of a file."""
        return self.send_command_expect(command)

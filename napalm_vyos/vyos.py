# -*- coding: utf-8 -*-
# Copyright 2016 Dravetech AB. All rights reserved.
#
# The contents of this file are licensed under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with the
# License. You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.

"""
Napalm driver for Vyos.

Read https://napalm.readthedocs.io for more information.
"""

from napalm.base import NetworkDriver
from netmiko import ConnectHandler
import os
import textfsm


class VyosDriver(NetworkDriver):
    """Napalm driver for Vyos."""

    def __init__(self, hostname, username, password, timeout=60,
                 optional_args=None):
        """Constructor."""
        self.device = None
        self.hostname = hostname
        self.username = username
        self.password = password
        self.timeout = timeout

        if optional_args is None:
            optional_args = {}

    def open(self):
        """Opens a connection to the device."""

        connect_params = {
            'device_type': 'vyos',
            'host': self.hostname,
            'username': self.username,
            'password': self.password,
            'timeout': self.timeout,
            }
        self.device = ConnectHandler(**connect_params)

    def close(self):
        """Closes the connection to the device."""

        if self.device:
            self.device.disconnect()

    def is_alive(self):
        """check if there is a device connected"""

        if self.device is None:
            return {"is_alive": False}
        return {"is_alive": self.device.is_alive()}

    def get_facts(self):
        """
        Returns a dictionary containing the following information:
         * uptime - Uptime of the device in seconds.
         * vendor - Manufacturer of the device.
         * model - Device model.
         * hostname - Hostname of the device
         * fqdn - Fqdn of the device
         * os_version - String with the OS version running on the device.
         * serial_number - Serial number of the device
         * interface_list - List of the interfaces of the device
         """

        uptime_command = "show system uptime"
        version_command = "show version"
        host_command = "show host name"
        uptime = self.device.send_command(uptime_command)
        version = self.device.send_command(version_command)
        host = self.device.send_command(host_command)

        uptime_template = os.path.join(os.path.dirname(__file__),
                                       'utils',
                                       'textfsm_templates',
                                       'vyos_show_system_uptime.template')

        version_template = os.path.join(os.path.dirname(__file__),
                                        'utils',
                                        'textfsm_templates',
                                        'vyos_show_version.template')

        with open(uptime_template) as uptime_file:
            fsm = textfsm.TextFSM(uptime_file)
            uptime_data = fsm.ParseText(uptime)

        with open(version_template) as version_file:
            fsm = textfsm.TextFSM(version_file)
            version_data = fsm.ParseText(version)

        facts = {
            'uptime': int(uptime_data[0][0])*60 +
            int(uptime_data[0][1]),
            'vendor': 'VyOS',
            'os_version': version_data[0][0],
            'serial_number': version_data[0][1],
            'model': version_data[0][2],
            'hostname': host,
            'fqdn': host,
            'interface_list': [key for key in self.get_interfaces().keys()]
        }
        return facts

    def get_config(self, retrieve='all'):
        """
        Return the configuration of a device.
        """
        configs = {
            'running': '',
            'startup': '',
            'candidate': ''
        }

        if retrieve in ("all", "running"):
            command = "show configuration"
            output = self.device.send_command(command)
            configs['running'] = output

        return configs

    def get_interfaces(self):
        """
        Returns a dictionary of dictionaries. The keys for the \
        first dictionary will be the  interfaces in the devices. \
        The inner dictionary will containing the following data for \
        each interface:

         * is_up (True/False)
         * is_enabled (True/False)
         * description (string)
         * last_flapped (float in seconds)
         * speed (float in Mbit)
         * MTU (in Bytes)
         * mac_address (string)
         """
        command = "show interfaces"
        output = self.device.send_command(command)

        template_path = os.path.join(os.path.dirname(__file__),
                                     'utils',
                                     'textfsm_templates',
                                     'vyos_show_interfaces.template')
        with open(template_path) as template_file:
            fsm = textfsm.TextFSM(template_file)
            parsed_data = fsm.ParseText(output)

        interfaces = {}
        for interface in parsed_data:
            name = interface[0]
            interfaces[name] = {
                'is_up': interface[5][0] == 'u',
                'is_enabled': interface[5][2] == 'u',
                'description': "unknown",
                'last_flapped': "unknown",
                'speed': interface[4],
                'mac_address': interface[2]
            }
        return interfaces

    def get_interfaces_ip(self):
        """
        Retrieve IP addresses assigned to the interfaces.
        :return: A dictionary with interface names as keys and IP information
        as values.
        """
        command = "show interfaces"
        output = self.device.send_command(command)

        template_path = os.path.join(os.path.dirname(__file__),
                                     'utils',
                                     'textfsm_templates',
                                     'vyos_show_interfaces_ip.template')
        with open(template_path) as template_file:
            fsm = textfsm.TextFSM(template_file)
            parsed_data = fsm.ParseText(output)

        interface_ip = {}
        for interface in parsed_data:
            if interface[0] not in interface_ip:
                interface_ip[interface[0]] = {'ipv4': {}, 'ipv6': {}}
            if ":" in interface[1]:
                interface_ip[interface[0]]['ipv6'][interface[1]] = \
                    {'prefix_length': interface[2]}
            else:
                interface_ip[interface[0]]['ipv4'][interface[1]] = \
                    {'prefix_length': interface[2]}

        return interface_ip

    def get_interfaces_counters(self):
        """
        Retrieve interface counters.
        :return: A dictionary with interface names as keys and counters
        as values.
        """
        command = "show interfaces counters"
        output = self.device.send_command(command)

        template_path = os.path.join(os.path.dirname(__file__),
                                     'utils',
                                     'textfsm_templates',
                                     'vyos_show_interfaces_counters.template')
        with open(template_path) as template_file:
            fsm = textfsm.TextFSM(template_file)
            parsed_data = fsm.ParseText(output)

        interfaces_counters = {}
        for interface in parsed_data:
            interfaces_counters[interface[0]] = {
                'tx_errors': int(interface[4]),
                'rx_errors': int(interface[1]),
                'tx_discards': int(interface[5]),
                'rx_discards': int(interface[2]),
                'tx_octets': int(interface[6]),
                'rx_octets': int(interface[3]),
                'tx_packets': int(interface[7]),
                'rx_packets': int(interface[8]),
            }

        return interfaces_counters


# driver = VyosDriver(hostname='192.168.0.28', username='vyos', password='vyos')

# print(driver.is_alive())

# driver.open()

# print(driver.is_alive())

# print(driver.get_facts())
# # print(driver.get_interfaces())
# # print(driver.get_interfaces_counters())
# # print(driver.get_interfaces_ip())
# # print(driver.get_config())

# driver.close()

# print(driver.is_alive())

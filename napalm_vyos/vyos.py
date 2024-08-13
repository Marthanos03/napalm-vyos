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
from napalm.base.exceptions import (
    ConnectionException,
    SessionLockedException,
    MergeConfigException,
    ReplaceConfigException,
    CommandErrorException,
)
from netmiko import ConnectHandler
import os
import textfsm


class VyosDriver(NetworkDriver):
    """Napalm driver for Vyos."""

    def __init__(self, hostname, username, password, timeout=60, optional_args=None):
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
        command = "show version"
        output = self.connection.send_command(command)

        # Use TextFSM to parse the output
        template_path = os.path.join(os.path.dirname(__file__),
                                     'utils',
                                     'textfsm_templates',
                                     'vyos_show_version.template')
        with open(template_path) as template_file:
            fsm = textfsm.TextFSM(template_file)
            parsed_data = fsm.ParseText(output)

        # Assume the parsed data is in the expected format
        facts = {
            'uptime': parsed_data[0][4],
            'vendor': 'VyOS',
            'os_version': parsed_data[0][1],
            'serial_number': parsed_data[0][3],
            'model': parsed_data[0][2],
            'hostname': parsed_data[0][0],
            'fqdn': parsed_data[0][0],
            'interface_list': self.get_interfaces().keys()
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
            output = self.connection.send_command(command)
            configs['running'] = output

        return configs

    def get_interfaces(self):
        """
        Returns a dictionary of dictionaries. The keys for the first dictionary will be the \
        interfaces in the devices. The inner dictionary will containing the following data for \
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
        output = self.connection.send_command(command)

        # Use TextFSM to parse the output
        template_path = os.path.join(os.path.dirname(__file__),
                                     'utils',
                                     'templates',
                                     'vyos_show_interfaces.template')
        with open(template_path) as template_file:
            fsm = textfsm.TextFSM(template_file)
            parsed_data = fsm.ParseText(output)

        interfaces = {}
        for interface in parsed_data:
            name = interface[0]
            interfaces[name] = {
                'is_up': interface[1] == 'up',
                'is_enabled': interface[2] == 'up',
                'description': interface[3],
                'last_flapped': interface[4],
                'speed': interface[6],
                'mac_address': interface[5]
            }
        return interfaces

    def get_interfaces_ip(self):
        """
        Retrieve IP addresses assigned to the interfaces.
        :return: A dictionary with interface names as keys and IP information as values.
        """
        command = "show interfaces"
        output = self.connection.send_command(command)

        # Use TextFSM to parse the output
        template_path = os.path.join(os.path.dirname(__file__),
                                     'utils',
                                     'templates',
                                     'vyos_show_interfaces_ip.template')
        with open(template_path) as template_file:
            fsm = textfsm.TextFSM(template_file)
            parsed_data = fsm.ParseText(output)

        interfaces_ip = {}
        for interface, ip, prefix in parsed_data:
            if interface not in interfaces_ip:
                interfaces_ip[interface] = {'ipv4': {}, 'ipv6': {}}
            if ":" in ip:  # IPv6 address
                interfaces_ip[interface]['ipv6'][ip] = {'prefix_length': int(prefix)}
            else:  # IPv4 address
                interfaces_ip[interface]['ipv4'][ip] = {'prefix_length': int(prefix)}

        return interfaces_ip

    def get_interfaces_counters(self):
        """
        Retrieve interface counters.
        :return: A dictionary with interface names as keys and counters as values.
        """
        command = "show interfaces"
        output = self.connection.send_command(command)

        # Use TextFSM to parse the output
        template_path = os.path.join(os.path.dirname(__file__),
                                     'utils',
                                     'templates',
                                     'vyos_show_interfaces_counters.template')
        with open(template_path) as template_file:
            fsm = textfsm.TextFSM(template_file)
            parsed_data = fsm.ParseText(output)

        interfaces_counters = {}
        for interface, rx_packets, tx_packets, rx_errors, tx_errors in parsed_data:
            interfaces_counters[interface] = {
                'tx_unicast_packets': int(tx_packets),
                'rx_unicast_packets': int(rx_packets),
                'tx_errors': int(tx_errors),
                'rx_errors': int(rx_errors),
            }

        return interfaces_counters

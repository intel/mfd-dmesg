# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Simple example of usage."""

from mfd_connect import SSHConnection
from mfd_connect import RPyCZeroDeployConnection
from mfd_dmesg import Dmesg, DmesgLevelOptions

# SSH Connection Example.
conn = SSHConnection(username="your_username", password="your_password", ip="x.x.x.x")
dmesg_obj = Dmesg(connection=conn)
print(dmesg_obj.get_messages(level=DmesgLevelOptions.NONE))
print(dmesg_obj.get_messages_additional())
print(dmesg_obj.get_os_package_info())

# RPyCConnection Example.
rpc = RPyCZeroDeployConnection(username="your_username", password="your_password", ip="x.x.x.x")
dmesg_rpc_obj = Dmesg(connection=rpc)
print(dmesg_rpc_obj.get_messages(level=DmesgLevelOptions.NONE))
print(dmesg_rpc_obj.get_messages_additional())
print(dmesg_rpc_obj.get_os_package_info())

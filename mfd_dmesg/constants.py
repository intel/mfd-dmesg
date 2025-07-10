# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Enums for Dmesg module."""

from dataclasses import dataclass
from typing import Optional
from .enums import DmesgLevelOptions # noqa: F401


@dataclass
class OSPackageInfo:
    """Decorator for OS Package Information."""

    package_name: Optional[str] = None
    package_file: Optional[str] = None
    package_version: Optional[str] = None


DMESG_WHITELIST = [
    r"vcpu0 disabled perfctr wrmsr:",  # https://bugzilla.redhat.com/show_bug.cgi?id=609032#c8
    r"failed to init package file package_file_1_0.pkg err:-22",  # ICE message
    r"unhandled rdmsr:",  # https://bugzilla.redhat.com/show_bug.cgi?id=874627
    r"Failed to set PTP clock index parameter",
    r"probe failed for device",  # os issue
    r"Use of the less secure dialect vers=1.0 is not recommended unless required for access to "
    "very old servers",  # os issue with old samba shares
    r"CIFS: VFS:",
    r"i8042: No controller found",  # Keyboard controller issue
    r"Module is not present.",  # incompatible QSFP DA cable or module with Intel NIC
    r"Possible Solution 1: Check that the module is inserted correctly.",  # cont
    r"Possible Solution 2: If the problem persists, use a cable/module that is found",  # cont
    r"Port Number: ",  # cont
    r"SELinux: CONFIG_SECURITY_SELINUX_CHECKREQPROT_VALUE is non-zero.  "
    "This is deprecated and will be rejected in a future kernel release.",
    r"SELinux: ",  # Upstream
    r"overlayfs: ",  # Overlayfs errors refers to filesystem, don't affect on network driver functionality
    r"A parallel fault was detected.",
    r"All configured link modes were attempted but failed to establish link. The device will restart the process to es",
    r"Possible Solution: Check link partner connection and configuration.",
    r"Can't open blockdev",  # This issue affect disk and USB disk, not tested driver
    # Error below don't affect tested components
    r"Deprecated Driver is detected: nft_compat will not be maintained in a future major release and may be disabled",
    r"CONFIG_IMA_DISABLE_HTABLE is disabled. Duplicate IMA measurements will not be recorded in the IMA log",
    r"DMAR: DRHD: handling fault status reg",
    r"PTE Write access is not set",
    # Errors below don't affect on driver:
    # https://forums.oracle.com/ords/apexds/post/unable-to-open-file-etc-keys-x509-ima-der-2-9238
    r"integrity: Unable to open file: /etc/keys/x509",
    r"tpm_tis MSFT0101:00: IRQ index 0 not found",
    r"PEFILE: Unsigned PE binary",  # level warning in dmesg, make fake FAILs on upstream, don't affect on functionality
    r"vers=2.0 mount not permitted when legacy dialects disabled",
    r"SysV service '/etc/rc.d/init.d/endpoint' lacks a native systemd unit file. Automatically generating a unit file",
    r"more queues but are not contiguous, falling back to default",
    r"integrity: Problem loading X.509 certificate",
    r"PTE Read access is not set",
    r"Failed to start Load AppArmor profiles.",
    r"Failed to lookup EFI memory descriptor for",
    r"kernel: DMAR",
    r"kernel: scsi",
    r"EnvironmentFile= path is not absolute, ignoring: @PCP_SYSCONFIG_DIR@/pmie",
    r"Can't lookup blockdev",  # Attempt to non-existent drive, not related to drivers
    r"Early cacheinfo failed, ret = -2",
    r"multi-user.target: Job disable-sleep.service/start deleted to break ordering cycle starting with multi-user.targ",
    r"graphical.target: Job disable-sleep.service/start deleted to break ordering cycle starting with graphical.target",
    r"Failed to set ACL on /var/log/journal/",
    r"can't delete DSCP netlink app when FW DCB agent is active",
    r"probed a monitor but no|invalid EDID",  # graphics card related error
    r"Unmaintained driver is detected: ip_tables",
    r"Unmaintained driver is detected: ip6_tables",
    r"Unmaintained driver is detected: cnic",
    r"Unmaintained driver is detected: bnx2i",
    r"Deprecated Driver is detected: qla4xxx will not be maintained in a future major release and may be disabled",
    r"Unsupported PF API version 0.0, expected 1.1",
    r"Unmaintained driver is detected: nft_compat",
    r"tpm tpm0: auth session is active",
    r"Deprecated Driver is detected: cnic",
    r"Deprecated Driver is detected: bnx2i",
    r"the capability attribute has been deprecated",  # related to disk
    r"VF could not set VLAN 0",
]
FAILS = ["no defer", "error", "fail", "timeout", "warning", "overruns", "excessive missed"]
INVALID_MODULE_ERRORS = ["Invalid", "default value", "outside of range", "Single Root Input/Output Virtualization"]
KNOWN_ERRORS = [
    "check that the module is inserted correctly",
    "if the problem persists, use a cable/module that is found in the supported "
    "modules and cables list for this device",
    "port number:",
    "module is not present",
    "ixgbevf_reset: pf still resetting",
    "mailbox message timedout",
    "failed to deallocate vectors",
    "vc response error iecm_vc_dealloc_vectors_err",
    "a parallel fault was detected",
    "possible solution: check link partner connection and configuration",
    "unhandled msg 00000010",
    "failed to add vlan filter",
    "vf could not set vlan",
]

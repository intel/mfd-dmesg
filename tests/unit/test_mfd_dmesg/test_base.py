# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Tests for `mfd_dmesg` package."""

from textwrap import dedent

import pytest
from mfd_common_libs import log_levels
from mfd_connect import SolConnection
from mfd_connect.base import ConnectionCompletedProcess
from mfd_connect.exceptions import ConnectionCalledProcessError

from mfd_dmesg import Dmesg, OSPackageInfo
from mfd_dmesg.constants import DmesgLevelOptions, FAILS
from mfd_dmesg.exceptions import DmesgNotAvailable, DmesgExecutionError, BadWordInLog
from mfd_typing import OSName


class TestDmesg:
    @pytest.fixture()
    def dmesg(self, mocker):
        mocker.patch("mfd_dmesg.Dmesg.check_if_available", mocker.create_autospec(Dmesg.check_if_available))
        mocker.patch("mfd_dmesg.Dmesg.get_version", mocker.create_autospec(Dmesg.get_version, return_value="2.31.1"))
        mocker.patch(
            "mfd_dmesg.Dmesg._get_tool_exec_factory",
            mocker.create_autospec(Dmesg._get_tool_exec_factory, return_value="dmesg"),
        )
        conn = mocker.create_autospec(SolConnection)
        conn.get_os_name.return_value = OSName.LINUX
        dg = Dmesg(connection=conn)
        mocker.stopall()
        return dg

    def test_check_if_available(self, dmesg):
        dmesg._connection.execute_command.return_value.return_code = 0
        dmesg.check_if_available()

    def test_check_if_available_tool_not_found(self, dmesg):
        dmesg._connection.execute_command.side_effect = DmesgNotAvailable(returncode=1, cmd="")
        with pytest.raises(DmesgNotAvailable):
            dmesg.check_if_available()

    def test_get_version(self, dmesg):
        output = dedent("""dmesg from util-linux 2.31.1""")
        expected = "2.31.1"
        dmesg._connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout=output, stderr="stderr"
        )
        assert expected == dmesg.get_version()

    def test_get_version_wrong_output(self, dmesg):
        dmesg._connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout="", stderr="stderr"
        )

        assert dmesg.get_version() == "NA"

    def test_get_os_package_info(self, dmesg):
        output = dedent(
            """
            [15197896.276724] IPv6: ens785: IPv6 duplicate address 24:1:1::1 used by aa:bb:cc:dd:ee:ff detected!
            [15222488.275756] ice 0000:4e:00.0 ens786:
            NIC Link is Down [    4.127626]
            ice 0000:4b:00.0: The DDP package was successfully loaded: ICE OS Default Package version 1.3.30.0"""
        )
        expected = OSPackageInfo(package_name="DDP", package_file="ICE OS Default Package", package_version="1.3.30.0")
        dmesg._connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout=output, stderr="stderr"
        )
        assert expected == dmesg.get_os_package_info()

    def test_get_os_package_info_not_matching(self, dmesg):
        output = dedent(
            """
            [15197896.276724] IPv6: ens785: IPv6 duplicate address 24:1:1::1 used by aa:bb:cc:dd:ee:ff
            detected! [15222488.275756] ice 0000:4e:00.0 ens786: NIC Link is Down [15222488.308184]
            ice 0000:4b:00.0 ens785: NIC Link is Down [15222506.769174] ice 0000:4e:00.0 ens786:
            A parallel fault was detected."""
        )
        expected = None
        dmesg._connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout=output, stderr="stderr"
        )
        assert expected == dmesg.get_os_package_info()

    def test_get_buffer_size_data(self, dmesg):
        output = dedent(
            """
            ix10: <Intel(R) PRO/10GbE PCI-Express Network Driver> port 0x4020-0x403f mem 0x91d00000-0x91dfffff,
            0x91f00000-0x91f03fff at device 0.0 numa-domain 0 on pci6
            ix10: using 64 tx descriptors and 128 rx descriptors
            ix10: msix_init qsets capped at 0
            ix10: pxm cpus: 18 queue msgs: 63 admincnt: 1
            ix10: using 18 rx queues 18 tx queues
            ix10: Using MSIX interrupts with 19 vectors
            ix10: allocated for 18 queues
            ix10: allocated for 18 rx queues
            ix10: Ethernet address: aa:bb:cc:dd:ee:ff
            ix10: Advertised speed can only be set on copper or multispeed fiber media types.
            ix10: PCI Express Bus: Speed 5.0GT/s Width x8
            ix10: netmap queues/slots: TX 18/1024, RX 18/1024
            ix1: <Intel(R) PRO/10GbE PCI-Express Network Driver> port 0x4000-0x401f mem 0x91e00000-0x91efffff,
            0x91f04000-0x91f07fff at device 0.1 numa-domain 0 on pci6
            ix1: using 256 tx descriptors and 512 rx descriptors
            ix1: msix_init qsets capped at 0
            ix1: pxm cpus: 18 queue msgs: 63 admincnt: 1
            ix1: using 18 rx queues 18 tx queues
            ix1: Using MSIX interrupts with 19 vectors
            ix1: allocated for 18 queues ix1: allocated for 18 rx queues
            ix1: Ethernet address: aa:bb:cc:dd:ee:ff
            ix1: Advertised speed can only be set on copper or multispeed fiber media types.
            ix1: PCI Express Bus: Speed 5.0GT/s Width x8
            ix1: netmap queues/slots: TX 18/1024, RX 18/1024
            ix1: <Intel(R) PRO/10GbE PCI-Express Network Driver> port 0x4000-0x401f mem 0x91e00000-0x91efffff,
            0x91f04000-0x91f07fff at device 0.1 numa-domain 0 on pci6
            ix1: using 1024 tx descriptors and 2048 rx descriptors ix1: msix_init qsets capped at 0
            ix1: pxm cpus: 18 queue msgs: 63 admincnt: 1 ix1: using 18 rx queues 18 tx queues
            ix1: Using MSIX interrupts with 19 vectors ix1: allocated for 18 queues ix1: allocated for 18 rx queues
            ix1: Ethernet address: aa:bb:cc:dd:ee:ff
            ix1: Advertised speed can only be set on copper or multispeed fiber media types.
            ix1: PCI Express Bus: Speed 5.0GT/s Width x8 ix1: netmap queues/slots: TX 18/1024, RX 18/1024"""
        )
        dmesg._connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout=output, stderr="stderr"
        )
        result = dmesg.get_buffer_size_data("ix", "1")
        assert result[0].groupdict() == dict(tx="256", rx="512")

    def test_get_buffer_size_data_wrong_input(self, dmesg):
        output = dedent(
            """
            ix10: <Intel(R) PRO/10GbE PCI-Express Network Driver> port 0x4020-0x403f mem 0x91d00000-0x91dfffff,
            0x91f00000-0x91f03fff at device 0.0 numa-domain 0 on pci6
            ix10: using 64 tx descriptors and 128 rx descriptors
            ix10: msix_init qsets capped at 0
            ix10: pxm cpus: 18 queue msgs: 63 admincnt: 1
            ix10: using 18 rx queues 18 tx queues
            ix10: Using MSIX interrupts with 19 vectors
            ix10: allocated for 18 queues
            ix10: allocated for 18 rx queues
            ix10: Ethernet address: aa:bb:cc:dd:ee:ff
            ix10: Advertised speed can only be set on copper or multispeed fiber media types.
            ix10: PCI Express Bus: Speed 5.0GT/s Width x8
            ix10: netmap queues/slots: TX 18/1024, RX 18/1024
            ix1: <Intel(R) PRO/10GbE PCI-Express Network Driver> port 0x4000-0x401f mem 0x91e00000-0x91efffff,
            0x91f04000-0x91f07fff at device 0.1 numa-domain 0 on pci6
            ix1: using 256 tx descriptors and 512 rx descriptors
            ix1: msix_init qsets capped at 0
            ix1: pxm cpus: 18 queue msgs: 63 admincnt: 1
            ix1: using 18 rx queues 18 tx queues
            ix1: Using MSIX interrupts with 19 vectors
            ix1: allocated for 18 queues ix1: allocated for 18 rx queues
            ix1: Ethernet address: aa:bb:cc:dd:ee:ff
            ix1: Advertised speed can only be set on copper or multispeed fiber media types.
            ix1: PCI Express Bus: Speed 5.0GT/s Width x8
            ix1: netmap queues/slots: TX 18/1024, RX 18/1024
            ix1: <Intel(R) PRO/10GbE PCI-Express Network Driver> port 0x4000-0x401f mem 0x91e00000-0x91efffff,
            0x91f04000-0x91f07fff at device 0.1 numa-domain 0 on pci6
            ix1: using 1024 tx descriptors and 2048 rx descriptors ix1: msix_init qsets capped at 0
            ix1: pxm cpus: 18 queue msgs: 63 admincnt: 1 ix1: using 18 rx queues 18 tx queues
            ix1: Using MSIX interrupts with 19 vectors ix1: allocated for 18 queues ix1: allocated for 18 rx queues
            ix1: Ethernet address: aa:bb:cc:dd:ee:ff
            ix1: Advertised speed can only be set on copper or multispeed fiber media types.
            ix1: PCI Express Bus: Speed 5.0GT/s Width x8 ix1: netmap queues/slots: TX 18/1024, RX 18/1024"""
        )
        dmesg._connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout=output, stderr="stderr"
        )
        expected = []
        result = dmesg.get_buffer_size_data("ix", "2")
        assert result == expected

    def test_get_messages(self, dmesg):
        output = dedent(
            """
            [15197896.276724] IPv6: ens785: IPv6 duplicate address 24:1:1::1
            used by aa:bb:cc:dd:ee:ff detected!
            [15222488.275756] ice 0000:4e:00.0 ens786: NIC Link is Down
            [15222488.308184] ice 0000:4b:00.0 ens785: NIC Link is Down
            [15222506.769174] ice 0000:4e:00.0 ens786: A parallel fault was detected."""
        )
        expected = dedent(
            """
            [15197896.276724] IPv6: ens785: IPv6 duplicate address 24:1:1::1
            used by aa:bb:cc:dd:ee:ff detected!
            [15222488.275756] ice 0000:4e:00.0 ens786: NIC Link is Down
            [15222488.308184] ice 0000:4b:00.0 ens785: NIC Link is Down
            [15222506.769174] ice 0000:4e:00.0 ens786: A parallel fault was detected."""
        ).strip()
        dmesg._connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout=output, stderr="stderr"
        )
        output = dmesg.get_messages(level=DmesgLevelOptions.NONE)
        assert expected == dmesg.get_messages(level=DmesgLevelOptions.NONE)

    def test_get_messages_imc_acc_command_level_none(self, dmesg):
        dmesg._connection.execute_command.side_effect = [
            ConnectionCalledProcessError(returncode=0, cmd=""),
            ConnectionCompletedProcess(return_code=0, args="command", stdout="", stderr="stderr"),
        ]
        dmesg.get_messages(level=DmesgLevelOptions.NONE)
        dmesg._connection.execute_command.assert_called_with("dmesg", shell=True, expected_return_codes={0, 1})

    def test_get_messages_imc_acc_command_level_error(self, dmesg):
        dmesg._connection.execute_command.side_effect = [
            ConnectionCalledProcessError(returncode=0, cmd=""),
            ConnectionCompletedProcess(return_code=0, args="command", stdout="", stderr="stderr"),
        ]
        dmesg.get_messages(level=DmesgLevelOptions.ERRORS)
        dmesg._connection.execute_command.assert_called_with(
            'dmesg | grep -v "Step" | grep -iE "error|fail" ',
            shell=True,
            expected_return_codes={0, 1},
        )

    def test_get_messages_imc_acc_command_level_error_service_name(self, dmesg):
        dmesg._connection.execute_command.side_effect = [
            ConnectionCalledProcessError(returncode=0, cmd=""),
            ConnectionCompletedProcess(return_code=0, args="command", stdout="", stderr="stderr"),
        ]
        dmesg.get_messages(level=DmesgLevelOptions.ERRORS, service_name="ix1")
        dmesg._connection.execute_command.assert_called_with(
            'dmesg | grep -v "Step" | grep -iE "error|fail" | grep \'ix1\'', shell=True, expected_return_codes={0, 1}
        )

    def test_get_messages_without_level(self, dmesg):
        output = dedent(
            """
            [15197896.276724] IPv6: ens785: IPv6 duplicate address 24:1:1::1
            used by aa:bb:cc:dd:ee:ff detected!
            [15222488.275756] ice 0000:4e:00.0 ens786: NIC Link is Down
            [15222488.308184] ice 0000:4b:00.0 ens785: NIC Link is Down
            [15222506.769174] ice 0000:4e:00.0 ens786: A parallel fault was detected."""
        )
        expected = dedent(
            """
            [15197896.276724] IPv6: ens785: IPv6 duplicate address 24:1:1::1
            used by aa:bb:cc:dd:ee:ff detected!
            [15222488.275756] ice 0000:4e:00.0 ens786: NIC Link is Down
            [15222488.308184] ice 0000:4b:00.0 ens785: NIC Link is Down
            [15222506.769174] ice 0000:4e:00.0 ens786: A parallel fault was detected."""
        ).strip()
        dmesg._connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout=output, stderr="stderr"
        )
        assert expected == dmesg.get_messages()

    def test_get_messages_additional(self, dmesg):
        output = dedent(
            """
            [15197896.276724] IPv6: ens785: IPv6 duplicate address 24:1:1::1
            used by aa:bb:cc:dd:ee:ff detected!
            [15222488.275756] ice 0000:4e:00.0 ens786: NIC Link is Down
            [15222488.308184] ice 0000:4b:00.0 ens785: NIC Link is Down
            [15222506.769174] ice 0000:4e:00.0 ens786: A parallel fault was detected."""
        )
        expected = dedent(
            """
            [15197896.276724] IPv6: ens785: IPv6 duplicate address 24:1:1::1
            used by aa:bb:cc:dd:ee:ff detected!
            [15222488.275756] ice 0000:4e:00.0 ens786: NIC Link is Down
            [15222488.308184] ice 0000:4b:00.0 ens785: NIC Link is Down
            [15222506.769174] ice 0000:4e:00.0 ens786: A parallel fault was detected."""
        ).strip()
        dmesg._connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout=output, stderr="stderr"
        )
        assert expected == dmesg.get_messages_additional()

    def test_verify_messages(self, dmesg):
        output = dedent(
            """
            [    4.660616] Couldn't get size: 0x800000000000000e
            [    4.694322] MODSIGN: Couldn't get UEFI db list
            [    4.728454] Couldn't get size: 0x800000000000000e
            [   33.580364] cdc_ether 1-1.1.2:1.0 enp0s29u1u1u2: CDC: unexpected notification 20!"""
        )
        expected = {
            "successful": False,
            "error": dedent(
                """
            [    4.660616] Couldn't get size: 0x800000000000000e
            [    4.694322] MODSIGN: Couldn't get UEFI db list
            [    4.728454] Couldn't get size: 0x800000000000000e
            [   33.580364] cdc_ether 1-1.1.2:1.0 enp0s29u1u1u2: CDC: unexpected notification 20!\n"""
            ).strip(),
        }
        dmesg._connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout=output, stderr="stderr"
        )
        assert expected == dmesg.verify_messages()

    def test_clear_messages_fail(self, dmesg):
        output = dedent(
            """
            ice0: Failed to remove RSS configuration for VSI 0, err ICE_ERR_HW_TABLE
            ice0: Free VSI 0 AQ call failed, err ICE_ERR_AQ_FW_CRITICAL aq_err OK"""
        )
        expected = (
            dedent(
                """
            ice0: Failed to remove RSS configuration for VSI 0, err ICE_ERR_HW_TABLE
            ice0: Free VSI 0 AQ call failed, err ICE_ERR_AQ_FW_CRITICAL aq_err OK"""
            ),
            [],
        )
        dmesg._connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout=output, stderr="stderr"
        )
        assert expected == dmesg.clear_messages()
        dmesg._connection.execute_command.assert_called_with(
            "dmesg -c", shell=True, custom_exception=DmesgExecutionError
        )

    def test_clear_messages(self, dmesg):
        output = dedent(
            """
            ice0: Failed to remove RSS configuration for VSI 0, err ICE_ERR_HW_TABLE
            ice0: Free VSI 0 AQ call failed, err ICE_ERR_AQ_FW_CRITICAL aq_err OK"""
        )
        expected = (
            dedent(
                """
            ice0: Failed to remove RSS configuration for VSI 0, err ICE_ERR_HW_TABLE
            ice0: Free VSI 0 AQ call failed, err ICE_ERR_AQ_FW_CRITICAL aq_err OK"""
            ),
            ["ice0: Free VSI 0 AQ call failed, err ICE_ERR_AQ_FW_CRITICAL aq_err OK"],
        )
        dmesg._connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout=output, stderr="stderr"
        )
        assert expected == dmesg.clear_messages(
            errors_filter=["ICE_ERR_HW_TABLE", "ICE_ERR_AQ_FW_CRITICAL"], ignore_filter=["ICE_ERR_HW_TABLE"]
        )
        dmesg._connection.execute_command.assert_called_with(
            "dmesg -c", shell=True, custom_exception=DmesgExecutionError
        )

    def test_clear_messages_after_error(self, dmesg, mocker):
        output = dedent(
            """
            ice0: Cannot set channels with ADQ configured
            ice0: Failed to remove RSS configuration for VSI 0, err ICE_ERR_HW_TABLE
            """
        )
        expected = (output, [])
        verify_msg_output = {
            "successful": False,
            "error": "ice0: Cannot set channels with ADQ configured\n"
            "ice0: Failed to remove RSS configuration for VSI 0, err ICE_ERR_HW_TABLE\n",
        }
        mocker.patch(
            "mfd_dmesg.base.Dmesg.verify_messages",
            mocker.create_autospec(Dmesg.verify_messages, return_value=verify_msg_output),
        )
        dmesg._connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout=output, stderr="stderr"
        )
        assert expected == dmesg.clear_messages_after_error(error_msg="Cannot set channels with ADQ configured")
        dmesg._connection.execute_command.assert_called_with(
            "dmesg -c", shell=True, custom_exception=DmesgExecutionError
        )

    def test_clear_messages_after_error_message_not_found(self, dmesg):
        dmesg._connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout="", stderr="stderr"
        )
        assert dmesg.clear_messages_after_error(error_msg="Cannot set channels with ADQ configured") is None

    def test_verify_messages_errors(self, dmesg):
        output = dedent(
            """
            [    4.660616] Couldn't get size: 0x800000000000000e
            [    4.694322] MODSIGN: Couldn't get UEFI db list
            [    4.728454] Couldn't get size: 0x800000000000000e
            [   33.580364] cdc_ether 1-1.1.2:1.0 enp0s29u1u1u2: CDC: unexpected notification 20!"""
        )
        dmesg._connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout=output, stderr="stderr"
        )
        assert not dmesg.verify_messages()["successful"]

    def test_verify_messages_no_errors(self, dmesg):
        dmesg._connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout="", stderr="stderr"
        )
        assert dmesg.verify_messages()["successful"]

    def test_check_errors(self, dmesg):
        output = dedent(
            """
            [    4.660616] Couldn't get size: 0x800000000000000e
            [    4.694322] error: Couldn't get UEFI db list
            [    4.728454] Couldn't get size: 0x800000000000000e
            [   33.580364] cdc_ether 1-1.1.2:1.0 enp0s29u1u1u2: CDC: unexpected notification 20!"""
        )
        expected = (False, ["[    4.694322] error: Couldn't get UEFI db list"])
        dmesg._connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout=output, stderr="stderr"
        )
        assert expected == dmesg.check_errors(FAILS)

    def test_check_no_errors(self, dmesg):
        output = dedent(
            """
            [    4.660616] Couldn't get size: 0x800000000000000e
            [    4.694322] MODSIGN: Couldn't get UEFI db list
            [    4.728454] Couldn't get size: 0x800000000000000e
            [   33.580364] cdc_ether 1-1.1.2:1.0 enp0s29u1u1u2: CDC: unexpected notification 20!"""
        )
        error_list = ["ix1: PCI Express Bus: Speed 5.0GT/s Width x8"]
        expected = (True, [])
        dmesg._connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout=output, stderr="stderr"
        )
        assert expected == dmesg.check_errors(error_list)

    def test_check_str_present(self, dmesg):
        output = dedent(
            """
            [    4.660616] Couldn't get size: 0x800000000000000e
            [    4.694322] MODSIGN: Couldn't get UEFI db list
            [    4.728454] Couldn't get size: 0x800000000000000e
            [   33.580364] cdc_ether 1-1.1.2:1.0 enp0s29u1u1u2: CDC: unexpected notification 20!"""
        )
        lookout_str = "Couldn't get size: 0x800000000000000e"
        dmesg._connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout=output, stderr="stderr"
        )
        assert dmesg.check_str_present(service_name="ix1", lookout_str=lookout_str)

    def test_check_no_str_present(self, dmesg):
        output = dedent(
            """
            [    4.660616] Couldn't get size: 0x800000000000000e
            [    4.694322] MODSIGN: Couldn't get UEFI db list
            [    4.728454] Couldn't get size: 0x800000000000000e
            [   33.580364] cdc_ether 1-1.1.2:1.0 enp0s29u1u1u2: CDC: unexpected notification 20!"""
        )
        lookout_str = "Couldn't get size: 0x800000000000000f"
        dmesg._connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout=output, stderr="stderr"
        )
        assert not dmesg.check_str_present(service_name="ix1", lookout_str=lookout_str)

    def test_check_new_errors(self, dmesg):
        output = dedent(
            """
            [    4.660616] Couldn't get size: 0x800000000000000e
            [    4.694322] MODSIGN: Couldn't get UEFI db list
            [    4.728454] Couldn't get size: 0x800000000000000e
            [   33.580364] cdc_ether 1-1.1.2:1.0 enp0s29u1u1u2: CDC: unexpected notification 20!"""
        )
        dmesg._connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout=output, stderr="stderr"
        )
        assert dmesg.check_new_errors()

    def test_check_time_format(self, dmesg):
        output = dedent(
            """2020-11-02T08:30:31.192Z cpu25:2729908)i40en: i40en_InitAdapterConfig:625: LLDP agent is successfully."""
        )
        dmesg._connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout=output, stderr="stderr"
        )
        assert dmesg.check_messages_format(driver="i40en")

    def test_check_wrong_time_format(self, dmesg):
        output = dedent(
            """11-2022-02T08:30:31.192 cpu25:2729908)i40en: i40en_InitAdapterConfig:625: LLDP agent is successfully."""
        )
        dmesg._connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout=output, stderr="stderr"
        )
        assert not dmesg.check_messages_format(driver="i40en")

    def test_check_time_format_no_output(self, dmesg):
        dmesg._connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout="", stderr="stderr"
        )
        assert dmesg.check_messages_format(driver="i40en") is None

    def test_verify_logs(self, dmesg, caplog, mocker):
        caplog.set_level(log_levels.MODULE_DEBUG)
        dmesg.get_messages = mocker.create_autospec(dmesg.get_messages)
        dmesg.get_messages.return_value = "log"
        assert dmesg.verify_log("driver_name") == ""
        dmesg.get_messages.assert_called_once_with(service_name="driver_name")
        assert "Driver module name: driver_name" in caplog.messages

    def test_verify_logs_empty(self, dmesg, mocker):
        dmesg.get_messages = mocker.create_autospec(dmesg.get_messages)
        dmesg.get_messages.return_value = ""
        assert dmesg.verify_log("driver_name") == ""

    def test_verify_logs_known_error(self, dmesg, mocker):
        dmesg.get_messages = mocker.create_autospec(dmesg.get_messages)
        dmesg.get_messages.return_value = "get phy capabilities failed"
        assert dmesg.verify_log("driver_name") == ""

    def test_verify_logs_expected_log(self, dmesg, mocker):
        dmesg.get_messages = mocker.create_autospec(dmesg.get_messages)
        dmesg.get_messages.return_value = "rd.driver.blacklist"
        assert dmesg.verify_log("driver_name") == ""

    def test_verify_logs_bad_word_not_error(self, dmesg, mocker):
        dmesg.get_messages = mocker.create_autospec(dmesg.get_messages)
        dmesg.get_messages.return_value = "fail"
        assert dmesg.verify_log("driver_name") == "fail"

    def test_verify_logs_bad_word_error(self, dmesg, mocker):
        dmesg.get_messages = mocker.create_autospec(dmesg.get_messages)
        dmesg.get_messages.return_value = "master of the universe"
        with pytest.raises(BadWordInLog, match="Word 'master' found in log line: 'master of the universe'"):
            dmesg.verify_log("driver_name")


class TestDmesgFreeBSD:
    @pytest.fixture()
    def dmesg(self, mocker):
        mocker.patch("mfd_dmesg.Dmesg.check_if_available", mocker.create_autospec(Dmesg.check_if_available))
        mocker.patch("mfd_dmesg.Dmesg.get_version", mocker.create_autospec(Dmesg.get_version, return_value="NA"))
        mocker.patch(
            "mfd_dmesg.Dmesg._get_tool_exec_factory",
            mocker.create_autospec(Dmesg._get_tool_exec_factory, return_value="dmesg -a"),
        )
        conn = mocker.create_autospec(SolConnection)
        conn.get_os_name.return_value = OSName.FREEBSD
        dg = Dmesg(connection=conn)
        mocker.stopall()
        return dg

    def test_check_if_available(self, dmesg):
        dmesg._connection.execute_command.return_value.return_code = 0
        dmesg.check_if_available()

    def test_get_version(self, dmesg):
        output = dedent("""dmesg from util-linux 2.31.1""")
        expected = "NA"
        dmesg._connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout=output, stderr="stderr"
        )
        assert expected == dmesg.get_version()

    def test_get_os_package_info(self, dmesg):
        output = dedent(
            """
            [15197896.276724] IPv6: ens785: IPv6 duplicate address 24:1:1::1 used by aa:bb:cc:dd:ee:ff detected!
            [15222488.275756] ice 0000:4e:00.0 ens786:
            NIC Link is Down [    4.127626]
            ice 0000:4b:00.0: The DDP package was successfully loaded: ICE OS Default Package version 1.3.30.0"""
        )
        expected = OSPackageInfo(package_name="DDP", package_file="ICE OS Default Package", package_version="1.3.30.0")
        dmesg._connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout=output, stderr="stderr"
        )
        assert expected == dmesg.get_os_package_info()

    def test_get_os_package_info_not_matching(self, dmesg):
        output = dedent(
            """
            [15197896.276724] IPv6: ens785: IPv6 duplicate address 24:1:1::1 used by aa:bb:cc:dd:ee:ff
            detected! [15222488.275756] ice 0000:4e:00.0 ens786: NIC Link is Down [15222488.308184]
            ice 0000:4b:00.0 ens785: NIC Link is Down [15222506.769174] ice 0000:4e:00.0 ens786:
            A parallel fault was detected."""
        )
        expected = None
        dmesg._connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout=output, stderr="stderr"
        )
        assert expected == dmesg.get_os_package_info()

    def test_get_buffer_size_data(self, dmesg):
        output = dedent(
            """
            ix10: <Intel(R) PRO/10GbE PCI-Express Network Driver> port 0x4020-0x403f mem 0x91d00000-0x91dfffff,
            0x91f00000-0x91f03fff at device 0.0 numa-domain 0 on pci6
            ix10: using 64 tx descriptors and 128 rx descriptors
            ix10: msix_init qsets capped at 0
            ix10: pxm cpus: 18 queue msgs: 63 admincnt: 1
            ix10: using 18 rx queues 18 tx queues
            ix10: Using MSIX interrupts with 19 vectors
            ix10: allocated for 18 queues
            ix10: allocated for 18 rx queues
            ix10: Ethernet address: aa:bb:cc:dd:ee:ff
            ix10: Advertised speed can only be set on copper or multispeed fiber media types.
            ix10: PCI Express Bus: Speed 5.0GT/s Width x8
            ix10: netmap queues/slots: TX 18/1024, RX 18/1024
            ix1: <Intel(R) PRO/10GbE PCI-Express Network Driver> port 0x4000-0x401f mem 0x91e00000-0x91efffff,
            0x91f04000-0x91f07fff at device 0.1 numa-domain 0 on pci6
            ix1: using 256 tx descriptors and 512 rx descriptors
            ix1: msix_init qsets capped at 0
            ix1: pxm cpus: 18 queue msgs: 63 admincnt: 1
            ix1: using 18 rx queues 18 tx queues
            ix1: Using MSIX interrupts with 19 vectors
            ix1: allocated for 18 queues ix1: allocated for 18 rx queues
            ix1: Ethernet address: aa:bb:cc:dd:ee:ff
            ix1: Advertised speed can only be set on copper or multispeed fiber media types.
            ix1: PCI Express Bus: Speed 5.0GT/s Width x8
            ix1: netmap queues/slots: TX 18/1024, RX 18/1024
            ix1: <Intel(R) PRO/10GbE PCI-Express Network Driver> port 0x4000-0x401f mem 0x91e00000-0x91efffff,
            0x91f04000-0x91f07fff at device 0.1 numa-domain 0 on pci6
            ix1: using 1024 tx descriptors and 2048 rx descriptors ix1: msix_init qsets capped at 0
            ix1: pxm cpus: 18 queue msgs: 63 admincnt: 1 ix1: using 18 rx queues 18 tx queues
            ix1: Using MSIX interrupts with 19 vectors ix1: allocated for 18 queues ix1: allocated for 18 rx queues
            ix1: Ethernet address: aa:bb:cc:dd:ee:ff
            ix1: Advertised speed can only be set on copper or multispeed fiber media types.
            ix1: PCI Express Bus: Speed 5.0GT/s Width x8 ix1: netmap queues/slots: TX 18/1024, RX 18/1024"""
        )
        dmesg._connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout=output, stderr="stderr"
        )
        result = dmesg.get_buffer_size_data("ix", "1")
        assert result[0].groupdict() == dict(tx="256", rx="512")

    def test_get_buffer_size_data_wrong_input(self, dmesg):
        output = dedent(
            """
            ix10: <Intel(R) PRO/10GbE PCI-Express Network Driver> port 0x4020-0x403f mem 0x91d00000-0x91dfffff,
            0x91f00000-0x91f03fff at device 0.0 numa-domain 0 on pci6
            ix10: using 64 tx descriptors and 128 rx descriptors
            ix10: msix_init qsets capped at 0
            ix10: pxm cpus: 18 queue msgs: 63 admincnt: 1
            ix10: using 18 rx queues 18 tx queues
            ix10: Using MSIX interrupts with 19 vectors
            ix10: allocated for 18 queues
            ix10: allocated for 18 rx queues
            ix10: Ethernet address: aa:bb:cc:dd:ee:ff
            ix10: Advertised speed can only be set on copper or multispeed fiber media types.
            ix10: PCI Express Bus: Speed 5.0GT/s Width x8
            ix10: netmap queues/slots: TX 18/1024, RX 18/1024
            ix1: <Intel(R) PRO/10GbE PCI-Express Network Driver> port 0x4000-0x401f mem 0x91e00000-0x91efffff,
            0x91f04000-0x91f07fff at device 0.1 numa-domain 0 on pci6
            ix1: using 256 tx descriptors and 512 rx descriptors
            ix1: msix_init qsets capped at 0
            ix1: pxm cpus: 18 queue msgs: 63 admincnt: 1
            ix1: using 18 rx queues 18 tx queues
            ix1: Using MSIX interrupts with 19 vectors
            ix1: allocated for 18 queues ix1: allocated for 18 rx queues
            ix1: Ethernet address: aa:bb:cc:dd:ee:ff
            ix1: Advertised speed can only be set on copper or multispeed fiber media types.
            ix1: PCI Express Bus: Speed 5.0GT/s Width x8
            ix1: netmap queues/slots: TX 18/1024, RX 18/1024
            ix1: <Intel(R) PRO/10GbE PCI-Express Network Driver> port 0x4000-0x401f mem 0x91e00000-0x91efffff,
            0x91f04000-0x91f07fff at device 0.1 numa-domain 0 on pci6
            ix1: using 1024 tx descriptors and 2048 rx descriptors ix1: msix_init qsets capped at 0
            ix1: pxm cpus: 18 queue msgs: 63 admincnt: 1 ix1: using 18 rx queues 18 tx queues
            ix1: Using MSIX interrupts with 19 vectors ix1: allocated for 18 queues ix1: allocated for 18 rx queues
            ix1: Ethernet address: aa:bb:cc:dd:ee:ff
            ix1: Advertised speed can only be set on copper or multispeed fiber media types.
            ix1: PCI Express Bus: Speed 5.0GT/s Width x8 ix1: netmap queues/slots: TX 18/1024, RX 18/1024"""
        )
        dmesg._connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout=output, stderr="stderr"
        )
        expected = []
        result = dmesg.get_buffer_size_data("ix", "2")
        assert result == expected

    def test_get_messages(self, dmesg):
        output = dedent(
            """
            [15197896.276724] IPv6: ens785: IPv6 duplicate address 24:1:1::1
            used by aa:bb:cc:dd:ee:ff detected!
            [15222488.275756] ice 0000:4e:00.0 ens786: NIC Link is Down
            [15222488.308184] ice 0000:4b:00.0 ens785: NIC Link is Down
            [15222506.769174] ice 0000:4e:00.0 ens786: A parallel fault was detected."""
        )
        expected = dedent(
            """
            [15197896.276724] IPv6: ens785: IPv6 duplicate address 24:1:1::1
            used by aa:bb:cc:dd:ee:ff detected!
            [15222488.275756] ice 0000:4e:00.0 ens786: NIC Link is Down
            [15222488.308184] ice 0000:4b:00.0 ens785: NIC Link is Down
            [15222506.769174] ice 0000:4e:00.0 ens786: A parallel fault was detected."""
        ).strip()
        dmesg._connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout=output, stderr="stderr"
        )
        assert expected == dmesg.get_messages(level=DmesgLevelOptions.NONE)

    def test_get_messages_without_level(self, dmesg):
        output = dedent(
            """
            [15197896.276724] IPv6: ens785: IPv6 duplicate address 24:1:1::1
            used by aa:bb:cc:dd:ee:ff detected!
            [15222488.275756] ice 0000:4e:00.0 ens786: NIC Link is Down
            [15222488.308184] ice 0000:4b:00.0 ens785: NIC Link is Down
            [15222506.769174] ice 0000:4e:00.0 ens786: A parallel fault was detected."""
        )
        expected = dedent(
            """
            [15197896.276724] IPv6: ens785: IPv6 duplicate address 24:1:1::1
            used by aa:bb:cc:dd:ee:ff detected!
            [15222488.275756] ice 0000:4e:00.0 ens786: NIC Link is Down
            [15222488.308184] ice 0000:4b:00.0 ens785: NIC Link is Down
            [15222506.769174] ice 0000:4e:00.0 ens786: A parallel fault was detected."""
        ).strip()
        dmesg._connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout=output, stderr="stderr"
        )
        assert expected == dmesg.get_messages()

    def test_get_messages_additional(self, dmesg):
        output = dedent(
            """
            [15197896.276724] IPv6: ens785: IPv6 duplicate address 24:1:1::1
            used by aa:bb:cc:dd:ee:ff detected!
            [15222488.275756] ice 0000:4e:00.0 ens786: NIC Link is Down
            [15222488.308184] ice 0000:4b:00.0 ens785: NIC Link is Down
            [15222506.769174] ice 0000:4e:00.0 ens786: A parallel fault was detected."""
        )
        expected = dedent(
            """
            [15197896.276724] IPv6: ens785: IPv6 duplicate address 24:1:1::1
            used by aa:bb:cc:dd:ee:ff detected!
            [15222488.275756] ice 0000:4e:00.0 ens786: NIC Link is Down
            [15222488.308184] ice 0000:4b:00.0 ens785: NIC Link is Down
            [15222506.769174] ice 0000:4e:00.0 ens786: A parallel fault was detected."""
        ).strip()
        dmesg._connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout=output, stderr="stderr"
        )
        assert expected == dmesg.get_messages_additional()

    def test_verify_messages(self, dmesg):
        output = dedent(
            """
            [    4.660616] Couldn't get size error: 0x800000000000000e
            [    4.694322] MODSIGN ERROR: Couldn't get UEFI db list
            [    4.728454] Couldn't get size ERROR: 0x800000000000000e
            [   33.580364] cdc_ether 1-1.1.2:1.0 enp0s29u1u1u2: CDC: unexpected notification 20!"""
        )
        expected = {
            "successful": False,
            "error": dedent(
                """
            [    4.660616] Couldn't get size error: 0x800000000000000e
            [    4.694322] MODSIGN ERROR: Couldn't get UEFI db list
            [    4.728454] Couldn't get size ERROR: 0x800000000000000e"""
            ).strip(),
        }
        dmesg._connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout=output, stderr="stderr"
        )
        assert expected == dmesg.verify_messages()

    def test_clear_messages_fail(self, dmesg):
        output = dedent(
            """
            ice0: Failed to remove RSS configuration for VSI 0, err ICE_ERR_HW_TABLE
            ice0: Free VSI 0 AQ call failed, err ICE_ERR_AQ_FW_CRITICAL aq_err OK"""
        )
        expected = (
            dedent(
                """
            ice0: Failed to remove RSS configuration for VSI 0, err ICE_ERR_HW_TABLE
            ice0: Free VSI 0 AQ call failed, err ICE_ERR_AQ_FW_CRITICAL aq_err OK"""
            ),
            [],
        )
        dmesg._connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout=output, stderr="stderr"
        )
        assert expected == dmesg.clear_messages()
        dmesg._connection.execute_command.assert_called_with(
            "dmesg -a -c", shell=True, custom_exception=DmesgExecutionError
        )

    def test_clear_messages(self, dmesg):
        output = dedent(
            """
            ice0: Failed to remove RSS configuration for VSI 0, err ICE_ERR_HW_TABLE
            ice0: Free VSI 0 AQ call failed, err ICE_ERR_AQ_FW_CRITICAL aq_err OK"""
        )
        expected = (
            dedent(
                """
            ice0: Failed to remove RSS configuration for VSI 0, err ICE_ERR_HW_TABLE
            ice0: Free VSI 0 AQ call failed, err ICE_ERR_AQ_FW_CRITICAL aq_err OK"""
            ),
            ["ice0: Free VSI 0 AQ call failed, err ICE_ERR_AQ_FW_CRITICAL aq_err OK"],
        )
        dmesg._connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout=output, stderr="stderr"
        )
        assert expected == dmesg.clear_messages(
            errors_filter=["ICE_ERR_AQ_FW_CRITICAL"], ignore_filter=["ICE_ERR_HW_TABLE"]
        )
        dmesg._connection.execute_command.assert_called_with(
            "dmesg -a -c", shell=True, custom_exception=DmesgExecutionError
        )

    def test_clear_messages_after_error(self, dmesg, mocker):
        output = dedent(
            """
            ice0: Error Cannot set channels with ADQ configured
            ice0: Error Failed to remove RSS configuration for VSI 0, err ICE_ERR_HW_TABLE
            """
        )
        expected = (output, [])
        verify_msg_output = {
            "successful": False,
            "error": "ice0: Error Cannot set channels with ADQ configured\n"
            "ice0: Error Failed to remove RSS configuration for VSI 0, err ICE_ERR_HW_TABLE\n",
        }
        mocker.patch(
            "mfd_dmesg.base.Dmesg.verify_messages",
            mocker.create_autospec(Dmesg.verify_messages, return_value=verify_msg_output),
        )
        dmesg._connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout=output, stderr="stderr"
        )
        assert expected == dmesg.clear_messages_after_error(error_msg="Cannot set channels with ADQ configured")
        dmesg._connection.execute_command.assert_called_with(
            "dmesg -a -c", shell=True, custom_exception=DmesgExecutionError
        )

    def test_clear_messages_after_error_message_not_found(self, dmesg):
        dmesg._connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout="", stderr="stderr"
        )
        assert dmesg.clear_messages_after_error(error_msg="Cannot set channels with ADQ configured") is None

    def test_verify_messages_errors(self, dmesg):
        output = dedent(
            """
            [    4.660616] Couldn't get size error: 0x800000000000000e
            [    4.694322] MODSIGN ERROR: Couldn't get UEFI db list
            [    4.728454] Couldn't get size: 0x800000000000000e
            [   33.580364] cdc_ether 1-1.1.2:1.0 enp0s29u1u1u2: CDC: unexpected notification 20!"""
        )
        dmesg._connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout=output, stderr="stderr"
        )
        assert not dmesg.verify_messages()["successful"]

    def test_verify_messages_no_errors(self, dmesg):
        dmesg._connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout="", stderr="stderr"
        )
        assert dmesg.verify_messages()["successful"]

    def test_check_errors(self, dmesg):
        output = dedent(
            """
            [    4.660616] Couldn't get size: 0x800000000000000e
            [    4.694322] error: Couldn't get UEFI db list
            [    4.728454] Couldn't get size: 0x800000000000000e
            [   33.580364] cdc_ether 1-1.1.2:1.0 enp0s29u1u1u2: CDC: unexpected notification 20!"""
        )
        expected = (False, ["[    4.694322] error: Couldn't get UEFI db list"])
        dmesg._connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout=output, stderr="stderr"
        )
        assert expected == dmesg.check_errors(FAILS)

    def test_check_no_errors(self, dmesg):
        output = dedent(
            """
            [    4.660616] Couldn't get size: 0x800000000000000e
            [    4.694322] MODSIGN: Couldn't get UEFI db list
            [    4.728454] Couldn't get size: 0x800000000000000e
            [   33.580364] cdc_ether 1-1.1.2:1.0 enp0s29u1u1u2: CDC: unexpected notification 20!"""
        )
        error_list = ["ix1: PCI Express Bus: Speed 5.0GT/s Width x8"]
        expected = (True, [])
        dmesg._connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout=output, stderr="stderr"
        )
        assert expected == dmesg.check_errors(error_list)

    def test_check_str_present(self, dmesg):
        output = dedent(
            """
            [    4.660616] Couldn't get size: 0x800000000000000e
            [    4.694322] MODSIGN: Couldn't get UEFI db list
            [    4.728454] Couldn't get size: 0x800000000000000e
            [   33.580364] cdc_ether 1-1.1.2:1.0 enp0s29u1u1u2: CDC: unexpected notification 20!"""
        )
        lookout_str = "Couldn't get size: 0x800000000000000e"
        dmesg._connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout=output, stderr="stderr"
        )
        assert dmesg.check_str_present(service_name="ix1", lookout_str=lookout_str)

    def test_check_no_str_present(self, dmesg):
        output = dedent(
            """
            [    4.660616] Couldn't get size: 0x800000000000000e
            [    4.694322] MODSIGN: Couldn't get UEFI db list
            [    4.728454] Couldn't get size: 0x800000000000000e
            [   33.580364] cdc_ether 1-1.1.2:1.0 enp0s29u1u1u2: CDC: unexpected notification 20!"""
        )
        lookout_str = "Couldn't get size: 0x800000000000000f"
        dmesg._connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout=output, stderr="stderr"
        )
        assert not dmesg.check_str_present(service_name="ix1", lookout_str=lookout_str)

    def test_check_new_errors(self, dmesg):
        output = dedent(
            """
            [    4.660616] Couldn't get size: 0x800000000000000e
            [    4.694322] MODSIGN: Couldn't get UEFI db list
            [    4.728454] Couldn't get size: 0x800000000000000e
            [   33.580364] cdc_ether 1-1.1.2:1.0 enp0s29u1u1u2: CDC: unexpected notification 20!"""
        )
        dmesg._connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout=output, stderr="stderr"
        )
        assert dmesg.check_new_errors()

    def test_check_time_format(self, dmesg):
        output = dedent(
            """2020-11-02T08:30:31.192Z cpu25:2729908)i40en: i40en_InitAdapterConfig:625: LLDP agent is successfully."""
        )
        dmesg._connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout=output, stderr="stderr"
        )
        assert dmesg.check_messages_format(driver="i40en")

    def test_check_wrong_time_format(self, dmesg):
        output = dedent(
            """11-2022-02T08:30:31.192 cpu25:2729908)i40en: i40en_InitAdapterConfig:625: LLDP agent is successfully."""
        )
        dmesg._connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout=output, stderr="stderr"
        )
        assert not dmesg.check_messages_format(driver="i40en")

    def test_check_time_format_no_output(self, dmesg):
        dmesg._connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout="", stderr="stderr"
        )
        assert dmesg.check_messages_format(driver="i40en") is None

    def test_verify_logs(self, dmesg, caplog, mocker):
        dmesg.get_messages = mocker.create_autospec(dmesg.get_messages)
        caplog.set_level(log_levels.MODULE_DEBUG)
        dmesg.get_messages.return_value = "log"
        assert dmesg.verify_log("driver_name") == ""
        dmesg.get_messages.assert_called_once()
        assert "Driver module name: driver_name" in caplog.messages

    def test_verify_logs_bad_word(self, dmesg, mocker):
        dmesg.get_messages = mocker.create_autospec(dmesg.get_messages)
        dmesg.get_messages.return_value = "driver_name: fail"
        assert dmesg.verify_log("driver_name") == "driver_name: fail"

    def test_verify_logs_empty(self, dmesg, mocker):
        dmesg.get_messages = mocker.create_autospec(dmesg.get_messages)
        dmesg.get_messages.return_value = ""
        assert dmesg.verify_log("driver_name") == ""

# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Dmesg module."""

import datetime
import logging
import re
from typing import Iterable, Optional, Union, List, Tuple, TYPE_CHECKING

from mfd_common_libs import add_logging_level, log_levels, os_supported
from mfd_connect.exceptions import ConnectionCalledProcessError
from mfd_base_tool import ToolTemplate
from mfd_typing import OSName

from mfd_dmesg.constants import DMESG_WHITELIST
from mfd_dmesg.constants import DmesgLevelOptions, OSPackageInfo
from mfd_dmesg.exceptions import DmesgException, DmesgNotAvailable, DmesgExecutionError, BadWordInLog

if TYPE_CHECKING:
    from mfd_connect import Connection

logger = logging.getLogger(__name__)
add_logging_level("MODULE_DEBUG", log_levels.MODULE_DEBUG)
RUNNING_ERRORS = []

OS_PACKAGE_RE = re.compile(
    ".+: The (?P<package_name>.+) package was successfully loaded: "
    "(?P<package_file>.+) version (?P<package_version>.+)",
    flags=re.IGNORECASE,
)


class Dmesg(ToolTemplate):
    """Utility for Dmesg."""

    tool_executable_name = {
        OSName.LINUX: "dmesg",
        OSName.FREEBSD: "dmesg -a",
        OSName.ESXI: "dmesg",
    }

    @os_supported(OSName.LINUX, OSName.FREEBSD, OSName.ESXI)
    def __init__(self, *, connection: "Connection"):
        """
        Initialize connection.

        :param connection: mfd_connect object for remote connection handling
        """
        self.os_name = connection.get_os_name()
        super().__init__(connection=connection)

    def _get_tool_exec_factory(self) -> str:
        return self.tool_executable_name[self._connection.get_os_name()]

    def _is_linux(self) -> bool:
        """Check if os is linux or not.

        :return: True or False based on the os on the given system
        """
        return self.os_name == OSName.LINUX

    def check_if_available(self) -> None:
        """
        Check if tool is available in system.

        :raises DmesgException when tool is not available.
        """
        logger.log(level=log_levels.MODULE_DEBUG, msg="Check if Dmesg is available.")
        command = f"{self._tool_exec}"
        self._connection.execute_command(command, custom_exception=DmesgNotAvailable, discard_stdout=True)

    def get_version(self) -> str:
        """
        Get Dmesg version.

        :return Dmesg version or "N/A" when it cannot read it.
        """
        logger.log(level=log_levels.MODULE_DEBUG, msg="Get Dmesg Version.")
        version_regex = r"dmesg\sfrom\sutil-linux\s(?P<version>.*)"
        if self._is_linux():
            result = self._connection.execute_command(
                f"{self._tool_exec} -V",
                expected_return_codes=None,
                stderr_to_stdout=True,
                custom_exception=DmesgExecutionError,
            ).stdout
            match = re.search(version_regex, result, re.M)
            if match:
                return match.group("version").rstrip()
        else:
            logger.log(
                level=log_levels.MODULE_DEBUG,
                msg=f"There is no support to check {self._tool_exec} version in {self.os_name.value}",
            )
        return "NA"

    def get_messages(self, level: DmesgLevelOptions = DmesgLevelOptions.NONE, service_name: str = None) -> str:
        """
        Read the message buffer of the kernel (dmesg).

        For ACC and IMC systems different set of commands need to be executed.

        :param service_name: limits dmesg messages only to provided service
        :param level: limits dmesg messages only to provided by DmesgLevelOptions
        :return: dmesg output
        """
        logger.log(level=log_levels.MODULE_DEBUG, msg="Get Dmesg Output")
        command = self._tool_exec
        acc_imc_command = self._tool_exec
        if f"{level.value}" != "None":
            command += f" --level={level.value} "
            acc_imc_command = self._prepare_imc_acc_command(command=acc_imc_command, level=level)
        if service_name is not None:
            command += f"| grep '{service_name}'"
            acc_imc_command += f"| grep '{service_name}'"
            try:
                out = self._connection.execute_command(command, shell=True, expected_return_codes={0, 1}).stdout
            except ConnectionCalledProcessError:
                out = self._connection.execute_command(acc_imc_command, shell=True, expected_return_codes={0, 1}).stdout

        else:
            try:
                out = self._connection.execute_command(command, shell=True).stdout
            except ConnectionCalledProcessError:
                out = self._connection.execute_command(acc_imc_command, shell=True, expected_return_codes={0, 1}).stdout

        return out.strip()

    def _prepare_imc_acc_command(self, command: str, level: DmesgLevelOptions) -> str:
        """
        Prepare command for IMC and ACC systems.

        :param command: Command to adjust for ACC and IMC systems
        :param level: limits dmesg messages only to provided by DmesgLevelOptions
        :return: Command valid for ACC and IMC systems
        """
        command += ' | grep -v "Step"'
        if level == DmesgLevelOptions.ERRORS:
            command += ' | grep -iE "error|fail" '
        elif level == DmesgLevelOptions.WARNINGS:
            command += ' | grep -iE "warning" '
        else:
            command += f" | grep {level.value} "

        return command

    def get_buffer_size_data(self, driver_name: str, driver_interface_number: str) -> Optional[list]:
        """Read the dmesg for driver buffer size information.

        :param driver_name: limits buffer size info only to provided driver name
        :param driver_interface_number: limits buffer size info only to provided driver interface number
        :return: list of buffer size match objects
        """
        logger.log(level=log_levels.MODULE_DEBUG, msg="Get Buffer Size Data from dmesg")
        return list(
            re.finditer(
                rf"^{driver_name}{driver_interface_number}: "
                r"using (?P<tx>\d*) tx descriptors and (?P<rx>\d*) rx descriptors$",
                self.get_messages(service_name=f"{driver_name}{driver_interface_number}"),
                re.MULTILINE | re.IGNORECASE,
            )
        )

    def get_os_package_info(self) -> Union[OSPackageInfo, None]:
        """Get loaded OS package information from dmesg log.

        :return: OSPackageMeta object or None when not found
        """
        logger.log(level=log_levels.MODULE_DEBUG, msg="Get OS Package Info from dmesg")
        dmesg_result = self.get_messages().splitlines()
        for line in dmesg_result:
            match = OS_PACKAGE_RE.match(line)
            if match:
                package_name = match.group("package_name")
                package_file = match.group("package_file")
                package_version = match.group("package_version")
                return OSPackageInfo(package_name, package_file, package_version)

    def get_messages_additional(
        self,
        service_name: str = None,
        lines: int = 1000,
        expected_return_codes: Iterable = frozenset({0}),
        additional_greps: Optional[List[str]] = None,
    ) -> str:
        """Read the last lines of message buffer of the kernel (dmesg).

        :param service_name: limits dmesg messages only to provided service
        :param lines: limit number of lines
        :param expected_return_codes: set of expected return codes
        :param additional_greps: list of text to find in addition
        :return: dmesg output
        """
        logger.log(level=log_levels.MODULE_DEBUG, msg="Get Latest Dmesg Output")
        if not additional_greps:
            additional_greps = []

        command = self._tool_exec
        if service_name is not None:
            command += f" | grep '{service_name}'"

        if additional_greps:
            grep_content = None
            for additional_grep in additional_greps:
                grep_content = grep_content + f"\\|{additional_grep}" if grep_content else f"{additional_grep}"
            command += f" | grep -i '{grep_content}'"
        command += f" | tail -n {lines}"
        out = self._connection.execute_command(command, shell=True, expected_return_codes=expected_return_codes).stdout
        return out.strip()

    def _check_specific_errors(self, error_msg: str) -> bool:
        """Check if error present in given string based on OS.

        :param error_msg: error message from dmesg output
        :return: success or failure if the error keyword present else False,
                for linux error_msg is anyhow error as level parameter is set while fetching dmesg output.
        """
        if not self._is_linux():
            return True if "error" in error_msg.lower() else False
        else:
            return True

    def verify_messages(self) -> dict:
        """Verify if there are err level messages in dmesg output.

        :return: dictionary indicating success or failure and the error messages if present.
        """
        logger.log(level=log_levels.MODULE_DEBUG, msg="Verify Dmesg Errors.")
        level = DmesgLevelOptions.ERRORS if self._is_linux() else DmesgLevelOptions.NONE
        out = self.get_messages(level=level)
        dmesg_result = {"successful": True, "error": ""}
        if out:
            for error in out.splitlines():
                is_error = True
                if self._check_specific_errors(error):
                    for benign_message in DMESG_WHITELIST:
                        if benign_message in error:
                            is_error = False
                            logger.log(
                                level=log_levels.MODULE_DEBUG,
                                msg=f'Ignored error "{error}" in dmesg because it is known to be benign',
                            )
                            break
                    if is_error:
                        dmesg_result["successful"] = False
                        dmesg_result["error"] += error + "\n"
            dmesg_result["error"] = dmesg_result["error"].strip()

        # log for debug purposes
        logger.log(level=log_levels.MODULE_DEBUG, msg=f"Dmesg dump: {out}")
        return dmesg_result

    def clear_messages(
        self,
        errors_filter: Optional[List[str]] = [],
        ignore_filter: Optional[List[str]] = [],
    ) -> Tuple[str, List[str]]:
        """Check current dmesg buffer for any errors and then clear dmesg.

        :param errors_filter: list of all possible errors to check
        :param ignore_filter: list of all possible errors to ignore
        :return: A tuple containing the output of dmesg -c and a list of errors
        """
        command = f"{self._tool_exec} -c"
        try:
            output = self._connection.execute_command(command, shell=True, custom_exception=DmesgExecutionError).stdout
            new_errors = []
            if errors_filter:
                for line in output.splitlines():
                    if any(x in line for x in errors_filter) and not any(x in line for x in ignore_filter):
                        new_errors.append(line)
                        logger.log(level=log_levels.MODULE_DEBUG, msg=f"Found error in dmesg: {line}")
            return (output, new_errors)
        except DmesgExecutionError as e:
            raise DmesgException("Failed to clear the dmesg contents.") from e

    def clear_messages_after_error(self, error_msg: str) -> Union[Tuple[str, List[str]], None]:
        """Clear dmesg if user defined error is raised.

        :param error_msg: error to be looked out in the log before clearing the dmesg
        :return: A tuple containing the output of dmesg -c and a list of err.
        """
        logger.log(
            level=log_levels.MODULE_DEBUG,
            msg="Check for expected errors in dmesg.",
        )
        if error_msg in self.verify_messages()["error"]:
            logger.log(level=log_levels.MODULE_DEBUG, msg=f"Expected error in dmesg: {self.verify_messages()['error']}")
            return self.clear_messages()
        else:
            logger.log(level=log_levels.MODULE_DEBUG, msg=f"{error_msg} is not present in dmesg")

    def check_errors(self, error_list: list) -> tuple:
        """Verify the Dmesg logs for any user defined errors.

        :param error_list: list of errors to be looked out in the dmesg log
        :return: tuple indicating success or failure and the list of error messages if present.
        """
        dmesg_output = self.get_messages()
        detected_fails_list = list()
        if dmesg_output:
            for dmesg_line in dmesg_output.splitlines():
                for fail in error_list:
                    if fail in dmesg_line:
                        logger.log(
                            level=log_levels.MODULE_DEBUG,
                            msg=f"User defined error present:\n{dmesg_line}",
                        )
                        detected_fails_list.append(dmesg_line)

        if detected_fails_list:
            logger.log(level=log_levels.MODULE_DEBUG, msg=f"Error(s) present in dmesg logs:\n{detected_fails_list}")
            return (False, detected_fails_list)
        else:
            logger.log(level=log_levels.MODULE_DEBUG, msg="Not found any user defined errors in dmesg log.")
            return (True, detected_fails_list)

    def check_str_present(
        self, service_name: str, lookout_str: str, additional_greps: Optional[List[str]] = None
    ) -> bool:
        """Check the dmesg logs for user specified string.

        :param service_name: limits dmesg messages only to provided service
        :param additional_greps: list of text to find in addition
        :param lookout_str: user specified string to be searched in the dmesg logs
        :return: returns True if no user define string present in dmesg logs, False otherwise
        """
        dmesg_result = self.get_messages_additional(
            service_name=service_name, lines=500, additional_greps=additional_greps
        ).splitlines()
        if dmesg_result:
            for line in dmesg_result:
                if lookout_str in line:
                    logger.log(level=log_levels.MODULE_DEBUG, msg="Log found in dmesg")
                    logger.log(level=log_levels.MODULE_DEBUG, msg=f"Line: {line}")
                    return True
            logger.log(level=log_levels.MODULE_DEBUG, msg=f"User specified {lookout_str} not present in dmesg log")
            return False
        else:
            logger.log(level=log_levels.MODULE_DEBUG, msg=f"No logs found for service {service_name} in dmesg")
            return False

    def check_messages_format(self, driver: str, time_format: str = "%Y-%m-%dT%H:%M:%S.%fZ") -> Union[bool, None]:
        """Verify if the dmesg logs are displayed in correct format.

        :param driver: Name of the driver such as i40en
        :param time_format: time format to be checked in dmesg logs for the specified driver
        :return: returns True if no specified format have found, False otherwise and if dmesg output is empty
        """
        dmesg = self.get_messages_additional(lines=1, additional_greps=[f"{driver}_InitSharedCode"])
        if dmesg:
            dmesg = dmesg.split()
            logger.log(level=log_levels.MODULE_DEBUG, msg=f"dmesg log is {dmesg}")
            try:
                dmesg_result = bool(datetime.datetime.strptime(dmesg[0], time_format))
                logger.log(level=log_levels.MODULE_DEBUG, msg=f"Date matches the format :{str(dmesg_result)}")

            except ValueError:
                dmesg_result = False
                logger.log(level=log_levels.MODULE_DEBUG, msg=f"Date does not match the format : {str(dmesg_result)}")

            if len(dmesg) >= 1:
                if "cpu" in dmesg[1] and driver in dmesg[1]:
                    logger.log(level=log_levels.MODULE_DEBUG, msg=f"Correct format : {dmesg[1]}")
                else:
                    logger.log(level=log_levels.MODULE_DEBUG, msg=f"Incorrect format: {dmesg[1]}")
                    dmesg_result = False
            else:
                logger.log(level=log_levels.MODULE_DEBUG, msg=f"{dmesg}")
                dmesg_result = False

            if len(dmesg) >= 2:
                if f"{driver}_" in dmesg[2]:
                    logger.log(level=log_levels.MODULE_DEBUG, msg=f"Correct format : {dmesg[2]}")
                else:
                    logger.log(level=log_levels.MODULE_DEBUG, msg=f"Incorrect format: {dmesg[2]}")
                    dmesg_result = False
            else:
                logger.log(level=log_levels.MODULE_DEBUG, msg=f"{dmesg}")
                dmesg_result = False
        else:
            logger.log(level=log_levels.MODULE_DEBUG, msg="Dmesg contents are empty")
            return None
        return dmesg_result

    def check_new_errors(self) -> dict:
        """Verify if there are new err level messages in dmesg output since the last time this was run.

        :return: dictionary indicating success or failure and the error message if present,
                 same return format as verify_messages() but only send back new errors.
        """
        results = self.verify_messages()
        global RUNNING_ERRORS
        if results["successful"] is not True:
            errors = results["error"].splitlines()
            old_errors = errors[: len(RUNNING_ERRORS)]
            new_errors = errors[len(RUNNING_ERRORS) :]
            if RUNNING_ERRORS == old_errors:
                if new_errors:
                    new_results = {"successful": False, "error": "\n".join(new_errors)}
                else:
                    new_results = {"successful": True, "error": ""}
            else:
                new_results = results
            RUNNING_ERRORS = errors
        else:
            new_results = {"successful": True, "error": ""}
        return new_results

    def verify_log(self, driver: str) -> str:
        """
        Check the system log (journal on Windows, dmesg on Linux) for errors.

        :param driver: Name of the driver such as i40en
        :return: empty string if no errors found, error content otherwise
        :raise BadWordInLog: Bad (ie. non-inclusive, offensive etc.) word found in log
        """
        return self._verify_log_linux(driver) if self._is_linux() else self._verify_log_freebsd(driver)

    def _verify_log_linux(self, driver: str) -> str:
        """
        Check the system log (journal on Windows, dmesg on Linux) for errors.

        :param driver: Name of the driver such as i40en
        :return: empty string if no errors found, error content otherwise
        :raise BadWordInLog: Bad (ie. non-inclusive, offensive etc.) word found in log
        """
        logger.log(level=log_levels.MODULE_DEBUG, msg=f"Driver module name: {driver}")

        # Look for bad words and whether they constitute error in log:)
        bad_words = [
            ("fail", False),
            (" hang", False),
            ("warning", False),
            ("master", True),
            ("slave", True),
            ("whitelist", True),
            ("blacklist", True),
        ]
        known_errors = ["get phy capabilities failed"]
        expected_logs = ["rd.driver.blacklist"]

        # Find lines that starts with service name and contain fail or hang keyword
        log = self.get_messages(service_name=driver)
        if not log:
            return ""

        for line in log.splitlines():
            if any(known_error in line for known_error in known_errors) or any(
                expected_log in line for expected_log in expected_logs
            ):
                logger.log(level=log_levels.MODULE_DEBUG, msg=f"Error log line: '{line}'.")
                continue

            for word, is_error in bad_words:
                if word in line.lower():
                    msg = f"Word '{word}' found in log line: '{line}'"
                    if is_error:
                        raise BadWordInLog(msg)
                    # Return the whole log if something bad was found
                    logger.log(level=log_levels.MODULE_DEBUG, msg=msg)
                    return log
        # Everything is ok
        return ""

    def _verify_log_freebsd(self, driver: str) -> str:
        """
        Check the system log for errors.

        :param driver: Name of the driver such as i40en
        :return: empty string if no errors found, error content otherwise.
        """
        logger.log(level=log_levels.MODULE_DEBUG, msg=f"Driver module name: {driver}")

        # Look for bad words in log:)
        bad_words = ["fail", " hang"]

        # Find lines that starts with service name and contain fail or hang keyword
        log = self.get_messages()
        if not log:
            return ""

        for line in log.splitlines():
            if line.startswith(driver):
                line_low = line.lower()
                for word in bad_words:
                    if word in line_low:
                        # Return the whole log if something bad was found
                        logger.log(level=log_levels.MODULE_DEBUG, msg=f"Word '{word}' found in log line: {line}")
                        return log
        # Everything is ok
        return ""

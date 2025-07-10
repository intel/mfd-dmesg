# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Exceptions for Dmesg."""

import subprocess
from mfd_base_tool.exceptions import ToolNotAvailable


class DmesgException(Exception):
    """Exception for Dmesg."""


class DmesgNotAvailable(ToolNotAvailable, DmesgException):
    """Handle tool not available exception."""


class DmesgExecutionError(DmesgException, subprocess.CalledProcessError):
    """Handle Dmesg execution errors."""


class BadWordInLog(DmesgException):
    """Exception raised when bad word is found in log."""

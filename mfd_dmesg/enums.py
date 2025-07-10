# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Enums for Dmesg module."""

from enum import Enum


class DmesgLevelOptions(Enum):
    """
    Enum class for Dmesg level.

    Will print levels err, crit, alert and emerg.
    """

    NONE = "None"
    ERRORS = "err"
    CRITICAL = "crit"
    ALERT = "alert"
    EMERGENCY = "emerg"
    WARNINGS = "warn"

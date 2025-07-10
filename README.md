> [!IMPORTANT]  
> This project is under development. All source code and features on the main branch are for the purpose of testing or evaluation and not production ready.
 
# MFD Dmesg

## Usage

from mfd_connect import SSHConnection
from mfd_connect import RPyCZeroDeployConnection
from mfd_dmesg import Dmesg, DmesgLevelOptions
from mfd_connect import RPyCConnection

conn = SSHConnection(username="***", password="***", ip="***")
dmesg_obj = Dmesg(connection=conn)
print(dmesg_obj.get_messages(level=DmesgLevelOptions.NONE))
print(dmesg_obj.get_messages_additional())
print(dmesg_obj.get_os_package_info())

## Implemented methods

`check_if_available(self) -> None` - responsible to check if tool is available in system.
`get_version(self) -> str` - responsible to get version of tool.
`get_messages(self, level: DmesgLevelOptions = DmesgLevelOptions.NONE, service_name: str = None) -> str` - responsible to return dmesg output will take service name, level of the dmesg contents and name as optional parameters.
`get_buffer_size_data(self, driver_name: str, driver_interface_number: str) -> Optional[list]` - responsible to return buffer size for respective drivername and interface number.
`get_os_package_info(self) -> Union[OSPackageInfo, None]` - responsible to return os package installed which is retrived from dmesg output.
`get_messages_additional(self, service_name: str = None, lines: int = 1000, expected_return_codes: Iterable = frozenset({0}), additional_greps: Optional[List[str]] = None) -> str` - responsible to return latest dmesg output based on addtional filters as specified by the user.
`verify_messages(self) -> dict` - responsible to check if there are err level messages in dmesg output.
`clear_messages(self, errors_filter: Optional[List[str]] = [], ignore_filter: Optional[List[str]] = [],) -> Tuple[str, List[str]]` - responsible to clear the message buffer of the kernel (dmesg).
`clear_messages_after_error(self, error_msg: str) -> Union[Tuple[str, List[str]], None]` - responsible to clear the message buffer of the kernel (dmesg) after user defined error occurred.
`check_errors(self, error_list: list) -> tuple` - responsible to check for the errors as specified by the user list or user can select from predefined list declared in constant file.
`check_str_present(self, service_name: str, lookout_str: str, additional_greps: Optional[List[str]] = None) -> bool` - responsible to check for particular user defined string in dmesg output.
`check_messages_format(self, driver: str, time_format: str = "%Y-%m-%dT%H:%M:%S.%fZ") -> Union[bool, None]` - responsible to check for userdefined time format or default time format in dmesg logs.
`check_new_errors(self) -> dict` - responsible to check for new errors in dmesg output apart from last time the dmesg log collected.

**Methods**
- `verify_log(driver: str) -> str` 

  Checks the system log for errors.

  **Parameters:**
  * driver - name of driver for check
  
  **Returns:**
  * `str` -  empty string if no errors found, error content otherwise

## Data Structures

Data structures returned by methods:

class OSPackageInfo:
    """Decorator for OS Package Information."""

    package_name: Optional[str] = None
    package_file: Optional[str] = None
    package_version: Optional[str] = None

## OS supported:

Here is a place to write what OSes support your MFD module:
* LINUX
* FREEBSD
* ESXI

## Issue reporting

If you encounter any bugs or have suggestions for improvements, you're welcome to contribute directly or open an issue [here](https://github.com/intel/mfd-dmesg/issues).
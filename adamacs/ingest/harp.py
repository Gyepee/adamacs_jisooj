import numpy as np
from element_interface.utils import find_full_path, find_root_directory
from adamacs.paths import get_experiment_root_data_dir
from pathlib import Path
import pandas as pd
from datetime import datetime

class HarpLoader:
    def __init__(self, harp_path):
        self.harp_path = Path(harp_path)
        if not self.harp_path.exists():
            self._harp_path_full = find_full_path(
                get_experiment_root_data_dir(), harp_path
            )
        else:
            self._harp_path_full = Path(harp_path)
        self._harp_path_relative = self._harp_path_full.relative_to(
            find_root_directory(get_experiment_root_data_dir(), self._harp_path_full)
        )

        self._harp_file = pd.read_csv(self._harp_path_full, header=None)


# ------------ Helper functions ------------

# class HarpLoader_csv:
#     def __init__(self, harp_path):
#         self.harp_path = Path(harp_path)
#         if not self.harp_path.exists():
#             self._harp_path_full = find_full_path(
#                 get_experiment_root_data_dir(), harp_path
#             )
#         else:
#             self._harp_path_full = Path(harp_path)
#         self._harp_path_relative = self._harp_path_full.relative_to(
#             find_root_directory(get_experiment_root_data_dir(), self._harp_path_full)
#         )

#         self._harp_file = open(self._harp_path_full, "rb")

#         self._reg34data = []
#         self._reg35data = []
#         self._reg34time = []
#         self._reg35time = []
#         self._reg35DI0 = []
#         self._reg35DI1 = []

#         while self._harp_file:
#             messageType = self._harp_file.read(1)
#             if messageType:
#                 messageType = messageType[0]
#             else:
#                 break
#             messageLength = self._harp_file.read(1)[0]
#             if messageLength == 4:
#                 message = self._harp_file.read(messageLength - 1)
#                 checksum = self._harp_file.read(1)
#                 # Daniel:  MATLAB if statement here doesn't seem to do anything
#             elif messageLength >= 10:
#                 message = self._harp_file.read(messageLength - 1)
#                 checksum = self._harp_file.read(1)
#                 # Daniel: MATLAB only does this if the checksum fulfills a condition
#                 dataLength = messageLength - 10
#                 elements = dataLength / (message[2] & 15)
#                 elementType = message[2] & 239
#                 register = message[0]
#                 if register == 35:
#                     if (message[2] & 16) == 0:
#                         self._reg35time.append(0)
#                     else:
#                         seconds = int.from_bytes(
#                             message[3:7], "little"
#                         )  # Daniel: correct byteorder?
#                         milliseconds_to_seconds = (
#                             int.from_bytes(message[7:9], "little") * 32 * 1e-6
#                         )
#                         self._reg35time.append(seconds + milliseconds_to_seconds)
#                     if elementType == 2:
#                         reg35_16bit = int.from_bytes(message[9:11], "little")
#                         reg35_16bit = clear_bit(
#                             reg35_16bit, 15
#                         )  # Daniel: set bits 16 and 15 to 0
#                         reg35_16bit = clear_bit(reg35_16bit, 14)
#                         self._reg35data.append(reg35_16bit)
#                         self._reg35DI1.append(bitget(reg35_16bit, 15))
#                         self._reg35DI0.append(bitget(reg35_16bit, 14))
#                 elif register == 34:
#                     if (message[2] & 16) == 0:
#                         self._reg34time.append(0)
#                     else:
#                         seconds = int.from_bytes(
#                             message[3:7], "little"
#                         )  # Daniel: Not sure if this is the correct byteorder
#                         milliseconds_to_seconds = (
#                             int.from_bytes(message[7:9], "little") * 32 * 1e-6
#                         )
#                         self._reg34time.append(seconds + milliseconds_to_seconds)
#                     if elementType == 130:
#                         self._reg34data.append(int.from_bytes(message[9:11], "little"))
#                         self._reg34data.append(int.from_bytes(message[11:13], "little"))
#                         self._reg34data.append(int.from_bytes(message[13:15], "little"))
#                         self._reg34data.append(int.from_bytes(message[15:17], "little"))
#                         self._reg34data.append(int.from_bytes(message[17:19], "little"))
#                         self._reg34data.append(int.from_bytes(message[19:21], "little"))
#                         self._reg34data.append(int.from_bytes(message[21:23], "little"))
#                         self._reg34data.append(int.from_bytes(message[23:25], "little"))
#                         self._reg34data.append(int.from_bytes(message[25:27], "little"))
#                         self._reg34data.append(int.from_bytes(message[27:29], "little"))

#         self._data_dict = {
#             "34_time": self._reg34time,
#             "34_data": self._reg34data,
#             "35_time": self._reg35time,
#             "35_data": self._reg35data,
#             "35_DI0_": self._reg35DI0,
#             "35_DI1_": self._reg35DI1,
#         }

    def data(self):
        return self._data_dict

    def data_for_insert(self):
        return [
            {
                "channel_name": "IMU accelerometer 1",
                "data": self._harp_file[0].to_numpy(),
                "time": [],
            },
            {
                "channel_name": "IMU accelerometer 2",
                "data": self._harp_file[1].to_numpy(),
                "time": [],
            },            
            {
                "channel_name": "IMU accelerometer 3",
                "data": self._harp_file[2].to_numpy(),
                "time": [],
            },            
            {
                "channel_name": "IMU gyroscope 1",
                "data": self._harp_file[3].to_numpy(),
                "time": [],
            },            
            {
                "channel_name": "IMU gyroscope 2",
                "data": self._harp_file[4].to_numpy(),
                "time": [],
            },            
            {
                "channel_name": "IMU gyroscope 3",
                "data": self._harp_file[5].to_numpy(),
                "time": [],
            },            
            {
                "channel_name": "IMU magnetometer 1",
                "data": self._harp_file[6].to_numpy(),
                "time": [],
            },            
            {
                "channel_name": "IMU magnetometer 2",
                "data": self._harp_file[7].to_numpy(),
                "time": [],
            },
            {
                "channel_name": "IMU magnetometer 3",
                "data": self._harp_file[8].to_numpy(),
                "time": [],
            },
        ]

    # def data_as_pandas(self):
    #     import pandas as pd

    #     self._data_dict = {
    #         "34_time": self._reg34time,
    #         "34_data": self._reg34data,
    #         "35_time": self._reg35time,
    #         "35_data": self._reg35data,
    #         "35_DI0_": self._reg35DI0,
    #         "35_DI1_": self._reg35DI1,
    #     }

    #     return pd.DataFrame(
    #         dict([(k, pd.Series(v)) for k, v in self._data_dict.items()])
    #     )


# ------------ Helper functions ------------

class HarpLoader_sync:
    def __init__(self, harp_sync_path):
        self.harp_sync_path = Path(harp_sync_path)
        if not self.harp_sync_path.exists():
            self._harp_sync_path_full = find_full_path(
                get_experiment_root_data_dir(), harp_sync_path
            )
        else:
            self._harp_sync_path_full = Path(harp_sync_path)
        self._harp_sync_path_relative = self._harp_sync_path_full.relative_to(
            find_root_directory(get_experiment_root_data_dir(), self._harp_sync_path_full)
        )

        self._harp_sync_file = pd.read_csv(self._harp_sync_path_full, header=None)


    def data(self):
        return self._data_dict

    def data_for_insert(self):
        
        # Convert the string to a datetime
        dt = pd.to_datetime(self._harp_sync_file[1].to_numpy())

        # Convert the datetime to UTC
        dt_utc = dt.tz_convert('UTC')

        # Get the Unix timestamp in milliseconds
        unix_timestamp_ms = dt_utc.astype(int) // 10**6
        time = unix_timestamp_ms - unix_timestamp_ms[0]   # subtract by AUX event HARP gate
             
        return [
            {
                "channel_name": "2p sync",
                "data": self._harp_sync_file[0].to_numpy(),
                "time": time.to_numpy(),
            },
        ]


def set_bit(value, bit):
    return value | (1 << bit)


def clear_bit(value, bit):
    return value & ~(1 << bit)


def bitget(value, bit_no):
    return (value >> bit_no) & 1


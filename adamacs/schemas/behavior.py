"""Tables related to behavioral data.

During some recordings behavioral data is recorded.
This module organizes the different types of behavioral
raw data and relates them to the Recording.
"""

import datajoint as dj
from ..pipeline import session, event, db_prefix
from ..paths import get_experiment_root_data_dir
from ..ingest.harp import HarpLoader
from element_interface.utils import find_full_path
from pywavesurfer import ws
import numpy as np
schema = dj.schema(db_prefix + "behavior")

__all__ = ["session", "db_prefix", "HarpDevice", "HarpRecording"]

# -------------- Table declarations --------------

# NOTE: Previous tables depreciated with the use of element-event


@schema
class HarpDevice(dj.Lookup):
    definition = """
    harp_device_id: int
    ---
    harp_device_name: varchar(36)
    harp_device_description='': varchar(1000)
    """

    contents = [(1, "HARP Wear IMU", "9doF IMU MPU-9250 Bonsai device")]


@schema
class HarpRecording(dj.Imported):
    definition = """
    -> event.BehaviorRecording
    -> HarpDevice
    """

    class Channel(dj.Part):
        definition = """
        -> master
        channel_name: varchar(36)
        ---
        data=null : longblob  # 1d array of acquired data for this channel
        time=null : longblob  # 1d array of timestamps for this channel 
        """

    def make(self, key):
        bpod_path_relative = (event.BehaviorRecording.File & key).fetch1("filepath")
        harp_paths = list(find_full_path(
            get_experiment_root_data_dir(), bpod_path_relative
        ).parent.glob("*IMU_harp*csv"))
        assert len(harp_paths) == 1, f"Found less or more than one harp file\n\t{harp_paths}"

        self.insert1(key)
        self.Channel.insert(
            [
                {**key, **channel} 
                for channel in HarpLoader(harp_paths[0]).data_for_insert()
            ]
        )

@schema
class TreadmillDevice(dj.Lookup):
    definition = """
    treadmill_device_id: int
    ---
    treadmill_device_name: varchar(36)
    treadmill_device_description='': varchar(1000)
    """

    contents = [(1, "rotary encoder", "BPod rotary encoder on running wheel")]


@schema
class TreadmillRecording(dj.Imported):
    definition = """
    -> event.BehaviorRecording
    -> TreadmillDevice
    """

    class Channel(dj.Part):
        definition = """
        -> master
        channel_name: varchar(36)
        ---
        data=null : longblob  # 1d array of acquired data for this channel
        time=null : longblob  # 1d array of timestamps for this channel 
        """

    def make(self, key):
        aux_path_relative = (event.BehaviorRecording.File & key).fetch1("filepath")
        
        curr_aux = ws.loadDataFile(filename=aux_path_relative, format_string='double' )
        sweep = [x for x in curr_aux.keys() if 'sweep' in x][0]
        sr = curr_aux['header']['AcquisitionSampleRate'][0][0]
        
        timebase = np.arange(curr_aux[sweep]['analogScans'].shape[1]) / sr
        bpod_wheel_data = curr_aux[sweep]['analogScans'][1]
        
        downsample = 10
        timebase = timebase[::downsample]
        bpod_wheel_data = bpod_wheel_data[::downsample]
        
        self.insert1(key)

        channeldata =  {
                "channel_name": 'wheel_pos',
                "data": bpod_wheel_data,
                "time": timebase
                }
        self.Channel.insert([{**key, **channeldata}])


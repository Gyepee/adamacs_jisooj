"""Ingest behavioral events from aux and bpod files.
The aux file is the only .h5 file in a scan directory.
The bpod file contains StimArenaMaster and is a .mat file."""

import numpy as np
import h5py
import matplotlib.pyplot as plt
from pywavesurfer import ws
from ..paths import get_imaging_root_data_dir
from element_interface.utils import find_full_path
from adamacs.pipeline import event, trial
import warnings
import pathlib
import re
import pdb


# TODO 
# 1. For each 

def demultiplex(auxdata, channels=5):
    """Demultiplex the digital data"""
    auxdata = auxdata.flatten()
    binary = [[int(x) for x in f'{x:0{channels}b}'] for x in auxdata]
    return np.array(binary, dtype=bool).T

def get_timestamps(data, sr, thr=1):
    """"""
    if data.dtype == 'bool':
        data = data > 0.5
    else:
        data = data > thr
    
    diff = np.diff(data)
    idc = np.argwhere(diff != 0)[:, 0]
    timestamps = idc / sr
    return timestamps

def prepare_timestamps(ts, session_key, scan_key, event_type):
    """Prepares timestamps for insert with datajoint"""
    ts_shutter_chan_start = ts[0::2]
    ts_shutter_chan_stop = ts[1::2]
    
    to_insert = [list(ts_shutter_chan_start), list(ts_shutter_chan_stop)]  
    to_insert = [[session_key, scan_key, event_type, *i] for i in zip(*to_insert)]  # transposes the list to get rows/cols right
    if len(to_insert) != len(ts_shutter_chan_start):
        to_insert.append([session_key, event_type, ts_shutter_chan_start[-1], ''])

    return to_insert

def ingest_aux(session_key, scan_key, root_paths=get_imaging_root_data_dir(),
                        verbose=False): #TR23: included scan key
     
    if not verbose:
        warnings.filterwarnings('ignore')

    paths = [pathlib.Path(path) for path in root_paths]
    valid_paths = [p for p in paths if p.is_dir()]
    match_paths = []
    for p in valid_paths:
        # match_paths.extend(list(p.rglob(f'*{session_key}*')))
        match_paths.extend([d for d in p.rglob(f'*{scan_key}*') if d.is_dir()]) #TR23: limit to dirs only
    
    n_aux = len(match_paths)
    if verbose:
        print(f'Number of aux-files found: {n_aux}')

    scan_pattern = "scan.{8}"
    basenames = [x.name for x in match_paths]
    scan_keys = [re.findall(scan_pattern, x) for x in basenames]
    scan_basenames = [x for x in basenames if bool(re.search(scan_pattern, x))]
    
    # For now this is only supposed to work for 1 scan per session
    if len(scan_basenames) != 1:
        raise ValueError(f"Found more or less than 1 scan in {session_key}")
    
    aux_files = []
    for k in scan_basenames:
        curr_path = find_full_path(root_paths, k)
        aux_file_paths = [fp.as_posix() for fp in curr_path.glob('*.h5')]
        if len(aux_file_paths) != 1:
            raise ValueError(f"More or less than 1 aux_files found in {k}")
        curr_file = ws.loadDataFile(filename=aux_file_paths[0], format_string='double' )
        aux_files.append(curr_file)
        
    start_datetime = aux_files[0]['header']['ClockAtRunStart'][:, 0]
    start_datetime = [x for x in start_datetime]
    for idx, x in enumerate(start_datetime):
        if idx != 5:
            start_datetime[idx] = str(int(start_datetime[idx]))
        else:
            start_datetime[idx] = str(float(start_datetime[idx]))
    start_datetime = '-'.join(start_datetime)
    sweep_duration = aux_files[0]['header']['SweepDuration'][0][0]

    event.BehaviorRecording.insert1({'session_id': session_key, 'scan_id': scan_key, 'recording_start_time': start_datetime, 'recording_duration': sweep_duration}, skip_duplicates=True)
    
    for p in aux_file_paths:
        event.BehaviorRecording.File.insert1([session_key, scan_key, p], skip_duplicates=True)
    for curr_aux in aux_files:
        sweep = [x for x in curr_aux.keys() if 'sweep' in x][0]

        sr = curr_aux['header']['AcquisitionSampleRate'][0][0]
        numberDI = len(curr_aux['header']['DIChannelNames'])
        timebase = np.arange(curr_aux[sweep]['analogScans'].shape[1]) / sr

        # DIGITAL SIGNALS
        digital_channels = demultiplex(curr_aux[sweep]['digitalScans'][0], numberDI)
        main_track_gate_chan = digital_channels[5]
        shutter_chan = digital_channels[4]
        mini2p_frame_chan = digital_channels[1]
        mini2p_line_chan = digital_channels[2]
        mini2p_vol_chan = digital_channels[3]
        mini2p_HARP_gate = digital_channels[0]

        main_track_gate_chan[-1] = 0  # TR23 - to partially save truncated recordings, set all last samples to zero
        shutter_chan[-1] = 0
        mini2p_frame_chan[-1] = 0
        mini2p_line_chan[-1] = 0
        mini2p_vol_chan[-1] = 0
        mini2p_HARP_gate[-1] = 0


        """Calculate timestamps"""
        ts_main_track_gate_chan = get_timestamps(main_track_gate_chan, sr)
        ts_shutter_chan = get_timestamps(shutter_chan, sr)
        ts_mini2p_frame_chan = get_timestamps(mini2p_frame_chan, sr)
        ts_mini2p_line_chan = get_timestamps(mini2p_line_chan, sr)
        ts_mini2p_vol_chan = get_timestamps(mini2p_vol_chan, sr)
        ts_mini2p_HARP_gate = get_timestamps(mini2p_HARP_gate, sr)
        


        """Analog signals"""
        cam_trigger = curr_aux[sweep]['analogScans'][0]
        bpod_trial_vis_chan = curr_aux[sweep]['analogScans'][1]
        bpod_reward1_chan = curr_aux[sweep]['analogScans'][2]
        bpod_tone_chan = curr_aux[sweep]['analogScans'][3]
        light_flash_chan = curr_aux[sweep]['analogScans'][4]
        
        cam_trigger[-1] = 0
        bpod_trial_vis_chan[-1] = 0
        bpod_reward1_chan[-1] = 0
        bpod_tone_chan[-1] = 0
        light_flash_chan[-1] = 0

        ts_cam_trigger = get_timestamps(cam_trigger, sr)
        ts_bpod_visual = get_timestamps(bpod_trial_vis_chan, sr)
        ts_bpod_reward = get_timestamps(bpod_reward1_chan, sr)
        ts_bpod_tone = get_timestamps(bpod_tone_chan, sr)
        ts_light_flash =  get_timestamps(light_flash_chan, sr)
        
        # Insert timestamps into tables 
        # - TR23: Why not define event type headers here?
        event_types = ['main_track_gate', 'HARP_gate', 'shutter',  'mini2p_frames', 'mini2p_lines', 'mini2p_volumes', 'aux_cam', 'arena_LED',
                    'aux_bpod_visual', 'aux_bpod_reward', 'aux_bpod_tone']

        for e in event_types:
            event.EventType.insert1({'event_type': e, 'event_type_description': ''}, skip_duplicates=True,)

        event_types = {
            'main_track_gate': ts_main_track_gate_chan,
            'HARP_gate': ts_mini2p_HARP_gate,
            'arena_LED': ts_light_flash,
            'shutter': ts_shutter_chan,
            'mini2p_frames': ts_mini2p_frame_chan,
            'mini2p_lines': ts_mini2p_line_chan,
            'mini2p_volumes': ts_mini2p_vol_chan,
            'aux_cam': ts_cam_trigger,
            'aux_bpod_visual': ts_bpod_visual,
            'aux_bpod_reward': ts_bpod_reward,
            'aux_bpod_tone': ts_bpod_tone
        }
        
        for event_type, timestamps in event_types.items():
            to_insert = prepare_timestamps(timestamps, session_key, scan_key, event_type)
            event.Event.insert(to_insert, skip_duplicates=True, allow_direct_insert=True)
        
        

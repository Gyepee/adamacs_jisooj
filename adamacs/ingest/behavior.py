"""Ingest behavioral events from aux and bpod files.
The aux file is the only .h5 file in a scan directory.
The bpod file contains StimArenaMaster and is a .mat file."""

import numpy as np
import h5py
import matplotlib.pyplot as plt
from pywavesurfer import ws
from ..paths import get_imaging_root_data_dir, get_experiment_root_data_dir
from element_interface.utils import find_full_path
from adamacs.pipeline import event, trial, scan
from adamacs.ingest.bpod import Bpodfile
import warnings
import pathlib
import re
import pdb
import pandas as pd

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
        data = np.abs(data) > thr #TR23: np.abs to cope with negative voltages
    
    diff = np.diff(data)
    idc = np.argwhere(diff != 0)[:, 0]
    timestamps = idc / sr
    return timestamps

def prepare_timestamps(ts, session_key, scan_key, event_type):
    """Prepares timestamps for insert with datajoint"""
    ts_chan_start = ts[0::2]
    ts_chan_stop = ts[1::2]
    
    to_insert = [list(ts_chan_start), list(ts_chan_stop)]  
    to_insert = [[session_key, scan_key, event_type, *i] for i in zip(*to_insert)]  # transposes the list to get rows/cols right
    if len(to_insert) != len(ts_chan_start):
        to_insert.append([session_key, event_type, ts_chan_start[-1], ''])

    return to_insert

def ingest_bpod(sessi, scansi, root_paths=get_imaging_root_data_dir(), aux_setup_type = "openfield",
                        verbose=False): #TR23: included scan key, included setupID
     
    if not verbose:
        warnings.filterwarnings('ignore')
    scan_key = (scan.Scan & f'scan_id = "{scansi}"').fetch('KEY')[0]
    bpod_path_relative = (scan.ScanPath & scan_key).fetch("path")[0]
    bpod_path_full = list(find_full_path(
        get_experiment_root_data_dir(), bpod_path_relative
        ).glob("*mat"))[0]
    bpod_object = Bpodfile(bpod_path_full)
    bpod_object.ingest(sessi, scansi)

        
def ingest_aux(session_key, scan_key, root_paths=get_imaging_root_data_dir(), aux_setup_type = "openfield",
                        verbose=False): #TR23: included scan key, included setupID
     
    if not verbose:
        warnings.filterwarnings('ignore')

    paths = [pathlib.Path(path) for path in root_paths]
    valid_paths = [p for p in paths if p.is_dir()]
    match_paths = []
    for p in valid_paths:
        # match_paths.extend(list(p.rglob(f'*{session_key}*')))
        match_paths.extend([d for d in p.rglob(f'*{scan_key}*{session_key}*') if d.is_dir()]) #TR23: limit to dirs only
    
    n_aux = len(match_paths)
    if verbose:
        print(f'Number of aux-files found: {n_aux}')
        print(match_paths)

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

    recording_notes = ''

    event.BehaviorRecording.insert1({'session_id': session_key, 'scan_id': scan_key, 'recording_start_time': start_datetime, 'recording_duration': sweep_duration, 'recording_notes': recording_notes}, skip_duplicates=True)
    
    for p in aux_file_paths:
        event.BehaviorRecording.File.insert1([session_key, scan_key, p], skip_duplicates=True)
    for curr_aux in aux_files:
        sweep = [x for x in curr_aux.keys() if 'sweep' in x][0]

        sr = curr_aux['header']['AcquisitionSampleRate'][0][0]
        numberDI = len(curr_aux['header']['DIChannelNames'])
        timebase = np.arange(curr_aux[sweep]['analogScans'].shape[1]) / sr

        if aux_setup_type == "openfield":
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
            # ts_mini2p_line_chan = get_timestamps(mini2p_line_chan, sr)
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

            # event_types = ['main_track_gate', 'HARP_gate', 'shutter',  'mini2p_frames', 'mini2p_lines', 'mini2p_volumes', 'aux_cam', 'arena_LED',
            #             'aux_bpod_visual', 'aux_bpod_reward', 'aux_bpod_tone']
            
            
            event_types = {
                'main_track_gate': ts_main_track_gate_chan,
                'HARP_gate': ts_mini2p_HARP_gate,
                'arena_LED': ts_light_flash,
                'shutter': ts_shutter_chan,
                'mini2p_frames': ts_mini2p_frame_chan,
                # 'mini2p_lines': ts_mini2p_line_chan,
                'mini2p_volumes': ts_mini2p_vol_chan,
                'aux_cam': ts_cam_trigger,
                'aux_bpod_visual': ts_bpod_visual,
                'aux_bpod_reward': ts_bpod_reward,
                'aux_bpod_tone': ts_bpod_tone
            }
                        
        elif aux_setup_type == "headfixed": #TR23 - HEADFIXED MINI2p - #mini2p01 - needs to be set in scan schema! Taken from userfunction_consolidate_files argument
            print("not done")
        elif aux_setup_type == "bench2p": #TR23 - HEADFIXED Bench2p - #bench2p - needs to be set in scan schema! Taken from userfunction_consolidate_files argument
            
            # LOAD STIMINFO
            for k in scan_basenames:
                stim_file_paths = [fp.as_posix() for fp in curr_path.glob('*bonsai_stimulus_events*.csv')]
                if len(stim_file_paths) != 1:
                    # raise ValueError(f"More or less than 1 stim_files found in {k}")
                    print(f"More or less than 1 stim_files found in {k} - not extracting stim IDs")
                    vis_stim_event_list = []
                else:
                    # Load the csv file
                    df = pd.read_csv(stim_file_paths[0])
                    # Extract the third column
                    vis_stim_event_list = df['Value']
            
            # DIGITAL SIGNALS
            digital_channels = demultiplex(curr_aux[sweep]['digitalScans'][0], numberDI)
            main_track_gate_chan = digital_channels[4]
            shutter_chan = digital_channels[3]
            bench2p_frame_chan = digital_channels[2]
            bench2p_line_chan = digital_channels[1]
            bench2p_vol_chan = digital_channels[0]

            main_track_gate_chan[-1] = 0  # TR23 - to partially save truncated recordings, set all last samples to zero
            shutter_chan[-1] = 0
            bench2p_line_chan[-1] = 0
            bench2p_frame_chan[-1] = 0
            bench2p_vol_chan[-1] = 0


            """Calculate timestamps"""
            ts_main_track_gate_chan = get_timestamps(main_track_gate_chan, sr)
            ts_shutter_chan = get_timestamps(shutter_chan, sr)
            ts_bench2p_frame_chan = get_timestamps(bench2p_frame_chan, sr)
            # ts_bench2p_line_chan = get_timestamps(bench2p_line_chan, sr)
            ts_bench2p_vol_chan = get_timestamps(bench2p_vol_chan, sr)


            """Analog signals"""
            cam_trigger = curr_aux[sweep]['analogScans'][2]
            bonsai_vis_chan = curr_aux[sweep]['analogScans'][0]
            # bpod_speed_chan = curr_aux[sweep]['analogScans'][1]
            
            cam_trigger[-1] = 0
            bonsai_vis_chan[-1] = 0
            # bpod_speed_chan[-1] = 0

            ts_cam_trigger = get_timestamps(cam_trigger, sr)
            ts_bonsai_vis = get_timestamps(bonsai_vis_chan, sr)
            # ts_bpod_speed = get_timestamps(bpod_speed_chan, sr) #TR23: Data channel! Not Event channel!
            
            # Insert timestamps into tables             
            
            event_types = {
                'main_track_gate': ts_main_track_gate_chan,
                'shutter': ts_shutter_chan,
                'bench2p_frames': ts_bench2p_frame_chan,
                # 'bench2p_lines': ts_bench2p_line_chan,
                'bench2p_volumes': ts_bench2p_vol_chan,
                'aux_cam': ts_cam_trigger,
                # 'aux_bonsai_vis': ts_bonsai_vis,
            }
            
            j = 0
            for stim_event in vis_stim_event_list:  
                event_types[stim_event] = []
            for i, stim_event in enumerate(vis_stim_event_list):  
                event_types[stim_event] = np.append(event_types[stim_event], ts_bonsai_vis[j:j+2])
                j += 2
            
            if len(vis_stim_event_list) != ts_bonsai_vis.size / 2:
                print('Aux-File und StimLog have not the same number of stimulus onsets!')
            #     print('Attempting repair - THIS IS A HACK! ARTIFICIALLY INTRODUCING STIMULUS ENDINGS IN FILE! MAKE SURE TO CRRECT THAT DURING ACQ!')
                
            #     ITI = np.sort(np.unique(np.round(np.diff(ts_bonsai_vis))))[1] #find stim duration
            #     DUR = np.sort(np.unique(np.round(np.diff(ts_bonsai_vis))))[0] #find ITI duration
                
            #     block_edges = np.where(np.diff(ts_bonsai_vis)>ITI + 1) #find index of stim block edges
            #     ts_bonsai_vis[block_edges]+ITI #add ITI duration
                
            #     on_off_values_insert = np.array(list(zip(ts_bonsai_vis[block_edges[0]]+DUR, ts_bonsai_vis[block_edges[0]]+DUR + ITI)))
                
            #     ts_bonsai_vis_corrected = ts_bonsai_vis
                
            #     index = block_edges[0] + 1
            #     for value in on_off_values_insert:
            #             ts_bonsai_vis_corrected = np.insert(ts_bonsai_vis_corrected, index, value)
            #             index += len(value)

                
                # raise ValueError(f"Aux-File und StimLog have not the same number of stimulus onsets!{k}")
                
            
            
        elif aux_setup_type == "macroscope": #TR23 -  HEADFIXED Macroscope - #macroscope - needs to be set in scan schema! Connot be taken from userfunction_consolidate_files
            print("not done")
        
        
        
        # Insert into tables
        for e in event_types:
            event.EventType.insert1({'event_type': e, 'event_type_description': ''}, skip_duplicates=True)
            
        for event_type, timestamps in event_types.items():
            to_insert = prepare_timestamps(timestamps, session_key, scan_key, event_type)
            event.Event.insert(to_insert, skip_duplicates=True, allow_direct_insert=True)
        
 
        
def get_and_ingest_trial_times(scan_key, aux_setup_type):                   
    session_key = (scan.Scan & f'scan_id = "{scan_key}"').fetch('session_id')[0]
    scan_key_key = (scan.Scan & f'scan_id = "{scan_key}"').fetch('KEY')[0]         
              
    if aux_setup_type == "bench2p":
                    
        # Extract Trials 
        
            
        stims_per_trial = len(set((event.Event & scan_key_key & 'event_type LIKE "%;%"').fetch("event_type")))
        # all_stims = (event.Event & scan_key & 'event_type LIKE "%;%"').fetch("event_type")
        # trial_stims = {x: list(all_stims).count(x) for x in all_stims}
        # trials = set([list(all_stims).count(x) for x in all_stims])
        
        trial_start_edges = (event.Event & scan_key_key & 'event_type LIKE "%;%"').fetch("event_start_time",order_by = "event_start_time")[::stims_per_trial] 
        trial_end_edges = (event.Event & scan_key_key & 'event_type LIKE "%;%"').fetch("event_end_time",order_by = "event_end_time")[stims_per_trial-1::stims_per_trial]     
            
        trial_event_name = (event.Event & scan_key_key & 'event_type LIKE "%;%"').fetch("event_type")[0].split(':')[0]
        trial.TrialType().insert1({'trial_type': trial_event_name, 'trial_type_description': 'Stimulus nomenclature: Type; Class; Azimuth; Elevation; Size; Orientation; Spatial Frequency; Temporal Frequency'}, skip_duplicates=True)
                
        for trialnum in enumerate(trial_start_edges):
            trial.Trial.insert1({'session_id': session_key, 'scan_id': scan_key, 'trial_id': trialnum[0]+1, 'trial_type': trial_event_name, 'trial_start_time': trial_start_edges[trialnum[0]], 'trial_stop_time': trial_end_edges[trialnum[0]]},  allow_direct_insert=True, skip_duplicates=True)
            
            # generate query object from joint Trial Event table
            TrialEvent_query_keys = (event.Event * trial.Trial & scan_key_key & f'event_type LIKE "%;%"' & f'event_start_time <= "{trial_end_edges[trialnum[0]]}"' & f'event_end_time >= "{trial_start_edges[trialnum[0]]}"' & f'trial_id= "{trialnum[0] + 1}"') #.fetch(format = "frame", order_by = "event_start_time")
            
            # do server-side insert - fetch does not work. The number key seems to be rounded.
            trial.TrialEvent.insert(TrialEvent_query_keys,  allow_direct_insert=True, skip_duplicates=True, ignore_extra_fields=True)

                
def compute_angular_velocity(time, angle, window):
    # Convert the angles to radians
    angle = np.radians(angle)
    
    # Unwrap the angles to handle wrap-around
    unwrapped_angle = np.unwrap(angle)
    
    # Convert back to degrees
    unwrapped_angle = np.abs(np.degrees(unwrapped_angle))
    
    # Calculate rolling mean with the defined window size
    unwrapped_angle_smoothed = np.convolve(unwrapped_angle, np.ones(window), 'valid') / window
    
    
    # Calculate the difference in angles and time
    angle_diff = np.diff(unwrapped_angle_smoothed)
    time_diff = np.diff(time)
    
    # Calculate angular velocity
    angular_velocity_smoothed = angle_diff / time_diff[:-window+1]
    
    return angular_velocity_smoothed, unwrapped_angle_smoothed
        
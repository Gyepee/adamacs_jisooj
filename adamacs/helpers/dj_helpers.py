#!/usr/bin/env python
# coding: utf-8

# Tobias Rose 2023

import numpy as np
import pathlib
import seaborn as sns
import matplotlib.pyplot as plt


def plot_event_trial_start_times(event_data, trial_data):
    # Set the Seaborn style to dark
    sns.set(style="dark")

    # Set the style to 'dark_background'
    plt.style.use('dark_background')

    # Preparing event data for plotting
    event_times_by_type = {}
    for data in event_data:
        etype = data['event_type']
        etime = data['event_start_time']
        if etype not in event_times_by_type:
            event_times_by_type[etype] = []
        event_times_by_type[etype].append(etime)

    # Integrating trial start times into event data
    for data in trial_data:
        ttype = data['trial_type']
        ttime = data['trial_start_time']
        # Use a prefix like 'trial-' to distinguish trial types from event types
        ttype_key = f'trial-{ttype}'
        if ttype_key not in event_times_by_type:
            event_times_by_type[ttype_key] = []
        event_times_by_type[ttype_key].append(ttime)

    # Define the HUSL color palette (one color per event/trial type)
    colors = sns.husl_palette(len(event_times_by_type), h=0.5, s=0.8, l=0.7)

    # Plotting
    plt.figure(figsize=(50, 8))
    for i, (etype, etimes) in enumerate(event_times_by_type.items()):
        plt.eventplot(etimes, lineoffsets=i, linelengths=0.8, colors=[colors[i]], label=etype)

    plt.yticks(range(len(event_times_by_type)), list(event_times_by_type.keys()))
    plt.xlabel('Event Start Time')
    plt.ylabel('Event/Trial Type')
    plt.title('Event and Trial Start Times Plot')
    # plt.legend()
    plt.show()


def get_session_dir_key_from_dir(directory):
    return [path.split('/')[-1] for path in directory]
     
def get_scan_dir_key_from_dir(directory):
    return [path.split('/')[-1] for path in directory]

def get_session_key_from_dir(string):
    result = [re.search(r'sess\S+', item).group(0) for item in string]
    return result

def get_user_initials_from_dir(string):
    result = [name[:2] for name in string]
    return result

def get_subject_key_from_dir(string):
    result = [item.split("_")[1] for item in string]
    return result

def get_date_key_from_dir(directory):
    return directory.split("_")[-3]

def get_scan_key_from_dir(string):
    result = [re.search(r'scan\S+_', item).group(0)[:-1] for item in string]
    return result
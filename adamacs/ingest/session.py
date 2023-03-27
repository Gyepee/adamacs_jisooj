import re
import pathlib
import warnings
from itertools import groupby
from ..pipeline import subject, session, scan
from ..paths import get_imaging_root_data_dir
from datajoint.errors import DuplicateError
from element_interface.utils import find_full_path
from adamacs.ingest.pyrat import PyratIngestion

""" Notes from Chris
1. I placed previous default (r'C:\\datajoint') as the default for
    get_imaging_root_data_dir when the relevant config field is empty
2. For improved functionality, we might make better use of get_scan_image_files, which
    concatenates the root and session dirs. Currently, the function below has to find
    the session directory from the root, rather than being root agnostic.
"""


def ingest_session_scan(session_key, root_paths=get_imaging_root_data_dir(), project_key='dummy', equipment_key='dummy', location_key='dummy', software_key='ScanImage', verbose=False):
    """Locate all directories in session_path that are part
    of the sesssion. Extract the following attributes from
    the directory names:
        Subject
        session_datetime
        User
    """
    if not verbose:
        warnings.filterwarnings('ignore')

    paths = [pathlib.Path(path) for path in root_paths]
    valid_paths = [p for p in paths if p.is_dir()]
    match_paths = []
    for p in valid_paths:
        match_paths.extend(list(p.rglob(f'*{session_key}*'))) #TR: added Tiff extention here.
    
    n_scans = len(match_paths)
    if verbose:
        print(f'Number of scans found: {n_scans}')

    scan_pattern = "scan.{8}"
    basenames = [x.name for x in match_paths]
    scan_keys = [re.findall(scan_pattern, x) for x in basenames]
    scan_basenames = [x for x in basenames if bool(re.search(scan_pattern, x))]

    for idx, k in enumerate(scan_keys):
        if verbose:
            print(scan_keys)
            print(basenames)
        if len(k) != 1:
            raise ValueError(f'Directory name contains {len(k)} scan keys. Must be 1.')
        scan_keys[idx] = k[0]

    # Find the animal ID by position
    subjects = [x.split('_')[1] for x in basenames]

    if not all_equal(subjects):
        raise ValueError("Scans from multiple animals found. Must be 1 animal.")
    subject_id = subjects[0]
    if not (subject.Subject & f'subject=\"{subject_id}\"'):
        # raise ValueError(f'Subject {subject_id} must be added before this session.')
        print(f'Subject {subject_id} will be added to ingest this session.')
        PyratIngestion().ingest_animal(subject_id, prompt=False)

    # Find the user ID by position
    # CB NOTE: Will future data folders match user_id int values from pyrat ingestion? 
    # TR NOTE: Actually, no. The pyrat ingestion users are not going to be the real users of the animals. These are Laura and myself. We are the "owners" of the animals. So this has to be separate, also for the pyrat ingest. I suggest to call the pyrat ingest from a specific user ID - and have the very monolithic user table generated once.

    user_keys = [x.split('_')[0] for x in basenames]
    if not all_equal(user_keys):
        raise ValueError("Scans from multiple users found. Must be 1 user.")
    query = (subject.User & f'initials=\"{user_keys[0]}\"') #TR: now taking user ID from dir name
    user = query.fetch('user_id')[0]

    dates = [x.split('_')[2] for x in basenames]
    if not all_equal(dates):
        raise ValueError("Found different dates for session. Must be on same date.")
    date = dates[0]
    
      

    try:
        session.Session.insert1((session_key, subject_id, date))
    except DuplicateError:
        warnings.warn(f'\nSkipped existing session row: {session_key, subject, date}',
                      stacklevel=2)

    # default_project_id = "TEC"
    try:
        session.ProjectSession.insert1((project_key, session_key)) #TR: has to match project table (shorthand - NOT description)
    except DuplicateError:
        warnings.warn(f'\nSkipped existing ProjectSession row: {project_key, session_key}',
                      stacklevel=2)

    # CB NOTE: I think this should be modified to store the relative path
    try:
        session.SessionDirectory.insert1((session_key, match_paths[0], user))
    except DuplicateError:
        warnings.warn('\nSkipped existing SessionDirectory: '
                      + f'{session_key, match_paths[0]}', stacklevel=2)
        
    try:
        session.SessionUser.insert1((session_key, user))
    except DuplicateError:
        warnings.warn(f'\nSkipped existing SessionUser row: {session_key, user}',
                      stacklevel=2)

    session_dict = {
        'same_site_id': session_key}
    try:
        session.SessionSite.insert1((session_dict))
    except DuplicateError:
        warnings.warn(f'\nSkipped existing SessionSite row: {session_key}',
                      stacklevel=2)
    
    session_dict = {
        'session_id': session_key,
        'same_site_id': session_key}
    try:
        session.SessionSameSite.insert1((session_dict)) # TR: Same Key is default. Update manually for chronic recordigns!
    except DuplicateError:
        warnings.warn(f'\nSkipped existing SessionSite row: {session_key}',
                      stacklevel=2)


    # Insert each scan %TR: Why is that not inherited from Session??
    for idx, s in enumerate(scan_keys):
        # equipment_placeholder = "dummy"  # TODO: Inherit From Session!
        # software_placeholder = "ScanImage"
        # location_placeholder = "dummy"
        path = find_full_path(root_paths, scan_basenames[idx])
        try:
            scan.Scan.insert1((session_key, s, equipment_key,
                               software_key, ''))
        except DuplicateError:
            warnings.warn(f'\nSkipped existing scan: {s}',
                          stacklevel=2)
        
        try:
            scan.ScanLocation.insert1((session_key, s, location_key))
        except DuplicateError:
            warnings.warn(f'\nSkipped existing ScanLocation: {s}',
                          stacklevel=2)
        # CB DEV NOTE: 1. How does ScanPath differ from SessionDirectory?
        #              2. Removed s scankey from this insert. Does ScanPath need
        #                 expanding to include ScanKey?
        try:
            scan.ScanPath.insert1((session_key, s, user, path))
        except DuplicateError:
            warnings.warn(f'\nSkipped existing ScanPath: {s}',
                          stacklevel=2)


def all_equal(iterable):
    # Return true if all elements in iterable are equal
    g = groupby(iterable)
    return next(g, True) and not next(g, False)

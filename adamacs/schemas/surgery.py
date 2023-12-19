"""Tables related to animal surgery

A User might perform one or more surgeries on a mouse.
During a surgery, several procedures might be performed. For
example, a viral injection at a certain stereotaxic coordinate
might be followed by a cranial window at different coordinates.
Anesthesia is required for a surgery. Analgesia must be given at
least once before the surgery but could be given multiple times
and might also be given after a surgery or might be associated
with other procedures."""

# from adamacs.utility import rspace_connect
import datajoint as dj
from . import subject
from .. import db_prefix

schema = dj.schema(db_prefix + 'surgery')

__all__ = ['Anesthesia', 'Analgesia', 'Antagonist', 'Surgery', 'SurgeryNote', 'Virus',
           'AnalgesiaSubject', 'Coordinates', 'ViralInjection', 'CranialWindow',
           'AnatomicalLocation', 'subject']


# -------------- Table declarations --------------


@schema
class Anesthesia(dj.Manual):
    definition = """
    anesthesia  : varchar(16)
    ---
    long_name   : varchar(300)
    """


@schema
class Analgesia(dj.Manual):
    definition = """
    analgesia   : varchar(16)
    ---
    long_name   : varchar(300)
    """


@schema
class Antagonist(dj.Manual):
    definition = """
    # The compound used to counter the anesthetic after surgery
    antagonist  : varchar(16)
    ---
    long_name   : varchar(300)
    """


@schema
class Surgery(dj.Manual):
    definition = """
    -> subject.Subject
    date              : date      
    ---
    weight            : float     # subject weight
    -> subject.User
    -> Anesthesia
    anesthesia_time   : time
    anesthesis_volume : float
    -> Antagonist
    antagonist_time   : time
    antagonist_volume : float
    """
    ''' Previous code for RSpace:
    def make(self, key):  #placeholder for RSpace query -> datajoint table
        rspace_doc = rspace_connect().get_documents(query='Filename_{}'.format(key))
        surgery_data = rspace_doc['contents']
        self.insert1()
        # Which other tables below will be populated from RSpace?
        # If any, consider making dj.Part tables to share the same RSpace query
    '''


@schema
class SurgeryNote(dj.Manual):
    definition = """
    -> Surgery
    ---
    note    : varchar(2048)
    """
    # DEV NOTE: 16383 is the max for varchar. BLOB or TEXT can handle more.
    #           How much is needed?


@schema
class Virus(dj.Manual):
    definition = """
    name        : varchar(16) 
    serotype    : varchar(64)
    ---
    long_name   : varchar(300)
    """


@schema
class AnalgesiaSubject(dj.Manual):
    definition = """
    -> Analgesia
    -> subject.Subject
    datetime   : datetime
    ---
    """


@schema
class Coordinates(dj.Manual):
    definition = """
    coordinates        : varchar(32)
    ---
    x_coordinate    : float  # in mm
    y_coordinate    : float  # in mm
    z_coordinate    : float  # in mm
    description=''  : varchar(300)
    """


@schema
class ViralInjection(dj.Manual):
    definition = """
    -> Surgery
    -> Virus
    -> Coordinates
    ---
    datetime   : time
    volume     : float  # in ul
    """


@schema
class CranialWindow(dj.Manual):
    definition = """
    -> Surgery
    ---
    time   : time
    """


@schema
class AnatomicalLocation(dj.Manual):
    definition = """
    anatomical_location    : varchar(16)
    """


anatomical_data = [{'anatomical_location': 'V1'},
        {'anatomical_location': 'LGNV1'},
        {'anatomical_location': 'ATN'},
        {'anatomical_location': 'RSCa'},
        {'anatomical_location': 'RSCg'},
        {'anatomical_location': 'dCA1'},
        {'anatomical_location': 'DG'},
        {'anatomical_location': 'Ctx'},
        {'anatomical_location': 'VISrl'},
        {'anatomical_location': 'VISam'},
        {'anatomical_location': 'VISpm'},
        {'anatomical_location': 'VISal'},
        {'anatomical_location': 'VISI'},
        {'anatomical_location': 'dummy'}]
AnatomicalLocation.insert(anatomical_data, skip_duplicates=True) 
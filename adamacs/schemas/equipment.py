"""Tables related to equipment.

We use a variety of different equipment 
"""
import datajoint as dj
from .. import db_prefix
schema = dj.schema(db_prefix + 'equipment')

__all__ = ['db_prefix', 'Equipment']

# -------------- Table declarations --------------


@schema
class Equipment(dj.Manual):
    definition = """
    scanner                        : varchar(32)
    ---
    scanner_description=''         : varchar(255)
    """

@schema
class Restraint(dj.Manual):
    definition = """
    restraint                        : varchar(32)
    ---
    restraint_description=''         : varchar(255)
    """

@schema
class Device(dj.Manual):
    definition = """
    camera                        : varchar(32)
    ---
    camera_description=''         : varchar(255)
    """

# CB DEV NOTE: I suggest adding Device here as a foreign key for DLC camera and then
#              changing the reference in adamacs.pipeline. Currently, dlc relies on
#              the above 'scanner' table for camera information, see model_videos.csv



restraint_data = [
 {'restraint': 'headfixed',
  'restraint_description': 'headfixed recording',
 },
 {'restraint': 'unrestrained',
  'restraint_description': 'freely moving recording',
 }
]

Restraint.insert(restraint_data, skip_duplicates=True)

import datajoint as dj
from .. import db_prefix

schema = dj.schema(db_prefix + 'subject')


# -------------- Table declarations --------------


@schema
class Lab(dj.Manual):
    definition = """
    lab             : varchar(8)   # short lab name   
    ---
    lab_name        : varchar(255)
    institution     : varchar(255)
    address         : varchar(255)
    """


@schema
class Protocol(dj.Manual):
    definition = """
    # protocol approved by some institutions like IACUC, IRB
    protocol                        : varchar(16)
    ---
    protocol_description=''         : varchar(255)
    """


@schema
class Line(dj.Manual):
    definition = """
    # animal line 
    line                        : varchar(32)
    ---
    line_name=''                : varchar(3000)
    target_genotype=''          : varchar(255)
    is_active                   : boolean
    """


@schema
class Mutation(dj.Manual):
    definition = """
    # The mutations of animal lines
    -> Line
    mutation                    : varchar(32)
    ---
    description=''              : varchar(2000)
    """


@schema
class User(dj.Lookup):
    definition = """
    user                : varchar(32)
    ---
    full_name           :
    -> Lab
    """


@schema
class Project(dj.Lookup):
    definition = """
    project                 : varchar(32)
    ---
    project_description=''  : varchar(1024)
    """


@schema
class Subject(dj.Manual):
    definition = """
    # Animal Subject
    # Our Animals are not uniquely identified by their ID
    # because different labs use different animal facilities.
    # CB: I see cage as an item in PyRAT export - relevant in analysis?

    subject                 : varchar(16)  # ID
    ---
    -> Lab
    earmark=''              : varchar(16)  # aka lab_id
    sex                     : enum('M', 'F', 'U')  # Geschlecht
    birth_date              : date  # Geb.
    subject_description=''  : varchar(1024)
    generation              : varchar(255)  # Generation (F2 in example sheet)
    litter                  : varchar(8)  # The single letter identifying the litter of the generation
    owner                   : varchar(255)  # Besitzer
    responsible             : varchar(255)  # Verantwortlicher
    -> Line                 # Linie / Stamm
    -> User                 # 
    -> Project
    -> Protocol
    """


@schema
class SubjectGenotype(dj.Manual):
    definition = """
    -> Subject
    -> Mutation
    ---
    genotype        : enum('wt/wt', 'wt/tg', 'tg/wt', 'tg/tg')
    """


@schema
class SubjectDeath(dj.Manual):
    definition = """
    -> Subject
    ---
    death_date      : date       # death date
    cause           :    varchar(255)
    """

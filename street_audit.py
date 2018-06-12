# This file was only used to audit the street names and test
# the data cleaning of those names.
# The data is actually cleaned when preparing the database, 
# which can be seen in database_prep.py

import xml.etree.cElementTree as ET
from collections import defaultdict
import re
import pprint

# The audit was performed with a small and medium sample, 
# as well as with the full OSM file.
# The small sample file is provided in the repository and can be used
# to see how the auditing and cleaning procedures work.
OSMFILE = "small_sample.osm"

# Regular expression were used to find the end of a street name
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)

# The street names are eventually standardized into the
# unabbreviated names ("Street" instead of "St.", for example)
# Therefore, these are some correct endings to street names 
# that the program looks for when auditing the names
expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road",
            "Trail", "Parkway", "Commons", "Circle", "Loop", "Terrace", "Way", "Circus", "View",
            "Row", "Broadway", "Highway"]

# A dictionary is used to correct the names into their proper form
# in the update function
mapping = { "St": "Street",
            "St.": "Street",
            "st.": "Street",
            "Ave.": "Avenue",
            "Ave": "Avenue",
            "AVE": "Avenue",
            "Rd.": "Road",
            "Rd": "Road",
            "Dr": "Drive",
            "Dr.": "Drive",
            "Blvd": "Boulevard",
            "Blvd.": "Boulevard",
            "Cir": "Circle",
            "Hwy": "Highway",
            "Pkwy": "Parkway",
            "Pky": "Parkway",
            }
# These were some cases that came up in the auditing process
# that I decided to manually correct
specific_mappings = { "8202 SE Flavel St, Portland, OR 97266": "8202 SE Flavel Street",
                      "US 26 (OR)": "US Highway 26",
                      "North Missouri Ave-Michigan Ave Alley": "North Missouri Avenue - Michigan Avenue Alley",
                      " Southeast Hwy 212": "Southeast Highway 212",
                      "Southeast Hwy 212": "Southeast Highway 212",
                      "Southeast Stark Street;SE Stark St": "Southeast Stark Street",
                      "North Marine Srive": "North Marine Drive",
                      "unknown": "N/A",
                      "gresham": "Gresham"
                      }
# A few street names ended with a "#" symbol 
# and then one of these characters.
# The "#" symbol followed by any of these characters were removed
# from the end of the street name
special_cases = {"D", "101", "C113", "E"}

#The following two functions were created for use in the audit function
def is_street_name(elem):
    """Check if the tag is a street name"""

    return (elem.attrib['k'] == "addr:street")

def audit_street_type(street_types, street_name):
    """Put any street type in the incorrect form and 
    any street names in that category in a default dict of a set"""

    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            street_types[street_type].add(street_name)

def audit(osmfile):
    """Parses the OSM file for node or way tags and performs the audit"""

    osm_file = open(osmfile, "r")
    street_types = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])
    osm_file.close()
    return street_types

def update_name(name):
    """Return a street name in its proper form 
    according to the conventions listed above"""

    m = street_type_re.search(name)
    street_type = m.group()
    if name in specific_mappings:
        name = name.replace(name, specific_mappings[name])
    elif street_type in mapping:
        name = name.replace(street_type, mapping[street_type]).strip(".").strip(" ")
    elif street_type in special_cases:
        name_to_replace = " #" + street_type
        name = name.replace(name_to_replace, "")
    return name

def test():
    """Run the audit and see if the cleaning steps work"""
    st_types = audit(OSMFILE)
    pprint.pprint(dict(st_types))

    for st_type, ways in st_types.iteritems():
        for name in ways:
            better_name = update_name(name)
            print name, "=>", better_name
            if name == "N. Charleston Ave.":
                assert better_name == "N. Charleston Avenue"
            if name == "Northeast 82nd Avenue #D":
                assert better_name == "Northeast 82nd Avenue"


if __name__ == '__main__':
    test()
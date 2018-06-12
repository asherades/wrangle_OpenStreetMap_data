# This file was only used to audit state names and test the 
# data cleaning of those state names
# Since the auditing and cleaning process was fairly similar to 
# that of the street names, I reused and modified those functions.
# To better understand how those functions are being used, 
# see the "street_audit.py" file.
# The data is actually cleaned when preparing the database,
# which can be seen in database_prep.py

import xml.etree.cElementTree as ET
from collections import defaultdict
import re
import pprint

OSMFILE = "small_sample.osm"

# I decided to standardize state names to be the full name of the state,
# since it is easier to read than abbreviations
# Since Oregon and Washington were the only states that came up
# in the auditing process (albeit in different forms),
# I used the full names in the "expected" list
expected = ['Oregon', 'Washington']

# Dictionary used to change any state abbreviations that came up
# in the auditing process to their full names
# One special case of a full address came up, 
# and it was corrected to "Oregon"
state_name_mapping = {"OR": "Oregon",
                      "ORs": "Oregon",
                      "Or": "Oregon",
                      "or": "Oregon",
                      "WA": "Washington",
                      "wa": "Washington",
                      "Wa": "Washington",
                      "1401 N.E. 68th Avenue  Portland, OR 97213": "Oregon"
                      }

def is_state(elem):
    return (elem.attrib['k'] == "addr:state")

def audit(osmfile):
    osm_file = open(osmfile, "r")
    states = set()
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_state(tag):
                    if (tag.attrib['v'] not in expected):
                        states.add(tag.attrib['v'])
    osm_file.close()
    return states

def update_state_name(state_name):
    if state_name in state_name_mapping:
        state_name = state_name.replace(state_name, state_name_mapping[state_name])
    return state_name

def test():
    states = audit(OSMFILE)
    pprint.pprint(states)

    for state in states:
        better_state = update_state_name(state)
        print state, "=>", better_state
        if state == "OR":
            assert better_state == "Oregon"

if __name__ == '__main__':
    test()
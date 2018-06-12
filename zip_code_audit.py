# This file was only used to audit the zip codes and test the
# data cleaning of those zip codes
# Since the auditing and cleaning process was fairly similar 
# to that of the street names,
# I reused and modified those functions
# To better understand how those functions are being used, 
# see the "street_audit.py" file
# The data is actually cleaned when preparing the database, 
# which can be seen in database_prep.py

import xml.etree.cElementTree as ET
from collections import defaultdict
import re
import pprint

OSMFILE = "small_sample.osm"

#Regular expression checks whether the zip code is a 5-digit number
zip_code_re = re.compile(r'^\d{5}$')

def is_zip_code(elem):
    return (elem.attrib['k'] == "addr:postcode")

def audit_zip(zip_codes, code):
    m = zip_code_re.match(code)
    if not m:
        zip_codes.add(code)

def audit(osmfile):
    osm_file = open(osmfile, "r")
    zip_codes = set()
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_zip_code(tag):
                    audit_zip(zip_codes, tag.attrib['v'])
    osm_file.close()
    return zip_codes

# No mapping dictionary was used for zip codes
# The only issues that needed to be corrected were hyphenated zip codes
# and "Portland, OR " being included before the code
# All zip codes were standardized to five digits
def update_zip(zip_code):
    if "-" in zip_code:
        zip_code = zip_code.split("-")[0]
    if "Portland, OR " in zip_code:
        zip_code = zip_code.split("Portland, OR ")[1]
    return zip_code

def test():
    zips = audit(OSMFILE)
    pprint.pprint(zips)

    for zip in zips:
        better_zip = update_zip(zip)
        print zip, "=>", better_zip

if __name__ == '__main__':
    test()
# Code used to clean the data in the osm file and prepare it for
# entry into a SQL database, Portland.db. 
# I cannot claim to have written all of this. Udacity instructors
# wrote about half of the code to assist with the process. 
# I did, however, create the mapping dictionaries, 
# write the update functions, as well as the "handle_tags" and
# "shape_element" functions.

# Warning: Do not run this file; it is only meant to show the steps
# in the database preparation. The "map.osm" file was not provided
# in the repository because it was too large, so the code will not
# work


import csv
import codecs
import pprint
import re
import xml.etree.cElementTree as ET

import cerberus

import schema

# When validating the schema, use small_sample.osm instead since
# it will take too long with the full OSM file
OSM_PATH = "map.osm"

NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

SCHEMA = schema.schema

# Make sure the fields order in the csvs matches the column order 
# in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']

# Recognize the correct types of street names and zip codes
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
zip_code_re = re.compile(r'^\d{5}$')

# The following mapping dictionaries and list were used to convert
# street names to their correct forms:
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

special_cases = {"D", "101", "C113", "E"}

#This dictionary was used to standardize state names
state_name_mapping = {"OR": "Oregon",
                      "ORs": "Oregon",
                      "Or": "Oregon",
                      "or": "Oregon",
                      "WA": "Washington",
                      "wa": "Washington",
                      "Wa": "Washington",
                      "1401 N.E. 68th Avenue  Portland, OR 97213": "Oregon"
                      }

def update_name(name):
    """Clean street names according to different data cleaning
     procedures"""

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

# Here the only issues that came up were hyphenated zip codes and
# "Portland, OR " being included before the zip code
# Both types were standardized to five digit zip codes
def update_zip(zip_code):
    """Clean zip codes"""

    if "-" in zip_code:
        zip_code = zip_code.split("-")[0]
    if "Portland, OR " in zip_code:
        zip_code = zip_code.split("Portland, OR ")[1]
    return zip_code

def update_state_name(state_name):
    """Clean state names"""

    if state_name in state_name_mapping:
        state_name = state_name.replace(state_name, state_name_mapping[state_name])
    return state_name

# Node tags and way tags were handled in the same way
# Therefore, this function is used in the function below it
# to eliminate repitition
def handle_tags(item, element, problem_chars):
    """Set the key, type, and value of tags when inserted
     into the database"""

    s = problem_chars.search(item.attrib['k'])
    # If there are no problematic characters in an attribute's key,
    # the function proceeds
    if not s:
        d = {}
        # The 'id' assigned in the osm file is assigned in the same
        # way for the database
        d['id'] = element.attrib['id']
        possible_type = str(item.attrib['k'])
        # If there is at least one colon in the name, the string
        # before the colon is assigned to the 'type'
        # and the remaining characters are assigned to the 'key'
        # (regardless of whether there is another colon)
        if possible_type.count(":") >= 1:
            separated = possible_type.split(":", 1)
            d['key'] = separated[1]
            d['type'] = separated[0]
            # Values for street, zip code, and state name 
            # are all cleaned here,
            # each according to their update functions
            if item.attrib["k"] == 'addr:street':
                d["value"] = update_name(item.attrib["v"])
            elif item.attrib["k"] == 'addr:postcode':
                d["value"] = update_zip(item.attrib["v"])
            elif item.attrib["k"] == 'addr:state':
                d["value"] = update_state_name(item.attrib["v"])
            # If the key does not pertain to the street name, 
            # zip code, or state name, the regular value is used
            else:
                d['value'] = item.attrib['v']
        # If there are no colons in the key, then the normal
        # key and value are used, and the type is just "regular"
        else:
            d['key'] = item.attrib['k']
            d['type'] = "regular"
            d['value'] = item.attrib['v']
        return d
    #For keys with problematic characters, no node was tag is added
    else:
        return None


def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
    """Clean and shape node or way XML element to Python dict"""

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []  

    if element.tag == 'node':
        for field in node_attr_fields:
            node_attribs[field] = element.attrib[field]
        for item in element.iter('tag'):
            d = handle_tags(item, element, problem_chars)
            tags.append(d)
        return {'node': node_attribs, 'node_tags': tags}
    elif element.tag == 'way':
        for field in way_attr_fields:
            way_attribs[field] = element.attrib[field]
        for item in element.iter('tag'):
            d = handle_tags(item, element, problem_chars)
            tags.append(d)
        for i, node in enumerate(element.iter("nd")):
            d = {}
            d['id'] = element.attrib['id']
            d['node_id'] = node.attrib['ref']
            d['position'] = i
            way_nodes.append(d)
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}


# ================================================== #
#               Helper Functions                     #
# ================================================== #
def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


def validate_element(element, validator, schema=SCHEMA):
    """Raise ValidationError if element does not match schema"""
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.iteritems())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_string = pprint.pformat(errors)

        raise Exception(message_string.format(field, error_string))


class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""

    with codecs.open(NODES_PATH, 'w') as nodes_file, \
            codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file, \
            codecs.open(WAYS_PATH, 'w') as ways_file, \
            codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file, \
            codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        validator = cerberus.Validator()

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
                if validate is True:
                    validate_element(el, validator)

                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])


if __name__ == '__main__':
    process_map(OSM_PATH, validate=False)

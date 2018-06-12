## Data Analyst Nanodegree Project: Wrangle OpenStreetMap Data

In this project, I chose to work with map data from the Portland, Oregon area (in XML format) and systemically identified areas
where the data could be cleaned for accuracy and consistency. Once the cleaned data was entered in a SQL database, I ran queries to find
interesting information about the area.

Files in this repository:

* `Portland Link & Description.rtf` - contains link to OpenStreetMap area for Portland and a short description of the area
* `References.rtf` - a list of web sites referred to or used in this project
* `Wrangling OpenStreepMap Data Report.pdf` - a report detailing the data wrangling process and the findings after performing queries
on the database
* `database_prep.py` - the main code file where the data is cleaned and prepared for entry into a SQL database. For reference only.
* `schema.py` - a Python file used to validate schema created in "database_prep.py". For reference only.
* `small_sample.osm` - one of the sample files used to identify issues in the dataset for the cleaning step.
* `state_audit.py` - code used to identify main issues with state name entries in the dataset and test data cleaning procedures
* `street_audit.py` - code used to identify main issues with street name entries
* `zip_code_audit.py` - code used to identify main issues with zip code entries


Note: Python 2.7 is required if you wish to run the code in this repository

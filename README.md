 [![Code of Conduct](https://img.shields.io/badge/%E2%9D%A4-code%20of%20conduct-blue.svg?style=flat)](https://github.com/edgi-govdata-archiving/overview/blob/main/CONDUCT.md)

# EW Screen Database for Jupyter notebooks and Report Cards

This repo has exploratory code for bringing EJ Screen into EEW notebooks and
report cards.

The Sqlite3 ejscreen2022.db database in the repository is constructed as follows:
* The EPA's [EJ Screen](https://gaftp.epa.gov/EJSCREEN/2022/EJSCREEN_2022_with_AS_CNMI_GU_VI.csv.zip) CSV file data must be downloaded and put into the current directory, and unzipped. (It is too large to include in this repository.)
* Run 'python Make_ejscreen_db.py'. It will select out the columns of EJ Screen data we are interested in, and bring in the census block group centroid point
coordinates for each EJ Screen record.
* The result will be the ejscreen2022.db Sqlite3 database.

## License & Copyright

Copyright (C) <year> Environmental Data and Governance Initiative (EDGI)
This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 3.0.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

See the [`LICENSE`](/LICENSE) file for details.


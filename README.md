# Web Crawler Scraper
This project implements a web crawler that traverses through certain sites on an outside server to scrape its contents.
It traverses through all sites on the server that have URLs meeting one of the below formats:
* \*.ics.uci.edu/\*
* \*.cs.uci.edu/\*
* \*.informatics.uci.edu/\*
* \*.stat.uci.edu/\*
* today.uci.edu/department/information_computer_sciences/\*

After crawling through these sites, it provides the following information to the user on the sites through the
`report_info.txt` file created:
* number of unique pages
* longest page in terms of number of words
* 50 most common words
* list of subdomains and their counts found within the *ics.uci.edu* domain

## General Info
This program references a server that is hosted and run by a professor at the University of California, Irvine.
As a result, the server must be started on their end for the program to execute.
If the program is able to run upon attempt, this will mean the server is not up.

## Technologies
The programs in this project were run using the following:
* Python 3.6

## Setup
You will need to ensure that certain dependencies are met in order to run this program.
To install the dependencies for this project, run the following two commands.
Make sure that you `cd` into the repository.
* `pip install packages/spacetime-2.1.1-py3-none-any.whl`
* `pip install -r packages/requirements.txt`

## Execution
To execute the crawler, run the `launch.py` file.
* `python3 launch.py`

You can restart the crawler and remove all previous progress done using the `--restart` command
* `python3 launch.py --restart`

You can specify a different config file to use by using the `--config_file` command
* `python3 launch.py --config_file path/to/config`

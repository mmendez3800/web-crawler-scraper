"""
This program is to assist with our web crawler being implemented.
Using the original files provided, we are to help construct the core of a web crawler.
This crawler is to go through only certain domains and collect various information.
The information obtained will be used to ouput a report showing our crawler's results.
"""
import dill as pickle
import json
import re

from bs4 import BeautifulSoup
from bs4 import Comment
from collections import Counter
from itertools import islice
from os import path
from simhash import Simhash
from simhash import SimhashIndex
from utils import get_logger
from utils import get_urlhash

from urllib.parse import quote_plus
from urllib.parse import urljoin
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

# Global variables to track simhash values, log information, record scraper info obtained
logger = get_logger("CRAWLER")
robot_parsers = {}
scraper_info = {'unique_pages': 0, 'longest_page_url': '', 'longest_page_count': 0}
simhash_index = SimhashIndex([], k=3)

def init():
    """
    The init function helps to start our scraper for the web crawler in case the crawler was stopped
    in the middle of its traversal previously
    """
    global scraper_info
    global simhash_index
    text_file = 'scraper_info.txt'
    pickle_file = 'simhash_index.pkl'
    
    if path.isfile(text_file) and path.isfile(pickle_file):
        with open(text_file) as tf:
            scraper_info = json.load(tf)
        
        with open(pickle_file, rb) as pf:
            simhash_index = pickle.load(pf)

def add_unique_page():
    """
    The add_unique_page function updates the number of unique pages encountered by our crawler and
    notes it on disk for review afterwards
    
    Raises:
        OSError: If file cannot be opened
    """
    global scraper_info
    
    try:
        file = open('scraper_info.txt', mode='w+', encoding='utf-8')
    except OSError as error:
        logger.error(f"OSError with 'add_unique_page' function: {error}")
    else:
        scraper_info['unique_pages'] += 1
        json.dump(scraper_info, file)
    finally:
        file.close()

def update_longest_page(url, count):
    """
    The update_longest_page function updates the page with the longest number of words encountered
    by our crawler and notes it on disk for review afterwards
    
    Args:
        url (str): A string of the page
        count (int): A integer for the number of words in the page
    
    Raises:
        OSError: If file cannot be opened
    """
    global scraper_info
    
    try:
        file = open('scraper_info.txt', mode='w+', encoding='utf-8')
    except OSError as error:
        logger.error(f"OSError with 'update_longest_page' function: {error}")
    else:
        scraper_info['longest_page_url'] = url
        scraper_info['longest_page_count'] = count
        json.dump(scraper_info, file)
    finally:
        file.close()

def update_common_words(word_list):
    """
    The update_common_words function adds the words encountered in a page by our crawler and notes
    it on disk for review afterwards
    
    Args:
        word_list (list): A list of words found for a page
    
    Raises:
        OSError: If file cannot be opened
    """
    try:
        file = open('word_frequencies.txt', mode='a+', encoding='utf-8')
    except OSError as error:
        logger.error(f"Error with 'update_common_words' function: {error}")
    else:
        for word in word_list:
            file.write(f"{word}\n")
    finally:
        file.close()

def update_subdomains(authority):
    """
    The update_subdomains function adds the page encounter and notes it on disk for review afterwards
    if the page is a subdomain of 'ics.uci.edu'
    
    Args:
        authority (str): A string of the subdomain encountered
    
    Raises:
        OSError: If file cannot be opened
    """
    try:
        file = open('subdomain_count.txt', mode='a+', encoding='utf-8')
    except OSError as error:
        logger.error(f"Error with 'update_subdomains' function: {error}")
    else:
        file.write(f"{authority}\n")
    finally:
        file.close()

def update_simhash_index(url, simhash_object):
    """
    The update_simhash_index function updates the index of simhash values obtained when crawling
    and notes it on disk for review afterwards
    
    Args:
        url (str): A string of the page
        count (object): A Simhash object that represents the contents of the page
    
    Raises:
        OSError: If file cannot be opened
    """
    global simhash_index
    
    try:
        file = open('simhash_index.pkl', mode='wb+')
    except OSError as error:
        logger.error(f"OSError with 'update_longest_page' function: {error}")
    else:
        simhash_index.add(get_urlhash(url), simhash_object)
        pickle.dump(simhash_index, file)
    finally:
        file.close()

def calc_content(url, body):
    """
    The calc_content function determines if a page is valid through the contents found within it
    
    Args:
        body (object): A BeautifulSoup object containing the body tag of a web page
    
    Returns:
        A boolean indicating if the page has low information value and a list of the words
        within it if it does not
    """  
    def visible_tag(element):
        """
        The visible_tag helper function determines if a tag in a page is visible to the user
        
        Note:
            The below function was obtained through an outside source found on
            https://stackoverflow.com/questions/1936466/beautifulsoup-grab-visible-webpage-text
        
        Args:
            element (object): A Tag object containing a reference link
        
        Returns:
            A boolean indicating if the tag is visible to the user
        """
        if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
            return False
        
        # Checks if tag is being used as a comment within the page
        elif isinstance(element, Comment):
            return False
        
        else:
            return True
    
    # Extracts visible text from page and joins it into a string
    # https://stackoverflow.com/questions/1936466/beautifulsoup-grab-visible-webpage-text
    all_text = body.find_all(text=True)
    visible_text = filter(visible_tag, all_text)
    combined_text = u" ".join(text.strip().lower() for text in visible_text)
    
    # Sets up word requirements
    with open('stop_words.txt') as file:
        stop_words = set(file.read().split(','))
    pattern = re.compile("[a-zA-Z0-9@#*&']{2,}")
    
    # Determines list of words and valid words in page
    word_list = pattern.findall(combined_text)
    valid_word_list = [word for word in word_list if not word in stop_words]
    
    # Checks if page has low information value
    valid_size = len(valid_word_list)
    if valid_size < 50 or (len(set(valid_word_list)) / valid_size) < 0.2:
        return True, []
    
    # Checks if contents of page is similar to a previously crawled page
    simhash_value = Simhash(valid_word_list)
    if simhash_index.get_near_dups(simhash_value):
        return True, []
    else:
        update_simhash_index(url, simhash_value)
    
    return False, valid_word_list

def scraper(url, resp):
    """
    The scraper function reviews the page provided, checks if it is valid, and extracts relevant information
    on the page in question
    
    Args:
        url (str): A string representing the URL of the page
        resp (object): A Response object containing the contents of the page
    
    Returns:
        A list of valid links extracted if the page itself is valid
    """
    extracted_links = []
    
    # Checks if Response object was obtained
    if resp.raw_response is None:
        return extracted_links
    
    # Checks if URL has a valid response status (i.e., less than 400)
    if not resp.status in range(200, 400):
        return extracted_links
    
    # Checks if URL has a valid content-type header
    pattern = re.compile('text|html')
    content_type = resp.raw_response.headers.get('content-type', '')
    if re.search(pattern, content_type) is None:
        return extracted_links
    
    # Grabs the contents of page from <body> tag
    body = BeautifulSoup(resp.raw_response.content, 'lxml').body
    if not body:
        return extracted_links
    
    # Checks if the page is invalid
    invalid_page, word_list = calc_content(url, body)
    if invalid_page:
        add_unique_page()
        return extracted_links
    
    # Passes valid page through ancillary functions for reporting purposes
    add_unique_page()
    page_count = len(word_list)
    if page_count > scraper_info['longest_page_count']:
        update_longest_page(url, page_count)
    update_common_words(word_list)
    authority = urlparse(url).netloc
    if authority.endswith('.ics.uci.edu'):
        update_subdomains(authority)
    
    # Extracts the links from page and returns the valid ones
    extracted_links = extract_next_links(url, body)
    return [link for link in extracted_links if is_valid(link)]

def extract_next_links(url, body):
    """
    The extract_next_links function reviews the page provided and pulls out all of the visible links
    that are present within it
    
    Args:
        url (str): A string representing the URL of the page
        resp (object): A Tag object containing body of the page
    
    Returns:
        A list of links extracted from the page
    """
    # Extracts the list of links present in the page
    links = set()
    link_locations = body.find_all('a', href=True)
    
    # Iterates through each link where the tag has text associated to it
    for tag in link_locations:
        if tag.text:
            
            # Obtaines the parsed URL of the extracted link
            extracted_url = tag['href']
            parsed_url = urlparse(extracted_url)
            if not parsed_url.scheme:
                updated_url = urljoin(url, extracted_url)
                parsed_url = urlparse(updated_url)
            
            # Update the path structure for storing
            path = parsed_url.path
            if re.search('%', path) is None:
                path = quote_plus(parsed_url.path, safe='/')
            pattern = re.compile(r"/index\.[a-zA-Z]+.?$|/page/[0-9]+.?$"
                                 + r"|/[0-9]{4}/[0-9]{2}.?$|/[0-9]{4}/[0-9]{2}/[0-9]{2}.?$"
                                 + r"|/[0-9]{4}-[0-9]{2}.?$|/[0-9]{4}-[0-9]{2}-[0-9]{2}.?$")
            new_path = pattern.sub('/', path)
            
            # Grabs core parts of URL and adds them to extracted links
            updated_url = f"{parsed_url.scheme.lower()}://{parsed_url.netloc.lower()}{new_path}"
            links.add(updated_url)
    
    return links

def repetitive_pattern(path):
    """
    The repetitive_pattern function reviews the path of a page and checks to see if the
    path has repeated folders in it
    
    Args:
        path (str): A string representing the path of a page
    
    Returns:
        A boolean indicating if the path has a repeat within it
    """
    # Checks if a path is not present
    if not path:
        return False
    
    # Splits the path into its components
    if path[-1] == '/':
        path_list = path[1:-1].split('/')
    else:
        path_list = path[1:].split('/')
    
    # Checks if there are repeates in the path
    if len(path_list) != len(set(path_list)):
        return True
    else:
        return False

def check_robots_file(url):
    """
    The check_robots_file function reviews the URL and looks at the 'robots.txt' file of the
    site to see if the page should be fetched or not
    
    Args:
        url (str): A string representing the URL of the page
    
    Returns:
        A boolean indicating of the URL should be seen crawled based on 'robots.txt' file
    """
    global robot_parsers
    
    parsed_url = urlparse(url)
    authority = parsed_url.netloc
    
    # Checks if robots_parser of domain was found before
    if not authority in robot_parsers:
        rp = RobotFileParser(url=f"{parsed_url.scheme}://{authority}/robots.txt")
        try:
            rp.read()
        except:
            robot_parsers[authority] = None
        else:
            robot_parsers[authority] = rp
    
    # Confirms if URL can be crawled based on 'robots.txt' file
    rp = robot_parsers[authority]
    if rp is None:
        return True
    else:
        can_crawl = rp.can_fetch('*', url)
        return can_crawl

def is_valid(url):
    """
    The is_valid function reviews the URL of a page and determines if the page link
    is valid for the crawler to traverse
    
    Args:
        url (str): A string representing the URL of the page
    
    Returns:
        A boolean indicating if the URL is valid for the crawler to traverse
    """
    # Parses the link
    parsed_url = urlparse(url)
    authority = parsed_url.netloc
    path = parsed_url.path
    
    # Checks if the link should be traversed based on restrictoin of domain name
    url_pattern = re.compile("\.ics\.uci\.edu$|\.cs\.uci\.edu$|\.informatics\.uci\.edu$|\.stat\.uci\.edu$")
    if url_pattern.search(authority) is None and not f"{authority}{path}".startswith('today.uci.edu/department/information_computer_sciences/'):
        return False
    
    # Checks if the link should be traversed based on no repeating path patterns and valid protocol
    if parsed_url.scheme not in set(["http", "https"]):
        return False
    if repetitive_pattern(path):
        return False
    
    # Checks if the link should be traverse based on extension of URL
    extension_pattern = re.compile(r"\.(css|js|bmp|gif|jpe?g|ico"
                                   + r"|png|tiff?|mid|mp2|mp3|mp4"
                                   + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
                                   + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
                                   + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
                                   + r"|apk|epub|dll|cnf|tgz|sha1"
                                   + r"|thmx|mso|arff|rtf|jar|csv"
                                   + r"|r|py|rkt|ss|sas|java|in|scm|odc|m"
                                   + r"|rm|smil|wmv|swf|wma|zip|rar|gz).?$")
    if extension_pattern.search(path.lower()):
        return False
    
    if not check_robots_file(url):
        return False
    
    return True

def create_report():
    """
    The create_report function outputs the results of our web crawler and provides details based
    on the requested information asked
    """
    try:
        file = open('report_info.txt', mode='w+', encoding='utf-8')
    except OSError as error:
        logger.error(f"OSError with 'create_report' function: {error}")
    else:
        # Write the number of unique pages found and longest page
        file.write(f"Number of unique pages found:\n{scraper_info['unique_pages']}\n")
        file.write(f"\nLongest page found:\n{scraper_info['longest_page_url']}\n")
        file.write(f"{scraper_info['longest_page_count']} words present\n")
        
        # Create counters for tracking unique words and subdomains
        word_frequencies = Counter()
        subdomain_count = Counter()
        
        # Loop through every 1000 unique words and store them into Counter
        with open('word_frequencies.txt') as wf:
            while True:
                next_lines = list(islice(wf, 100))
                if not next_lines:
                    break
                updated_lines = [line.strip() for line in next_lines]
                word_frequencies.update(updated_lines)
        
        # Loop through every 1000 subdomains and store them into Counter
        with open('subdomain_count.txt') as sc:
            while True:
                next_lines = list(islice(sc, 100))
                if not next_lines:
                    break
                updated_lines = [line.strip() for line in next_lines]
                subdomain_count.update(updated_lines)
        
        # Write the 50 most frequent words found
        file.write('\nMost common words:\n')
        for (word, frequency) in word_frequencies.most_common(50):
            file.write(f"{word}, {frequency}\n")
        
        # Write the subdomains found and their counts
        file.write('\nSubdomains found:\n')
        for (subdomain, count) in sorted(subdomain_count.items()):
            file.write(f"{subdomain}, {count}\n")
    finally:
        file.close()

import urllib2
import re
import logging
import time
from datetime import date, timedelta, datetime
from dateutil.relativedelta import relativedelta
from BeautifulSoup import BeautifulSoup
import robotparser

LISTING_BASE_URL = 'http://www.bfi.org.uk'
LISTING_PATH_TMPL = '%s/whatson/calendar/southbank/day/%%s' % LISTING_BASE_URL

LOCATIONS = ['southbank',]

USER_AGENT = 'BFiCal'
robot_parser = None

TEST_EVENT_URL = 'http://www.bfi.org.uk/whatson/bfi_southbank/film_programme/november_seasons/rediscovering_frank_capra/it_happened_one_night'
#TEST_EVENT_URL = 'http://www.bfi.org.uk/whatson/bfi_southbank/film_programme/regular_strands/studio_screenings/police_adjective'
#TEST_EVENT_URL = 'http://www.bfi.org.uk/whatson/bfi_southbank/events/african_odysseys/new_nigeria_cinema_the_figurine'
#TEST_EVENT_URL = 'http://www.bfi.org.uk/whatson/bfi_southbank/events/london'
#TEST_EVENT_URL = 'http://www.bfi.org.uk/whatson/bfi_southbank/film_programme/november_seasons/rediscovering_frank_capra/submarine'
#TEST_EVENT_URL = 'http://www.bfi.org.uk/whatson/bfi_southbank/events/a_day_in_the_life_four_portraits_of_postwar_britain'
#TEST_EVENT_URL = 'http://www.bfi.org.uk/whatson/bfi_southbank/events/african_odysseys/african_odysseys_the_negro_soldier_discussion'
TEST_EVENT_URL = 'http://www.bfi.org.uk/whatson/bfi_southbank/events/projecting_the_archive_/_capital_tales/projecting_the_archive_i_was_happy_here'
#TEST_EVENT_URL = 'http://www.bfi.org.uk/whatson/bfi_southbank/film_programme/regular_strands/previews_in_conversation/preview_another_year_mike_leig'
#TEST_EVENT_URL = 'http://www.bfi.org.uk/whatson/bfi_southbank/events/missing_believed_wiped_session_1_music_miscellany'
#TEST_EVENT_URL = 'http://www.bfi.org.uk/whatson/bfi_southbank/events/african_odysseys_cy_grant_tribute'
TEST_EVENT_URL = 'http://www.bfi.org.uk/whatson/bfi_southbank/film_programme/november_seasons/clandest%C3%AD_invisible_catalan_cinema_under_franco/countr'
TEST_EVENT_URL = 'http://www.bfi.org.uk/whatson/bfi_southbank/film_programme/november_seasons/rediscovering_frank_capra/the_way_of_the_strong'

TEST_LISTING_URL = 'http://www.bfi.org.uk/whatson/calendar/southbank/day/20101119'


class BFIEvent(object):
    def __init__(self, url=None, title=None, precis=None, description=None, directors=None, cast=None, year=None, showings=None):
        self.url = unicode(url).encode('ascii', 'ignore')
        self.title = unicode(title).encode('ascii', 'ignore')
        self.precis = unicode(precis).encode('ascii', 'ignore')
        self.description = unicode(description).encode('ascii', 'ignore')
        self.directors = directors
        if self.directors is None: self.directors = []
        self.cast = cast
        if self.cast is None: self.cast = []
        self.year = year
        self.showings = showings
        if self.showings is None: self.showings = []


    def __unicode__(self):
        return u"Title:%s, Precis:%s, Year:%s, Director:%s, Cast:%s, Desc:%s" % (self.title, self.precis, self.year, ', '.join(self.directors), ', '.join(self.cast), self.description)

    def add_showing(self, id, location, start, end):
        showing = BFIShowing(id, location, start, end)
        self.showings.append(showing)

class BFIShowing(object):
    def __init__(self, id, location, start, end):
        self.id = id
        self.location = unicode(location).encode('ascii', 'ignore')
        self.start = start
        self.end = end

    def __unicode__(self):
        return u"ID:%s Location:%s Start:%s End:%s" % (self.id, self.location, self.start, self.end)

def can_access_url(url):
    global robot_parser
    if robot_parser is None:
        robot_parser = robotparser.RobotFileParser()
        robot_parser.set_url("%s/robots.txt" % LISTING_BASE_URL)

    if time.time() - robot_parser.mtime() >= 3600:
        robot_parser.read()
        robot_parser.modified()   # wonder what the point is if it doesn't maintain last_checked itself

    return robot_parser.can_fetch(USER_AGENT, url)

def daterange(start_date, end_date):
    for n in range((end_date - start_date).days):
        yield start_date + timedelta(n)

def parse_dates(datestr='', running_delta=timedelta(minutes=1)):
    match = None
    if datestr: match = re.search(r'(\d+\s\w{3}\s\d{2}:\d{2})', datestr)
    if match:
        showingdate = datetime.strptime(match.group(1), '%d %b %H:%M')
        if showingdate:
            showingdate = showingdate.replace(year=datetime.today().year) #TODO - year of target page
            showingenddate = showingdate + running_delta
            return (showingdate, showingenddate)
    return (None, None)

def parse_ident(identstr):
    showingid = None
    if identstr:
        match = re.search(r'PerIndex=(\d+)', identstr)
        if match: showingid = match.group(1)
    return showingid

def parse_url(url):
    url = str(url)
    if can_access_url(url):
        req = urllib2.Request(url, headers={'User-Agent': USER_AGENT})
        page = urllib2.urlopen(req)
        soup = BeautifulSoup(page, convertEntities=BeautifulSoup.HTML_ENTITIES)
        page.close()
    else:
        logging.error("robots.txt denied access to %s" % url)

    return soup

def generate_listing_urls():
    TODAY = date.today()
    listings = []
    for day in daterange(TODAY, TODAY + relativedelta(months=+2, day=1)):
        listings.append(LISTING_PATH_TMPL % day.strftime('%Y%m%d'))
    return listings

def parse_listings_page(url):
    soup = parse_url(url)

    events = []
    for listing in soup.findAll('li', 'event'):
        events.append(LISTING_BASE_URL + listing.a['href'])
    return events

def parse_event_page(url):
    soup = parse_url(url)

    title = soup.find('h1', 'title').string
    precis = title.findNext('p', 'standfirst').string

    description = ""
    if precis is not None:
        for p in precis.findNext('div', id='read_more').findAll('p'):
            if getattr(p, 'string', None):
                description = p.string
                break

    running_time = 60
    director_list = []
    cast_list = []
    year = None

    infotable = precis.findNext('table', 'credits_list')
    if infotable is not None:
        for row in infotable:
            rowtitle = row.find('td', 'credit_role').string
            if rowtitle == 'Director':
                directors = row.find('td', 'credit_content').string
                if directors is not None:
                    director_list = [unicode(x).strip() for x in directors.split(',')]
            elif rowtitle == 'Cast':
                casts = row.find('td', 'credit_content').string
                if casts is not None:
                    cast_list = [unicode(x).strip() for x in casts.split(',')]
            elif rowtitle == 'Year':
                year = unicode(row.find('td', 'credit_content').string)
            elif rowtitle == 'Running time':
                runningstr = row.find('td', 'credit_content').string
                match = re.search(r'(\d+)min', runningstr)
                if match: running_time = int(match.group(1))
                break
    running_delta = timedelta(minutes=running_time)

    showings = []
    showtimes_table = soup.find('table', id=re.compile('^showtimes_list'))
    if showtimes_table:
        for row in soup.find('table', id=re.compile('^showtimes_list')):
            dateelem = row.find('td')
            datestr = getattr(dateelem, 'string', None)
            (showingdate, showingend) = parse_dates(datestr, running_delta)
            if showingdate and showingend:
                showingloc = getattr(dateelem.findNextSiblings('td')[1], 'string', None)
                bookelem = getattr(dateelem.findNextSiblings('td')[2], 'a', None)
                if bookelem:
                    showingid = parse_ident(bookelem['href'])
                    showings.append((showingid, showingloc, showingdate, showingend))
    else:
        dates_lines = soup.find('ul', {'class': re.compile('dates')})
        for dates_line in dates_lines.findAll('li'):
            (showingdate, showingend) = parse_dates(dates_line.contents[0], running_delta)
            if showingdate and showingend:
                showingloc = ''
                for elem in dates_line.contents[0].rstrip().split()[::-1]:
                    if re.match(r'\d+:\d{2}', elem): break
                    showingloc = ' '.join((showingloc, elem))
                    showingloc = showingloc.lstrip()  # TODO: horrible, change
                    showingid = parse_ident(dates_line.contents[1]['href'])
                    showings.append((showingid, showingloc, showingdate, showingend))

    logging.debug("Showings:%s" % len(showings))
    event = BFIEvent(url=url, title=title, precis=precis, directors=director_list, cast=cast_list, year=year, description=description)

    for showing in showings:
        event.add_showing(*showing)

    return event

if __name__ == '__main__':
    event = parse_event_page(TEST_EVENT_URL)
    print unicode(event)
    for showing in event.showings:
        print unicode(showing)

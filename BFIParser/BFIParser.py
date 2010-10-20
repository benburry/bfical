import urllib2
import re
from datetime import date, timedelta, datetime
from dateutil.relativedelta import relativedelta
from BeautifulSoup import BeautifulSoup

LISTING_BASE_URL = 'http://www.bfi.org.uk'
LISTING_PATH_TMPL = '%s/whatson/calendar/southbank/day/%%s' % LISTING_BASE_URL

TEST_EVENT_URL = 'http://www.bfi.org.uk/whatson/bfi_southbank/film_programme/november_seasons/rediscovering_frank_capra/it_happened_one_night'
#TEST_EVENT_URL = 'http://www.bfi.org.uk/whatson/bfi_southbank/film_programme/regular_strands/studio_screenings/police_adjective'
#TEST_EVENT_URL = 'http://www.bfi.org.uk/whatson/bfi_southbank/events/african_odysseys/new_nigeria_cinema_the_figurine'
TEST_EVENT_URL = 'http://www.bfi.org.uk/whatson/bfi_southbank/events/london'
TEST_LISTING_URL = 'http://www.bfi.org.uk/whatson/calendar/southbank/day/20101119'

class BFIEvent(object):
    def __init__(self, title=None, precis=None, description=None, showings=[]):
        self.title = title
        self.precis = precis
        self.description = description
        self.showings = showings

    def __unicode__(self):
        return "Title:%s, Precis:%s, Desc:%s" % (self.title, self.precis, self.description)

    def add_showing(self, id, location, start, end):
        showing = BFIShowing(id, location, start, end)
        self.showings.append(showing)

class BFIShowing(object):
    def __init__(self, id, location, start, end):
        self.id = id
        self.location = location
        self.start = start
        self.end = end

    def __unicode__(self):
        return "ID:%s Location:%s Start:%s End:%s" % (self.id, self.location, self.start, self.end)


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
    page = urllib2.urlopen(url)
    soup = BeautifulSoup(page, convertEntities=BeautifulSoup.HTML_ENTITIES)
    page.close()

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

    for p in precis.findNext('div', id='read_more').findAll('p'):
        if getattr(p, 'string', None):
            description = p.string
            break

    for row in precis.findNext('table', 'credits_list'):
        if row.find('td', 'credit_role').string == 'Running time':
            runningstr = row.find('td', 'credit_content').string
            match = re.match(r'(\d+)min', runningstr)
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

    event = BFIEvent(title=title, precis=precis, description=description)

    for showing in showings:
        event.add_showing(*showing)

    return event

if __name__ == '__main__':
    event = parse_event_page(TEST_EVENT_URL)
    print unicode(event)
    for showing in event.showings:
        print unicode(showing)

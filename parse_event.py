URL = 'http://www.bfi.org.uk/whatson/bfi_southbank/film_programme/november_seasons/rediscovering_frank_capra/it_happened_one_night'
URL = 'http://www.bfi.org.uk/whatson/bfi_southbank/film_programme/regular_strands/studio_screenings/police_adjective'
URL = 'http://www.bfi.org.uk/whatson/bfi_southbank/events/african_odysseys/new_nigeria_cinema_the_figurine'

import urllib2
import re
from datetime import datetime, timedelta
from BeautifulSoup import BeautifulSoup

def parse_dates(datestr='', running_delta=timedelta(minutes=1)):
  match = None
  if datestr: match = re.search(r'(\d+\s\w{3}\s\d{2}:\d{2})', datestr)
  if match:
    showingdate = datetime.strptime(match.group(1), '%d %b %H:%M')
    if showingdate:
      showingdate = showingdate.replace(year=datetime.today().year) #TODO - year of target page
      #print showingdate
      showingenddate = showingdate + running_delta
      #print showingenddate
      return (showingdate, showingenddate)
  return (None, None)

def parse_ident(identstr):
  showingid = None
  if identstr:
    match = re.search(r'PerIndex=(\d+)', identstr)
    if match: showingid = match.group(1)
  return showingid

def parse(url):
  page = urllib2.urlopen(url)
  soup = BeautifulSoup(page, convertEntities=BeautifulSoup.HTML_ENTITIES)
  page.close()

  title = soup.find('h1', 'title')
  print title.string

  precis = title.findNext('p', 'standfirst')
  print precis.string

  for p in precis.findNext('div', id='read_more').findAll('p'):
    if getattr(p, 'string', None):
      description = p
      break
  print description.string

  for row in precis.findNext('table', 'credits_list'):
    if row.find('td', 'credit_role').string == 'Running time':
      runningstr = row.find('td', 'credit_content').string
      match = re.match(r'(\d+)min', runningstr)
      if match: running_time = int(match.group(1))
      break
  print running_time
  running_delta = timedelta(minutes=running_time)  

  showtimes_table = soup.find('table', id=re.compile('^showtimes_list'))
  if showtimes_table:
    for row in soup.find('table', id=re.compile('^showtimes_list')):
      dateelem = row.find('td')
      datestr = getattr(dateelem, 'string', None)
      (showingdate, showingenddate) = parse_dates(datestr, running_delta)
      if showingdate and showingenddate:
        print showingdate, showingenddate 
        showingloc = getattr(dateelem.findNextSiblings('td')[1], 'string', None)
        print showingloc
        bookelem = getattr(dateelem.findNextSiblings('td')[2], 'a', None)
        if bookelem:
          showingid = parse_ident(bookelem['href'])
          print showingid
  else:
    dates_line = soup.find('ul', {'class': re.compile('dates')}).li
    (showingdate, showingenddate) = parse_dates(dates_line.contents[0], running_delta)
    if showingdate and showingenddate:
      print showingdate, showingenddate 
      showingloc = ''
      for elem in dates_line.contents[0].rstrip().split()[::-1]:
        if re.match(r'\d+:\d{2}', elem): break
        showingloc = ' '.join((showingloc, elem))
      showingloc = showingloc.lstrip()  # TODO: horrible, change
      print showingloc
      showingid = parse_ident(dates_line.contents[1]['href'])
      print showingid

      #<tr>
      #<td>29 Oct 18:30</td>
      #<td>Fri evening</td>
      #<td>NFT1</td>
      #<td><a href="https://tickets.bfi.org.uk/selectseat.asp?Venue=BFI&amp;PerIndex=54257" class="action_butt" id="book_butt">book</a></td>
      #</tr>

#<ul class="dates clearfix">
#    <li>
#    30 Oct 14:00 NFT1 <a href="https://tickets.bfi.org.uk/selectseat.asp?Venue=BFI&amp;PerIndex=54287" class="action_butt" id="book_butt">book</a>  </li>
#  </ul>


if __name__ == '__main__':
  parse(URL)

URL = 'http://www.bfi.org.uk/whatson/bfi_southbank/film_programme/november_seasons/rediscovering_frank_capra/it_happened_one_night'

import urllib2
from BeautifulSoup import BeautifulSoup

def parse(url):
  page = urllib2.urlopen(url)
  soup = BeautifulSoup(page)
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
      running_time = row.find('td', 'credit_content').string
      break
  print running_time

if __name__ == '__main__':
  parse(URL)

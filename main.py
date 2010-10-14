#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

import urllib2
import logging
import os

from BeautifulSoup import BeautifulSoup
from icalendar.cal import Event


DEBUG = os.getenv('SERVER_SOFTWARE').split('/')[0] == "Development" if os.getenv('SERVER_SOFTWARE') else False

BFI_BASEURL = 'http://www.bfi.org.uk'

class MainHandler(webapp.RequestHandler):
    def get(self):
        page = urllib2.urlopen("%s/whatson/calendar/southbank/day/20101029" % BFI_BASEURL)
        soup = BeautifulSoup(page)
        page.close()

        for event in soup.findAll('li', attrs={'class': 'event'}):
            self.response.out.write('%s - %s' % (event.a.renderContents(), event.find('p', 'event_time').contents[0]))

#            calevent = Event()
#            calevent.add('uid', '%s@bfi.org.uk.whatson' % event['id'])
#            calevent.add('summary', event.a.renderContents())
#            calevent.add('description', 'Hello dave')
#            calevent.add('location', event.find('p', 'event_time').contents[0])
#	        calevent.add('dtstart', datetime.datetime.fromtimestamp((eventdetails['start'] + cal['tz']) / 1000))
#            calevent.add('sequence', int(time.time()))



def main():
    logging.getLogger().setLevel(logging.DEBUG if DEBUG else logging.WARN)

    application = webapp.WSGIApplication([('/', MainHandler)], debug=DEBUG)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()

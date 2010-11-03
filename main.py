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
from google.appengine.api import memcache
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.ext import ereporter
from models import Event, Showing

from datetime import date
import logging
import os
import tasks
import urllib


DEBUG = os.getenv('SERVER_SOFTWARE').split('/')[0] == "Development" if os.getenv('SERVER_SOFTWARE') else False
ereporter.register_logger()

class MainHandler(webapp.RequestHandler):
    def get(self, location='southbank', weekoffset=0):
        output = None
        weekoffset = int(weekoffset)
        if weekoffset == 0:
            cachekey = tasks.HOME_CACHEKEY_TMPL % location
            output = memcache.get(cachekey)
        if output is None:
            output = tasks.generate_homepage(location, weekoffset)
            if weekoffset == 0:
                memcache.set(cachekey, output, time=86400)
        self.response.out.write(output)

class ICSHandler(webapp.RequestHandler):
    def get(self, location='southbank', sublocation=None):

        calendar = None
        if not DEBUG:
            calendar = memcache.get(tasks.ICS_CACHEKEY_TMPL % (location, sublocation))

        if calendar is None:
            calendar = tasks.generate_calendar(location, sublocation)
            memcache.set(tasks.ICS_CACHEKEY_TMPL % (location, sublocation), calendar, time=86400)

        if calendar is not None:
            self.response.headers['Content-Type'] = "text/calendar"
            self.response.out.write(calendar.as_string())
        else:
            self.error(404)

class EventHandler(webapp.RequestHandler):
    def get(self, eventkey):
        event = Event.get(eventkey)
        if event is not None:
            showings = db.Query(Showing).ancestor(event).filter("start >=", date.today()).order("start")   # TODO - cache this
            path = os.path.join(os.path.dirname(__file__), 'templates', 'event.html')
            self.response.out.write(template.render(path, {"event": event, "showings": showings,}))
        else:
            self.error(404)

class YearHandler(webapp.RequestHandler):
    def get(self, year):
        events = db.Query(Event).filter("year", year).order("name")   # TODO - cache this
        path = os.path.join(os.path.dirname(__file__), 'templates', 'events.html')
        self.response.out.write(template.render(path, {"events": events, "year": year,}))

class MoreHandler(webapp.RequestHandler):
    def get(self, more):
        more = urllib.unquote(more)
        events_d = db.Query(Event).filter("directors", more)
        events_c = db.Query(Event).filter("cast", more)

        dedupe = {}
        for event in events_d: dedupe[event] = 1
        for event in events_c: dedupe[event] = 1

        events = sorted(dedupe.keys(), key=lambda x: x.name)

        path = os.path.join(os.path.dirname(__file__), 'templates', 'events.html')
        self.response.out.write(template.render(path, {"events": events, "more": more,}))

def main():
    #logging.getLogger().setLevel(logging.DEBUG if DEBUG else logging.WARN)
    logging.getLogger().setLevel(logging.DEBUG)

    application = webapp.WSGIApplication([
                                            (r'/calendar/([^\/]*)/([^\/]*)/[^\/]+\.ics$', ICSHandler),
                                            (r'/calendar/([^\/]*)/[^\/]+\.ics$', ICSHandler),
                                            (r'/calendar/[^\/]+\.ics$', ICSHandler),
                                            (r'/event/([^\/]*)$', EventHandler),
                                            (r'/year/([^\/]*)$', YearHandler),
                                            (r'/more/([^\/]*)$', MoreHandler),
                                            (r'/$', MainHandler),
                                            (r'/(\w+)/(\d+)$', MainHandler),
                                         ], debug=DEBUG)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()

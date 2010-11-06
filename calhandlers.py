
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.api import memcache
from google.appengine.ext import ereporter
from models import Showing

from datetime import date
import logging
import os
import tasks
import pytz

GB_TZ = pytz.timezone('Europe/London')

DEBUG = os.getenv('SERVER_SOFTWARE').split('/')[0] == "Development" if os.getenv('SERVER_SOFTWARE') else False
ereporter.register_logger()

class GoogleShowingHandler(webapp.RequestHandler):
    def get(self, showingkey):
        showing = Showing.get(showingkey)

        if showing:
            self.redirect(
                    "http://www.google.com/calendar/event?action=TEMPLATE&text=%s&dates=%s/%s&location=%s&details=%s&sprop=website:http://bfical.burry.name/&sprop=name:BFiCal" %
                    (showing.parent().name,
                     showing.start.replace(tzinfo=GB_TZ).astimezone(pytz.utc).strftime("%Y%m%dT%H%M%SZ"),
                     showing.end.replace(tzinfo=GB_TZ).astimezone(pytz.utc).strftime("%Y%m%dT%H%M%SZ"),
                     '%s, BFI %s, London' % (showing.location, showing.master_location.capitalize()),
                     showing.parent().precis,
                     ))
        else:
            self.error(404)


class ICSShowingHandler(webapp.RequestHandler):
    def get(self, showingkey):
        showing = Showing.get(showingkey)
        if showing:
            calendar = tasks.generate_ics([showing,], showing.master_location)

        if calendar is not None:
            self.response.headers['Content-Type'] = "text/calendar"
            self.response.out.write(calendar.as_string())
        else:
            self.error(404)

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

def main():
    #logging.getLogger().setLevel(logging.DEBUG if DEBUG else logging.WARN)
    logging.getLogger().setLevel(logging.DEBUG)

    application = webapp.WSGIApplication([
                                            (r'/calendar/google/([^\/]+)$', GoogleShowingHandler),
                                            (r'/calendar/([^\/]+)/showing\.ics$', ICSShowingHandler),
                                            (r'/calendar/([^\/]*)/([^\/]*)/[^\/]+\.ics$', ICSHandler),
                                            (r'/calendar/([^\/]*)/[^\/]+\.ics$', ICSHandler),
                                            (r'/calendar/[^\/]+\.ics$', ICSHandler),
                                         ], debug=DEBUG)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
from BFIParser import BFIParser
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.api.labs import taskqueue
from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext import ereporter
from google.appengine.ext.webapp import template
from models import Event, Showing
from datetime import date, timedelta
from icalendar.cal import Calendar, Event as CalEvent
import time
import logging
import os
import pytz

ereporter.register_logger()

DEBUG = os.getenv('SERVER_SOFTWARE').split('/')[0] == "Development" if os.getenv('SERVER_SOFTWARE') else False
QUEUE_RETRY = 5

ICS_CACHEKEY_TMPL = 'cal-%s-%s'
HOME_CACHEKEY_TMPL = 'home-%s'
LATCH_CACHEKEY_TMPL = 'lat-%s-%s'

GB_TZ = pytz.timezone('Europe/London')

def generate_homepage(location='southbank', weekoffset=0):
    today = date.today()

    if weekoffset > 0:
        startdate = today + timedelta((weekoffset * 7) - today.weekday())
        enddate = startdate + timedelta(7)
    else:
        startdate = today
        enddate = startdate + timedelta(7 - startdate.weekday())

    showings = db.Query(Showing).filter("master_location", location).filter("start >=", startdate).filter("start <", enddate).order("start").fetch(1000)
    path = os.path.join(os.path.dirname(__file__), 'templates', 'index.html')
    return template.render(path, {"showings": showings, "location": location, "page": weekoffset, "startdate": startdate,})

def generate_ics(showings, location):
    calendar = Calendar()
    caplocation = location.capitalize()
    calendar.add('prodid', '-//BFiCal %s Calendar//bfical.com//' % caplocation)
    calendar.add('version', '2.0')

    for showing in showings:
        if showing.master_location == location:
            calevent = CalEvent()
            if showing.ident:
                calevent.add('uid', '%s@bfical.com' % showing.ident)
            else:
                calevent.add('uid', '%s@bfical.com' % int(time.time()))
            calevent.add('summary', showing.parent().name)
            calevent.add('description', showing.parent().precis)
            calevent.add('location', '%s, BFI %s, London' % (showing.location, caplocation))
            calevent.add('dtstart', showing.start.replace(tzinfo=GB_TZ).astimezone(pytz.utc))
            calevent.add('dtend', showing.end.replace(tzinfo=GB_TZ).astimezone(pytz.utc))
            calevent.add('url', showing.parent().src_url)
            calevent.add('sequence', int(time.time())) # TODO - fix
            #calevent.add('dtstamp', datetime.datetime.now())

            calendar.add_component(calevent)

    return calendar


def generate_calendar(location = 'southbank', sublocation=None):
    showings = db.Query(Showing).filter("start >=", date.today())
    if sublocation is not None:
        showings = showings.filter("location", sublocation)

    return generate_ics(showings, location)


def continue_processing_task(request):
    retrycount = request.headers['X-AppEngine-TaskRetryCount']
    logging.debug("Queue retry count:%s" % retrycount)
    return retrycount is None or int(retrycount) <= QUEUE_RETRY

class UpdateHandler(webapp.RequestHandler):
    def get(self):
        return self.post()

    def post(self, location='southbank'):
        memcache.set(ICS_CACHEKEY_TMPL % (location, None), generate_calendar(location, None), time=1800)
        listing_urls = BFIParser.generate_listing_urls()
        countdown = 1
        cachekey = LATCH_CACHEKEY_TMPL % (location, time.time())
        for url in listing_urls:
            logging.debug("Queueing listing url:%s" % url)
            taskqueue.add(url='/tasks/process_listings_url', params={'url': url, 'cachekey': cachekey}, queue_name='background-queue', countdown=countdown)
            countdown = countdown + 1
        self.response.out.write(listing_urls)

        taskqueue.add(url='/tasks/generate_calendar', countdown=1800)


class PurgeHandler(webapp.RequestHandler):
    def get(self):
        self.post()

    def post(self):
        memcache.flush_all()

        db.delete(Showing.all())
        db.delete(Event.all())

        handler = UpdateHandler()
        handler.initialize(self.request, self.response)
        handler.post()


class ListingsHandler(webapp.RequestHandler):
    def post(self):
        if continue_processing_task(self.request):
            urls = BFIParser.parse_listings_page(self.request.get('url'))
            countdown = 1
            cachekey = self.request.get('cachekey')
            for url in urls:
                if memcache.get(url) is None:
                    memcache.set(url, 1, time=1800)
                    logging.debug("Queueing event url:%s" % url)
                    remaining = memcache.incr(cachekey, initial_value=0)
                    logging.debug("Incremented remaining count to %s" % remaining)
                    taskqueue.add(url='/tasks/process_event_url', params={'url': url, 'cachekey': cachekey}, queue_name='background-queue', countdown=countdown)
                    countdown = countdown + 1
                    self.response.out.write(url)
                else:
                    logging.debug("Already process(ed|ing) url %s" % url)

class GenerateHandler(webapp.RequestHandler):
    def post(self):
        for location in BFIParser.LOCATIONS:
            memcache.set(HOME_CACHEKEY_TMPL % location, generate_homepage(location), time=86400)
            memcache.set(ICS_CACHEKEY_TMPL % (location, None), generate_calendar(location, None), time=86400)

class EventHandler(webapp.RequestHandler):
    def post(self, location='southbank'):
        if continue_processing_task(self.request):
            eventurl = self.request.get('url')
            cachekey = self.request.get('cachekey')

            logging.debug("Processing event url %s" % eventurl)
            # Parse page
            bfievent = BFIParser.parse_event_page(eventurl)

            def persist_showings(dbevent, bfievent):
                # Delete existing showings for this event
                db.delete(db.Query(Showing).ancestor(dbevent))

                # Save events
                for showing in bfievent.showings:
                    Showing(parent=dbevent,
                            ident=showing.id,
                            location=showing.location,
                            master_location=location,
                            start=showing.start,
                            end=showing.end).put()

            event = Event.get_or_insert(key_name=bfievent.url,
                                        src_url=db.Link(bfievent.url),
                                        name=bfievent.title,
                                        precis=bfievent.precis,
                                        year=bfievent.year,
                                        directors=bfievent.directors,
                                        cast=bfievent.cast,
                                        description=bfievent.description)
            event.src_url=db.Link(bfievent.url)
            event.name=bfievent.title
            event.precis=bfievent.precis
            event.year=bfievent.year
            event.directors=bfievent.directors
            event.cast=bfievent.cast
            event.description=bfievent.description
            event.put()

            db.run_in_transaction(persist_showings, event, bfievent)
            logging.debug("Processed event url %s" % eventurl)

            remaining = memcache.decr(cachekey, initial_value=0)
            logging.debug("Decremented remaining count to %s" % remaining)
            if remaining <= 0:
                db.delete(db.Query(Showing).filter("updated <", date.today()))
                db.delete(db.Query(Event).filter("updated <", date.today()))
                memcache.delete(HOME_CACHEKEY_TMPL % location)


def main():
    logging.getLogger().setLevel(logging.DEBUG if DEBUG else logging.WARN)

    application = webapp.WSGIApplication([
                                            ('/tasks/update', UpdateHandler),
                                            ('/tasks/purge', PurgeHandler),
                                            ('/tasks/process_listings_url', ListingsHandler),
                                            ('/tasks/process_event_url', EventHandler),
                                            ('/tasks/generate_calendar', GenerateHandler),
                                         ], debug=DEBUG)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()

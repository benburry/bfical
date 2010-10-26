from BFIParser import BFIParser
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.api.labs import taskqueue
from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext import ereporter
from models import Event, Showing
from datetime import date
from icalendar.cal import Calendar, Event as CalEvent
import time
import logging
import os
import main

ereporter.register_logger()

DEBUG = os.getenv('SERVER_SOFTWARE').split('/')[0] == "Development" if os.getenv('SERVER_SOFTWARE') else False
QUEUE_RETRY = 5
ICS_CACHEKEY_TMPL = 'cal-%s'
HOME_CACHEKEY_TMPL = 'home-%s'

def generate_calendar(location = 'southbank'):
    calendar = Calendar()
    caplocation = location.capitalize()
    calendar.add('prodid', '-//BFiCal %s Calendar//bfical.com//' % caplocation)
    calendar.add('version', '2.0')

    for showing in db.Query(Showing).filter("start >=", date.today()):
        if showing.parent().location == location:
            calevent = CalEvent()
            calevent.add('uid', '%s@bfical.com' % showing.ident)
            calevent.add('summary', showing.parent().name)
            calevent.add('description', showing.parent().description)
            calevent.add('location', '%s, %s' % (showing.location, caplocation))
            calevent.add('dtstart', showing.start)
            calevent.add('dtend', showing.end)
            calevent.add('url', showing.parent().src_url)
            calevent.add('sequence', int(time.time())) # TODO - fix
            #calevent.add('dtstamp', datetime.datetime.now())
            calendar.add_component(calevent)

    return calendar

def continue_processing_task(request):
    retrycount = request.headers['X-AppEngine-TaskRetryCount']
    logging.debug("Queue retry count:%s" % retrycount)
    return retrycount is None or int(retrycount) <= QUEUE_RETRY

class UpdateHandler(webapp.RequestHandler):
    def get(self):
        return self.post()

    def post(self, location='southbank'):
        memcache.set(ICS_CACHEKEY_TMPL % location, generate_calendar(location), time=1800)
        listing_urls = BFIParser.generate_listing_urls()
        countdown = 1
        for url in listing_urls:
            logging.debug("Queueing listing url:%s" % url)
            taskqueue.add(url='/tasks/process_listings_url', params={'url': url}, queue_name='background-queue', countdown=countdown)
            countdown = countdown + 1
        self.response.out.write(listing_urls)

        taskqueue.add(url='/tasks/generate_calendar', countdown=1800)
        # TODO - Send out queued task for clearing events non-updated showing past today after all processing complete

class PurgeHandler(webapp.RequestHandler):
    def get(self):
        self.post()

    def post(self):
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
            for url in urls:
                if memcache.get(url) is None:
                    memcache.set(url, 1, time=1800)
                    logging.debug("Queueing event url:%s" % url)
                    taskqueue.add(url='/tasks/process_event_url', params={'url': url}, queue_name='background-queue', countdown=countdown)
                    countdown = countdown + 1
                    self.response.out.write(url)
                else:
                    logging.debug("Already process(ed|ing) url %s" % url)

class GenerateHandler(webapp.RequestHandler):
    def post(self):
        for location in BFIParser.LOCATIONS:
            memcache.set(HOME_CACHEKEY_TMPL % location, main.generate_homepage(location), time=86400)
            memcache.set(ICS_CACHEKEY_TMPL % location, generate_calendar(location), time=86400)

class EventHandler(webapp.RequestHandler):
    def post(self, location='southbank'):
        if continue_processing_task(self.request):
            eventurl = self.request.get('url')

            logging.debug("Processing event url %s" % eventurl)
            # Parse page
            bfievent = BFIParser.parse_event_page(eventurl)

            def persist_events(dbevent, bfievent):
                # Delete existing showings for this event past current date
                db.delete(db.Query(Showing).ancestor(dbevent).filter("start >=", date.today()))

                # Save events
                for showing in bfievent.showings:
                    if showing.id:  # TODO - how to store fully-booked showings?
#                        db.delete(Showing.get_by_key_name(showing.id))

                        Showing(key_name=showing.id,
                                parent=dbevent,
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

            db.run_in_transaction(persist_events, event, bfievent)
            memcache.delete(HOME_CACHEKEY_TMPL % location)
            logging.debug("Processed event url %s" % eventurl)


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

from BFIParser import BFIParser
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.api.labs import taskqueue
from google.appengine.api import memcache
from google.appengine.ext import db
from models import Event
import logging
import os

DEBUG = os.getenv('SERVER_SOFTWARE').split('/')[0] == "Development" if os.getenv('SERVER_SOFTWARE') else False

def events_from_bfievent(bfievent):
    events = []
    for showing in bfievent.showings:
        events.append(Event(showing_ident=showing.id,
                            src_url=db.Link(bfievent.url),
                            event_location='southbank', #TODO - changeme
                            name=bfievent.title,
                            precis=bfievent.precis,
                            description=bfievent.description,
                            showing_location=showing.location,
                            showing_start=showing.start,
                            showing_end=showing.end))
    return events

class UpdateHandler(webapp.RequestHandler):
    def post(self):
        listing_urls = BFIParser.generate_listing_urls()
        for url in listing_urls:
            taskqueue.add(url='/tasks/process_listings_url', params={'url': url}, queue_name='background-queue', countdown=1)
        self.response.out.write(listing_urls)
        # Send out queued task for clearing event non-updated showing past today after all processing complete

class ListingsHandler(webapp.RequestHandler):
    def post(self):
        urls = BFIParser.parse_listings_page(self.request.get('url'))
        for url in urls:
            taskqueue.add(url='/tasks/process_event_url', params={'url': url}, queue_name='background-queue', countdown=1)
            self.response.out.write(url)

class EventHandler(webapp.RequestHandler):
    def post(self):
        eventurl = self.request.get('url')

        if memcache.get(eventurl) is None:
            memcache.set(eventurl, 1, time=1200)
            logging.debug("Processing event url %s" % eventurl)
            # Parse page
            bfievent = BFIParser.parse_event_page(eventurl)
            # Delete existing showings for this event past current date
            def persist_events(events):
                # Save events
                for event in events:
                    logging.debug("About to persist event %s" % event.showing_ident)

            db.run_in_transaction(persist_events, events_from_bfievent(bfievent))

        else:
            logging.debug("Already process(ed|ing) url %s" % eventurl)


def main():
    logging.getLogger().setLevel(logging.DEBUG if DEBUG else logging.WARN)

    application = webapp.WSGIApplication([
                                            ('/tasks/update', UpdateHandler),
                                            ('/tasks/process_listings_url', ListingsHandler),
                                            ('/tasks/process_event_url', EventHandler),
                                         ], debug=DEBUG)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()

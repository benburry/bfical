from BFIParser import BFIParser
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.api.labs import taskqueue
from google.appengine.api import memcache
from google.appengine.ext import db
from models import Event, Showing
from datetime import date
import logging
import os


DEBUG = os.getenv('SERVER_SOFTWARE').split('/')[0] == "Development" if os.getenv('SERVER_SOFTWARE') else False
QUEUE_RETRY = 5


def continue_processing_task(request):
    retrycount = request.headers['X-AppEngine-TaskRetryCount']
    return not(retrycount is not None and int(retrycount) > QUEUE_RETRY)

class UpdateHandler(webapp.RequestHandler):
    def post(self):
        listing_urls = BFIParser.generate_listing_urls()
        for url in listing_urls[0]:
            taskqueue.add(url='/tasks/process_listings_url', params={'url': url}, queue_name='background-queue', countdown=1)
        self.response.out.write(listing_urls)
        # Send out queued task for clearing event non-updated showing past today after all processing complete

class ListingsHandler(webapp.RequestHandler):
    def post(self):
        if continue_processing_task(self.request):
            urls = BFIParser.parse_listings_page(self.request.get('url'))
            for url in urls:
                if memcache.get(url) is None:
                    memcache.set(url, 1, time=1200)
                    taskqueue.add(url='/tasks/process_event_url', params={'url': url}, queue_name='background-queue', countdown=1)
                    self.response.out.write(url)
                else:
                    logging.debug("Already process(ed|ing) url %s" % url)

class EventHandler(webapp.RequestHandler):
    def post(self):
        if continue_processing_task(self.request):
            eventurl = self.request.get('url')

            logging.debug("Processing event url %s" % eventurl)
            # Parse page
            bfievent = BFIParser.parse_event_page(eventurl)

            def persist_events(dbevent, bfievent):
                # Delete existing showings for this event past current date
                db.delete(db.Query(Showing).ancestor(dbevent).filter("end >=", date.today()))

                # Save events
                for showing in bfievent.showings:
                    if showing.id:  # TODO - how to store fully-booked showings?
#                        db.delete(Showing.get_by_key_name(showing.id))

                        Showing(key_name=showing.id,
                                parent=dbevent,
                                ident=showing.id,
                                location=showing.location,
                                start=showing.start,
                                end=showing.end).put()

            event = Event.get_or_insert(key_name=bfievent.url,
                                  src_url=db.Link(bfievent.url),
                                  location='southbank', #TODO - changeme
                                  name=bfievent.title,
                                  precis=bfievent.precis,
                                  description=bfievent.description)

            db.run_in_transaction(persist_events, event, bfievent)


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

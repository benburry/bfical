from BFIParser import BFIParser
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.api.labs import taskqueue
import logging
import os

DEBUG = os.getenv('SERVER_SOFTWARE').split('/')[0] == "Development" if os.getenv('SERVER_SOFTWARE') else False

class ListingsHandler(webapp.RequestHandler):
    def post(self):
        urls = BFIParser.parse_listings_page(self.request.get('url'))
        for url in urls:
            taskqueue.add(url='/tasks/process_event_url', params={'url': url}, queue_name='background-queue')
            self.response.out.write(url)

class EventHandler(webapp.RequestHandler):
    def post(self):
        BFIParser.parse_event_page(self.request.get('url'))


def main():
    logging.getLogger().setLevel(logging.DEBUG if DEBUG else logging.WARN)

    application = webapp.WSGIApplication([
                                            ('/tasks/process_listings_url', ListingsHandler),
                                            ('/tasks/process_event_url', EventHandler),
                                         ], debug=DEBUG)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()

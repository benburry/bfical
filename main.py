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
from google.appengine.api.labs import taskqueue

import logging
import os

from icalendar.cal import Event
from BFIParser import BFIParser


DEBUG = os.getenv('SERVER_SOFTWARE').split('/')[0] == "Development" if os.getenv('SERVER_SOFTWARE') else False

class MainHandler(webapp.RequestHandler):
    def get(self):
        listing_urls = BFIParser.generate_listing_urls()
        for url in listing_urls:
            taskqueue.add(url='/tasks/process_listings_url', params={'url': url}, queue_name='background-queue', countdown=1)
        self.response.out.write(listing_urls)


def main():
    logging.getLogger().setLevel(logging.DEBUG if DEBUG else logging.WARN)

    application = webapp.WSGIApplication([
                                            ('/', MainHandler),
                                         ], debug=DEBUG)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()

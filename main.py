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

import logging
import os
import tasks


DEBUG = os.getenv('SERVER_SOFTWARE').split('/')[0] == "Development" if os.getenv('SERVER_SOFTWARE') else False

class MainHandler(webapp.RequestHandler):
    def get(self):
        handler = tasks.UpdateHandler()
        handler.initialize(self.request, self.response)
        handler.post()

        #for showing in db.Query(Showing).filter("start >=", date.today()):
        #    self.response.out.write(unicode(showing))

class SouthBankHandler(webapp.RequestHandler):
    def get(self):

        calendar = None
        if not DEBUG:
            calendar = memcache.get(tasks.CACHEKEY)

        if calendar is None:
            calendar = tasks.generate_calendar()
            memcache.set(tasks.CACHEKEY, calendar)

        if calendar is not None:
            self.response.headers['Content-Type'] = "text/calendar"
            self.response.out.write(calendar.as_string())
        else:
            self.error(404)

def main():
    logging.getLogger().setLevel(logging.DEBUG if DEBUG else logging.WARN)

    application = webapp.WSGIApplication([
                                            ('/', MainHandler),
                                            ('/southbank/ics', SouthBankHandler),
                                         ], debug=DEBUG)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()

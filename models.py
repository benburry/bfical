__author__ = 'ben'

from google.appengine.ext import db

class Event(db.Model):
    showing_ident = db.StringProperty(required=True)
    src_url = db.LinkProperty(required=True)
    event_location = db.StringProperty(required=True)
    name = db.StringProperty()
    precis = db.StringProperty()
    showing_location = db.StringProperty()
    showing_start = db.DateTimeProperty(required=True)
    showing_end = db.DateTimeProperty(required=True)
    description = db.TextProperty()


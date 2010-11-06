__author__ = 'ben'

from google.appengine.ext import db

class Showing(db.Model):
    ident = db.StringProperty()
    location = db.StringProperty()
    master_location = db.StringProperty()
    start = db.DateTimeProperty(required=True)
    end = db.DateTimeProperty(required=True)
    updated = db.DateTimeProperty(auto_now=True)

class Event(db.Model):
    src_url = db.LinkProperty(required=True)
    name = db.StringProperty()
    precis = db.StringProperty()
    year = db.StringProperty()
    directors = db.StringListProperty()
    cast = db.StringListProperty()
    description = db.TextProperty()
    updated = db.DateTimeProperty(auto_now=True)


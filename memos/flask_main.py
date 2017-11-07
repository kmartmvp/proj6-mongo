"""
Flask web app connects to Mongo database.
Keep a simple list of dated memoranda.

Representation conventions for dates: 
   - We use Arrow objects when we want to manipulate dates, but for all
     storage in database, in session or g objects, or anything else that
     needs a text representation, we use ISO date strings.  These sort in the
     order as arrow date objects, and they are easy to convert to and from
     arrow date objects.  (For display on screen, we use the 'humanize' filter
     below.) A time zone offset will 
   - User input/output is in local (to the server) time.  
"""

import flask
from flask import g
from flask import render_template
from flask import request
from flask import url_for

import json
import logging
import random

import sys

# Date handling 
import arrow   
from dateutil import tz  # For interpreting local times

# Mongo database
from pymongo import MongoClient

import config

if __name__ == "__main__":
    CONFIG = config.configuration()
else:
    CONFIG = config.configuration(proxied=True)


MONGO_CLIENT_URL = "mongodb://{}:{}@{}:{}/{}".format(
    CONFIG.DB_USER,
    CONFIG.DB_USER_PW,
    CONFIG.DB_HOST, 
    CONFIG.DB_PORT, 
    CONFIG.DB)


print("Using URL '{}'".format(MONGO_CLIENT_URL))


###
# Globals
###

app = flask.Flask(__name__)
app.secret_key = CONFIG.SECRET_KEY

####
# Database connection per server process
###

try: 
    dbclient = MongoClient(MONGO_CLIENT_URL)
    db = getattr(dbclient, CONFIG.DB)
    collection = db.memos

except:
    print("Failure opening database.  Is Mongo running? Correct password?")
    sys.exit(1)



###
# Pages
###

@app.route("/")
@app.route("/index")
def index():
  app.logger.debug("Main page entry")
  g.memos = get_memos()
  for memo in g.memos: 
      app.logger.debug("Memo: " + str(memo))
  return flask.render_template('index.html')


# We don't have an interface for creating memos yet
@app.route("/create")
def create():
    app.logger.debug("Create")
    return flask.render_template('create.html')


# Handle requests to create new memos and add to db
@app.route("/create_handler")
def create_handler():
    date          = flask.request.args.get('date')
    txt           = flask.request.args.get('text')
    redirect_json = {"redirect": "/index"}

    # Insert into collection
    collection.insert_one({
        "type": "dated_memo",
        "date": date,
        "text": txt,
        "token": random.randrange(1,1000000)
    })

    # Return to request the correct redirect
    return flask.jsonify(result=redirect_json)


# Handle deleting of memos from db
@app.route("/delete")
def delete():
    delete_id = int(flask.request.args.get('id'))
    # Use remove() for Pi compatibility, as delete_one was added in 3.0
    collection.remove({'token': delete_id})

    return flask.jsonify({})


@app.errorhandler(404)
def page_not_found(error):
    app.logger.debug("Page not found")
    return flask.render_template('page_not_found.html',
                                 badurl=request.base_url,
                                 linkback=url_for("index")), 404

#################
#
# Functions used within the templates
#
#################


@app.template_filter( 'humanize' )
def humanize_arrow_date( date ):
    """
    Date is internal UTC ISO format string.
    Output should be "today", "yesterday", "in 5 days", etc.
    Arrow will try to humanize down to the minute, so we
    need to catch 'today' as a special case. 
    """
    try:
        then = arrow.get(date).to('local')
        now = arrow.utcnow().to('local')
        if then.date() == now.date():
            human = "Today"
        else: 
            human = then.humanize(now)
            if human == "in a day":
                human = "Tomorrow"
    except: 
        human = date
    return human


#############
#
# Functions available to the page code above
#
##############
def get_memos():
    """
    Returns all memos in the database, in a form that
    can be inserted directly in the 'session' object.
    """
    records = [ ]
    for record in collection.find( { "type": "dated_memo" } ):
        record['date'] = arrow.get(record['date']).isoformat()
        del record['_id']
        records.append(record)
    
    # Sort according to the date value of each "dictionary" x in results
    sorted_records = sorted(records, key=lambda x: x['date'])
    
    return sorted_records 


if __name__ == "__main__":
    app.debug=CONFIG.DEBUG
    app.logger.setLevel(logging.DEBUG)
    app.run(port=CONFIG.PORT,host="0.0.0.0")

    

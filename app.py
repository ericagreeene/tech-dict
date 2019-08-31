import os
import json
import contentful
from flask import Flask, render_template
from flaskext.markdown import Markdown
from jinja2 import Environment

app = Flask(__name__)

Markdown(app)

SPACE_ID = '0iipfzf6z60u'
DELIVERY_ACCESS_TOKEN = os.environ.get('DELIVERY_ACCESS_TOKEN')

# We set the Contentful client timeout high because we only have to
# to fetch when we freeze, not per request
CLIENT_TIMEOUT_SECONDS=60
N_RECENT_ENTRIES = 10

app.jinja_env.filters['datetime'] = lambda x: x.strftime('%B %d %Y')

def _get_client():
    if DELIVERY_ACCESS_TOKEN is None:
        print('Must set DELIVERY_ACCESS_TOKEN env variable')
        exit(1)

    return contentful.Client(
        space_id=SPACE_ID,
        access_token=DELIVERY_ACCESS_TOKEN,
        timeout_s=CLIENT_TIMEOUT_SECONDS,
    )

def _entries_to_dict(entries):
    """
    Takes an array of Contentful entries and returns dict of data required
    to render templates.


    """
    return [
            {
                'title': e.fields().get('title').lower(),
                'id': e.id,
                'definitions': [
                    {
                        'body': d.fields().get('body'),
                        'id': d.id,
                        'tags': [t.lower() for t in d.fields().get('tags', [])],

                        # the author is a link so we need to make another
                        # api call to resolve it
                        'author': d.author.name,
                        'publish_date': d.fields().get('publish_date'),
                    } for d in e.fields().get('definition', [])
                ]
            } for e in entries]

def _get_recent_entries():
    """Fetch all entries"""
    client = _get_client()

    entries = client.entries({
        'content_type': 'entry',
        'include': 2,
        'order': 'fields.title',
#        'limit': N_RECENT_ENTRIES,
    })

    return _entries_to_dict(entries)

def _get_entry(entry_id):
    """Fetch single entry by ID"""
    client = _get_client()
    entry = client.entry(entry_id, query={'include': 2})
    return _entries_to_dict([entry])

def _get_about():
    """Fetch About Page"""
    client = _get_client()
    abouts =  client.entries({
        'content_type': 'aboutPage',
        'limit': 1,
        })

    # HACK -- we assume there is only one About Page. We blindly take
    # the first one in the list.
    if len(abouts) == 0:
        return ""

    return abouts[0].text

def _get_homepage():
    """Fetch homepage content"""
    client = _get_client()
    modules =  client.entries({
        'content_type': 'homepageModule',
        'include': 2,
        'limit': 5,
        })

    return [
        {
            'title': m.title,
            'body': m.body,
            'entries': [
                {
                    'title': e.title.lower(),
                    'id': e.id,
                    'teaser': e.fields().get("teaser", ""),
                    'tags': e.definition[0].fields().get("tags", []),
                } for e in m.entries],
        } for m in modules
    ]

def _get_contribute():
    """Fetch Contribute Page"""
    client = _get_client()
    pages =  client.entries({
        'content_type': 'contributePage',
        'limit': 1,
        })

    # HACK -- we assume there is only one
    if len(pages) == 0:
        return ""

    return pages[0].text

@app.route("/")
def home():
    hp_modules = _get_homepage()

    all_entries = _get_recent_entries()
    entries = {
        'a_f': [e for e in all_entries if e['title'][0] <= 'f'],
        'g_z': [e for e in all_entries if e['title'][0] > 'f'],
    }

    return render_template(
        "homepage.html",
        hp_modules=hp_modules,
        entries=entries,
    )

@app.route("/about.html")
def about():
    text = _get_about()

    return render_template("about.html", text=text)

@app.route("/contribute.html")
def contribute():
    text = _get_contribute()

    return render_template("contribute.html", text=text)

@app.route("/entry-<entry_id>.html")
def entry(entry_id):
    entry = _get_entry(entry_id)
    return render_template("entry.html", entries=entry)


if __name__ == "__main__":
    app.run()

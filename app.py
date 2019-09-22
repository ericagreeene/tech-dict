import os
import json
import random
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

# number of recirculation entries on the entry pages
N_RECIRC = 3

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

                # HACK, take the tags from the first definition
                'tags': e.definition[0].fields().get("tags", []),
                'teaser': e.fields().get("teaser", ""),
                'definitions': [
                    {
                        'body': d.fields().get('body'),
                        'id': d.id,
                        'tags': [t.lower() for t in d.fields().get('tags', [])],
                        'author': d.author.name,
                        'publish_date': d.fields().get('publish_date'),
                    } for d in e.fields().get('definition', [])
                ]
            } for e in entries if len(e.definition) > 0]

def _get_recent_entries():
    """Fetch all entries"""
    client = _get_client()

    entries = client.entries({
        'content_type': 'entry',
        'include': 2,
        'order': 'fields.title',
    })

    return _entries_to_dict(entries)

def _get_random_entries(client, n=3):
    """Returns n random entries"""

    # Find the total number of available entries
    entries = client.entries({
        'content_type': 'entry',
        'include': 0,
    })
    n_entries = len(entries)

    entries = []
    for i in range(n):
        entry = client.entries(
            {
                'content_type': 'entry',
                'skip': random.randint(0, n_entries-1),
                'limit': 1,
                'include': 2
            })

        entries.append(entry[0])

    return _entries_to_dict(entries)

def _get_entry(client, entry_id):
    """Fetch single entry by ID"""
    entry = client.entry(entry_id, query={'include': 2})

    return _entries_to_dict([entry])

# def _get_about():
#     """Fetch About Page"""
#     client = _get_client()
#     abouts =  client.entries({
#         'content_type': 'aboutPage',
#         'limit': 1,
#         })

#     # HACK -- we assume there is only one About Page. We blindly take
#     # the first one in the list.
#     if len(abouts) == 0:
#         return ""

#     return abouts[0].text

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
    # hp_modules = _get_homepage()
    hp_modules = []

    all_entries = _get_recent_entries()
    contribute_text = _get_contribute()
    entry_groups = [
        {
            'title': 'A - E',
            'entries': [e for e in all_entries if e['title'][0] <= 'e'],
        },
        {
            'title': 'F - S':
            'entries': [e for e in all_entries if e['title'][0] > 'e' and e['title'][0] =< 's'],
        },
        {
            'title': 'T - Z':
            'entries': [e for e in all_entries if e['title'][0] > 's'],
        },
    ]

    return render_template(
        "homepage.html",
        hp_modules=hp_modules,
        entry_groups=entry_groups,
        contribute_text=contribute_text,
    )

# @app.route("/about.html")
# def about():
#     text = _get_about()

#     return render_template("about.html", text=text)

@app.route("/contribute.html")
def contribute():
    text = _get_contribute()

    return render_template("contribute.html", text=text)

@app.route("/entry-<entry_id>.html")
def entry(entry_id):
    client = _get_client()
    entry = _get_entry(client, entry_id)
    random_entries = _get_random_entries(client, N_RECIRC + 1)

    # Filter out current entry from recirc
    random_entries = [e for e in random_entries if e["id"] != entry_id]

    return render_template(
        "entry.html",
        entries=entry,
        random_entries=random_entries[0:N_RECIRC],
    )


if __name__ == "__main__":
    app.run()

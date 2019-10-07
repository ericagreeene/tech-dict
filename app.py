import os
import json
import random
import contentful
from collections import defaultdict
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
                # 'id': e.id,
                'id': e.fields().get('slug', '').lower(),
                'slug': e.definition[0].slug,

                # HACK, take the tags from the first definition
                'tags': e.definition[0].fields().get("tags", []),
                'teaser': e.fields().get("teaser", ""),
                'pos': e.fields().get("part_of_speech", "").lower(),
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

    # entry = client.entry(entry_id, query={'include': 2})
    entries = client.entries({
        'fields.slug': entry_id,
        'content_type': 'entry',
        'include': 2,
    })

    # TODO: error checking if entry doesn't exist

    return _entries_to_dict([entries[0]])

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

def _get_wishlist():
    """Fetch wishlist of terms and phrases"""
    client = _get_client()
    wishlist =  client.entries({
        'content_type': 'wishList',
        'limit': 1,
        })

    # HACK -- we assume there is only one
    if len(wishlist) == 0:
        return ""

    # List of newline separated terms
    terms = [w.strip() for w in wishlist[0].terms.split('\n')]

    return terms

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
    all_entries = _get_recent_entries()
    about_text = _get_about()
    contribute_text = _get_contribute()

    entries_by_pos = defaultdict(list)
    for e in all_entries:
        entries_by_pos[e['pos']] += [e]

    entry_groups = []
    for pos, entries in entries_by_pos.items():
        entry_groups.append(
            {
                'title': (pos + 's').title(),
                'entries': entries,
            }
        )

    return render_template(
        "homepage.html",
        about_text=about_text,
        entry_groups=entry_groups,
        contribute_text=contribute_text,
    )

@app.route("/wishlist.html")
def wishlist():
    terms = _get_wishlist()
    return render_template("wishlist.html", terms=terms)

@app.route("/<entry_id>.html")
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

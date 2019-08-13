import os
import contentful
from flask import Flask, render_template
from flaskext.markdown import Markdown
from jinja2 import Environment

app = Flask(__name__)

Markdown(app)

SPACE_ID = '0iipfzf6z60u'
DELIVERY_ACCESS_TOKEN = os.environ.get('DELIVERY_ACCESS_TOKEN')

app.jinja_env.filters['datetime'] = lambda x: x.strftime('%B %d %Y')


def _get_client():
    if DELIVERY_ACCESS_TOKEN is None:
        print('Must set DELIVERY_ACCESS_TOKEN env variable')
        exit(1)

    return contentful.Client(SPACE_ID, DELIVERY_ACCESS_TOKEN)

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

def get_entries():
    client = _get_client()

    entries = client.entries({
        'content_type': 'entry',
        'include': 2,
        'order': 'fields.title',
    })

    return _entries_to_dict(entries)

def get_entry(entry_id):
    client = _get_client()
    entry = client.entry(entry_id, query={'include': 2})
    return _entries_to_dict([entry])

@app.route("/")
def home():
    entries = get_entries()

    return render_template("dict.html", entries=entries)

@app.route("/about.html")
def about():
    text = "This is an about page"

    return render_template("about.html", text=text)

@app.route("/entry-<entry_id>.html")
def entry(entry_id):
    entry = get_entry(entry_id)

    return render_template("dict.html", entries=entry)


if __name__ == "__main__":
    app.run()

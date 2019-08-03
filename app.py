import os
from contentful import Client
from flask import Flask, render_template
from flaskext.markdown import Markdown
from jinja2 import Environment

app = Flask(__name__)

Markdown(app)

SPACE_ID = '0iipfzf6z60u'
DELIVERY_ACCESS_TOKEN = os.environ.get('DELIVERY_ACCESS_TOKEN')

app.jinja_env.filters['datetime'] = lambda x: x.strftime('%B %d %Y')


def getEntries():
    if DELIVERY_ACCESS_TOKEN is None:
        print('Must set DELIVERY_ACCESS_TOKEN env variable')
        exit(1)

    client = Client(SPACE_ID, DELIVERY_ACCESS_TOKEN)

    entries = client.entries({'content_type': 'entry', 'include': 2})

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


@app.route("/")
def home():
    entries = getEntries()

    return render_template("dict.html", entries=entries)

if __name__ == "__main__":

    app.run()

import os
import json
import contentful
from flask import Flask, render_template
from flaskext.markdown import Markdown
from PIL import Image, ImageDraw, ImageFont
from jinja2 import Environment

app = Flask(__name__)

Markdown(app)

SPACE_ID = '0iipfzf6z60u'
DELIVERY_ACCESS_TOKEN = os.environ.get('DELIVERY_ACCESS_TOKEN')

# We set the Contentful client timeout high because we only have to
# to fetch when we freeze, not per request
CLIENT_TIMEOUT_SECONDS=60
N_RECENT_ENTRIES = 10

# HACK -- must run from root directory of repo
BASEPATH = os.path.dirname(os.path.abspath(__file__))

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

def text_wrap(text, font, max_width):
    lines = []

    if font.getsize(text)[0] <= max_width:
        lines.append(text)
    else:
        words = text.split(' ')
        i = 0

        while i < len(words):
            line = ''
            while i < len(words) and font.getsize(line + words[i])[0] <= max_width:
                line = line + words[i] + " "
                i += 1
            if not line:
                line = words[i]
                i += 1

            lines.append(line)
    return lines

def _make_twitter_card(entry, font, subtitle_font, top_font,
                       pos_font):
    eid = entry.id
    title = entry.title
    subtitle = entry.fields().get('teaser', '')
    pos = entry.fields().get('part_of_speech', '').upper()

    imagepath = os.path.join(BASEPATH, 'static/twitter/twitter-card-blank.png')
    image = Image.open(imagepath)

    max_width = 4 * (image.size[0] / 5)
    W, H = image.size

    draw = ImageDraw.Draw(image)

    # Tech Buzzwords Dictionary
    text = 'TECH BUZZWORDS DICTIONARY'
    h = 50
    _draw_centered(h, W, text, top_font, 'black', draw)

    # Title
    h = H / 4
    text = title.upper()
    h = _draw_multiline(h, W, text, font, 'black', draw, max_width)

    # Part of Speech
    line_height = pos_font.getsize('hg')[1]
    if pos != '':
        text = "[{0}]".format(pos)
        h += line_height
        _draw_centered(h, W, text, pos_font, 'black', draw)

    # Subtitle
    h += 2.5 * line_height
    h = _draw_multiline(h, W, subtitle, subtitle_font, 'black', draw, max_width)

    # write image
    filepath = os.path.join(BASEPATH, 'static/twitter/twitter-card-{0}.png')
    # image.show(command='fim')

    image.save(filepath.format(eid))

def _draw_multiline(h, W, text, font, color, draw, max_width):
    lines = text_wrap(text, font, max_width)
    line_height = font.getsize('hg')[1]

    for line in lines:
        _draw_centered(h, W, line, font, 'black', draw)
        h = h + (.8 * line_height)

    return h

def _draw_centered(h, W, text, font, color, draw):
    w, line_height = draw.textsize(text, font=font)
    draw.text(((W-w)/2, h), text, fill='black', font=font)

def _load_font(filename, size):
    fontpath = os.path.join(BASEPATH, 'static/external/fonts', filename)
    font = ImageFont.truetype(fontpath, size=size, encoding='unic')

    return font

def make_twitter_cards():
    client = _get_client()
    entries =  client.entries({
        'content_type': 'entry',
        })

    font = _load_font('Oswald-Bold.ttf', 65)
    subtitle_font = _load_font('Oswald-Light.ttf', 26)
    pos_font = _load_font('Oswald-Bold.ttf', 20)
    top_font = _load_font('Montserrat-SemiBold.ttf', 16)

    for e in entries:
        _make_twitter_card(
            e,
            font=font,
            subtitle_font=subtitle_font,
            pos_font=pos_font,
            top_font=top_font,
        )

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
    # make_twitter_cards()
    app.run()

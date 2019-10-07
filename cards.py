import os
import contentful
from PIL import Image, ImageDraw, ImageFont

SPACE_ID = '0iipfzf6z60u'
DELIVERY_ACCESS_TOKEN = os.environ.get('DELIVERY_ACCESS_TOKEN')

# HACK -- must run from root directory of repo
BASEPATH = os.path.dirname(os.path.abspath(__file__))

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

def make_twitter_card(entry, font, subtitle_font, top_font,
                       pos_font):
    eid = entry.id
    title = entry.title
    subtitle = entry.fields().get('teaser', '')
    pos = entry.fields().get('part_of_speech', '').upper()

    imagepath = os.path.join(BASEPATH, 'static/twitter/twitter-card-blank.png')
    image = Image.open(imagepath)

    max_width = 4.5 * (image.size[0] / 5)
    W, H = image.size

    draw = ImageDraw.Draw(image)

    # Tech Buzzwords Dictionary
    text = 'TECH BUZZWORDS DICTIONARY'
    h = 50
    draw_centered(h, W, text, top_font, 'black', draw)

    # Title
    h = H / 4
    text = title.upper()
    h = draw_multiline(h, W, text, font, 'black', draw, max_width)

    # Part of Speech
    line_height = pos_font.getsize('hg')[1]
    if pos != '':
        text = "[{0}]".format(pos)
        h += (.6 * line_height)
        draw_centered(h, W, text, pos_font, 'black', draw)

    # Subtitle
    h += 2.5 * line_height
    h = draw_multiline(h, W, subtitle, subtitle_font, 'black', draw, max_width)

    # write image
    filepath = os.path.join(BASEPATH, 'static/twitter/twitter-card-{0}.png').format(eid)
    image.save(filepath)

def draw_multiline(h, W, text, font, color, draw, max_width):
    lines = text_wrap(text, font, max_width)
    line_height = font.getsize('hg')[1]

    for line in lines:
        draw_centered(h, W, line, font, 'black', draw)
        h = h + (.8 * line_height)

    return h

def draw_centered(h, W, text, font, color, draw):
    w, line_height = draw.textsize(text, font=font)
    draw.text(((W-w)/2, h), text, fill='black', font=font)

def load_font(filename, size):
    fontpath = os.path.join(BASEPATH, 'static/external/fonts', filename)
    font = ImageFont.truetype(fontpath, size=size, encoding='unic')

    return font

def make_twitter_cards():
    client = contentful.Client(
        space_id=SPACE_ID,
        access_token=DELIVERY_ACCESS_TOKEN,
    )
    entries =  client.entries({
        'content_type': 'entry',
        })

    font = load_font('Oswald-Bold.ttf', 70)
    subtitle_font = load_font('Oswald-Light.ttf', 40)
    pos_font = load_font('Oswald-Bold.ttf', 30)
    top_font = load_font('Montserrat-SemiBold.ttf', 16)

    for e in entries:
        make_twitter_card(
            e,
            font=font,
            subtitle_font=subtitle_font,
            pos_font=pos_font,
            top_font=top_font,
        )



if __name__ == "__main__":

    if DELIVERY_ACCESS_TOKEN is None:
        print('Must set DELIVERY_ACCESS_TOKEN env variable')
        exit(1)

    print('making twitter cards')
    make_twitter_cards()
    print('done!')

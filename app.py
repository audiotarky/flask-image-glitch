from glitch_this import ImageGlitcher
from flask import Flask, send_file
import logging
from io import BytesIO
from random import choice, shuffle
from pathlib import Path
from PIL import Image

glitcher = ImageGlitcher()

app = Flask(
    __name__,
)


def glitch_me(filepath, frames=23):
    return glitcher.glitch_image(
        filepath,
        2,
        cycle=True,
        color_offset=True,
        gif=True,
        frames=frames,
        glitch_change=0.25,
        scan_lines=choice([True, False])
        # seed=100,
    )


@app.route("/<nft>")
@app.route("/")
def serve(nft=None):
    imgs = []
    files = Path("../audiotarky-hugo/content/").glob(
        "artists/anechoics/patterns-of-hope-destruction/**/*.png"
    )
    for filepath in files:
        print(filepath)
        new_glitches = glitch_me(str(filepath))
        imgs.extend(new_glitches)

        with Image.open("audiotarky_ident@2x.png") as logo_img:
            w, h = new_glitches[0].size
            logo_frames = new_glitches[0].copy()
            resized = logo_img.resize((4 * logo_img.size[0], 4 * logo_img.size[1]))
            w = int((w - resized.size[0]) / 2)
            h = int((h - resized.size[1]) / 2)
            logo_frames.paste(resized, (w, h), resized)
            imgs.extend(glitch_me(logo_frames, frames=5))

    sublist = imgs[1:]
    shuffle(sublist)
    img_io = BytesIO()
    imgs[0].save(
        img_io,
        "gif",
        save_all=True,
        quality=70,
        append_images=sublist,
        duration=150,
        loop=0,
    )
    img_io.seek(0)
    return send_file(img_io, mimetype="image/gif")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    app.run(host="0.0.0.0", port=5051, debug=True)  # nosec

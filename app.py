import logging
from io import BytesIO
from pathlib import Path
from random import choice, randint, shuffle

from flask import Flask, send_file
from glitch_this import ImageGlitcher
from PIL import Image

glitcher = ImageGlitcher()

app = Flask(
    __name__,
)


def make_glitch(files, seed=None):
    files = files.split(" ")
    imgs = []
    for filepath in files:
        with Image.open(choice(["audiotarky_ident@2x.png", "skull.png"])) as logo_img:
            mult = randint(1, 10)
            resized = logo_img.copy().resize(
                (mult * logo_img.size[0], mult * logo_img.size[1])
            )
            resized.putalpha(int(0.75 * 255))
            imgs.extend(glitch_me(str(filepath), seed=seed))
            w, h = imgs[0].size
            logo_frames = imgs[0].copy()
            w = int((w - resized.size[0]) / 2)
            h = int((h - resized.size[1]) / 2)
            logo_frames.paste(resized, (w, h), resized)
            imgs.extend(glitch_me(logo_frames, frames=5, seed=seed))

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
    return img_io


def glitch_me(src_img, frames=23, seed=None):
    kwargs = {
        "cycle": True,
        "color_offset": True,
        "gif": True,
        "frames": frames,
        "glitch_change": 0.25,
        "scan_lines": choice([True, False]),
        "frames": frames,
    }
    if seed:
        kwargs["seed"] = seed

    return glitcher.glitch_image(src_img, 2, **kwargs)


@app.route("/favicon.ico")
def favicon():
    return "favicon"


def files_to_glitch(seed):
    files = list(
        Path("../audiotarky-hugo/content/").glob(
            "artists/anechoics/patterns-of-hope-destruction/**/*.png"
        )
    )
    files.sort()
    files = " ".join([f.as_posix() for f in files])
    return make_glitch(files, seed)


@app.route("/<nft>")
@app.route("/")
def serve(nft=None):
    seed = None
    img_io = None
    if nft:
        seed = int(nft[-16:-8], 16) / int(nft[-8:], 16)
        if Path(f"{nft}.gif").exists():
            return send_file(f"{nft}.gif", mimetype="image/gif")
    if not img_io:
        img_io = files_to_glitch(seed)
        if nft:
            with open(f"{nft}.gif", "wb") as outfile:
                outfile.write(img_io.getbuffer())
    img_io.seek(0)
    return send_file(img_io, mimetype="image/gif")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    app.run(host="0.0.0.0", port=5051, debug=True)  # nosec

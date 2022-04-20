import logging
from io import BytesIO
from pathlib import Path
from random import choice, randint, shuffle, sample
import math
from flask import Flask, send_file
from glitch_this import ImageGlitcher
from PIL import Image

glitcher = ImageGlitcher()

app = Flask(
    __name__,
)


def tile_images(filelist, n_tiles, img_size, seed):
    output = Image.new("RGB", img_size)
    size = int(math.sqrt(n_tiles))
    new_w = int(img_size[0] / size)
    new_h = int(img_size[1] / size)

    o = 0
    for c, i in enumerate(sample(filelist * n_tiles, n_tiles)):
        tile = Image.open(i).resize((new_w, new_h))
        r = o
        if c - (size - 2) > (o * size):
            o += 1

        output.paste(tile, ((c % size) * new_w, r * new_h))
    output.save(f"output_{c}.png")
    return glitch_me(output, seed=seed)


def make_glitch(files, seed=None):
    imgs = []
    for filepath in files:
        with Image.open(choice(["audiotarky_ident@2x.png", "skull.png"])) as logo_img:
            imgs.extend(glitch_me(str(filepath), seed=seed))

            mult = randint(1, 10)
            resized = logo_img.copy().resize(
                (mult * logo_img.size[0], mult * logo_img.size[1])
            )

            w = int((imgs[0].size[0] - resized.size[0]) / 2)
            h = int((imgs[0].size[1] - resized.size[1]) / 2)

            logo_frames = Image.new("RGBA", imgs[0].size)
            logo_frames.paste(resized, (w, h), resized.convert("RGBA"))
            logo_frames.putalpha(int(0.5 * 255))

            final = Image.new("RGBA", imgs[0].size)
            final = Image.alpha_composite(final, imgs[0])
            final = Image.alpha_composite(final, logo_frames)
            final.save("final.png")

            imgs.extend(glitch_me(final, frames=5, seed=seed))

    for n_tiles in [4, 9, 16]:
        imgs.extend(tile_images(files, n_tiles, imgs[0].size, seed))

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
    return make_glitch([f.as_posix() for f in files], seed)


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

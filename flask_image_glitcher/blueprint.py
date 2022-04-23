from flask import Blueprint, request, send_file, current_app
from io import BytesIO
from pathlib import Path
from random import choice, randint, shuffle, sample
import math
from glitch_this import ImageGlitcher
from PIL import Image
import logging

glitcher = ImageGlitcher()
app = Blueprint("glitcher", __name__)

glitch_logger = logging.getLogger("glitch")
glitch_logger.setLevel(logging.INFO)


def tile_images(filelist, n_tiles, img_size, seed):
    glitch_logger.debug(f"tile_images: {filelist}, {n_tiles}, {img_size}, {seed}")
    output = Image.new("RGB", img_size)
    size = int(math.sqrt(n_tiles))
    new_w = int(img_size[0] / size)
    new_h = int(img_size[1] / size)

    o = 0
    try:
        for c, i in enumerate(sample(filelist * n_tiles, n_tiles)):
            tile = Image.open(i).resize((new_w, new_h))
            r = o
            if c - (size - 2) > (o * size):
                o += 1
            output.paste(tile, ((c % size) * new_w, r * new_h))
        return glitch_me(output, seed=seed, size=img_size)
    except:
        glitch_logger.warning(
            f"tile_images: {filelist}, {len(filelist)}, {n_tiles}, {img_size}, {seed}"
        )
        return []


def image_mixin(seed, original, overlay_filename, size=None):
    glitch_logger.debug(f"image_mixin: {seed}, {original}, {overlay_filename}, {size}")
    if not size:
        size = original.size
    original = original.convert("RGBA")
    with Image.open(overlay_filename) as overlay:

        mult = randint(1, 10)
        resized = overlay.copy().resize(
            (mult * overlay.size[0], mult * overlay.size[1])
        )

        w = int((original.size[0] - resized.size[0]) / 2)
        h = int((original.size[1] - resized.size[1]) / 2)

        logo_frames = Image.new("RGBA", original.size)
        logo_frames.paste(resized, (w, h), resized.convert("RGBA"))
        logo_frames.putalpha(int(0.5 * 255))

        final = Image.new("RGBA", original.size)
        final = Image.alpha_composite(final, original)
        final = Image.alpha_composite(final, logo_frames)

        return glitch_me(final, frames=5, seed=seed, size=size)


def make_glitch(files, seed=None, size=None):
    glitch_logger.debug(f"make_glitch: {files}, {seed}, {size}")
    imgs = []
    for filepath in files:
        if size:
            glitch_logger.info(f"setting size to {size} from arg")
        elif len(imgs) > 0:
            size = imgs[0].size
            glitch_logger.info(f"setting size to {size} from image list")
        else:
            i = Image.open(str(filepath))
            size = i.size
            glitch_logger.info(f"setting size to {size} from first image")

        imgs.extend(glitch_me(str(filepath), seed=seed, size=size))

        overlays = current_app.config.get("overlay_images", False)
        if overlays:
            imgs.extend(image_mixin(seed, imgs[0], choice(overlays), size=size))
    for n_tiles in [4, 9, 16]:
        imgs.extend(tile_images(files, n_tiles, size, seed))

    sublist = imgs[1:]
    shuffle(sublist)

    img_io = BytesIO()
    imgs[0].save(
        img_io,
        "gif",
        save_all=True,
        quality=50,
        append_images=sublist,
        duration=150,
        loop=0,
    )
    return img_io


def glitch_me(src_img, frames=None, seed=None, size=None):
    glitch_logger.debug(f"glitch_me: {src_img}, {frames}, {seed}, {size}")
    cfg_frames = current_app.config.get("number_glitch_frames", 23)
    if not frames or frames > cfg_frames:
        frames = cfg_frames

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
    if size:
        if isinstance(src_img, str):
            src_img = Image.open(src_img)
        src_img = src_img.resize(size)
    return glitcher.glitch_image(src_img, 2, **kwargs)


def files_to_glitch():
    files = list(current_app.config["to_glitch_glob"])
    files.sort()
    return [f.as_posix() for f in files]


def get_requested_size(request):
    requested_size = [
        request.args.get("width", False),
        request.args.get("height", False),
    ]
    config_size = current_app.config.get("glitch_dimensions", None)
    glitch_logger.info(f"get_requested_size: {requested_size}")
    if requested_size == [False, False]:
        glitch_logger.info(
            f"get_requested_size: No width/height from query so return the config_size: {config_size}"
        )
        return config_size
    else:
        try:
            requested_size[0] = int(requested_size[0])
        except ValueError:
            glitch_logger.warning("couldn't cast width")
            if config_size:
                requested_size[0] = config_size[0]
            else:
                # Not given an int-castable, and no config, so bail
                return None
        # If a height isn't set, make the image square
        if requested_size[0] and not requested_size[1]:
            glitch_logger.warning(
                f"couldn't get height, setting to width {requested_size[0]}"
            )
            requested_size[1] = requested_size[0]
        else:
            try:
                requested_size[1] = int(requested_size[1])
            except ValueError:
                glitch_logger.warning("couldn't cast height")
                if config_size:
                    requested_size[1] = config_size[1]
                else:
                    requested_size[1] = requested_size[0]
        # Limit the max size to the configuration
        if config_size:
            if requested_size[0] > config_size[0]:
                glitch_logger.warning("requested width larger than config")
                requested_size[0] = config_size[0]
            if requested_size[1] > config_size[1]:
                glitch_logger.warning("requested height larger than config")
                requested_size[1] = config_size[1]
        requested_size = tuple(requested_size)

    return requested_size


@app.route("/<nft>")
@app.route("/")
def serve(nft=None):
    if current_app.config.get("glitch_log_level", None):
        glitch_logger.setLevel(current_app.config.get("glitch_log_level", logging.INFO))
    seed = None
    img_io = None
    requested_size = get_requested_size(request)
    if nft:
        seed = int(nft[-16:-8], 16) / int(nft[-8:], 16)
        if Path(f"{nft}.gif").exists():
            return send_file(f"{nft}.gif", mimetype="image/gif")
    if not img_io:
        img_io = make_glitch(files_to_glitch(), seed, size=requested_size)
        if nft and current_app.config.get("cache_glitch", False):
            with open(f"{nft}.gif", "wb") as outfile:
                outfile.write(img_io.getbuffer())
    img_io.seek(0)
    return send_file(img_io, mimetype="image/gif")

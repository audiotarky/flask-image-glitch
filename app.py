import logging
from flask import Flask
from flask_image_glitcher.blueprint import app as glitcher
from pathlib import Path

app = Flask(__name__)

app.config["to_glitch_glob"] = Path("../audiotarky-hugo/content/").glob(
    "artists/anechoics/patterns-of-hope-destruction/**/*.png"
)
app.config["overlay_images"] = ["audiotarky_ident@2x.png", "skull.png"]
app.config["default_glitch_frames"] = 10
app.config["cache_glitch"] = True
app.config["glitch_log_level"] = logging.WARNING
# app.config["glitch_dimensions"] = (400, 400)
app.register_blueprint(glitcher)

pil_logger = logging.getLogger("PIL")
pil_logger.setLevel(logging.INFO)


@app.route("/favicon.ico")
def favicon():
    # Done to clean up the Flask log
    return "favicon"


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    app.run(host="0.0.0.0", port=5051, debug=True)  # nosec

# flask-image-glitch
Simple image glitching webserver, implemented as a flask Blueprint.

The blueprint presents a single endpoint (`serve`) which can be accessed either at the root url or with an [XLS20](https://github.com/XRPLF/XRPL-Standards/discussions/46) `NFTokenID`. If accessed at the root URL the glitch image will be generated uniquely each time. If accessed with a `NFTokenID` the glitched image will be deterministic.

```
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

The example app (`app.py`) pulls the blueprint in and configures it. The server has the following configurables that can be set:

`app.config["to_glitch_glob"]` is a list of files, or `pathlib` `glob` that you want to use as your sources for glitching. This will be cast from the `glob` generator to a list if the generator is presented. The first file in the list will set the size of the final image, unless `app.config["glitch_dimensions"]` is set. This configuration is **required**.

`app.config["cache_glitch"]` is an optional parameter which tells the server to write to disk any glitches accessed via an NFT. Since these images are the same each time, and creating them is time consuming, its probably worth caching for a period. Be warned, though, the resulting gif's can be quite large.

`app.config["glitch_dimensions"]` is a 2-tuple of size (width, height) you want applied to the glitched image. If not set the size of the first image is used for all subsequent images (which may cause cropping, stretching or other unintended consequences). But that's sort of the point. If set, this will set an upper limit for the image size when setting that via the `?width=<int>&height=<int>` query string.

`app.config["number_glitch_frames"]` is an optional parameter which tells the server how many frames of glitchy goodness to generate. This deafults to 23, but you may want to increase or decrease depending on your purposes, number of images invovled etc.

`app.config["overlay_images"]` is an optional configuration variable which lets you mix in other images into your glitching. These will be randomly resized, superimposed (at 50% opacity) on glitched images, and then glitched again. This is fun for making flashing images, and works best if the overlays are images with transparent areas.

`app.config["glitch_log_level"]` sets the log level of the blueprint, defaults to `INFO`.

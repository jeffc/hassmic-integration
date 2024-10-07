# HassMic (The Integration)

This is the HassMic integration, a Home assistant integration designed to
enable Android devices acting as Home Assistant voice assistant satellites.

It is meant to pair with the [HassMic App](http://github.com/jeffc/hassmic-app).

## Usage

Install this integration in Home Assistant, either by using HACS (preferred) or
by cloning the repository into your `custom_components/` directory as `hassmic`.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jeffc&repository=hassmic-integration&category=integration)

Once installed, you have two options. If your Home Assistant has Zeroconf
discovery enabled (it does unless you've turned it off explicitly or your
network configuration is whacky), devices running the HassMic app will
automatically be discovered.

If you don't have Zeroconf enabled or it isn't working, you can add devices by
IP address (or hostname). The port should remain set to the default, `11700`.

## Known Bugs (the good ones)

It is currently in active development and probably has lots of bugs. Some
highlights:

- Deleting or disabling instances usually requires restarting Home Assistant
- There is currently **NO configurability**. HassMic uses your default assist
  pipeline, default wakework, and default text-to-speech engine, and outputs the
  result through the HassMic app. All of this will be improving soon!
- The integration can usually handle satellite device restarts or app crashes,
  but not always. You may need to reload the device or restart home assistant if
  it gets stuck.

Please report all other bugs using the issue tracker!


## License

[![CC BY-SA 4.0][cc-by-sa-shield]][cc-by-sa]

This work is licensed under a
[Creative Commons Attribution-ShareAlike 4.0 International License][cc-by-sa].

[![CC BY-SA 4.0][cc-by-sa-image]][cc-by-sa]

[cc-by-sa]: http://creativecommons.org/licenses/by-sa/4.0/
[cc-by-sa-image]: https://licensebuttons.net/l/by-sa/4.0/88x31.png
[cc-by-sa-shield]: https://img.shields.io/badge/License-CC%20BY--SA%204.0-lightgrey.svg

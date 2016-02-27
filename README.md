nemubot
=======

An extremely modulable IRC bot, built around XML configuration files!


Requirements
------------

*nemubot* requires at least Python 3.3 to work.

Some modules (like `cve`, `nextstop` or `laposte`) require the
[BeautifulSoup module](http://www.crummy.com/software/BeautifulSoup/),
but the core and framework has no dependency.


Installation
------------

Use the `setup.py` file: `python setup.py install`.

### VirtualEnv setup

The easiest way to do this is through a virtualenv:

```sh
virtualenv venv
. venv/bin/activate
python setup.py install
```

### Create a new configuration file

There is a sample configuration file, called `bot_sample.xml`. You can
create your own configuration file from it.


Usage
-----

Don't forget to activate your virtualenv in further terminals, if you
use it.

To launch the bot, run:

```sh
nemubot bot.xml
```

Where `bot.xml` is your configuration file.

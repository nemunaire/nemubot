#!/usr/bin/env python3

import os
import re
from glob import glob
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

with open(os.path.join(os.path.dirname(__file__),
                      'nemubot',
                       '__init__.py')) as f:
        version = re.search("__version__ = '([^']+)'", f.read()).group(1)

with open('requirements.txt', 'r') as f:
    requires = [x.strip() for x in f if x.strip()]

#with open('test-requirements.txt', 'r') as f:
#    test_requires = [x.strip() for x in f if x.strip()]

dirs = os.listdir("./modules/")
data_files = []
for i in dirs:
    data_files.append(("nemubot/modules", glob('./modules/' + i + '/*')))

setup(
    name = "nemubot",
    version = version,
    description = "An extremely modulable IRC bot, built around XML configuration files!",
    long_description = open('README.md').read(),

    author = 'nemunaire',
    author_email = 'nemunaire@nemunai.re',

    url = 'https://github.com/nemunaire/nemubot',
    license = 'AGPLv3',

    classifiers = [
        'Development Status :: 2 - Pre-Alpha',

        'Environment :: Console',

        'Topic :: Communications :: Chat :: Internet Relay Chat',
        'Intended Audience :: Information Technology',

        'License :: OSI Approved :: GNU Affero General Public License v3',

        'Operating System :: POSIX',

        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],

    keywords = 'bot irc',

    provides = ['nemubot'],

    install_requires = requires,

    packages=[
        'nemubot',
        'nemubot.config',
        'nemubot.datastore',
        'nemubot.event',
        'nemubot.exception',
        'nemubot.hooks',
        'nemubot.hooks.keywords',
        'nemubot.message',
        'nemubot.message.printer',
        'nemubot.module',
        'nemubot.server',
        'nemubot.server.message',
        'nemubot.tools',
        'nemubot.tools.xmlparser',
    ],

    scripts=[
        'bin/nemubot',
#        'bin/module_tester',
    ],

#    data_files=data_files,
)

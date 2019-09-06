# maruchamp
![GitHub](https://img.shields.io/github/license/ericmburgess/maruchamp)
![GitHub code size in bytes](https://img.shields.io/github/languages/code-size/ericmburgess/maruchamp)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
![GitHub issues](https://img.shields.io/github/issues/ericmburgess/maruchamp)
![GitHub last commit](https://img.shields.io/github/last-commit/ericmburgess/maruchamp)

MaruChamp Rocket League bot by Ramen and Vitamins

Language: Python

I've rewritten about 90% of Maru's code. This version is close to what I submitted for Season 1 weekend 1 (but a little worse because I'm in the middle of tweaking stuff). It uses a "utility AI" to choose what to do from moment to moment. 

My intent is that the `ramen` and `vitamins` packages should be useful for anyone else who wants to make a Python bot. Everything in there is general-purpose, and all the MaruChamp-specific stuff is under `maruchamp`. I'm working on documentation for `ramen` and `vitamins` and I'm planning to make a tutorial for using them to create a basic utility AI bot.

## A few notes for anyone checking out the code

* `vitamins.match.match.Match` (what a name) is a singleton (implemented as a class) which represents the current match.
All the other match information is accessed through it, so any file that needs access to game information just needs
to have `from vitamins.match.match import Match` at the top. I'm not yet settled on whether this is the best way to
do things, but it works.
* The guts of MaruChamp's brains are contained in the `Task` subclasses defined in `maruchamp_main.py`. A few things are
split out into separate packages, but it's really haphazard. Most of it is just in that one file.
* That's a lot of dot products everywhere, huh? Dot product is so good.

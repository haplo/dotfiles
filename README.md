Fidel's dotfiles
================

This is my personal set up of configuration files.

I use Arch Linux in desktop and Debian GNU/Linux in servers so they are particularly tailored for these OSes.
My main shell is [fish](https://fishshell.com/), it's set as default.

Feel free to fork the repository, adapt it to your needs, or just to
copy whatever you like.
**Use at your own risk!**

Any ideas or suggestions? I would love to
[hear about them](https://github.com/haplo/dotfiles/issues),
I'm always up for improving my setup.

Dependencies
------------

- [yadm](https://yadm.io/)
- [fish shell](https://fishshell.com/)
- [fzf](https://github.com/junegunn/fzf)
- [bat](https://github.com/sharkdp/bat)
- [exa](https://github.com/ogham/exa) or [eza](https://github.com/eza-community/eza)
- [fd](https://github.com/sharkdp/fd)
- [delta](https://github.com/dandavison/delta)

Installation
------------

First [install yadm](https://yadm.io/docs/install).
It's available in Arch Linux, Debian and many other distros.
And if not packaged, in the end it's just a single shell script, you can just download it and put it in `PATH`.
This simplicity is one reason why I chose *yadm* over other tools.

With *yadm* in hand use this to clone this repository, install the files into `$HOME` and run the [bootstrap script](.config/yadm/bootstrap):

    $ yadm clone --bootstrap -f https://github.com/haplo/dotfiles.git

Updating
--------

    $ yadm pull

Fish plugins
------------

I try to minimize the amount of plugins I use, but the ones I do use I decided to vendor, i.e. include in full in this repository.
This allows me to control the source code precisely, review updates manually and not to depend on an unverified external download whenever I install the dotfiles.

The vendored plugins are in [.config/fish/vendor/](.config/fish/vendor/).

To update the vendored plugins to their latest versions, in a *fish* shell:

    $ update_fish_vendored_plugins

Disabling fzf
-------------

*fzf* can be slow in some systems, to disable its *fish* integration set a universal
variable:

```fish
set -U disable_fzf true
```

Then running `yadm bootstrap` will not install the *fzf-fish* plugin.

Thanks and inspiration
----------------------

* The original version of this repository was based on [Mathias Bynens'
  dotfiles](https://github.com/mathiasbynens/dotfiles).
  I also copied many a useful thing from his files, so thanks to him and to people on his thanks list.

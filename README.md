Fidel's dotfiles
================

This is my personal set up of configuration files.
I use Debian and Kubuntu GNU/Linux so they are particularly tailored for these OSes.

Feel free to fork the project and adapt it to your needs, or just to
copy whatever you like. **Use at your own risk!**

Any ideas or suggestions? I would love to
[hear about them](https://github.com/haplo/dotfiles/issues),
I'm always up for improving my setup.

Dependencies
------------

- [rsync](https://rsync.samba.org/)
- [fish shell](https://fishshell.com/)
- [diff-so-fancy](https://github.com/so-fancy/diff-so-fancy)
- [fzf](https://github.com/junegunn/fzf)
- [bat](https://github.com/sharkdp/bat)
- [exa](https://github.com/ogham/exa) or [eza](https://github.com/eza-community/eza)
- [fd](https://github.com/sharkdp/fd)

Installation with git
---------------------

⚠ _WARNING_: this will potentially overwrite files in your home directory!

    $ git clone https://github.com/haplo/dotfiles.git
    $ dotfiles/init_dotfiles.sh

*init_dotfiles.sh* depends on *rsync*.

Installation without git
------------------------

⚠ _WARNING_: this will potentially overwrite files in your home directory!

This will download and unpack the latest version of the dotfiles,
**overwriting existing files in the home directory**!

    $ cd; curl -#L https://github.com/haplo/dotfiles/tarball/master | tar -xzv --strip-components 1 --exclude={README.md,init_dotfiles.sh,LICENSE}

Thanks and inspiration
----------------------

* I based the repo and the README on
  [Mathias Bynens' dotfiles](https://github.com/mathiasbynens/dotfiles),
  and I also copied many a useful thing from his files, so thanks to
  him and to people on his thanks list.

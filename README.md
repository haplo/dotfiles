Fidel's dotfiles
================

This is my personal set up of configuration files. I use Debian
GNU/Linux so they are particularly tailored for this OS.

Feel free to fork the project and adapt it to your needs, or just to
copy whatever you like. **Use at your own risk!**

Any ideas or suggestions? I would love to
[hear about them](https://github.com/haplo/dotfiles/issues),
I'm always up for improving my setup.

Installation with git
---------------------

    $ cd; git clone https://github.com/haplo/dotfiles.git
    $ source dotfiles/init_dotfiles.sh

*init_dotfiles.sh* currently depends on *rsync*.

Installation without git
------------------------

This will download and unpack the latest version of the dotfiles,
**overwriting existing files in the home directory**!

    $ cd; curl -#L https://github.com/haplo/dotfiles/tarball/master | tar -xzv --strip-components 1 --exclude={README.md,init_dotfiles.sh,LICENSE}

Thanks and inspiration
----------------------

* I based the repo and the README on
  [Mathias Bynens' dotfiles](https://github.com/mathiasbynens/dotfiles),
  and I also copied many a useful thing from his files, so thanks to
  him and to people on his thanks list.

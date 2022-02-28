# PREREQUISITES

Before building	the hope-src repository, some packages need to be updated and/or installed.


## Verify packages

1. Make sure git is at least version 2.17.1 (tested), or else cloning qemu submodules will fail; the latest version of git is available at git://git.kernel.org/pub/scm/git/git.git.

2. Ensure that the following packages are installed:
   - expat-devel
   - devtoolset-7
   - llvm-toolset-9.0
   - snap
   - cmake3
   - yaml-cpp-devel
   - libyaml-devel
   - gflags-devel
   - pixman
   - glibc-devel.i686
   - libgcc.i686
   - python3-setuptools
   - python-virtualenv
   - mpfr-devel
   - gmp-devel
   - elfutils-libelf-devel
   - boost-devel
   - boost-program-options
   - glib2-devel

One may use `yum list packageName` to check if packageName is installed. If the package is not installed, one may use the following to install the desired package: `yum install packageName`.

## Acquire packages

1. Install device-tree-compiler via `snap`:
   1. start the snap communication socket with "sudo systemctl enable --now snapd.socket", then log out or restart
   2. `snap install device-tree-compiler`

2. Install `expect` via `pip3` to ensure version is 4.0 or higher

3. Install autotools from source, all into the same location:
   - https://ftp.gnu.org/gnu/automake/automake-1.16.4.tar.gz
   - https://ftp.gnu.org/gnu/libtool/libtool-2.4.6.tar.gz
   - https://pkgconfig.freedesktop.org/releases/pkg-config-0.29.2.tar.gz
   - http://git.sv.gnu.org/r/autoconf.git

There are no special requirements when compiling the above packages, so the following sequence should work:
```
wget packageName
cd packageName
./configure --prefix=desiredDir
make && make install
export PATH=desiredDir/bin:$PATH
```

4. Install ninja from source from https://github.com/ninja-build/ninja (RHEL version is too old)

5. Install stack from https://get.haskellstack.org/

#### IMPORTANT

`stack` uses /tmp and if you do not have exec privileges to it (or to the directories created there) either make sure you do have such privileges, or make a local temp folder and set TMPDIR to it:
```
mktemp -p tempXXXX
export TMPDIR=..... (see above for the name of the created directory)
```

6. Install ncurses-6.3 from https://invisible-mirror.net/archives/ncurses/ncurses-6.3.tar.gz. We have not tested with newer versions of ncurses.
```
wget https://invisible-mirror.net/archives/ncurses/ncurses-6.3.tar.gz
tar zxvf ncurses-6.3.tar.gz
cd ncurses-6.3
./configure --with-shared --with-cxx-binding --with-cxx-shared --with-versioned-syms --with-termlib
make && make install
```

7. Install the following python packages (via pip3):
   - distutils
   - pytest
   - pytest-xdist
   - pytest-timeout
   - pyelftools
   - psutil 

# BUILDING

If building on a Draper machine, or any machine where FTP is restricted, change base_url in riscv-gnu-toolchain/riscv-gcc/contrib/download_prerequisites so that the ftp link is https instead.

1. Enable devtoolset-7: `scl enable devtoolset-7 llvm-toolset-9.0 bash`. Note that newer versions of `devtoolset` do not work and newer versions of `llvm-toolset` are not tested.

2. Set up the `ISP_PREFIX` variable: `export ISP_PREFIX=/path/to/desired/install/location`.

3. Ensure autotools, $ISP_PREFIX/bin (even though it doesn't exist yet), and ninja are on `$PATH`.

4. make sure "cmake" command uses RHEL's cmake3 binary. You could do this as follows:
```
ln -s /bin/cmake3 $HOME/.local/bin
export PATH=$HOME/.local/bin:$PATH
```

5. Ensure that the libusb-1.0 library is found (it should be installed by default) by updating the `PKG_CONFIG_PATH` variable: `export PKG_CONFIG_PATH=$PKG_CONFIG_PATH:/usr/lib64/pkgconfig`.

6. Update `LD_LIBRARY_PATH`: `export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/opt/rh/llvm-toolset-9.0/root/usr/lib64`.

7. In hope-src, run `make`.

## Building as Root

To install the tool set for all users, running `make` as root may be necessary. To do that, use the following steps:

1. Ensure there is no `.stack` directory in `$HOME` unless it is owned by root, or `stack` will refuse to build anything.

2. Run `make` using `/bin/sudo -E env PATH=$PATH TMPDIR=$TMPDIR LD_LIBRARY_PATH=$LD_LIBRARY_PATH make`.
   - Explicitly using `/bin/sudo` is necessary as `devtoolset-7` includes a version of `sudo` that doesn't have the `-E` flag for passing environment variables.
   - `env PATH=$PATH TMPDIR=$TMPDIR LD_LIBRARY_PATH=$LD_LIBRARY_PATH` is needed to ensure those variables aren't overwritten when switching to root.
   - `TMPDIR=$TMPDIR` is needed if a new temp directory was created.

3. After building, ensure `$ISP_PREFIX` and subdirectories and binaries in `$ISP_PREFIX`/bin and `$ISP_PREFIX/venv/bin` have read and execute privileges for all users and other files have read permissions for all users.

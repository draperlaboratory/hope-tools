# PREREQUISITES

Before building	the hope-src repository, some packages need to be updated and/or installed.


## Verify packages

1. Make sure git is at least version 2.17.1 (tested), or else cloning qemu submodules will fail;
The latest version of git is available at git://git.kernel.org/pub/scm/git/git.git


2. Ensure that the following packages are installed.

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
 = gmp-devel
 - elfutils-libelf-devel
 - boost-devel
 - boost-program-options
 - glib2-devel

One may use

```
yum list packageName
```
to check if packageName is installed. If the package is not installed, one may use the following to install
the desired package:

```
yum install packageName
```


## Acquire packages

1. Install device-tree-compiler via snap:
 - start the snap communication socket with "sudo systemctl enable --now snapd.socket", then log out or restart
 - snap install device-tree-compiler

2. Install pexpect via pip3 to ensure version is 4.0 or higher

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

stack uses /tmp and if you do not have exec privileges to it (or to the directories created there)
either make sure you do have such privileges, or make a local temp folder and set TMPDIR to it

```
mktemp -p tempXXXX
export TMPDIR=..... (see above for the name of the created directory)
```

6. Install ncurses-6.3 from https://invisible-mirror.net/archives/ncurses/ncurses-6.3.tar.gz
We have not tested with newer versions of ncurses.

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

## Additional steps for Draper users

The following additional steps were required by users working on Draper machines. They might
or might not be required by users using machines that have less restrictive set-ups.

Note that the build requires over 8GB of memory

1. Change base_url in riscv-gnu-toolchain/riscv-gcc/contrib/download_prerequisites so that the ftp link is https instead
2. Enable devtoolset-7

```
scl enable devtoolset-7 llvm-toolset-9.0 bash
```
3. Set up the ISP_PREFIX variable:

```
export ISP_PREFIX=/path/to/desired/install/location
```

4. Ensure autotools, $ISP_PREFIX/bin (even though it doesn't exist yet), and ninja are on $PATH

5. make sure "cmake" command uses RHEL's cmake3 binary.
You could do this as follows:

```
ln -s /bin/cmake3 $HOME/.local/bin
export PATH=$HOME/.local/bin:$PATH
```
6. Ensure that the libusb-1.0 library is found (it should be installed by default)
by updating the PKG_CONFIG_PATH variable

```
export PKG_CONFIG_PATH=$PKG_CONFIG_PATH:/usr/lib64/pkgconfig
```

7. Update the LD_LIBRARY_PATH

```
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/opt/rh/llvm-toolset-9.0/root/usr/lib64
```

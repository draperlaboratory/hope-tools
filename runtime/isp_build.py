import functools
import itertools
import operator
import subprocess
import os
import shutil
import time
import glob
import errno

from isp_utils import *

# backend helper to compile a C program to be run on an ISP processor

# possible module outcomes
class retVals:
    UNKNOWN_FAIL = "No binary produced"
    NO_RUNTIME   = "Target runtime not found"
    NO_TEST      = "Target source not found"
    SUCCESS      = "Target built successfully"

# -- MAIN MODULE FUNCTIONALITY

# arguments:
#  src_dir - Directory containing the C code to be run. The "main" function
#    of the C code should be named "isp_main" so that it can be found by the
#    runtime/OS running on the processor.
#  template_dir - Directory containing ISP provided generic runtime code and
#    build tools.
#  runtime - Currently supported: frtos, hifive (bare metal)
#  out_dir - Location of output directory. Structure will look as follows:
#    out_dir
#      Makefile
#      (srcs)
#      build
#        binary
#        Makefile
#  copy_src - default = True. Generate a `srcs` directory in out_dir and copy
#    the source from src_dir before running.

#  TODO: eliminate this assumption of the runtime build process
#  NOTE: The runtime build process assumes that the source is located in
#    build/../srcs, so copy_src should remain true unless care is taken to
#    satisfy that assumption elsewhere.

def do_build(src_dir,
             template_dir,
             runtime,
             out_dir,
             copy_src = True):

    if not os.path.isdir(src_dir):
        return retVals.NO_TEST

    # output directory
    doMkDir(out_dir)

    if copy_src:
        src_copy = os.path.join(out_dir, "srcs")
        doMkDir(src_copy)
        for f in os.listdir(src_dir):
            shutil.copy(os.path.join(src_dir, f), src_copy)
        src_dir = src_copy

    # make policy-common test sources & tools
    add_runtime(runtime, out_dir, template_dir, src_dir)

    # make build dir for test
    make_build_dir(out_dir, template_dir, runtime)

    # do the build
    subprocess.Popen(["CDEFINES=-DISP_RUNTIME", "make", "-f", "Makefile.ispbuild"], stdout=open(os.path.join(out_dir, "build/build.log"), "w+"), cwd=out_dir).wait()

    # check that build succeeded
    if not os.path.isfile(os.path.join(out_dir, "build", "main")):
        return retVals.UNKNOWN_FAIL

    return retVals.SUCCESS


def make_build_dir(dp, template_dir, runtime):

    # build directory is 1 per test
    build_dir = os.path.join(dp, "build")
    if os.path.isdir(build_dir):
        return

    # make test/build
    doMkDir(build_dir)

    # provide test/build makefile
    if "frtos" in runtime:
        shutil.copy(os.path.join(template_dir, "frtos.cmake"), os.path.join(build_dir, "CMakeLists.txt"))
    elif "hifive" in runtime:
        shutil.copy(os.path.join(template_dir, "hifive.makefile"), os.path.join(build_dir, "Makefile"))
        shutil.copytree(os.getenv("ISP_PREFIX")+"/hifive_bsp", os.path.join(build_dir, "bsp"))
 

def add_runtime(runtime, dp, template_dir, src_dir):

    shutil.copy(os.path.join(template_dir, "test.h"), os.path.join(src_dir, "test.h"))

    # runtime specific code
    if "frtos" in runtime:
        shutil.copy(os.path.join(template_dir, "frtos-mem.h"), os.path.join(src_dir, "mem.h"))
        shutil.copy(os.path.join(template_dir, "frtos.c"), os.path.join(src_dir, "frtos.c"))
        shutil.copyfile(os.path.join(template_dir, "test.cmakefile"), os.path.join(dp, "Makefile.ispbuild"))
    elif "hifive" in runtime:
        shutil.copy(os.path.join(template_dir, "hifive-mem.h"), os.path.join(src_dir, "mem.h"))
        shutil.copy(os.path.join(template_dir, "hifive.c"), os.path.join(src_dir, "hifive.c"))
        shutil.copyfile(os.path.join(template_dir, "test.makefile"), os.path.join(dp, "Makefile.ispbuild"))
    else:
        return isp.buildRetVals.NO_RUNTIME

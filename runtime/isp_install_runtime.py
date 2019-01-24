import os
import shutil
import isp_utils
import argparse

# possible module outcomes
class retVals:
    UNKNOWN_FAIL = "Target failed to build"
    NO_RUNTIME   = "Target runtime not found"
    NO_SOURCE    = "Target source not found"
    NO_TEMPLATE  = "Template directory not found"
    SUCCESS      = "Target built successfully"

# -- MAIN MODULE FUNCTIONALITY

# Arguments:
#  build_dir - path to the build directory. Must contain the user's Makefile
#  template_dir - path to ISP generic runtime code and template Makefiles
#  runtime - Currently supported: frtos, hifive (bare metal)

# User must have:
#  include isp-build.mk in Makefile
#  $(ISP_OBJECTS) and $(ISP_LIBS) linked with final target
#  $(ISP_INCLUDES) and $(ISP_LDFLAGS) passed to final target
#  $(ISP_DEPS) as a dependency to final target
#  $(ISP_CLEAN) removed in the clean target
#  main() renamed to isp_main()


def doInstall(build_dir, template_dir, runtime):
    if not os.path.isdir(build_dir):
        return retVals.NO_TEST

    if not os.path.isdir(template_dir):
        return retVals.NO_TEMPLATE

    runtime_dir = os.path.join(build_dir, "isp-runtime")

    isp_utils.removeIfExists(runtime_dir)
    isp_utils.doMkDir(runtime_dir)

    if "frtos" in runtime:
        frtos_dir = os.path.join(runtime_dir, "frtos")
        isp_utils.doMkDir(frtos_dir)
        shutil.copy(os.path.join(template_dir, "frtos-mem.h"),
                    os.path.join(runtime_dir, "mem.h"))
        shutil.copy(os.path.join(template_dir, "frtos.c"),
                    os.path.join(runtime_dir, "frtos.c"))
        shutil.copy(os.path.join(template_dir, "frtos.cmake"),
                    os.path.join(frtos_dir, "CMakeLists.txt"))
        shutil.copy(os.path.join(template_dir, "frtos.mk"),
                    os.path.join(build_dir, "isp-runtime.mk"))

    elif "hifive" in runtime:
        shutil.copy(os.path.join(template_dir, "hifive-mem.h"),
                    os.path.join(runtime_dir, "mem.h"))
        shutil.copy(os.path.join(template_dir, "hifive.c"),
                    os.path.join(runtime_dir, "hifive.c"))
        shutil.copy(os.path.join(template_dir, "hifive.mk"),
                    os.path.join(build_dir, "isp-runtime.mk"))
        shutil.copytree(os.path.join(os.getenv("ISP_PREFIX"), "hifive_bsp"),
                        os.path.join(runtime_dir, "bsp"))

    else:
        return retVals.NO_RUNTIME

    return retVals.SUCCESS


def main():
    parser = argparse.ArgumentParser(description='''
    Install ISP runtime into standalone C project
    ''')
    parser.add_argument("runtime", type=str, help='''
    Currently supported: frtos, hifive (bare metal) (default)
    ''')
    parser.add_argument("-b", "--build-dir", type=str, default=".", help='''
    Directory containing the Makefile for the main executable.
    Default is current working directory.
    ''')

    args = parser.parse_args()
    
    build_dir_full = os.path.abspath(args.build_dir)

    result = doInstall(build_dir_full,
                       isp_utils.getTemplatesDir(),
                       args.runtime)

    if result is not retVals.SUCCESS:
        print("Failed to build application: {}".format(result))


if __name__ == "__main__":
    main()

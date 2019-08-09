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
#  runtime - Currently supported: frtos, sel4, bare (bare metal), stock_frtos, stock_bare

# User must have:
#  include isp-build.mk in Makefile
#  $(ISP_OBJECTS) and $(ISP_LIBS) linked with final target
#  $(ISP_INCLUDES) and $(ISP_LDFLAGS) passed to final target
#  $(ISP_DEPS) as a dependency to final target
#  $(ISP_CLEAN) removed in the clean target
#  main() renamed to isp_main()

def getTemplatesDir():
    isp_prefix = isp_utils.getIspPrefix()
    return os.path.join(isp_prefix, "sources",
                                    "tools",
                                    "runtime",
                                    "templates")


def doInstall(build_dir, template_dir, runtime):
    if not os.path.isdir(build_dir):
        return retVals.NO_TEST

    if not os.path.isdir(template_dir):
        return retVals.NO_TEMPLATE

    runtime_dir = os.path.join(build_dir, "isp-runtime-{}".format(runtime))

    isp_utils.removeIfExists(runtime_dir)
    isp_utils.doMkDir(runtime_dir)

    shutil.copy(os.path.join(template_dir, "isp_utils.h"),
                os.path.join(runtime_dir, "isp_utils.h"))
    shutil.copy(os.path.join(template_dir, "mem.h"),
                os.path.join(runtime_dir, "mem.h"))

    if "frtos" == runtime:
        frtos_dir = os.path.join(runtime_dir, "frtos")
        isp_utils.doMkDir(frtos_dir)
        shutil.copy(os.path.join(template_dir, "frtos.mk"),
                    os.path.join(build_dir, "isp-runtime-frtos.mk"))

    elif "sel4" == runtime:
        sel4_dir = os.path.join(runtime_dir, "sel4")
        isp_utils.doMkDir(sel4_dir)
        shutil.copy(os.path.join(template_dir, "sel4.mk"),
                    os.path.join(build_dir, "isp-runtime-sel4.mk"))

    elif "bare" in runtime:
        shutil.copy(os.path.join(template_dir, "bare.c"),
                    os.path.join(runtime_dir, "bare.c"))
        shutil.copy(os.path.join(template_dir, "bare.mk"),
                    os.path.join(build_dir, "isp-runtime-bare.mk"))
        shutil.copytree(os.path.join(isp_utils.getIspPrefix(), "hifive_bsp"),
                        os.path.join(runtime_dir, "bsp"))

    elif "stock_frtos" == runtime:
        frtos_dir = os.path.join(runtime_dir, "stock_frtos")
        isp_utils.doMkDir(frtos_dir)
        shutil.copy(os.path.join(template_dir, "stock_frtos.mk"),
                    os.path.join(build_dir, "isp-runtime-stock_frtos.mk"))

    elif "stock_sel4" == runtime:
        sel4_dir = os.path.join(runtime_dir, "stock_sel4")
        isp_utils.doMkDir(sel4_dir)
        shutil.copy(os.path.join(template_dir, "stock_sel4.mk"),
                    os.path.join(build_dir, "isp-runtime-stock_sel4.mk"))

    elif "stock_bare" == runtime:
        shutil.copy(os.path.join(template_dir, "bare.c"),
                    os.path.join(runtime_dir, "bare.c"))
        shutil.copy(os.path.join(template_dir, "stock_bare.mk"),
                    os.path.join(build_dir, "isp-runtime-stock_bare.mk"))
        shutil.copytree(os.path.join(isp_utils.getIspPrefix(), "hifive_bsp"),
                        os.path.join(runtime_dir, "bsp"))

    else:
        return retVals.NO_RUNTIME

    return retVals.SUCCESS


def main():
    parser = argparse.ArgumentParser(description='''
    Install ISP runtime into standalone C project
    ''')
    parser.add_argument("runtime", type=str, help='''
    Currently supported: frtos, sel4, bare (bare metal) (default), stock_frtos, stock_bare
    ''')
    parser.add_argument("-b", "--build-dir", type=str, default=".", help='''
    Directory containing the Makefile for the main executable.
    Default is current working directory.
    ''')

    args = parser.parse_args()

    build_dir_full = os.path.abspath(args.build_dir)

    result = doInstall(build_dir_full,
                       getTemplatesDir(),
                       args.runtime)

    if result is not retVals.SUCCESS:
        print("Failed to build application: {}".format(result))


if __name__ == "__main__":
    main()

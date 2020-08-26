#! /usr/bin/python3

import os
import shutil
import isp_utils
import argparse
import logging

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
#  runtime - Currently supported: frtos, sel4, bare (bare metal),
#            stock_frtos, stock_sel4, stock_bare

# User must have:
#  include isp-build.mk in Makefile
#  $(ISP_OBJECTS) and $(ISP_LIBS) linked with final target
#  $(ISP_INCLUDES) and $(ISP_LDFLAGS) passed to final target
#  $(ISP_DEPS) as a dependency to final target
#  $(ISP_CLEAN) removed in the clean target
#  main() renamed to isp_main()

bare_bsp = {
    "qemu": "hifive_bsp",
    "vcu118": "vcu118_bsp"
}

sim_aliases = {
    "vcs": "vcu118"
}

def getTemplatesDir():
    isp_prefix = isp_utils.getIspPrefix()
    return os.path.join(isp_prefix, "sources",
                                    "tools",
                                    "runtime",
                                    "templates")


def sel4_setup_source(build_dir, template_dir):
    sel4_prefix_source_dir = os.path.join(isp_utils.getIspPrefix(), "hope-seL4-app-template")
    sel4_local_source_dir = os.path.join(build_dir, "hope-seL4-app-template")

    try:
        shutil.copytree(sel4_prefix_source_dir, sel4_local_source_dir)
    except OSError as e:
        logging.warn("WARNING - seL4 copy failed with message: {}".format(e))


def doInstall(build_dir, template_dir, runtime, sim, stock):
    if not os.path.isdir(build_dir):
        return retVals.NO_TEST

    if not os.path.isdir(template_dir):
        return retVals.NO_TEMPLATE

    runtime_dir = os.path.join(build_dir, "isp-runtime-{}".format(runtime))

    isp_utils.removeIfExists(runtime_dir)
    isp_utils.doMkDir(runtime_dir)

    shutil.copy(os.path.join(template_dir, "isp_utils.h"),
                os.path.join(runtime_dir, "isp_utils.h"))

    runtime_main_c = os.path.join(template_dir, (runtime + "_main.c"))   
    sim_utils_c = os.path.join(template_dir, sim, "isp_utils.c")
    
    makefile_path = os.path.join(template_dir, sim)
    if stock:
        makefile_path = os.path.join(makefile_path, "stock")

    makefile = os.path.join(makefile_path, (runtime + ".mk"))
    try:
        shutil.copy(runtime_main_c, runtime_dir)
        shutil.copy(sim_utils_c, runtime_dir)
        shutil.copy(makefile, os.path.join(build_dir, ("isp-runtime-" + runtime + ".mk")))

        if runtime in ["bare", "vm"]:
            shutil.copytree(os.path.join(isp_utils.getIspPrefix(), bare_bsp[sim]),
                            os.path.join(runtime_dir, "bsp"))

        if "sel4" == runtime:
            sel4_setup_source(build_dir, template_dir)
            sel4_dir = os.path.join(runtime_dir, "sel4")
            if stock:
                sel4_dir = os.path.join(runtime_dir, "stock_sel4")
            isp_utils.doMkDir(sel4_dir)
    except:
        logging.error("Runtime {} is incompatible with sim {}".format(runtime, sim))
        return retVals.NO_RUNTIME

    return retVals.SUCCESS


def main():
    parser = argparse.ArgumentParser(description='''
    Install ISP runtime into standalone C project
    ''')
    parser.add_argument("runtime", type=str, help='''
    Currently supported: frtos, sel4, bare
    ''')
    parser.add_argument("sim", type=str, help='''
    Currently supported: qemu, vcu118, vcs
    ''')
    parser.add_argument("-b", "--build-dir", type=str, default=".", help='''
    Directory containing the Makefile for the main executable.
    Default is current working directory.
    ''')
    parser.add_argument("-s", "--stock", action="store_true", help='''
    Use a stock build configuration
    ''')
    parser.add_argument("--disable-colors", action="store_true", help='''
    Disable colored logging
    ''')

    args = parser.parse_args()

    log_level = logging.INFO
    logger = isp_utils.setupLogger(log_level, (not args.disable_colors))

    build_dir_full = os.path.abspath(args.build_dir)

    sim = args.sim
    if args.sim in sim_aliases:
        sim = sim_aliases[args.sim]

    result = doInstall(build_dir_full,
                       getTemplatesDir(),
                       args.runtime,
                       sim,
                       args.stock)

    if result is not retVals.SUCCESS:
        logger.error("Failed to install runtime: {}".format(result))


if __name__ == "__main__":
    main()

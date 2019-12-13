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
#  runtime - Currently supported: frtos, sel4, bare (bare metal), stock_frtos, stock_sel4, stock_bare

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

def sel4_setup_source(build_dir, template_dir):
    sel4_prefix_source_dir = os.path.join(isp_utils.getIspPrefix(), "hope-seL4-app-template")
    sel4_local_source_dir = os.path.join(build_dir, "hope-seL4-app-template")

    try:
        shutil.copytree(sel4_prefix_source_dir, sel4_local_source_dir)
    except OSError as e:
        logging.warn("WARNING - seL4 copy failed with message: {}".format(e))


def doInstall(build_dir, template_dir, runtime, sim):
    if not os.path.isdir(build_dir):
        return retVals.NO_TEST

    if not os.path.isdir(template_dir):
        return retVals.NO_TEMPLATE

    runtime_dir = os.path.join(build_dir, "isp-runtime-{}".format(runtime))

    isp_utils.removeIfExists(runtime_dir)
    isp_utils.doMkDir(runtime_dir)

    shutil.copy(os.path.join(template_dir, "isp_utils.h"),
                os.path.join(runtime_dir, "isp_utils.h"))

    if "frtos" == runtime:
        if "qemu" == sim:
            shutil.copy(os.path.join(template_dir, "hifive.c"),
                        os.path.join(runtime_dir, "hifive.c"))
            shutil.copy(os.path.join(template_dir, "frtos.c"),
                        os.path.join(runtime_dir, "frtos.c"))
            shutil.copy(os.path.join(template_dir, "frtos.mk"),
                        os.path.join(build_dir, "isp-runtime-frtos.mk"))
        if "stock_qemu" == sim:
            shutil.copy(os.path.join(template_dir, "hifive.c"),
                        os.path.join(runtime_dir, "hifive.c"))
            shutil.copy(os.path.join(template_dir, "frtos.c"),
                        os.path.join(runtime_dir, "frtos.c"))
            shutil.copy(os.path.join(template_dir, "stock_frtos.mk"),
                        os.path.join(build_dir, "isp-runtime-stock_frtos.mk"))
        return retVals.SUCCESS

    if "bare" == runtime:
        if "qemu" == sim:
            shutil.copy(os.path.join(template_dir, "hifive.c"),
                        os.path.join(runtime_dir, "hifive.c"))
            shutil.copy(os.path.join(template_dir, "bare.c"),
                        os.path.join(runtime_dir, "bare.c"))
            shutil.copy(os.path.join(template_dir, "hifive.mk"),
                        os.path.join(build_dir, "isp-runtime-bare.mk"))
            shutil.copytree(os.path.join(isp_utils.getIspPrefix(), "hifive_bsp"),
                            os.path.join(runtime_dir, "bsp"))
        if "stock_qemu" == sim:
            shutil.copy(os.path.join(template_dir, "hifive.c"),
                        os.path.join(runtime_dir, "hifive.c"))
            shutil.copy(os.path.join(template_dir, "bare.c"),
                        os.path.join(runtime_dir, "bare.c"))
            shutil.copy(os.path.join(template_dir, "stock_bare.mk"),
                        os.path.join(build_dir, "isp-runtime-stock_bare.mk"))
            shutil.copytree(os.path.join(isp_utils.getIspPrefix(), "hifive_bsp"),
                            os.path.join(runtime_dir, "bsp"))
        if "vcu118" == sim:
            shutil.copy(os.path.join(template_dir, "vcu118.c"),
                        os.path.join(runtime_dir, "vcu118.c"))
            shutil.copy(os.path.join(template_dir, "bare.c"),
                        os.path.join(runtime_dir, "bare.c"))
            shutil.copy(os.path.join(template_dir, "vcu118.mk"),
                        os.path.join(build_dir, "isp-runtime-bare.mk"))
            shutil.copytree(os.path.join(isp_utils.getIspPrefix(), "vcu118_bsp"),
                            os.path.join(runtime_dir, "bsp"))
        return retVals.SUCCESS

    elif "sel4" == runtime:
        if "qemu" == sim:
            sel4_setup_source(build_dir, template_dir)

            sel4_dir = os.path.join(runtime_dir, "sel4")
            isp_utils.doMkDir(sel4_dir)

            shutil.copy(os.path.join(template_dir, "sel4.mk"),
                        os.path.join(build_dir, "isp-runtime-sel4.mk"))
        if "stock_qemu" == sim:
            sel4_setup_source(build_dir, template_dir)

            sel4_dir = os.path.join(runtime_dir, "stock_sel4")
            isp_utils.doMkDir(sel4_dir)
            shutil.copy(os.path.join(template_dir, "stock_sel4.mk"),
                        os.path.join(build_dir, "isp-runtime-stock_sel4.mk"))

        return retVals.SUCCESS

    logging.error("Runtime {} is incompatible with sim {}".format(runtime, sim))
    return retVals.NO_RUNTIME


def main():
    parser = argparse.ArgumentParser(description='''
    Install ISP runtime into standalone C project
    ''')
    parser.add_argument("runtime", type=str, help='''
    Currently supported: frtos, sel4, bare
    ''')
    parser.add_argument("sim", type=str, help='''
    Currently supported: qemu, stock_qemu, vcu118
    ''')
    parser.add_argument("-b", "--build-dir", type=str, default=".", help='''
    Directory containing the Makefile for the main executable.
    Default is current working directory.
    ''')
    parser.add_argument("--disable-colors", action="store_true", help='''
    Disable colored logging
    ''')

    args = parser.parse_args()

    log_level = logging.INFO
    logger = isp_utils.setupLogger(log_level, (not args.disable_colors))

    build_dir_full = os.path.abspath(args.build_dir)

    result = doInstall(build_dir_full,
                       getTemplatesDir(),
                       args.runtime,
                       args.sim)

    if result is not retVals.SUCCESS:
        logger.error("Failed to build application: {}".format(result))


if __name__ == "__main__":
    main()

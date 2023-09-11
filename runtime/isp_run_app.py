#! /usr/bin/python3

import os
import re
import argparse
import isp_utils
import logging
import sys
import subprocess

isp_prefix = isp_utils.getIspPrefix()
sys.path.append(os.path.join(isp_prefix, "runtime", "modules"))
sim_module = None
import isp_pex_kernel

logger = logging.getLogger()

def printUartOutput(run_dir):
    process_log = open(os.path.join(run_dir, "uart.log"))
    logging.info("Process output:")
    print(process_log.read())


def getProcessExitCode(run_dir, runtime):
    try:
        process_log = open(os.path.join(run_dir, "uart.log"))
    except:
        return
    process_out = process_log.readlines()
    hex_pattern = r"0x[0-9A-Fa-f]+$"
    for line in process_out:
        if isp_utils.terminateMessage(runtime.replace("stock_", '')) in line:
            matches = re.findall(hex_pattern, line)

            if len(matches) > 0:
                return int(matches[0], 0)

    return -1


# TODO: external entities file currently unused
def doEntitiesFile(run_dir, name):
    filename = os.path.join(run_dir, (name + ".entities.yml"))
    if os.path.exists(filename) is False:
        open(filename, "a").close()


def compileMissingPex(policy_dir, pex_path, sim, arch, extra):
    logger.info("Attempting to compile missing PEX binary")
    install_path = os.path.dirname(pex_path)
    args = ["isp_install_policy",
             "-p", policy_dir,
             "-s", sim,
             "--arch", arch,
             "-o", install_path]

    if extra:
        args += ["-e"] + extra

    logger.debug("Building PEX kernel with command: {}".format(" ".join(args)))
    result = subprocess.call(args)

    if result != 0:
        return False

    logger.info("Successfully compiled missing PEX binary")
    return True


def compileMissingPolicy(policies, global_policies, output_dir, debug):
    logger.info("Attempting to compile missing policy")
    args = ["isp_install_policy",
            "-O", output_dir,
            "-p"] + policies

    if global_policies:
        args += ["-P"] + global_policies

    if debug:
        args += ["-D"]

    logger.debug("Building policy with command: {}".format(" ".join(args)))
    result = subprocess.call(args)

    if result != 0:
        return False

    logger.info("Successfully compiled missing policy")
    return True


def main():
    global sim_module
    parser = argparse.ArgumentParser(description="Run standalone ISP applications")
    parser.add_argument("exe_path", type=str, help='''
    Path of the executable to run
    ''')
    parser.add_argument("-p", "--policies", nargs='+', default=["none"], help='''
    List of policies to apply to run, or path to a policy directory
    Default is none
    ''')
    parser.add_argument("-P", "--global-policies", nargs='+', help='''
    List of global policies to apply to run
    Default is none
    ''')
    parser.add_argument("-s", "--simulator", type=str, default="qemu", help='''
    Module for simulating/running application. Must be installed to $ISP_PREFIX/runtime_modules
    ''')
    parser.add_argument("-r", "--runtime", type=str, default="bare", help='''
    Currently supported: frtos, sel4, bare (bare metal) (default), stock_frtos, stock_sel4, stock_bare
    ''')
    parser.add_argument("-o", "--output", type=str, default="", help='''
    Location of simulator output directory. Contains supporting files and
    runtime logs.
    Default is current working directory.
    ''')
    parser.add_argument("-u", "--uart", action="store_true", help='''
    Forward UART output from the simulator to stdout
    ''')
    parser.add_argument("-g", "--gdb", type=int, default=0, help='''
    Start the simulator in gdbserver mode on specified port
    ''')
    parser.add_argument("-d", "--debug", action="store_true", help='''
    Enable debug logging in this script
    ''')
    parser.add_argument("-D", "--policy-debug", action="store_true", help='''
    Use a debug policy
    ''')
    parser.add_argument("-t", "--tag-only", action="store_true", help='''
    Run the tagging tools without running the application
    ''')
    parser.add_argument("-T", "--tagfile", default=None, help='''
    Path of tag file to use rather than generating it based on policy
    ''')
    parser.add_argument("-C", "--rule-cache-name", type=str, default="", help='''
    Name of the rule cache
    ''')
    parser.add_argument("-c", "--rule-cache-size", type=int, default=16, help='''
    Size of the rule cache (if name is provided). Default is 16
    ''')
    parser.add_argument("-e", "--extra", nargs="+", help='''
    Extra command line arguments for the simulator
    ''')
    parser.add_argument("-S", "--suffix", type=str, help='''
    Extra suffix to add to the test directory name
    ''')
    parser.add_argument("--soc", type=str, help='''
    SOC configuration YAML file
    ''')
    parser.add_argument("-N", "--no_validator", action="store_true", help='''
    Do not use the validator and run the stock version of the simulator (which
    must be located at ISP_PREFIX/stock-tools/bin/qemu-system-riscv32.
    ''')
    parser.add_argument("--disable-colors", action="store_true", help='''
    Disable colored logging
    ''')
    parser.add_argument("--pex", type=str, help='''
    Path to a custom PEX implementation (validator lib, kernel, etc)
    ''')

    args = parser.parse_args()

    log_level = logging.INFO
    if args.debug is True:
        log_level = logging.DEBUG

    logger = isp_utils.setupLogger(log_level, (not args.disable_colors))

    sim_module = __import__("isp_" + args.simulator)

    if not os.path.isfile(args.exe_path):
        logger.error("No binary found to run")
        exit(1)

    if args.output == "":
        output_dir = os.getcwd()
    else:
        output_dir = os.path.abspath(args.output)

    if args.runtime not in ["frtos", "sel4", "bare", "stock_frtos", "stock_sel4", "stock_bare"]:
        logger.error("Invalid choice of runtime. Valid choices: frtos, sel4, bare, stock_frtos, stock_sel4, stock_bare")
        return

    arch = isp_utils.getArch(args.exe_path)
    if not arch:
        logger.error("Invalid choice of architecture. Valid choices: {}".format(isp_utils.supportedArchs))
        return

    logger.debug("Executable has architecture {}".format(arch))

    if args.rule_cache_name not in ["", "finite", "infinite", "dmhc"]:
        logger.error("Invalid choice of rule cache name. Valid choices: finite, infinite, dmhc")
        return

    policies = args.policies
    policy_dir = ""
    policy_name = ""

    use_validator = not args.no_validator

    # Policy Directory Building
    # Force policy to none if we're using stock
    if "stock_" in args.simulator or "stock_" in args.runtime:
        logger.info("Using a stock simulator or runtime, setting policy to 'none'")
        policies = ["none"]

    # use existing policy directory if -p arg refers to path
    if (len(policies) == 1 and  "/" in args.policies[0] and os.path.isdir(policies[0])):
        policy_dir = os.path.abspath(policies[0])
        policy_name = os.path.basename(policy_dir)
    else:
        policy_name = isp_utils.getPolicyFullName(policies, args.global_policies, args.policy_debug)

    args.exe_path = os.path.realpath(args.exe_path)
    exe_name = os.path.basename(args.exe_path)
    run_dir = os.path.join(output_dir, "isp-run-{}-{}".format(exe_name, policy_name))
    if args.rule_cache_name != "":
        run_dir = run_dir + "-{}-{}".format(args.rule_cache_name, args.rule_cache_size)
    if args.suffix:
        run_dir = run_dir + "-" + args.suffix
    
    # set policy_dir based on run_dir if it's not an existing directory
    if (not (len(policies) == 1 and  "/" in args.policies[0] and os.path.isdir(policies[0]))):
        policy_dir = os.path.join(run_dir, policy_name)

    isp_utils.removeIfExists(run_dir)
    isp_utils.doMkDir(run_dir)
    logger.addHandler( logging.FileHandler("{0}/{1}.log".format(run_dir, "isp_run_app")))
    logger.info("isp_run_app called with 'isp_run_app {}'".format(' '.join([arg for arg in sys.argv])))

    pex_path = args.pex
    if not pex_path:
        pex_path = os.path.join(run_dir, os.path.basename(sim_module.defaultPexPath(policy_name, "rv", args.extra)))
    else:
        pex_path = os.path.realpath(args.pex)

    if "stock_" not in args.runtime and use_validator == True:
        if not os.path.isdir(policy_dir):
            if compileMissingPolicy(policies, args.global_policies, run_dir, args.policy_debug) is False:
                logger.error("Failed to compile missing policy")
                sys.exit(1)

        if not os.path.isfile(pex_path):
            if compileMissingPex(policy_dir, pex_path, args.simulator, arch, args.extra) is False:
                logger.error("Failed to compile missing PEX binary")
                sys.exit(1)

        logger.debug("Using PEX at path: {}".format(pex_path))

        doEntitiesFile(run_dir, exe_name)

    logger.debug("Starting simulator...")
    result = sim_module.runSim(args.exe_path,
                               run_dir,
                               policy_dir,
                               pex_path,
                               args.runtime,
                               (args.rule_cache_name, args.rule_cache_size),
                               args.gdb,
                               args.tagfile,
                               args.soc,
                               arch,
                               args.extra,
                               use_validator,
                               args.tag_only)

    if result != isp_utils.retVals.SUCCESS:
        logger.error(result)
        os._exit(-1)

    if args.tag_only is True:
        return

    if args.uart is True:
        printUartOutput(run_dir)

    process_exit_code = getProcessExitCode(run_dir, args.runtime)
    logger.debug("Process exited with code {}".format(process_exit_code))

    if result is not isp_utils.retVals.SUCCESS:
        logger.error("Failed to run application: {}".format(result))


if __name__ == "__main__":
    main()

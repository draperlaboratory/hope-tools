#! /usr/bin/python3

import isp_run
import os
import re
import argparse
import isp_utils
import logging
import sys

def printUartOutput(run_dir):
    process_log = open(os.path.join(run_dir, "uart.log"))
    logging.info("Process output:")
    print(process_log.read())


def getProcessExitCode(run_dir, runtime):
    process_log = open(os.path.join(run_dir, "uart.log"))
    process_out = process_log.readlines()
    hex_pattern = r"0x[0-9A-Fa-f]+$"
    for line in process_out:
        if isp_utils.terminateMessage(runtime.replace("stock_", '')) in line:
            matches = re.findall(hex_pattern, line)

            if len(matches) > 0:
                return int(matches[0], 0)

    return -1


def main():
    parser = argparse.ArgumentParser(description="Run standalone ISP applications")
    parser.add_argument("exe_path", type=str, help='''
    Path of the executable to run
    ''')
    parser.add_argument("-p", "--policy", type=str, default="none", help='''
    Name of the installed policy to run or directory containing policy. Default is none
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
    Enable debug logging
    ''')
    parser.add_argument("-t", "--tag-only", action="store_true", help='''
    Run the tagging tools without running the application
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
    SOC configuration YAML file (default is <policy_dir>/soc_cfg/hifive_e_cfg.yml)
    ''')
    parser.add_argument("-N", "--no_validator", action="store_true", help='''
    Do not use the validator and run the stock version of the simulator (which
    must be located at ISP_PREFIX/stock-tools/bin/qemu-system-riscv32.
    ''')

    args = parser.parse_args()

    logger = isp_utils.setupLogger()
    logger.setLevel(logging.INFO)
    if args.debug is True:
        logger.setLevel(logging.DEBUG)

    sys.path.append(os.path.join(isp_utils.getIspPrefix(), "runtime", "modules"))

    output_dir = args.output
    if args.output == "":
        output_dir = os.getcwd()

    if args.runtime not in ["frtos", "sel4", "bare", "stock_frtos", "stock_sel4", "stock_bare"]:
        logger.error("Invalid choice of runtime. Valid choices: frtos, sel4, bare, stock_frtos, stock_sel4, stock_bare")
        return

    if args.rule_cache_name not in ["", "finite", "infinite", "dmhc"]:
        logger.error("Invalid choice of rule cache name. Valid choices: finite, infinite, dmhc")

    if args.simulator not in ["qemu", "renode"]:
        logger.error("Invalid choice of simulator. Valid choices are: qemu, renode")

    # Policy Directory Building
    # Force policy to none if we're using stock
    if "stock_" in args.simulator or "stock_" in args.runtime:
        logger.info("Using a stock simulator or runtime, setting policy to 'none'")
        policy_name = 'none'
        policy_full_name = 'osv.bare.main.none'
    else:
        policy_name = args.policy

    policy_full_name = isp_utils.getPolicyFullName(policy_name, args.runtime)
    if os.path.isdir(policy_name):
        policy_full_name = os.path.abspath(policy_name)
        policy_name = os.path.basename(policy_full_name)

    kernels_dir = os.path.join(isp_utils.getIspPrefix(), "kernels")
    policy_dir = os.path.join(kernels_dir, policy_full_name)

    exe_name = os.path.basename(args.exe_path)
    exe_full_path = os.path.abspath(args.exe_path)
    run_dir = os.path.join(output_dir,
                           "isp-run-{}-{}".format(exe_name, policy_name))
    if args.rule_cache_name != "":
        run_dir = run_dir + "-{}-{}".format(args.rule_cache_name,
                                            args.rule_cache_size)

    if args.suffix:
        run_dir = run_dir + "-" + args.suffix

    soc_path = os.path.join(policy_dir, "soc_cfg", "hifive_e_cfg.yml")
    if args.soc is not None:
        soc_path = os.path.abspath(args.soc)

    use_validator = True
    if args.no_validator == True:
        use_validator = False

    run_dir_full_path = os.path.abspath(run_dir)
    isp_utils.removeIfExists(run_dir_full_path)

    logger.debug("Starting simulator...")
    result = isp_run.runSim(exe_full_path,
                            policy_dir,
                            run_dir_full_path,
                            args.simulator,
                            args.runtime,
                            (args.rule_cache_name, args.rule_cache_size),
                            args.gdb,
                            args.tag_only,
                            soc_path,
                            use_validator,
                            args.extra)

    if result != isp_run.retVals.SUCCESS:
        logger.error(result)
        sys.exit(-1)

    if args.tag_only is True:
        return

    if args.uart is True:
        printUartOutput(run_dir)

    process_exit_code = getProcessExitCode(run_dir, args.runtime)
    logger.debug("Process exited with code {}".format(process_exit_code))

    if result is not isp_run.retVals.SUCCESS:
        logger.error("Failed to run application: {}".format(result))


if __name__ == "__main__":
    main()

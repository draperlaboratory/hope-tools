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
        if isp_utils.terminateMessage(runtime) in line:
            matches = re.findall(hex_pattern, line)
            if matches is not None:
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
    Currently supported: qemu (default), renode
    ''')
    parser.add_argument("-r", "--runtime", type=str, default="bare", help='''
    Currently supported: frtos, bare (bare metal) (default)
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
    parser.add_argument("-e", "--extra", type=str, help='''
    Extra command line arguments for the simulator
    ''')
    parser.add_argument("-S", "--suffix", type=str, help='''
    Extra suffix to add to the test directory name
    ''')

    args = parser.parse_args()

    logger = isp_utils.setupLogger()
    logger.setLevel(logging.INFO)
    if args.debug is True:
        logger.setLevel(logging.DEBUG)


    output_dir = args.output
    if args.output == "":
        output_dir = os.getcwd()

    if args.runtime not in ["frtos", "bare"]:
        logger.error("Invalid choice of runtime. Valid choices: frtos, bare")
        return

    if args.rule_cache_name not in ["", "finite", "infinite", "dmhc"]:
        logger.error("Invalid choice of rule cache name. Valid choices: finite, infinite, dmhc")

    policy_full_name = isp_utils.getPolicyFullName(args.policy, args.runtime)
    policy_name = args.policy
    if os.path.isdir(args.policy):
        policy_full_name = os.path.abspath(args.policy)
        policy_name = os.path.basename(policy_full_name)

    exe_name = os.path.basename(args.exe_path)
    exe_full_path = os.path.abspath(args.exe_path)
    run_dir = os.path.join(output_dir, "isp-run-{}-{}".format(exe_name, policy_name))
    if args.rule_cache_name != "":
        run_dir = run_dir + "-{}-{}".format(args.rule_cache_name, args.rule_cache_size)

    if args.suffix:
        run_dir = run_dir + "-" + args.suffix

    run_dir_full_path = os.path.abspath(run_dir)
    isp_utils.removeIfExists(run_dir_full_path)

    kernels_dir = isp_utils.getKernelsDir()

    logger.debug("Starting simulator...")
    result = isp_run.runSim(exe_full_path,
                            kernels_dir,
                            run_dir_full_path,
                            policy_full_name,
                            args.simulator,
                            args.runtime,
                            (args.rule_cache_name, args.rule_cache_size),
                            args.gdb,
                            args.tag_only,
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

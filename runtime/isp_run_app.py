import isp_run
import os
import re
import argparse
import isp_utils
import logging

def printUartOutput(run_dir):
    process_log = open(os.path.join(run_dir, "uart.log"))
    logging.info("Process output:")
    print(process_log.read())


def getProcessExitCode(run_dir):
    process_log = open(os.path.join(run_dir, "uart.log"))
    process_out = process_log.readlines()
    hex_pattern = r"0x[0-9A-Fa-f]+$"
    for line in process_out:
        if "Progam has exited with code:" in line:
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
    Name of the policy to run. Default is none
    ''')
    parser.add_argument("-s", "--simulator", type=str, default="qemu", help='''
    Currently supported: qemu (default)
    ''')
    parser.add_argument("-r", "--runtime", type=str, default="hifive", help='''
    Currently supported: frtos, hifive (bare metal) (default)
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

    args = parser.parse_args()

    logger = isp_utils.setupLogger()
    logger.setLevel(logging.INFO)
    if args.debug is True:
        logger.setLevel(logging.DEBUG)


    output_dir = args.output
    if args.output == "":
        output_dir = os.getcwd()

    exe_name = os.path.basename(args.exe_path)
    exe_full_path = os.path.abspath(args.exe_path)
    run_dir = os.path.join(output_dir, "isp_run_" + exe_name)
    isp_utils.removeIfExists(run_dir)

    policy_full_name = isp_utils.getPolicyFullName(args.policy, args.runtime)

    logger.debug("Starting simulator...")
    result = isp_run.runSim(exe_full_path,
                            isp_utils.getKernelsDir(),
                            run_dir,
                            policy_full_name,
                            args.simulator,
                            ("", 16),
                            args.gdb)

    if result != isp_run.retVals.SUCCESS:
        logger.error(result)

    if args.uart is True:
        printUartOutput(run_dir)

    process_exit_code = getProcessExitCode(run_dir)
    logger.debug("Process exited with code {}".format(process_exit_code))

    if result is not isp_run.retVals.SUCCESS:
        logger.error("Failed to run application: {}".format(result))


if __name__ == "__main__":
    main()

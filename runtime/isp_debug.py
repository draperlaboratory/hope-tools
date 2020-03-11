#! /usr/bin/python3

import argparse
import subprocess
import os
import sys
import time
import isp_utils
import signal

gdb_command = "riscv32-unknown-elf-gdb"

def getGdbScriptPath(sim):
    isp_prefix = isp_utils.getIspPrefix()
    return os.path.join(isp_prefix, "gdb-scripts", "{}.gdb".format(sim))


def startGdb(exe_path, port, sim):
    args = [gdb_command, "-q", "-ix", getGdbScriptPath(sim),
                         "-ex", "target remote :{}".format(port),
                         exe_path]
    if sim == "renode":
        args.insert(6, "-ex")
        args.insert(7, "monitor start")

    # Ignore ctrl-c so it's possible to interrupt gdb in a loop
    signal.signal(signal.SIGINT, signal.SIG_IGN)
        
    proc = subprocess.call(args)


def main():
    parser = argparse.ArgumentParser(description="Debug client for ISP applications")
    parser.add_argument("exe_path", type=str, help='''
    Path of the executable to debug
    ''')
    parser.add_argument("port", type=int, help='''
    Port of the gdbserver session
    ''')
    parser.add_argument("-s", "--simulator", type=str, default="qemu", help='''
    Simulator being used in isp_run_app
    ''')

    args = parser.parse_args()
    exe_full_path = os.path.abspath(args.exe_path)

    startGdb(exe_full_path, args.port, args.simulator)


if __name__ == "__main__":
    main()

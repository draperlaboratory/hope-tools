import socket
import select
import threading
import time
import sys
import subprocess
import os
import logging
import isp_utils

logger = logging.getLogger()

# set timeout seconds
timeout_seconds = 60

# configure the test log files
uart_port = 4444
uart_log_file = "uart.log"

status_port = 3344
status_log_file = "pex.log"

renode_port = 3320
renode_log_file = "sim.log"

process_exit = False
    
def watchdog():
    global process_exit
    for i in range(timeout_seconds * 10):
        if not process_exit:
            time.sleep(0.1)
    logging.warn("Watchdog timeout")
    process_exit = True


def socketConnect(host, port):
    global process_exit
    res = None
    connecting = True
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while connecting and not process_exit:
        try:
            s.connect((host, port))
            connecting = False
            res = s
            logging.debug("connected {0}:{1}".format(host, port))
        except:
            logging.debug("trying {0}:{1}...".format(host, port))
            time.sleep(1)
    if connecting:
        logger.error("Failed to connect {0}:{1}...".format(host, port))
    return res


def logPort(terminate_msg, log_file, port):
    global process_exit
    data = ""
    logger.info("Logging to: {}".format(log_file))
    f = open(log_file, "w")
    s = socketConnect(socket.gethostname(), port)
    while(s and not process_exit):
        time.sleep(1)
        if terminate_msg in data:
            process_exit = True
        data = ""
        ready_r, ready_w, err = select.select([s], [], [],1)
        if ready_r:
            data = s.recv(1024).decode().replace('\r', '')
            f.write(data)
                
    if s:
        s.close()
    f.close()

def logUart(run_dir, runtime):
    uart_log_path = os.path.join(run_dir, uart_log_file)
    logPort(isp_utils.terminateMessage(runtime), uart_log_path, uart_port)


def logStatus(run_dir):
    status_log_path = os.path.join(run_dir, status_log_file)
    logPort("Policy Violation:", status_log_path, status_port)
    if "Policy Violation:" in open(status_log_path, 'r').read():
        logger.warn("Process exited due to policy violation")


def launchRenode(run_dir):
    global process_exit
    try:
        cmd = ["renode",
               "--plain",
               "--disable-xwt",
               "--hide-log",
               "--port={}".format(renode_port)]
        logger.debug("Running command: {}".format(cmd))

        renode_log_path = os.path.join(run_dir, renode_log_file)
        process = subprocess.Popen(cmd, stdout=open(renode_log_path, 'w'), stderr=subprocess.STDOUT)
        while process.poll() is None:
            time.sleep(0.01)
    finally:
        process_exit = True
        process.kill()


def runOnRenode(exe_path, run_dir, policy_dir, runtime, gdb_port):
    global process_exit
    global connecting

    doRescScript(exe_path, run_dir, policy_dir, gdb_port)

    try:
        logger.debug("Begin Renode test... (timeout: {})".format(timeout_seconds))
        wd = threading.Thread(target=watchdog)
        wd.start()

        logger.debug("Start Renode server...")
        renode = threading.Thread(target=launchRenode, args=(run_dir,))
        renode.start()

        time.sleep(2)
        logger.debug("Start Logging...")
        uart_logger = threading.Thread(target=logUart, args=(run_dir, runtime))
        uart_logger.start()

        logging.info(run_dir)
        status_logger = threading.Thread(target=logStatus, args=(run_dir,))
        status_logger.start()

        logger.debug("Connecting to Renode server...")
        s = socketConnect(socket.gethostname(), renode_port)
        logger.debug("Connected.")
        if s:
            with open(os.path.join(run_dir, "main.resc"), 'r') as f:
                s.send(f.read().replace('\n', '\r\n').encode())
                s.send('start\r\n'.encode())
            while not process_exit:
                time.sleep(0.1)
                ready_r, ready_w, err = select.select([s], [], [],1)
                if ready_r:
                    print(s.recv(1024).decode().replace('\r', ''))
        if s:
            try:
                s.send('quit\r\n'.encode())
                time.sleep(1)
                s.close()
            except:
                pass

        wd.join()
        uart_logger.join()
        status_logger.join()
        renode.join()
    finally:
        try:
            if s:
                s.send('quit\r\n'.encode())
                time.sleep(1)
                s.close()
        except:
            pass


def doRescScript(exe_path, run_dir, policy_dir, gdb_port):
    resc_script = rescScript(exe_path, run_dir, policy_dir, gdb_port)

    with open(os.path.join(run_dir, "main.resc"), 'w') as f:
        f.write(resc_script)

def rescScript(exe_path, run_dir, policy_dir, gdb_port):
    gdb_command = ""

    if gdb_port != 0:
        gdb_command = "sysbus.ap_core StartGdbServer {}".format(gdb_port)

    return """
mach create
machine LoadPlatformDescription @platforms/boards/dover-riscv-board.repl
sysbus.ap_core MaximumBlockSize 1
emulation CreateServerSocketTerminal {uart_port} "uart-socket"
connector Connect sysbus.uart1 uart-socket
#showAnalyzer sysbus.uart Antmicro.Renode.UI.ConsoleWindowBackendAnalyzer
#emulation CreateUartPtyTerminal "uart-pty" "/tmp/uart-pty"
#connector Connect sysbus.uart uart-pty
sysbus LoadELF @{exe_path}
sysbus.ap_core SetExternalValidator @{policy_dir}/librv32-renode-validator.so @{run_dir}/validator_cfg.yml
{gdb_command}
logLevel 1 sysbus.ap_core
sysbus.ap_core StartStatusServer {status_port}
""".format(exe_path=exe_path, run_dir=run_dir,
           policy_dir=policy_dir, gdb_command=gdb_command,
           uart_port=uart_port, status_port=status_port)

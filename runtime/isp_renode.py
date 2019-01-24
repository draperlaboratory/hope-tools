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

test_done = False
    
def watchdog():
    global test_done
    for i in range(timeout_seconds * 10):
        if not test_done:
            time.sleep(0.1)
    logging.warn("Watchdog timeout")
    test_done = True


def socketConnect(host, port):
    global test_done
    res = None
    connecting = True
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while connecting and not test_done:
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


def logPort(name, log_file, port, runtime):
    global test_done
    data = ""
    logger.info("Logging {} to: {}".format(name, log_file))
    f = open(log_file, "w")
    s = socketConnect(socket.gethostname(), port)
    while(s and not test_done):
        time.sleep(1)
        if isp_utils.terminateMessage(runtime) in data:
            test_done = True
        data = ""
        ready_r, ready_w, err = select.select([s], [], [],1)
        if ready_r:
            data = s.recv(1024).decode().replace('\r', '')
            f.write(data)
                
    if s:
        s.close()
    f.close()


def launchRenode():
    global test_done
    try:
        cmd = ["renode",
               "--plain",
               "--disable-xwt",
               "--hide-log",
               "--port={}".format(renode_port)]
        logger.debug("Running command: {}".format(cmd))
        rc = subprocess.Popen(cmd, stdout=open(os.devnull, 'w'), stderr=subprocess.STDOUT)
        while rc.poll() is None:
            time.sleep(0.01)
    finally:
        test_done = True


def launchRenodeDebug(run_dir, uart_log, status_log):
    open(uart_log, 'w').close()
    open(status_log, 'w').close()
    cmd = ["renode",
            "--disable-xwt",
            os.path.join(run_dir, "main.resc")]
    subprocess.call(cmd)
 

def runOnRenode(exe_path, run_dir, policy_dir, runtime, gdb_port):
    global test_done
    global connecting
    uart_log_path = os.path.join(run_dir, uart_log_file)
    status_log_path = os.path.join(run_dir, status_log_file)

    doRescScript(exe_path, run_dir, policy_dir, gdb_port)

    if gdb_port != 0:
        launchRenodeDebug(run_dir, uart_log_path, status_log_path)
        return

    try:
        logger.debug("Begin Renode test... (timeout: {})".format(timeout_seconds))
        wd = threading.Thread(target=watchdog)
        wd.start()

        logger.debug("Start Renode server...")
        renode = threading.Thread(target=launchRenode)
        renode.start()

        time.sleep(2)
        logger.debug("Start Logging...")
        uart_logger = threading.Thread(target=logPort, args=("Uart", uart_log_path, uart_port, runtime))
        uart_logger.start()

        status_logger = threading.Thread(target=logPort, args=("Status", status_log_path, status_port, runtime))
        status_logger.start()

        logger.debug("Connecting to Renode server...")
        s = socketConnect(socket.gethostname(), renode_port)
        logger.debug("Connected.")
        if s:
            with open(os.path.join(run_dir, "main.resc"), 'r') as f:
                s.send(f.read().replace('\n', '\r\n').encode())
                s.send('start\r\n'.encode())
            while not test_done:
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
        # TODO: have the watchdog timer kill the renode process
        # if test_done:
        #     rc.kill()
        logger.debug("Test Completed")
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

import isp_utils
import os
import argparse
import logging
import subprocess
import serial
import pexpect
import pexpect_serial
import threading
import sys
import time
import multiprocessing
import glob
import shutil

sys.path.append(os.path.join(isp_utils.getIspPrefix(), "runtime"))
import isp_load_image
import isp_pex_kernel

logger = logging.getLogger()

isp_prefix = isp_utils.getIspPrefix()
bitstream_dir = os.path.join(isp_prefix, "vcu118", "bitstreams")

pex_tty_symlink = "/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_*-if00-port0"
ap_tty_symlink = "/dev/serial/by-id/usb-Silicon_Labs_CP2105_Dual_USB_to_UART_Bridge_Controller_*-if01-port0"

fpga = "gfe"

#################################
# Build/Install PEX kernel
# Invoked by isp_install_policy
#################################

def defaultPexPath(policy_name, arch, extra):
    extra_args = parseExtra(extra)
    return os.path.join(isp_prefix, "pex-kernel", isp_pex_kernel.pexKernelName(policy_name, fpga,
                        extra_args.processor))


def installPex(design, policy_dir, output_dir, arch, extra):
    logger.info("Installing pex kernel for VCU118")
    pex_kernel_source_dir = os.path.join(isp_prefix, "sources", "pex-kernel")
    pex_firmware_source_dir = os.path.join(isp_prefix, "sources", "pex-firmware")
    policy_name = os.path.basename(policy_dir)

    extra_args = parseExtra(extra)

    if not isp_utils.checkDependency(pex_kernel_source_dir, logger):
        return False

    if not isp_pex_kernel.copyPexKernelSources(pex_kernel_source_dir, output_dir):
        return False

    if not isp_pex_kernel.copyPolicySources(policy_dir, output_dir, fpga, extra_args.processor):
        return False

    if not isp_pex_kernel.buildPexKernel(design, policy_name, output_dir, fpga, extra_args.processor):
        return False

    if not isp_pex_kernel.movePexKernel(policy_name, output_dir, fpga, extra_args.processor):
        return False

    return True


#################################
# Run VCU118
# Invoked by isp_run_app
#################################

def parseExtra(extra):
    parser = argparse.ArgumentParser(prog="isp_run_app ... -s vcu118 -e")
    parser.add_argument("--pex-tty", help="TTY for PEX UART (autodetect by default)")
    parser.add_argument("--ap-tty", help="TTY for AP UART (autodetect by default)")
    parser.add_argument("--no-log", action="store_true", help="Do not read from the TTYs. This disables exit handling and output logging")
    parser.add_argument("--stock", action="store_true", help="Use a stock (no PIPE) bitstream")
    parser.add_argument("--flash-init", type=str, help="Pre-built flash init")
    parser.add_argument("--kernel-address", type=str, default="0xf8000000", help='''
    Hex address (0x format) for the kernel load image in the flash init.
    ''')
    parser.add_argument("--ap-address", type=str, default="0xf8040000", help='''
    Hex address (0x format) for the application processor load image in the flash init.
    ''')
    parser.add_argument("--bitstream", type=str,
                        help="Re-program the FPGA with the specified bitstream")
    parser.add_argument("--no-reset", action="store_true", help="Skip resetting the FPGA")
    parser.add_argument("--reset-address", type=str, default="0x6fff0000", help="Soft reset address (default is 0x6fff0000)")
    parser.add_argument("--processor", type=str, default="P1", help="GFE processor configuration (P1/P2/P3)")
    parser.add_argument("--board", type=str, default="vcu118", help="Target board: vcu118 or vcu108")

    if not extra:
        return parser.parse_args([])

    extra_dashed = []
    for e in extra:
        if e.startswith("+"):
            extra_dashed.append("--" + e[1:])
        else:
            extra_dashed.append(e)

    return parser.parse_args(extra_dashed)


def detectTTY(symlink):
    symlink_glob = glob.glob(symlink)
    if not symlink_glob:
        logger.warn("Default symlink {} not found".format(symlink))
        return None

    symlink_path = symlink_glob[0]

    try:
        target = os.readlink(symlink_path)
        fullpath = os.path.join(os.path.dirname(symlink_path), target)
        return os.path.realpath(fullpath)
    except:
        logger.warn("Failed to resolve default symlink {}".format(symlink))
        return None


def program_fpga(bit_file, ltx_file, board, log_file):
    tcl_script = os.path.join(isp_prefix, "vcu118", "tcl", "prog_bit.tcl")
    args = ["vivado", "-mode", "batch", "-source", tcl_script, "-tclargs", bit_file, ltx_file, board]

    if not isp_utils.checkDependency(tcl_script, logger, "hope-gfe"):
        return False

    vivado_log = open(log_file, "w")

    try:
        result = subprocess.call(args, cwd=bitstream_dir,
                        stdout=vivado_log, stderr=subprocess.STDOUT)
    except FileNotFoundError:
        # Attempt to run vivado_lab is vivado is not found
        logger.info("Vivado executable not found. Attempting to program using vivado_lab")
        args[0] = "vivado_lab"
        result = subprocess.call(args, cwd=bitstream_dir,
                                stdout=vivado_log, stderr=subprocess.STDOUT)

    vivado_log.close()

    if result != 0:
        logger.error("Failed to re-program FPGA")
        return False

    return True


def start_openocd(log_file=None):
    openocd_path = os.path.join(isp_prefix, "bin", "openocd")
    gfe_cfg_path = os.path.join(isp_prefix, "vcu118", "ssith_gfe.cfg")

    if not isp_utils.checkDependency(gfe_cfg_path, logger, "hope-gfe"):
        return None
    
    if log_file:
        openocd_log = open(log_file, "w")
        openocd_proc = subprocess.Popen([openocd_path, "-f", gfe_cfg_path], stdout=openocd_log,
                        stderr=subprocess.STDOUT)
    else:
        openocd_proc = subprocess.Popen([openocd_path, "-f", gfe_cfg_path])

    return openocd_proc


def soft_reset(exe_path, reset_address, openocd_log_file, gdb_log_file):
    logger.info("Soft resetting FPGA")
    openocd_proc = start_openocd(log_file=openocd_log_file)
    gdb_reset(exe_path, reset_address, gdb_log_file)

    if openocd_proc.poll():
        logger.error("Openocd process terminated early with code {}".format(openocd_proc.returncode))
        return False

    openocd_proc.terminate()
    return True


def start_gdb(exe_path, gdb_log=None):
    child = pexpect.spawn("riscv64-unknown-elf-gdb", [exe_path], encoding="utf-8", timeout=None)
    if not gdb_log:
        child.logfile = sys.stdout
    else:
        child.logfile = gdb_log

    return child


def send_gdb_command(child, com):
    child.expect_exact(["(gdb)", ">"])
    child.sendline(com)


def gdb_reset(exe_path, reset_address, log_file=None):
    if log_file:
        gdb_log = open(log_file, "w")

    child = start_gdb(exe_path, gdb_log)

    send_gdb_command(child, "set style enabled off")
    send_gdb_command(child, "set confirm off")
    send_gdb_command(child, "target remote :3333")
    send_gdb_command(child, "set {{int}}{} = 1".format(reset_address))
    child.expect_exact(["(gdb)", ">"])

    # Wait to make sure write goes through due to latency
    time.sleep(1)

    child.terminate(force=True)

    if log_file:
        gdb_log.close()


def gdb_thread(exe_path, log_file=None, arch="rv32"):
    if log_file:
        gdb_log = open(log_file, "w")

    child = start_gdb(exe_path, gdb_log)

    send_gdb_command(child, "set style enabled off")
    send_gdb_command(child, "set confirm off")
    send_gdb_command(child, "target remote :3333")
    send_gdb_command(child, "load")
    send_gdb_command(child, "continue")
    logger.info("Process running in gdb")
    child.expect_exact("[Inferior 1 (Remote target) detached]")
    logger.info("Program successfully exited")

    if log_file:
        gdb_log.close()


def ap_thread(ap_tty, ap_log, runtime, processor):
    baud_rate = 115200

    ap_serial = serial.Serial(ap_tty, baud_rate, timeout=3000000, bytesize=serial.EIGHTBITS,
                               parity=serial.PARITY_NONE, xonxoff=False, rtscts=False, dsrdtr=False)
    ap_expect = pexpect_serial.SerialSpawn(ap_serial, timeout=3000000, encoding='utf-8', codec_errors='ignore')
    ap_expect.logfile = ap_log

    ap_expect.expect(isp_utils.terminateMessage(runtime))


def pex_thread(pex_tty, pex_log):
    pex_serial = serial.Serial(pex_tty, 115200, timeout=3000000, bytesize=serial.EIGHTBITS,
                                parity=serial.PARITY_NONE, xonxoff=False, rtscts=False, dsrdtr=False)
    pex_expect = pexpect_serial.SerialSpawn(pex_serial, timeout=3000000, encoding='utf-8', codec_errors='ignore')
    pex_expect.logfile = pex_log

    pex_expect.expect("Unrecoverable failure")
    logger.warn("Process failed to run to completion")


def tagInit(exe_path, run_dir, policy_dir, soc_cfg, arch, pex_kernel_path,
            flash_init_image_path, kernel_address, ap_address):
    ap_load_image_path = os.path.join(run_dir, os.path.basename(exe_path) + ".load_image")
    pex_load_image_path = os.path.join(run_dir, "pex.load_image")
    tag_file_path = os.path.join(run_dir, "bininfo", os.path.basename(exe_path) + ".taginfo")

    logger.debug("Using PEX kernel at path: {}".format(pex_kernel_path))

    if not isp_utils.generateTagInfo(exe_path, run_dir, policy_dir, soc_cfg=soc_cfg, arch=arch):
        return False
    
    logger.debug("Using flash init file {}".format(flash_init_image_path))
    if not os.path.exists(flash_init_image_path):
        logger.info("Generating flash init")
        isp_load_image.generate_tag_load_image(ap_load_image_path, tag_file_path)
        isp_load_image.generate_load_image(pex_kernel_path, pex_load_image_path)

        flash_init_map = {kernel_address:pex_load_image_path,
                          ap_address:ap_load_image_path}
        isp_load_image.generate_flash_init(flash_init_image_path, flash_init_map)

    return True


def runPipe(exe_path, ap, pex_tty, pex_log, openocd_log_file,
            gdb_log_file, flash_init_image_path, gdb_port, no_log, arch):
    logger.debug("Connecting to {}".format(pex_tty))
    pex_serial = serial.Serial(pex_tty, 115200, timeout=3000000,
            bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, xonxoff=False, rtscts=False, dsrdtr=False)

    pex_expect = pexpect_serial.SerialSpawn(pex_serial, timeout=3000000, encoding='utf-8', codec_errors='ignore')
    pex_expect.logfile = pex_log
    
    logger.info("Sending flash init file {} to {}".format(flash_init_image_path, pex_tty))
    pex_serial.write(open(flash_init_image_path, "rb").read())
    logger.debug("Done writing init file")

    found = pex_expect.expect(["Entering idle loop.", "Entering infinite loop.", pexpect.EOF])
    if found > 0:
        pex_expect.close()
        return isp_utils.retVals.FAILURE
    pex_expect.close()

    pex = multiprocessing.Process(target=pex_thread, args=(pex_tty, pex_log))
    if not no_log:
        pex.start()

    logger.debug("Spawning openocd")
    openocd_proc = start_openocd(openocd_log_file)
    if not openocd_proc:
        return isp_utils.retVals.FAILURE

    logger.debug("Spawning gdb")
    gdb = multiprocessing.Process(target=gdb_thread, args=(exe_path, gdb_log_file, arch))

    if gdb_port == 0:
        gdb.start()

    if no_log:
        logger.info("Application is running. Press CTRL-C to exit")
        while True:
            pass

    logger.debug("waiting for pex and ap to finish")
    while pex.is_alive() and ap.is_alive():
        pass

    openocd_proc.terminate()
    gdb.terminate()

    ap.terminate()
    pex.terminate()

    return isp_utils.retVals.SUCCESS


def runStock(exe_path, ap, openocd_log_file, gdb_log_file,
             gdb_port, no_log, arch):
    logger.debug("Spawning openocd")
    openocd_proc = start_openocd(openocd_log_file)
    if not openocd_proc:
        return isp_utils.retVals.FAILURE

    logger.debug("Spawning gdb")
    gdb = threading.Thread(target=gdb_thread, args=(exe_path, gdb_log_file, arch))
    if gdb_port == 0:
        gdb.start()

    if no_log:
        logger.info("Application is running. Press CTRL-C to exit")
        while True:
            pass

    while ap.is_alive():
        pass

    openocd_proc.terminate()

    if gdb_port != 0:
        gdb.join()

    ap.terminate()

    return isp_utils.retVals.SUCCESS


def runSim(exe_path, run_dir, policy_dir, pex_path, runtime, rule_cache,
           gdb_port, tagfile, soc_cfg, arch, extra, use_validator=False, tag_only=False):
    extra_args = parseExtra(extra)
    ap_log_file = os.path.join(run_dir, "uart.log")
    pex_log_file = os.path.join(run_dir, "pex.log")
    vivado_log_file = os.path.join(run_dir, "vivado.log")
    openocd_log_file = os.path.join(run_dir, "openocd.log")
    gdb_log_file = os.path.join(run_dir, "gdb.log")

    if not soc_cfg:
        soc_cfg = os.path.join(isp_prefix, "bsp", "vcu118", "config", "soc_vcu118.yml")
    else:
        soc_cfg = os.path.realpath(soc_cfg)
    logger.debug("Using SOC config {}".format(soc_cfg))

    flash_init_image_path = os.path.join(run_dir, "full.init")
    if extra_args.flash_init:
        flash_init_image_path = os.path.realpath(extra_args.flash_init)

    if not extra_args.stock:
        if not tagInit(exe_path, run_dir, policy_dir, soc_cfg,
                       arch, pex_path, flash_init_image_path,
                       extra_args.kernel_address, extra_args.ap_address):
            return isp_utils.retVals.TAG_FAIL

    if tag_only:
        return isp_utils.retVals.SUCCESS

    ap_log = open(ap_log_file, "w")
    pex_log = open(pex_log_file, "w")

    if extra_args.bitstream:
        bit_file = os.path.realpath(extra_args.bitstream)
        ltx_file = os.path.splitext(bit_file)[0] + ".ltx"
        logger.info("Re-programming FPGA with bitstream {}".format(bit_file))
        if program_fpga(bit_file, ltx_file, extra_args.board, vivado_log_file) is False:
            return isp_utils.retVals.FAILURE
    elif not extra_args.no_reset:
        if not soft_reset(exe_path, extra_args.reset_address, openocd_log_file, gdb_log_file):
            logger.error('''
            Soft reset failed. Please re-program the FPGA by providing a +bitstream argument or with the command:
            vivado -mode batch -source $ISP_PREFIX/vcu118/tcl/prog_bit.tcl -tclargs <bitstream> <ltx> vcu118
            ''')
            return isp_utils.retVals.FAILURE

    ap_tty = detectTTY(ap_tty_symlink)
    if not ap_tty:
        logger.error("Failed to autodetect AP TTY file. If you know the symlink, re-run with the +ap_tty option")
        return isp_utils.retVals.FAILURE

    pex_tty = detectTTY(pex_tty_symlink)
    if not pex_tty:
        logger.error("Failed to autodetect PEX TTY file. If you know the symlink, re-run with the +pex_tty option")
        return isp_utils.retVals.FAILURE

    ap = multiprocessing.Process(target=ap_thread, args=(ap_tty, ap_log, runtime, extra_args.processor))
    if not extra_args.no_log:
        logger.debug("Connecting to {}".format(ap_tty))
        ap.start()

    if extra_args.stock:
        result = runStock(exe_path, ap, openocd_log_file, gdb_log_file, gdb_port, extra_args.no_log, arch)
    else:
        result = runPipe(exe_path, ap, pex_tty, pex_log, openocd_log_file,
                         gdb_log_file, flash_init_image_path, gdb_port, extra_args.no_log, arch)

    pex_log.close()
    ap_log.close()

    return result

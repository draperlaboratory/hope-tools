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

pex_tty_symlink = "/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A904CYT1-if00-port0"
ap_tty_symlink =  "/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A904CYX0-if00-port0"

fpga = "gfe"

#################################
# Build/Install PEX kernel
# Invoked by isp_install_policy
#################################

def defaultPexPath(policy_name, soc):
    return os.path.join(isp_prefix, "pex-kernel", isp_pex_kernel.pexKernelName(policy_name, soc))


def installPex(soc, policy_dir, output_dir):
    logger.info("Installing pex kernel for iveia")
    pex_kernel_source_dir = os.path.join(isp_prefix, "sources", "pex-kernel")
    pex_firmware_source_dir = os.path.join(isp_prefix, "sources", "pex-firmware")
    policy_name = os.path.basename(policy_dir)

    if not isp_utils.checkDependency(pex_kernel_source_dir, logger):
        return False

    if not isp_pex_kernel.copyPexKernelSources(pex_kernel_source_dir, output_dir):
        return False

    if not isp_pex_kernel.copyPolicySources(policy_dir, output_dir, soc):
        return False

    if not isp_pex_kernel.buildPexKernel(soc, policy_name, output_dir, "gfe"):
        return False

    if not isp_pex_kernel.movePexKernel(policy_name, output_dir, soc):
        return False

    return True


#################################
# Run VCU118
# Invoked by isp_run_app
#################################

def parseExtra(extra):
    parser = argparse.ArgumentParser(prog="isp_run_app ... -s iveia -e")
    parser.add_argument("--pex-tty", help="TTY for PEX UART (autodetect by default)")
    parser.add_argument("--ap-tty", help="TTY for AP UART (autodetect by default)")
    parser.add_argument("--no-log", action="store_true", help="Do not read from the TTYs. This disables exit handling and output logging")
    parser.add_argument("--iveia-tmp", type=str, default="/opt", help="Temp location on iveia's FS")
    parser.add_argument("--flash-init", type=str, help="Pre-built flash init")
    parser.add_argument("--kernel-address", type=str, default="0x40000000", help='''
    Hex address (0x format) for the kernel load image in the flash init.
    ''')
    parser.add_argument("--ap-address", type=str, default="0x78040000", help='''
    Hex address (0x format) for the application processor load image in the flash init.
    ''')
    parser.add_argument("--bitstream", type=str,
                        help="Re-program the FPGA with the specified bitstream")
    parser.add_argument("--no-reset", action="store_true", help="Skip resetting the FPGA")
    parser.add_argument("--board", type=str, default="iveia", help="Target board: iveia or iwave")
    parser.add_argument("--pex-br", type=str, default="115200", help="pex uart baud rate")
    parser.add_argument("--ap-br", type=str, default="115200", help="ap uart baud rate")

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



def ap_thread(ap_tty, ap_baud_rate, ap_log, runtime):

    ap_serial = serial.Serial(ap_tty, ap_baud_rate, timeout=3000000, bytesize=serial.EIGHTBITS,
                               parity=serial.PARITY_NONE, xonxoff=False, rtscts=False, dsrdtr=False)
    ap_expect = pexpect_serial.SerialSpawn(ap_serial, timeout=3000000, encoding='utf-8', codec_errors='ignore')
    ap_expect.logfile = ap_log

    ap_expect.expect(isp_utils.terminateMessage(runtime))


def pex_thread(pex_tty, pex_baud_rate, pex_log):
    pex_serial = serial.Serial(pex_tty, pex_baud_rate, timeout=3000000, bytesize=serial.EIGHTBITS,
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

def runIveiaCmd(cmd, pex_log, run_dir):
    local_cmd = ["ssh",
                 "root@atlas-ii-z8-hp"] + cmd

    result = subprocess.call(local_cmd, stdout=pex_log, stderr=subprocess.STDOUT, cwd=run_dir)

    if result != 0:
        logger.error("Failed to execute command remotely on the iveia board ...")
        logger.error("Used command : {} returned {}".format(cmd, result))
        return isp_utils.retVals.FAILURE

    return isp_utils.retVals.SUCCESS

def runPipe(exe_path, ap, pex_tty, pex_baud_rate, pex_log, run_dir, pex_kernel_path, no_log, iveia_tmp):
    logger.debug("Connecting PEX uart to {}, baud rate {}".format(pex_tty, pex_baud_rate))
    pex_serial = serial.Serial(pex_tty, pex_baud_rate, timeout=3000000,
            bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, xonxoff=False, rtscts=False, dsrdtr=False)

    pex_expect = pexpect_serial.SerialSpawn(pex_serial, timeout=3000000, encoding='utf-8', codec_errors='ignore')
    pex_expect.logfile = pex_log

    ap_tags_load_image = os.path.join(run_dir, os.path.basename(exe_path) + ".load_image")

    # before you copy the images to the iveia_tmp, make sure you clear that dir (e.g. remove all the
    # files in there possibly from other runs )
#    cmd = ["/bin/rm -f",
#           iveia_tmp + "/" + os.path.basename(exe_path),
#           iveia_tmp + "/" + os.path.basename(pex_path),
#           iveia_tmp + "/" + os.path.basename(exe_path) + ".load_image"]
#    result1 = runIveiaCmd(cmd, pex_log, run_dir)


    load_pex_and_tag_files_args = ["scp",
                                   pex_kernel_path,
                                   ap_tags_load_image,
                                   exe_path,
                                   "root@atlas-ii-z8-hp:" + iveia_tmp]

    result = subprocess.call(load_pex_and_tag_files_args, stdout=pex_log, stderr=subprocess.STDOUT, cwd=run_dir)

    if result != 0:
        logger.error("Failed to copy to iveia board the pex kernel and the ap_tag_info files ...")
        logger.error("Used command : {} returned {}".format(load_pex_and_tag_files_args, result))
        return isp_utils.retVals.FAILURE

    isp_load_args = ["isp-loader",
                     iveia_tmp + "/" + os.path.basename(exe_path),
                     iveia_tmp + "/" + os.path.basename(pex_kernel_path),
                     iveia_tmp + "/" + os.path.basename(exe_path) +
                     ".load_image"]

    logger.info("Loading pex kernel and ap tags into the mem space of the PIPE and AP respectively and issuing reset")
    result = runIveiaCmd(isp_load_args, pex_log, run_dir)

    if result != isp_utils.retVals.SUCCESS:
        return isp_utils.retVals.FAILURE

    # when the data is already in the memory, the PEX is interrupted (to process rule cache misses)
    # before it can print "Entering idle loop"
    found = pex_expect.expect(["Releasing host core.", "Unrecoverable failure.", pexpect.EOF])
    if found > 0:
        pex_expect.close()
        return isp_utils.retVals.FAILURE
    pex_expect.close()

    pex = multiprocessing.Process(target=pex_thread, args=(pex_tty, pex_baud_rate, pex_log))
    if not no_log:
        pex.start()

    logger.debug("waiting for pex and ap to finish")
    while pex.is_alive() and ap.is_alive():
        pass

    ap.terminate()
    pex.terminate()

    return isp_utils.retVals.SUCCESS

def runSim(exe_path, soc, run_dir, policy_dir, pex_path, runtime, rule_cache,
           gdb_port, tagfile, soc_cfg, arch, extra, use_validator=False, tag_only=True):
    extra_args = parseExtra(extra)
    ap_log_file = os.path.join(run_dir, "uart.log")
    pex_log_file = os.path.join(run_dir, "pex.log")

    flash_init_image_path = os.path.join(run_dir, "full.init")
    if extra_args.flash_init:
        flash_init_image_path = os.path.realpath(extra_args.flash_init)

    if not tagInit(exe_path, run_dir, policy_dir, soc_cfg,
                   arch, pex_path, flash_init_image_path,
                   extra_args.kernel_address, extra_args.ap_address):
            return isp_utils.retVals.TAG_FAIL

    if tag_only:
        return isp_utils.retVals.SUCCESS

    ap_log = open(ap_log_file, "w")
    pex_log = open(pex_log_file, "w")

    ap_tty = detectTTY(ap_tty_symlink)
    if not ap_tty:
        logger.error("Failed to autodetect AP TTY file. If you know the symlink, re-run with the +ap_tty option")
        return isp_utils.retVals.FAILURE

    pex_tty = detectTTY(pex_tty_symlink)
    if not pex_tty:
        logger.error("Failed to autodetect PEX TTY file. If you know the symlink, re-run with the +pex_tty option")
        return isp_utils.retVals.FAILURE

    ap = multiprocessing.Process(target=ap_thread, args=(ap_tty, extra_args.ap_br, ap_log, runtime))
    if not extra_args.no_log:
        logger.debug("Connecting AP uart to {}, baud rate {}".format(ap_tty, extra_args.ap_br))
        ap.start()

    result = runPipe(exe_path, ap, pex_tty, extra_args.pex_br, pex_log, run_dir, pex_path, extra_args.no_log, extra_args.iveia_tmp)

    # clean after yourself - remove any files stored in the iveia_tmp
    logger.info("Cleaning after yourself ...")
    cmd = ["/bin/rm -f",
           extra_args.iveia_tmp + "/" + os.path.basename(exe_path),
           extra_args.iveia_tmp + "/" + os.path.basename(pex_path),
           extra_args.iveia_tmp + "/" + os.path.basename(exe_path) + ".load_image"]
    result1 = runIveiaCmd(cmd, pex_log, run_dir)
    if result1 != isp_utils.retVals.SUCCESS:
        logger.warning("Failed to clean after yourself, check out the {} log for details!".format(pex_log))

    pex_log.close()
    ap_log.close()

    return result

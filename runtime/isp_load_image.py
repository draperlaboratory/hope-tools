#!/usr/bin/env python3

import sys
import argparse
import subprocess
from struct import Struct
import logging
import os
import zlib
from pathlib import Path
from itertools import zip_longest

from elftools.elf.elffile import ELFFile
from elftools.elf.constants import SH_FLAGS

logger = logging.getLogger()

#
# Follows the format of load_image_t in load_image.h
#
load_segment_t = Struct('<II')
load_image_t = Struct('<IIIII')
flash_address_t = Struct('<III')

# aligns a value to 4 byte boundary
def align(v):
    return (v + 3) & ~3


class SectionElision:
    def __init__(self, section):
        self.write_segment = False
        sz = section["sh_size"]
        self.segment_size = align(sz)
        self.front_pad = 0
        self.pad = self.segment_size - sz
        self.end = section["sh_addr"] + self.segment_size

    def extend(self, start, elided):
        front_padding = start - self.end
        elided.front_pad = front_padding
        self.segment_size += elided.segment_size + front_padding
        self.end += elided.segment_size + front_padding


def auto_int(x):
    return int(x, 0)


def unique_section_name(s):
    return f"{s['sh_name']}{s['sh_addr']}"

def include_section(s):
    return ((s['sh_flags'] & SH_FLAGS.SHF_ALLOC) != 0) and (s['sh_type'] != 'SHT_NOBITS') and (s['sh_size'] != 0)


def generate_load_image(elf_binary, output_image, tag_info=None):
    with open(output_image, 'wb') as out:
        with open(elf_binary, 'rb') as f:
            ef = ELFFile(f)
            logger.debug("entry point at 0x{0:x}".format(ef.header["e_entry"]))
            entry_point = ef.header["e_entry"]
            out.write(load_image_t.pack(0xD04EA001, entry_point, 0, 0, 0))

            open_segment = None
            elision = None
            elision_dict = {}
            for s in sorted(ef.iter_sections(), key=lambda s: s["sh_addr"]):
                if include_section(s):
                    logger.debug("section {0} at 0x{1:x}, for 0x{2:x} bytes".format(s.name, s["sh_addr"], s["sh_size"]))
                    elision = SectionElision(s)
                    elision_dict[unique_section_name(s)] = elision
                    if open_segment is None:
                        open_segment = elision
                        open_segment.write_segment = True
                    else:
                        if s["sh_addr"] - open_segment.end > 16:
                            open_segment = elision
                            open_segment.write_segment = True
                        else:
                            open_segment.extend(s["sh_addr"], elision)

            segment_count = 0
            for s in sorted(ef.iter_sections(), key=lambda s: s["sh_addr"]):
                if include_section(s):
                    elision = elision_dict[unique_section_name(s)]
                    if elision.write_segment:
                        logger.debug("segment at 0x{0:x}, for 0x{1:x} bytes".format(s["sh_addr"], elision.segment_size))
                        out.write(load_segment_t.pack(s["sh_addr"], elision.segment_size))
                        segment_count = segment_count + 1
            for s in sorted(ef.iter_sections(), key=lambda s: s["sh_addr"]):
                if include_section(s):
                    elision = elision_dict[unique_section_name(s)]
                    size = s["sh_size"]
                    if elision.front_pad > 0:
                        pad = bytearray(elision.front_pad)
                        out.write(pad)
                    out.write(s.data())
                    if elision.pad != 0:
                        pad = bytearray(elision.pad)
                        out.write(pad)

        taginfo_bytes = []
        taginfo_offset = 0;

        if (tag_info):
            taginfo_offset = out.tell()
            taginfo_bytes = Path(tag_info).read_bytes()
            out.write(taginfo_bytes)
            if (len(taginfo_bytes) & 3 != 0):
                pad = bytearray(4 - (len(taginfo_bytes) & 3))
                out.write(pad)

        out.seek(0)
        out.write(load_image_t.pack(0xD04EA001,
                                    entry_point,
                                    segment_count,
                                    taginfo_offset,
                                    len(taginfo_bytes)))

def generate_tag_load_image(output_image, tag_info):
    with open(output_image, 'wb') as out:
        out.write(load_image_t.pack(0xD04EA001,
                                    0xffffffff,
                                    0xffffffff,
                                    0xffffffff,
                                    0xffffffff))

        taginfo_offset = out.tell()
        taginfo_bytes = Path(tag_info).read_bytes()
        out.write(taginfo_bytes)
        if (len(taginfo_bytes) & 3 != 0):
            pad = bytearray(4 - (len(taginfo_bytes) & 3))
            out.write(pad)

        out.seek(0)
        out.write(load_image_t.pack(0xD04EA001,
                                    0xffffffff,
                                    0xffffffff,
                                    taginfo_offset,
                                    len(taginfo_bytes)))


def generate_flash_init(output_image, input_images):
    out = open(output_image, 'wb')
    hdr = open(output_image + '.hdr', 'wb')
    pairs = [(int(addr, 16), name) for addr, name in input_images.items()]
    for p in pairs:
        fh = open(p[1], 'rb')
        rom_data = fh.read()
        fh.close()
        
        # pad the payload, otherwise we'll get CRC failures when we load it
        pad_len = 4 - (len(rom_data) % 4);
        if pad_len != 4:
            rom_data += '\0'*pad_len
            
        rom_bytes = bytearray(rom_data)
        
        crc = zlib.crc32(flash_address_t.pack(p[0], len(rom_bytes), 0))
        crc = zlib.crc32(rom_data, crc) & 0xffffffff
        hdr.write(flash_address_t.pack(p[0], len(rom_bytes), crc))
        out.write(flash_address_t.pack(p[0], len(rom_bytes), crc))
        out.write(rom_bytes)
    # indicate end of stream
    hdr.write(flash_address_t.pack(0xffffffff, 0, 0))
    hdr.close()
    out.write(flash_address_t.pack(0xffffffff, 0, 0))
    out.close()


def group_hex_chunks(iterable, n, fillvalue=None):
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


def generate_hex_dump(in_path, out_path, bit_width=64):
    byte_width = bit_width // 8

    infile = open(in_path, "rb")
    outfile = open(out_path, "w")

    for row in group_hex_chunks(infile.read(), byte_width, fillvalue=0):
        # Reverse because in Verilog most-significant bit of vectors is first.
        hex_row = ''.join('{:02x}'.format(b) for b in reversed(row))
        outfile.write(hex_row + '\n')

    infile.close()
    outfile.close()


def main():
    parser = argparse.ArgumentParser(description="Generate load image or flash images")
    parser.add_argument("--image_type", type=str,
    required=True, help=''' Generate load or flash image.
    ''')
    parser.add_argument("-o", "--out", type=str, required=True,
    help='''
    Output file.
    ''')
    parser.add_argument("--tag_info", type=str, help='''
    Taginfo file.
    ''')
    parser.add_argument("--kernel_address", type=str, help='''
    Hex address (0x format) for the kernel load image in the flash init.
    ''')
    parser.add_argument("--ap_address", type=str, help='''
    Hex address (0x format) for the application processor load image in the flash init.
    ''')
    parser.add_argument("input_files", metavar="Input File(s)", nargs='*',
    help="Input files to generate images from. Flash requires the kernel image first.")
    args = parser.parse_args()


    if args.image_type == "flash":
        flash_init_map = dict(zip([int(args.kernel_address, 16), int(args.ap_address, 16)], args.input_files))
        generate_flash_init(args.out, flash_init_map)
    elif args.image_type == "load":
        generate_load_image(args.input_files[0], args.out, args.tag_info)

if (__name__ == "__main__"):
    main()

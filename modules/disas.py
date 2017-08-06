"""The Ultimate Disassembler Module"""

# PYTHON STUFFS #######################################################

import capstone

from nemubot.exception import IMException
from nemubot.hooks import hook

from more import Response


# MODULE CORE #########################################################

ARCHITECTURES = {
    "arm": capstone.CS_ARCH_ARM,
    "arm64": capstone.CS_ARCH_ARM64,
    "mips": capstone.CS_ARCH_MIPS,
    "ppc": capstone.CS_ARCH_PPC,
    "sparc": capstone.CS_ARCH_SPARC,
    "sysz": capstone.CS_ARCH_SYSZ,
    "x86": capstone.CS_ARCH_X86,
    "xcore": capstone.CS_ARCH_XCORE,
}

MODES = {
    "arm": capstone.CS_MODE_ARM,
    "thumb": capstone.CS_MODE_THUMB,
    "mips32": capstone.CS_MODE_MIPS32,
    "mips64": capstone.CS_MODE_MIPS64,
    "mips32r6": capstone.CS_MODE_MIPS32R6,
    "16": capstone.CS_MODE_16,
    "32": capstone.CS_MODE_32,
    "64": capstone.CS_MODE_64,
    "le": capstone.CS_MODE_LITTLE_ENDIAN,
    "be": capstone.CS_MODE_BIG_ENDIAN,
    "micro": capstone.CS_MODE_MICRO,
    "mclass": capstone.CS_MODE_MCLASS,
    "v8": capstone.CS_MODE_V8,
    "v9": capstone.CS_MODE_V9,
}

# MODULE INTERFACE ####################################################

@hook.command("disas",
              help="Display assembly code",
              help_usage={"CODE": "Display assembly code corresponding to the given CODE"},
              keywords={
                  "arch=ARCH": "Specify the architecture of the code to disassemble (default: x86, choose between: %s)" % ', '.join(ARCHITECTURES.keys()),
                  "modes=MODE[,MODE]": "Specify hardware mode of the code to disassemble (default: 32, between: %s)" % ', '.join(MODES.keys()),
              })
def cmd_disas(msg):
    if not len(msg.args):
        raise IMException("please give me some code")

    # Determine the architecture
    if "arch" in msg.kwargs:
        if msg.kwargs["arch"] not in ARCHITECTURES:
            raise IMException("unknown architectures '%s'" % msg.kwargs["arch"])
        architecture = ARCHITECTURES[msg.kwargs["arch"]]
    else:
        architecture = capstone.CS_ARCH_X86

    # Determine hardware modes
    modes = 0
    if "modes" in msg.kwargs:
        for mode in msg.kwargs["modes"].split(','):
            if mode not in MODES:
                raise IMException("unknown mode '%s'" % mode)
        modes += MODES[mode]
    elif architecture == capstone.CS_ARCH_X86 or architecture == capstone.CS_ARCH_PPC:
        modes = capstone.CS_MODE_32
    elif architecture == capstone.CS_ARCH_ARM or architecture == capstone.CS_ARCH_ARM64:
        modes = capstone.CS_MODE_ARM
    elif architecture == capstone.CS_ARCH_MIPS:
        modes = capstone.CS_MODE_MIPS32

    # Get the code
    code = bytearray.fromhex(''.join([a.replace("0x", "") for a in msg.args]))

    # Setup capstone
    md = capstone.Cs(architecture, modes)

    res = Response(channel=msg.channel, nomore="No more instruction")

    for isn in md.disasm(code, 0x1000):
        res.append_message("%s %s" %(isn.mnemonic, isn.op_str), title="0x%x" % isn.address)

    return res

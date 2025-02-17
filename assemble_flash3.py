import argparse
import os

parser = argparse.ArgumentParser(description="Keitai FlashFX3.00 Assemble")
parser.add_argument("input")
parser.add_argument("output")

args = parser.parse_args()

os.makedirs(args.output, exist_ok=True)

MAGIC = b"\xCC\xDD\x44\x4C\x5F\x46\x53\x33\x2E\x30\x30\xFF\xFF\xFF\xFF\xFF"

array = {}
with open(args.input, "rb") as file:
    data = file.read(0x200)
    while len(data) > 0:
        if data[:0x10] == MAGIC:
            ld = int.from_bytes(data[0x18:0x1C], "little")
            data += file.read(ld - 0x200)
            if int.from_bytes(data[0x34:0x36], "little") != 0xFFFF:
                shift = int.from_bytes(data[0x36:0x38], "little")
                if data[shift + 2 : shift + 4] in (b"\xFF\x4F", b"\xFF\xCF"):
                    vs = int.from_bytes(data[shift : shift + 2], "little")
                    region = int.from_bytes(data[0x14:0x16], "little")
                    rst = int.from_bytes(data[0x20:0x24], "little")
                    rlg = int.from_bytes(data[0x24:0x28], "little")
                    array[region] = array.get(region, {})
                    array[region][rst] = array[region].get(rst, bytearray(rlg))
                    off = shift + 0x4
                    while data[off : off + 4] != b"\xFF\xFF\xFF\xFF":
                        v = data[off + 2] + (data[off + 3] << 8)
                        st = data[off + 1] * shift
                        ed = data[off] * shift
                        if v & 0x8000 and vs >= 3:
                            st += 256 * shift
                        if v & 0x4000:
                            ofs = (v & 0x3FFF) * shift
                            array[region][rst][ofs : ofs + ed] = data[st : st + ed]
                        off += 4
        data = file.read(0x200)

for k, v in array.items():
    with open(os.path.join(args.output, "region_%04d.bin" % k), "wb") as file:
        buffer = bytearray()
        for e, s in sorted(v.items()):
            if len(buffer) < e:
                buffer += bytes(e - len(buffer))
            buffer[e : e + len(s)] = s
        file.write(buffer)

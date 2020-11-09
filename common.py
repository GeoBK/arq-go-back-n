TERMINATOR = b'000000000000000000000000000000000000000000000000000000000000000000000000'
def calculateChecksum(payload):
    res = 0
    for c in payload:
        res = res ^ ord(c)
    return res.to_bytes(2, byteorder='big')

import Crypto.Cipher.DES

def DES(key):
    key = key56_to_key64(str_to_key56(key))
    return Crypto.Cipher.DES.new(key, Crypto.Cipher.DES.MODE_ECB)


def str_to_key56(key_str):
    ""
    key_56 = key_str.ljust(7, b'\0')[:7]
    return key_56

def key56_to_key64(key_56):
    ""
    key = bytearray(8)
    key[0] = key_56[0];
    key[1] = ((key_56[0] << 7) & 0xFF) | (key_56[1] >> 1);
    key[2] = ((key_56[1] << 6) & 0xFF) | (key_56[2] >> 2);
    key[3] = ((key_56[2] << 5) & 0xFF) | (key_56[3] >> 3);
    key[4] = ((key_56[3] << 4) & 0xFF) | (key_56[4] >> 4);
    key[5] = ((key_56[4] << 3) & 0xFF) | (key_56[5] >> 5);
    key[6] = ((key_56[5] << 2) & 0xFF) | (key_56[6] >> 6);
    key[7] =  (key_56[6] << 1) & 0xFF;
    key = set_key_odd_parity(key)
    return key

def set_key_odd_parity(key):
    ""
    for i in range(len(key)):
        for k in range(7):
            bit = 0
            t = key[i] >> k
            bit = (t ^ bit) & 0x1
        key[i] = (key[i] & 0xFE) | bit
    return key

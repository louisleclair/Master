# Some utility functions 
def bytes_to_nibbles(m):
    m_nibbles = []
    for b in m:
        m_nibbles.append((b >> 4) & 0xf)
        m_nibbles.append(b & 0x0f)
    return m_nibbles

def nibbles_to_byte_arr(nb_arr):
    byte_arr = []
    for i in range(0, len(nb_arr), 2):
        b_high = nb_arr[i]
        b_low = nb_arr[i+1]
        byte_arr.append((b_high << 4) ^ b_low)
    return byte_arr

# Print int array in hexadecimal
def print_hex(arr):
    print([hex(i) for i in arr])

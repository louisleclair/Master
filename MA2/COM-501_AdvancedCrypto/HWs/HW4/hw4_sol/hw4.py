import random
import os

from utils import *

# Put parameters in sboxes.py
from sboxes import *

P = [6, 11, 0, 1, 2, 3, 4, 5, 7, 8, 9, 10]
P_inv = [2, 3, 4, 5, 6, 7, 0, 8, 9, 10, 11, 1]


# Apply a permutation per on an integer x
def p_i(per, x):
    x_b = '{0:04b}'.format(x)
    res_b = [x_b[i] for i in per]
    res_int = 0
    for b in res_b:
        res_int = (res_int << 1) | int(b)
    return res_int

# Bit permutation of the cipher
def p1(x): return p_i([2, 0, 1, 3], x)

# Inverse permutation
def p1_inv(x): return p_i([1, 2, 0, 3], x)

# Permutation applied on a byte (0xb1b2 -> p1(0xb1)p1(0xb2))
def p1_8(x): 
    b_h = (x >> 4) & 0xf
    b_l = x & 0x0f
    b_h = p1(b_h)
    b_l = p1(b_l)
    return (b_h << 4) ^ b_l

# Compute difference table 
def compute_df(sbox):
    n = len(sbox)
    df_table = [[0 for i in range(n)] for j in range(n)]
    for a in range(n):
        for x in range(n):
            b = sbox[x ^ a] ^ sbox[x]
            df_table[a][b] += 1
    return df_table 

    
# Given a plaintext m, generate a pt m' s.t. m'[i] = m[i] + diff
def gen_diff_pt(m, i, diff):
    m_arr = [int(b) for b in m]
    m_diff_arr = [int(b) for b in m]
    m_diff_arr[i] =  m_arr[i] ^ diff
    return bytes(m_diff_arr)

# Invert an sbox on a value y (return x s.t. S(x) = y)
def sbox_inv(S, y):
    x = -1
    for i in range(len(S)):
        if S[i] == y:
            x = i
            break
    return x

# Decryption function
def decrypt(c, k):
    n_round = 5

    keys = [encrypt(k, K_S, True)]
    for r in range(1, n_round+1):
        keys.append(encrypt(keys[r-1], K_S, True))
    k_byte_arr = list(keys[n_round])
    state_byte_arr = [int(b) for b in c]
    # Final xor inversion
    state_byte_arr = [b_m ^ k_m for (b_m, k_m) in zip(state_byte_arr, k_byte_arr)]
    state_byte_arr = [sbox_inv(S_fin, b) for b in state_byte_arr]
    for r in range(n_round):
        state_nb_arr = bytes_to_nibbles(state_byte_arr)
        state_nb_arr = [p1_inv(state_nb_arr[P_inv[i]]) for i in range(len(state_nb_arr))]
        state_byte_arr = nibbles_to_byte_arr(state_nb_arr)
         # S-box
        state_byte_arr[0] = sbox_inv(S_1, state_byte_arr[0])
        state_byte_arr[1] = sbox_inv(S_2, state_byte_arr[1])
        state_byte_arr[2] = sbox_inv(S_3, state_byte_arr[2])
        state_byte_arr[3] = sbox_inv(S_4, state_byte_arr[3])
        state_byte_arr[4] = sbox_inv(S_fin, state_byte_arr[4])
        state_byte_arr[5] = sbox_inv(S_fin, state_byte_arr[5])
        k_byte_arr = list(keys[n_round-r-1])
        state_byte_arr = [b_m ^ k_m for (b_m, k_m) in zip(state_byte_arr, k_byte_arr)]

    return bytes(state_byte_arr)

# Encryption function
def encrypt(m, k, key_schedule=False, key_ks=None):
    global K_S
    if key_ks:
        K_S = key_ks
    n_round = 5
    state_byte_arr = [int(b) for b in m]
    if not key_schedule:
        keys = [encrypt(k, K_S, True)]
        for r in range(1, n_round+1):
            keys.append(encrypt(keys[r-1], K_S, True))
    else:
        keys = [k]*(n_round+1)
    for r in range(n_round):
        k_byte_arr = list(keys[r])

        # xor with key
        state_byte_arr = [b_m ^ k_m for (b_m, k_m) in zip(state_byte_arr, k_byte_arr)]
        # S-box
        state_byte_arr[0] = S_1[state_byte_arr[0]]
        state_byte_arr[1] = S_2[state_byte_arr[1]]
        state_byte_arr[2] = S_3[state_byte_arr[2]]
        state_byte_arr[3] = S_4[state_byte_arr[3]]
        state_byte_arr[4] = S_fin[state_byte_arr[4]]
        state_byte_arr[5] = S_fin[state_byte_arr[5]]

        # Permute    
        state_nb_arr = bytes_to_nibbles(state_byte_arr)
        state_nb_arr = [p1(state_nb_arr[P[i]]) for i in range(len(state_nb_arr))]
        state_byte_arr = nibbles_to_byte_arr(state_nb_arr)
    # Final S-box
    state_byte_arr = [S_fin[b] for b in state_byte_arr]
    # Final xor
    k_byte_arr = list(keys[n_round])
    state_byte_arr = [b_m ^ k_m for (b_m, k_m) in zip(state_byte_arr, k_byte_arr)]
    return bytes(state_byte_arr)

# Recover key byte j
def recover_key_byte(i, diff, j, out, mask=False):
    cnt = [0 for i in range(256)]
    mask_b = 0xff if not mask else 0xf0

    # Use more pairs for first byte
    nb_t = 500 if mask else 300
    for t in range(nb_t):
        m = os.urandom(6)
        ct1 = encrypt(m,K)
        m2 = gen_diff_pt(m, i, diff)
        ct2 = encrypt(m2, K)
        
        for k_try in range(256):
            a = sbox_inv(S_fin, ct1[j] ^ k_try)
            b = sbox_inv(S_fin, ct2[j] ^ k_try)
            if (a^b) & mask_b == out:
                cnt[k_try] += 1
    max_k = -1
    max_i = -1
    for i in range(len(cnt)):
        #if j == 0:
        #    print(hex(i), cnt[i])
        if cnt[i] > max_k:
            max_k = cnt[i]
            max_i = i
    return max_i

# Given last round key, recover original key
def decrypt_key(c, k):
    n_round = 5
    keys = [k]*(n_round+1)
    k_byte_arr = list(keys[n_round])
    state_byte_arr = [int(b) for b in c]
    # Final xor inversion
    state_byte_arr = [b_m ^ k_m for (b_m, k_m) in zip(state_byte_arr, k_byte_arr)]
    state_byte_arr = [sbox_inv(S_fin, b) for b in state_byte_arr]
    for r in range(n_round):
        state_nb_arr = bytes_to_nibbles(state_byte_arr)
        state_nb_arr = [p1_inv(state_nb_arr[P_inv[i]]) for i in range(len(state_nb_arr))]
        state_byte_arr = nibbles_to_byte_arr(state_nb_arr)
         # S-box
        state_byte_arr[0] = sbox_inv(S_1, state_byte_arr[0])
        state_byte_arr[1] = sbox_inv(S_2, state_byte_arr[1])
        state_byte_arr[2] = sbox_inv(S_3, state_byte_arr[2])
        state_byte_arr[3] = sbox_inv(S_4, state_byte_arr[3])
        state_byte_arr[4] = sbox_inv(S_fin, state_byte_arr[4])
        state_byte_arr[5] = sbox_inv(S_fin, state_byte_arr[5])
        
        k_byte_arr = list(keys[n_round-r-1])
        state_byte_arr = [b_m ^ k_m for (b_m, k_m) in zip(state_byte_arr, k_byte_arr)]
    return bytes(state_byte_arr)

# Recover key
def recover_key():
    #print_hex([int(b) for b in key])
    key_arr = [0 for _ in range(6)]
    key_arr[1] = recover_key_byte(0, 0xa0, 1, p1_8(0x1b))
    key_arr[4] = recover_key_byte(0, 0xa0, 4, 0x01) # or any 0x0?
    key_arr[5] = recover_key_byte(0, 0xa0, 5, 0x10) # or 0x?0
    key_arr[2] = recover_key_byte(1, p1_8(0x1b), 2, p1_8(0x4f))
    key_arr[3] = recover_key_byte(2, p1_8(0x4f), 3, p1_8(0xea))
    key_arr[0] = recover_key_byte(3, p1_8(0xea), 0, 0xa0, mask=True)
    key_ct = bytes(key_arr)
    print("Last round key recovered:", key_ct)
    for _ in range(5+1):
        key_ct = decrypt_key(key_ct, K_S)
    return key_ct

if __name__ == '__main__':
    print(compute_df(S_1)[0xa0][0x1b]/256)
    print(compute_df(S_2)[p1_8(0x1b)][0x4f]/256)
    print(compute_df(S_3)[p1_8(0x4f)][0xea]/256)
    print(compute_df(S_4)[p1_8(0xea)][0x66]/256)
    m = os.urandom(6)
    ct = encrypt(m,K)
    m1_dec = decrypt(ct, K)
    assert m1_dec == m
    print('pt_2', decrypt(ct_2, K))
    print('ct_1', encrypt(pt_1, K))
    n_round = 5
    keys = [encrypt(K, K_S, True)]
    for r in range(1, n_round+1):
            keys.append(encrypt(keys[r-1], K_S, True))
    print("Last round key:", keys[n_round])
    k_r = recover_key()
    print("Key recovered:", k_r)
    print("Key:", K)
    assert k_r == K 


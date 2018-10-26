# This file was converted from the original C source:
# 	lzhuf.c
# 	written by Haruyasu Yoshizaki 11/20/1988
# 	some minor changes 4/6/1989
# 	comments translated by Haruhiko Okumura 4/7/1989

# LZHUF.C (c)1989 by Haruyasu Yoshizaki, Haruhiko Okumura, and Kenji Rikitake.
# All rights reserved. Permission granted for non-commercial use.

# Huffman coding

N = 4096  # buffer size
F = 60  # lookahead buffer size
THRESHOLD = 2

N_CHAR = 256 - THRESHOLD + F  # kinds of characters (character code = 0..N_CHAR-1)
T = N_CHAR * 2 - 1  # size of table
R = T - 1  # position of root
MAX_FREQ = 0x4000  # updates tree when the root frequency comes to this value
N_MASK = N - 1


def decompress_buffer(buffer: bytearray, textsize: int) -> bytearray:
    buffer_pos = 0
    buffer_size = len(buffer)

    def getcz():
        nonlocal buffer_pos, buffer_size
        if buffer_pos == buffer_size:
            return 0
        result = buffer[buffer_pos]
        buffer_pos += 1
        return result

    getbuf = 0
    getlen = 0

    def GetBit() -> int:  # get one bit
        nonlocal getbuf, getlen
        while getlen <= 8:
            i = getcz()
            getbuf |= i << (8 - getlen)
            getlen += 8
        i = getbuf
        getbuf = (getbuf << 1) & 0xFFFFFFFF
        getlen -= 1
        return (i >> 15) & 1

    def GetByte() -> int:  # get one byte
        nonlocal getbuf, getlen
        while getlen <= 8:
            i = getcz()
            getbuf |= i << (8 - getlen)
            getlen += 8
        i = getbuf
        getbuf = (getbuf << 8) & 0xFFFFFFFF
        getlen -= 8
        return (i & 0xff00) >> 8

    result = bytearray()

    freq = [0] * (T + 1)  # frequency table

    prnt = [0] * (T + N_CHAR)  # pointers to parent nodes, except for the
    # elements [T..T + N_CHAR - 1] which are used to get
    # the positions of leaves corresponding to the codes

    son = [0] * T  # pointers to child nodes (son[], son[] + 1)
    text_buf = [0] * (N + F - 1)

    def StartHuff():  # initialization of tree
        for i in range(N_CHAR):
            freq[i] = 1
            son[i] = i + T
            prnt[i + T] = i

        i, j = 0, N_CHAR
        while j <= R:
            freq[j] = freq[i] + freq[i + 1]
            son[j] = i
            prnt[i] = prnt[i + 1] = j
            i += 2
            j += 1
        freq[T] = 0xffff
        prnt[R] = 0

    def reconst():  # reconstruction of tree
        # collect leaf nodes in the first half of the table
        # and replace the freq by (freq + 1) / 2.
        j = 0
        for i in range(T):
            if son[i] >= T:
                freq[j] = (freq[i] + 1) // 2
                son[j] = son[i]
                j += 1

        # begin constructing tree by connecting sons
        i, j = 0, N_CHAR
        while j < T:
            k = i + 1
            f = freq[j] = freq[i] + freq[k]

            k = j - 1
            while f < freq[k]:
                k -= 1
            k += 1

            for l in range(j - k):
                t = j - l
                s = t - 1
                freq[t] = freq[s]
                son[t] = son[s]

            freq[k] = f
            son[k] = i
            i += 2
            j += 1

        # connect prnt
        for i in range(T):
            k = son[i]
            if k >= T:
                prnt[k] = i
            else:
                prnt[k] = prnt[k + 1] = i

    def update(c: int):  # increment frequency of given code by one, and update tree
        if freq[R] == MAX_FREQ:
            reconst()

        c = prnt[c + T]
        while True:
            k = freq[c] + 1
            freq[c] = k

            # if the order is disturbed, exchange nodes
            l = c + 1
            if k > freq[l]:
                while k > freq[l + 1]:
                    l += 1
                freq[c] = freq[l]
                freq[l] = k

                i = son[c]
                prnt[i] = l
                if i < T:
                    prnt[i + 1] = l

                j = son[l]
                son[l] = i

                prnt[j] = c
                if j < T:
                    prnt[j + 1] = c
                son[c] = j

                c = l
            c = prnt[c]
            if c == 0:  # repeat up to root
                break

    def DecodeChar() -> int:
        c = son[R]

        # travel from root to leaf,
        # choosing the smaller child node (son[]) if the read bit is 0,
        # the bigger (son[]+1} if 1
        while c < T:
            c += GetBit()
            c = son[c]
        c -= T
        update(c)
        return c

    def DecodePosition() -> int:
        # recover upper 6 bits from table
        i = GetByte()
        c = D_CODE[i] << 6
        j = D_LEN[i]

        # read lower 6 bits verbatim
        j -= 2
        while j:
            j -= 1
            i = (i << 1) + GetBit()
        return c | (i & 0x3f)

    StartHuff()

    # Decode
    for i in range(N - F):
        text_buf[i] = 32
    r = N - F
    count = 0
    while count < textsize:
        c = DecodeChar()
        if c < 256:
            result.append(c)
            text_buf[r] = c
            r = (r + 1) & N_MASK
            count += 1
        else:
            i = (r - DecodePosition() - 1) & N_MASK
            j = c - 255 + THRESHOLD
            for k in range(j):
                c = text_buf[(i + k) & N_MASK]
                result.append(c)
                text_buf[r] = c
                r = (r + 1) & N_MASK
                count += 1

    return result


# table for encoding and decoding the upper 6 bits of position

D_CODE = tuple(code - 48
               for code in b'\
0000000000000000000000000000000011111111111111112222222222222222\
3333333333333333444444445555555566666666777777778888888899999999\
::::::::;;;;;;;;<<<<====>>>>????@@@@AAAABBBBCCCCDDDDEEEEFFFFGGGG\
HHIIJJKKLLMMNNOOPPQQRRSSTTUUVVWWXXYYZZ[[\\\\]]^^__`abcdefghijklmno\
')

D_LEN = tuple(code - 48
              for code in b'\
3333333333333333333333333333333344444444444444444444444444444444\
4444444444444444555555555555555555555555555555555555555555555555\
5555555555555555666666666666666666666666666666666666666666666666\
7777777777777777777777777777777777777777777777778888888888888888\
')

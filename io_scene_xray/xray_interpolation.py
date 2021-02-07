def incoming(k1v, k1t, k2v, k2t, k2ts, k2c, k2b, n2v, n2t):
    a = (1.0 - k2ts) * (1.0 - k2c) * (1.0 + k2b)
    b = (1.0 - k2ts) * (1.0 + k2c) * (1.0 - k2b)
    d = k2v - k1v
    if not n2t is None:
        t = (k2t - k1t) / (n2t - k1t)
        in_ = t * (b * (n2v - k2v) + a * d)
    else:
        in_ = 0.5 * (a + b) * d
    return in_


def outgoing(k1v, k1t, k1ts, k1c, k1b, k2v, k2t, p1v, p1t):
    a = (1.0 - k1ts) * (1.0 + k1c) * (1.0 + k1b)
    b = (1.0 - k1ts) * (1.0 - k1c) * (1.0 - k1b)
    d = k2v - k1v
    if not p1t is None:
        t = (k2t - k1t) / (k2t - p1t)
        out = t * (a * (k1v - p1v) + b * d)
    else:
        out = 0.5 * (a + b) * d
    return out


def hermite(t):    # t - time
   t2 = t * t    # time square
   t3 = t * t2    # time cubic
   h2 = 3.0 * t2 - t3 - t3    # hermite basis 2
   h1 = 1.0 - h2    # hermite basis 1
   h4 = t3 - t2    # hermite basis 4
   h3 = h4 - t2 + t    # hermite basis 3
   return h1, h2, h3, h4


def evaluate_tcb(
        k1t, k1v, k1ts, k1c, k1b,
        k2t, k2v, k2ts, k2c, k2b,
        p1t, p1v, n2t, n2v, t
    ):

    # k1t - key 1 time
    # k1v - key 1 value
    # k1ts - key 1 tension
    # k1c - key 1 continuity
    # k1b - key 1 bias

    # k2t - key 2 time
    # k2v - key 2 value
    # k2ts - key 2 tension
    # k2c - key 2 continuity
    # k2b - key 2 bias

    # p1v - key 1 preview key value
    # p1t - key 1 preview key time

    # n2v - key 2 next key value
    # n2t - key 2 next key time

    # t - time

    if t == k1t:
        return k1v
    elif t == k2t:
        return k2v

    tn = (t - k1t) / (k2t - k1t)    # normalized time in [0, 1]
    out = outgoing(k1v, k1t, k1ts, k1c, k1b, k2v, k2t, p1v, p1t)
    in_ = incoming(k1v, k1t, k2v, k2t, k2ts, k2c, k2b, n2v, n2t)
    h1, h2, h3, h4 = hermite(tn)    # hermite basics
    return h1 * k1v + h2 * k2v + h3 * out + h4 * in_

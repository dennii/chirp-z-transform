# Implements the Chirp Z-Transform and its inverse, as described in
#   V. Sukhoy and A. Stoytchev, Generalizing the inverse FFT off the unit
#   circle. Sci Rep 9, 14443 (2019).
#   https://doi.org/10.1038/s41598-019-50234-9
# (While a fast algorithm for the Chirp Z-Transform has been known for 50 years,
# a fast algorithm for the inverse was only recently discovered (By Sukhoy and
# Stoychev).

import numpy as np
import scipy.fftpack

def circulant_multiply(c, x):
    # Compute the product y = Gx of a circulant matrix G and a vector x, where G is generated by its first column
    #     c = (c[0], c[1], ..., c[n-1]).
    if len(x) != len(c):
        raise Exception("should have len(x) equal to len(c), but instead len(x) = %d, len(c) = %d" % (len(x), len(c)))
    
    return scipy.fftpack.ifft( scipy.fftpack.fft(c) * scipy.fftpack.fft(x) )

def toeplitz_multiply_e(r, c, x):
    # Compute the product y = Tx of a Toeplitz matrix T and a vector x, where T is specified by its first row
    #     r = (r[0], r[1], r[2], ..., r[N-1])
    # and its first column
    #     c = (c[0], c[1], c[2], ..., c[M-1]),
    # where r[0] = c[0].
    N = len(r)
    M = len(c)
    
    if r[0] != c[0]:
        raise Exception("should have r[0] == c[0], but r[0] = %f and c[0] = %f" % (r[0], c[0]))
    if len(x) != len(r):
        raise Exception("should have len(x) equal to len(r), but instead len(x) = %d, len(r) = %d" % (len(x), len(r)))
    
    n = (2 ** np.ceil(np.log2(M+N-1))).astype(np.int64)
    
    # Form an array C by concatenating c, n - (M + N - 1) zeros, and the reverse of the last N-1 elements of r, ie.
    #     C = (c[0], c[1], ..., c[M-1], 0,..., 0, r[N-1], ..., r[2], r[1]).
    C = np.concatenate(( np.pad(c, (0, n - (M + N - 1)), 'constant'), np.flip(r[1:]) ))
    
    X = np.pad(x, (0, n-N), 'constant')
    Y = circulant_multiply(C, X)
    
    # The result is the first M elements of C * X.    
    return Y[:M]

def czt(x, M, W, A):
    # Computes the Chirp Z-transform of a vector x.
    #
    # To recover a Fourier transform, take
    #   M = len(x), W = exp(2pi/M * i), A = 1.
    N = len(x)
    X = np.empty(N) * 1.0j
    r = np.empty(N) * 1.0j
    c = np.empty(M) * 1.0j
    
    for k in range(N):
        X[k] = np.power(W, k**2/2.0) * np.power(A*1.0, -k) * x[k]
        r[k] = np.power(W, -k**2/2.0)
    
    for k in range(M):
        c[k] = np.power(W, -k**2/2)
    
    X = toeplitz_multiply_e(r, c, X) # len(X) == M
    for k in range(M):
        X[k] = np.power(W, k**2/2) * X[k]
    return X

def iczt(X, N, W, A):
    # Compute the inverse Chirp Z-transform of a vector X.
    M = len(X)
    if M != N:
        raise Exception("should have len(X) equal to N, but instead len(X) = %d, N = %d" % (len(X), N))

    n = N
    x = np.empty(n) * 1.0j
    for k in range(n):
        x[k] = np.power(W, -k**2/2) * X[k]
    
    p = np.empty(n) * 1.0j
    p[0] = 1
    for k in range(1, n):
        p[k] = p[k-1] * (np.power(W, k)-1)
    
    u = np.empty(n) * 1.0j
    for k in range(n):
        u[k] = (-1)**k * ( np.power(W, 0.5 * (2*k**2 - (2*n-1)*k + n*(n-1))) / (p[n - k - 1] * p[k]) )
    
    z = np.zeros(n)
    uhat = np.pad(np.flip(u[1:]), (1, 0), 'constant')
    util = np.pad(u[:1], (0, n-1), 'constant')
    
    xp  = toeplitz_multiply_e(z, uhat, toeplitz_multiply_e(uhat, z, x))
    xpp = toeplitz_multiply_e(util, u, toeplitz_multiply_e(u, util, x))
    
    for k in range(n):
        x[k] = (xpp[k] - xp[k]) / u[0]
    
    for k in range(n):
        x[k] = np.power(A, k) * np.power(W, -k**2/2) * x[k]
    
    return x

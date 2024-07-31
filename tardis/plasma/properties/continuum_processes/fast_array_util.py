# It is currently not possible to use scipy.integrate.cumulative_trapezoid in
# numba. So here is my own implementation.
from tardis.transport.montecarlo import njit_dict


import numpy as np
from numba import njit, prange


@njit(**njit_dict)
def __faster_cumsum(arr):
    """Faster alternative for numpy's cumsum."""
    result = np.empty_like(arr)
    result[0] = arr[0]
    for i in range(1, len(arr)):
        result[i] = result[i - 1] + arr[i]
    return result


@njit(**njit_dict)
def __faster_diff(arr):
    """Calculates x diffs."""
    s = arr.shape[0]
    result = np.empty((s - 1,))
    for i in prange(0, s - 1):
        result[i] = arr[i + 1] - arr[i]
    return result


@njit(**njit_dict)
def __faster_add(arr):
    """Calculates trapezoid's total parallel length."""
    s = arr.shape[0]
    result = np.empty((s - 1,))
    for i in prange(0, s - 1):
        result[i] = arr[i + 1] + arr[i]
    return result


@njit(**njit_dict)
def numba_cumulative_trapezoid(f, x):
    """
    Cumulatively integrate f(x) using the composite trapezoidal rule.

    Parameters
    ----------
    f : numpy.ndarray, dtype float
        Input array to integrate.
    x : numpy.ndarray, dtype float
        The coordinate to integrate along.

    Returns
    -------
    numpy.ndarray, dtype float
        The result of cumulative integration of f along x
    """                  
    integ = __faster_cumsum(__faster_diff(x) * __faster_add(f) / 2.0)
    return integ / integ[-1]


@njit(**njit_dict)
def cumulative_integrate_array_by_blocks(f, x, block_references):
    """
    Cumulatively integrate a function over blocks.

    This function cumulatively integrates a function `f` defined at
    locations `x` over blocks given in `block_references`.

    Parameters
    ----------
    f : numpy.ndarray, dtype float
        Input array to integrate. Shape is (N_freq, N_shells), where
        N_freq is the number of frequency values and N_shells is the number
        of computational shells.
    x : numpy.ndarray, dtype float
        The sample points corresponding to the `f` values. Shape is (N_freq,).
    block_references : numpy.ndarray, dtype int
        The start indices of the blocks to be integrated. Shape is (N_blocks,).

    Returns
    -------
    numpy.ndarray, dtype float
        Array with cumulatively integrated values. Shape is (N_freq, N_shells)
        same as f.
    """
    n_rows = len(block_references) - 1
    integrated = np.zeros_like(f)
    for i in prange(f.shape[1]):  # columns
        # TODO: Avoid this loop through vectorization of cumulative_trapezoid
        for j in prange(n_rows):  # rows
            start = block_references[j]
            stop = block_references[j + 1]
            integrated[start + 1 : stop, i] = numba_cumulative_trapezoid(
                f[start:stop, i], x[start:stop]
            )
    return integrated

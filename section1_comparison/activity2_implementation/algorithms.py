"""Bubble Sort (iterative) and Quicksort (recursive, median-of-three pivot).

Both sort the list in place and only compare and swap, so they accept ints and floats.

Quicksort takes an optional `trace` callback. The animation runs this same function
and replays the events, so what is drawn is what the algorithm did. Events:
    ("range", lo, hi)                    subarray being partitioned
    ("candidates", lo, mid, hi)          the three median-of-three candidates
    ("compare_median", x, y)             comparison between two candidates
    ("pivot", index)                     chosen pivot
    ("compare", index, pointer)          a[index] compared with the pivot; pointer is "i" or "j"
    ("swap", i, j)                       a[i] and a[j] exchanged
    ("partition", lo, j, i, hi)          partition finished: a[lo..j] <= pivot <= a[i..hi]
    ("sorted", first, last)              positions first..last are in their final place
"""


def bubble_sort(a):
    for end in range(len(a) - 1, 0, -1):
        swapped = False
        for i in range(end):
            if a[i] > a[i + 1]:
                a[i], a[i + 1] = a[i + 1], a[i]
                swapped = True
        if not swapped:
            return


def _less(a, x, y, trace):
    if trace:
        trace("compare_median", x, y)
    return a[x] < a[y]


def median_of_three(a, lo, hi, trace=None):
    """Return the index, among lo, mid and hi, holding the median of those three values."""
    mid = (lo + hi) // 2
    if trace:
        trace("candidates", lo, mid, hi)
    if _less(a, lo, mid, trace):
        if _less(a, mid, hi, trace):
            return mid
        return hi if _less(a, lo, hi, trace) else lo
    if _less(a, lo, hi, trace):
        return lo
    return hi if _less(a, mid, hi, trace) else mid


def quicksort(a, trace=None):
    _quicksort(a, 0, len(a) - 1, trace)


def _quicksort(a, lo, hi, trace):
    if lo >= hi:
        if trace and lo == hi:
            trace("sorted", lo, lo)
        return
    if trace:
        trace("range", lo, hi)
    pivot_index = median_of_three(a, lo, hi, trace)
    pivot = a[pivot_index]
    if trace:
        trace("pivot", pivot_index)

    i, j = lo, hi
    while i <= j:
        # Comparison events are emitted after each scan, not inside it, so the timed
        # path (trace=None) keeps its inner loops free of any tracing check.
        start = i
        while a[i] < pivot:
            i += 1
        if trace:
            for k in range(start, i + 1):
                trace("compare", k, "i")
        start = j
        while a[j] > pivot:
            j -= 1
        if trace:
            for k in range(start, j - 1, -1):
                trace("compare", k, "j")
        if i <= j:
            if i < j:
                a[i], a[j] = a[j], a[i]
                if trace:
                    trace("swap", i, j)
            i += 1
            j -= 1

    if trace:
        trace("partition", lo, j, i, hi)
        # Anything strictly between j and i equals the pivot and is already in place.
        if j + 1 < i:
            trace("sorted", j + 1, i - 1)
    _quicksort(a, lo, j, trace)
    _quicksort(a, i, hi, trace)

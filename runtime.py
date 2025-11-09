import ctypes

# Handle-based runtime
_next_handle = 1
_handles = {}

def _new_handle(obj):
    global _next_handle
    h = _next_handle
    _next_handle += 1
    _handles[h] = obj
    return h

# ----- Array / String Creation -----
def rt_new_array():
    return _new_handle([])

def rt_new_string(c):
    # c is Python string
    return _new_handle(str(c))

# ----- Array Ops -----
def rt_push(h, v):
    _handles[h].append(int(v))
    return 0

def rt_pop(h):
    arr = _handles[h]
    if not arr:
        return 0
    return int(arr.pop())

def rt_length(h):
    return len(_handles[h])

def rt_clear(h):
    _handles[h].clear()
    return 0

def rt_contains(h, v):
    return 1 if int(v) in _handles[h] else 0

def rt_sort(h):
    _handles[h].sort()
    return h

def rt_sum(h):
    return sum(_handles[h])

# array index get/set
def rt_get(h, idx):
    return int(_handles[h][idx])

def rt_set(h, idx, val):
    _handles[h][idx] = int(val)
    return 0

# ----- Math / Logic -----
def rt_isPrime(n):
    n = int(n)
    if n < 2: return 0
    for i in range(2, int(n**0.5)+1):
        if n % i == 0:
            return 0
    return 1

# ----- IO -----
def rt_print_int(x):
    print(int(x))
    return 0

def rt_print_str(h):
    s = _handles.get(h, "")
    print(str(s))
    return 0

def rt_input(prompt_handle):
    prompt = _handles.get(prompt_handle, "")
    s = input(str(prompt))
    return _new_handle(s)

# ----- C Mappings -----
def _mk_cfunc(pyfunc, restype=ctypes.c_longlong, argtypes=None):
    if argtypes is None:
        argtypes = []
    return ctypes.CFUNCTYPE(restype, *argtypes)(pyfunc)

EXPORTED = {
    "rt_new_array": _mk_cfunc(lambda: rt_new_array(), ctypes.c_longlong, []),
    "rt_new_string": _mk_cfunc(lambda: rt_new_string(""), ctypes.c_longlong, []),  # placeholder
    "rt_push": _mk_cfunc(lambda a,b: rt_push(a,b), ctypes.c_longlong, [ctypes.c_longlong, ctypes.c_longlong]),
    "rt_pop": _mk_cfunc(lambda a: rt_pop(a), ctypes.c_longlong, [ctypes.c_longlong]),
    "rt_length": _mk_cfunc(lambda a: rt_length(a), ctypes.c_longlong, [ctypes.c_longlong]),
    "rt_clear": _mk_cfunc(lambda a: rt_clear(a), ctypes.c_longlong, [ctypes.c_longlong]),
    "rt_contains": _mk_cfunc(lambda a,b: rt_contains(a,b), ctypes.c_longlong, [ctypes.c_longlong, ctypes.c_longlong]),
    "rt_sort": _mk_cfunc(lambda a: rt_sort(a), ctypes.c_longlong, [ctypes.c_longlong]),
    "rt_sum": _mk_cfunc(lambda a: rt_sum(a), ctypes.c_longlong, [ctypes.c_longlong]),
    "rt_get": _mk_cfunc(lambda a,b: rt_get(a,b), ctypes.c_longlong, [ctypes.c_longlong, ctypes.c_longlong]),
    "rt_set": _mk_cfunc(lambda a,b,c: rt_set(a,b,c), ctypes.c_longlong, [ctypes.c_longlong, ctypes.c_longlong, ctypes.c_longlong]),
    "rt_isPrime": _mk_cfunc(lambda n: rt_isPrime(n), ctypes.c_longlong, [ctypes.c_longlong]),
    "rt_print_int": _mk_cfunc(lambda x: rt_print_int(x), ctypes.c_longlong, [ctypes.c_longlong]),
    "rt_print_str": _mk_cfunc(lambda h: rt_print_str(h), ctypes.c_longlong, [ctypes.c_longlong]),
    "rt_input": _mk_cfunc(lambda ph: rt_input(ph), ctypes.c_longlong, [ctypes.c_longlong]),
}

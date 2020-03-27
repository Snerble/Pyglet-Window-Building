import time
import threading
import asyncio

LIN = lambda x:x
EXP = lambda x:x**2
SQRT = lambda x:x**0.5

GIBIBYTE = 1073741820
MEBIBYTE = 1048576
KIBIBYTE = 1024

recorded_delays = list()
custom_delays = dict()
transitionCache = dict()

def cacheTransition(id, value): transitionCache[id] = value
def getTransition(id, default): return transitionCache[id] if id in transitionCache else default

transitions = dict()
def transition(id, duration, value, mod=LIN, stage=-1):
    id = str(id)
    if ((stage >= 0 and (duration == 0 or not id in transitions or not transitions[id][2] == stage)) or
       (stage < 0 and (duration == 0 or not id in transitions or not transitions[id][1] == value))):
        transitions[id] = (time.perf_counter()*1000+duration, value, stage)
        nv = getTransition(id+'#MEM', value)
        cacheTransition(id,nv)
        # return nv
    if duration == 0:
        return value

    v = transitions[id]
    x = constrain(time.perf_counter()*1000,0,v[0])
    t = constrain(mod(abs(1 - (v[0] - x)/duration)), 0, 1)
    dv = value - getTransition(id, value)
    nv = getTransition(id, value) + dv*t
    cacheTransition(id+'#MEM', nv)
    return nv

def constrain(val, min, max):
    if val < min:
        return min
    if val > max:
        return max
    return val

def runAsNewThread(name=None):
    def decorator(func):
        def wrapper(*args, **kwargs):
            t = threading.Thread(target=func, name=name, args=args, kwargs=kwargs)
            t.start()
        return wrapper
    return decorator

def fire_and_forget(func):
    """Runs an async function on a new thread."""
    assert asyncio.iscoroutinefunction(func)
    def wrapper(*args, **kwargs):
        threading.Thread(target=asyncio.run, args=(func(*args, **kwargs),)).start()
    return wrapper

def gauge(amount, length, **kwargs):
    fillchar = kwargs.get('fillchar', '-=≡■')
    format   = kwargs.get('format', '[%s]')
    amount = constrain(amount, 0, 1)

    size = round(length*amount*len(fillchar))
    i = (size%len(fillchar))-1
    s = fillchar[-1:]*int(size/len(fillchar))
    if i >= 0:
        s += fillchar[i]
    s += ' '*(length-len(s))
    return format % s

def force_decimals(x, decimals):
    if decimals <= 0: return str(int(x))
    s = str(int(x)) + '.'
    x -= int(x)
    d = str(round(x, decimals))[2:][:decimals]
    while len(d) < decimals: d += '0'
    return s+d

def format_data(x, decimals=0, tag=True):
    if x >= GIBIBYTE: return str(force_decimals(x / GIBIBYTE, decimals)) + (' GB' if tag else '')
    elif x >= MEBIBYTE: return str(force_decimals(x / MEBIBYTE, decimals)) + (' MB' if tag else '')
    elif x >= KIBIBYTE: return str(force_decimals(x / KIBIBYTE, decimals)) + (' kB' if tag else '')
    return str(force_decimals(x, decimals)) + (' B' if tag else '')

def getNum(query, **kwargs):
    min     = kwargs.get('min')
    max     = kwargs.get('max')
    inc_min = kwargs.get('inclusive_min', False) or kwargs.get('inclusive', False)
    inc_max = kwargs.get('inclusive_max', False) or kwargs.get('inclusive', False)
    default = kwargs.get('default')

    error   = kwargs.get('error', 'Error: Invalid number format.')
    oob_err = kwargs.get('out_of_bounds error', 'Error: Input is out of bounds. %s')

    bounds = ''
    if not min == None and not max == None:
        if inc_min: bounds += ' (' + str(min) + ' <= x'
        else:       bounds += ' (' + str(min) + ' < x'
        if inc_max: bounds += ' < ' + str(max) + ')'
        else:       bounds += ' <= ' + str(max) + ')'
    elif not min == None:
        if inc_min: bounds += ' (' + str(min) + ' <= x)'
        else:       bounds += ' (' + str(min) + ' < x)'
    elif not max == None:
        if inc_max: bounds += ' (x < ' + str(max) + ')'
        else:       bounds += ' (x <= ' + str(max) + ')'

    default_suffix = ''
    if not default == None:
        default_suffix = ' (default: '+str(default)+')'

    while True:
        try:
            s = input(query + bounds + default_suffix + ' ')
            if len(s) == 0:
                return default
            
            i = float(s)
            if not len(bounds) == 0 and not eval(bounds.replace('x', str(i))):
                print(oob_err % bounds)
                continue
            
            return i
        except ValueError:
            print(error)

def rec_delay(index=None):
    global recorded_delays, custom_delays
    if index == None:
        recorded_delays.append(time.perf_counter())
    else:
        custom_delays[index] = time.perf_counter()

def get_delay(index=None):
    global recorded_delays, custom_delays
    if index == None:
        return time.perf_counter() - recorded_delays.pop()
    elif index in custom_delays:
        return time.perf_counter() - custom_delays.pop(index)
    return 0
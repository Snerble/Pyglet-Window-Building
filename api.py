from tools import constrain
from queue import Queue
from post import Post
import threading
import requests
import config
import time

download_threads = []
download_queue = Queue()

def queue_controlled(queue):
    parent_thread = threading.current_thread()
    def funcgetter(func):
        def wrapper(*args, **kwargs):
            while parent_thread.isAlive():
                try: _args = queue.get(True, 1)
                except: continue
                func(*args, *_args, **kwargs)
                queue.task_done()
            return
        return wrapper
    return funcgetter

@queue_controlled(download_queue)
def download_thread(session, url, params, response_handler, error_handler):
    try:
        session.params = params
        response = session.get(url)
        response_handler(response)
    except requests.HTTPError as e:
        error_handler(e)

def spawn_session():
    if len(download_threads) >= config.CONCURRENT_LIMIT:
        return
    session = requests.session()
    process = threading.Thread(target=download_thread, name='Session-'+str(len(download_threads)+1), args=(session,))
    download_threads.append(process)
    process.start()

def limit_rate(rate):
    interval = 1/rate
    def decorator(func):
        last_called = [interval]
        def wrapper(*args, **kwargs):
            delay = time.perf_counter() - last_called[0]
            if delay < interval:
                time.sleep(interval - delay)
            ret = func(*args, **kwargs)
            last_called[0] = time.perf_counter()
            return ret
        return wrapper
    return decorator

def queue_request(url, params={}, **kwargs):
    print('queuing request')
    if download_queue.unfinished_tasks >= len(download_threads):
        spawn_session()
    response_handler = kwargs.get('response_handler', lambda : None)
    error_handler = kwargs.get('error_handler', lambda x : None)
    download_queue.put_nowait((url, params, response_handler, error_handler))

def request(url, params={}):
    response = requests.get(
        url,
        params.items(),
        headers = {'User-Agent': config.USER_AGENT}
    )
    response.raise_for_status()
    return response

@limit_rate(2)
def search(limit, **kwargs):
    print('Searching', kwargs)
    kwargs['limit'] = constrain(limit, 1, 500)
    url = config.BASE_URL + '/post/index.json'
    data = request(url, kwargs).json()
    for post_data in data:
        yield Post(post_data)
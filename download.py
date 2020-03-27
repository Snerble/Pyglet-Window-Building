import config as prgm_config
import configparser
import tools
import api
import sys
import os

if not os.path.exists(prgm_config.METADATA):
    os.makedirs(os.path.dirname(prgm_config.METADATA))
    open(prgm_config.METADATA, 'a').close()

def load_parser():
    config = configparser.ConfigParser()
    with open(prgm_config.METADATA, encoding='utf8') as src_file:
        config.read_file(src_file)
    return config

def save_parser(config):
    with open(prgm_config.METADATA, 'w', encoding='utf8') as tgt_file:
        config.write(tgt_file)

def download_posts(posts, tgt_dir=prgm_config.DOWNLOADS):
    config = load_parser()
    for post in posts:
        download_post(config, post, tgt_dir)
    save_parser(config)

def download_post(config, post, tgt_dir):
    if not os.path.exists(tgt_dir):
        os.mkdir(tgt_dir)
    if str(post.id) in config.sections():
        print('Skipped post \''+str(post.id)+'\'; Already in repository.')
        return
    tgt_dir += str(post.id) + '.' + post.file_ext
    config[post.id] = dict(post.reduce_data())
    config[post.id]['file_path'] = tgt_dir
    with open(tgt_dir, 'w') as outfile:
        download_file(post.file_url, outfile)

def download_file(url, tgt_fd):
    outfile = tgt_fd.buffer

    print('Requesting \''+url+'\'')
    response = api.request(url)
    size = len(response.content)

    strlen = 0
    progress = 0
    for data in response.iter_content(chunk_size=4096):
        if data:
            outfile.write(data)
            outfile.flush()
            progress += len(data)
            g = tools.gauge(progress / size, 20, format='\r    Downloading... [%s]')
            s = g + ' ' + tools.format_data(progress, 2) + ' / ' + tools.format_data(size, 2)
            s += ' ' * (strlen - len(s))
            strlen = len(s)
            sys.stdout.write(s)
            sys.stdout.flush()
    sys.stdout.write('\n')
    sys.stdout.flush()
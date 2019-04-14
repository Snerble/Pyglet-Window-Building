from pyglet import image
import threading
import download
import tempfile
import config
import api
import os
import time
import tools

class Post:
    def __init__(self, data):
        self.data = data
        self.temp_file = None
        self.temp_preview = None
        self.file_image = None
        self.loading_file = threading.Event()
        self.preview_image = None
        self.loading_preview = threading.Event()
        self._message = None
        self.column = 0
        self.row = 0
    
    def get_file(self):
        if self.temp_file == None:
            fd, self.temp_file = tempfile.mkstemp('_e621dl.'+self.file_ext, str(self.id))
            with open(self.temp_file, 'w') as temp:
                download.download_file(self.file_url, temp)
            os.close(fd)
        return self.temp_file

    def get_preview(self):
        if self.temp_preview == None:
            extension = self.preview_url[::-1].split('.')[0][::-1]
            fd, self.temp_preview = tempfile.mkstemp('_e621dl.'+extension, str(self.id))
            with open(self.temp_preview, 'w') as temp:
                download.download_file(self.preview_url, temp)
            os.close(fd)
        return self.temp_preview

    def load_preview(self, file_handler=lambda x:None):
        if self.preview_image == None:
            if not self.loading_preview.is_set():
                self.loading_preview.set()
                clear_load_flag = lambda e: self.loading_preview.clear()
                def response_handler(response):
                    if self.temp_preview == None:
                        size = len(response.content)
                        delay = tools.get_delay(self)
                        self.print(tools.format_data(size, 2) + '  \t' + str(round(delay, 2)) + ' s    \t' + tools.format_data(size/delay, 2) + '/s')
                        ext = self.preview_url[::-1].split('.')[0][::-1]
                        fd, temp_preview = tempfile.mkstemp('_preview_e621dl.'+ext, str(self.id), tempfile.gettempdir() + config.TEMP_SUBD_DIR)
                        with open(temp_preview, 'wb') as outfile:
                            outfile.write(response.content)
                        #self.print('Downloaded ' + str(self.id) + ' preview')
                        os.close(fd)
                        self.temp_preview = temp_preview
                    try:
                        file_handler((self, self.temp_preview))
                        clear_load_flag(None)
                    except Exception as e:
                        self.print(e)
                tools.rec_delay(self)
                api.queue_request(self.preview_url, response_handler=response_handler, error_handler=clear_load_flag)
            return None
        return self.preview_image

    def load_file(self, file_handler=lambda x:None):
        if self.file_image == None:
            if not self.loading_file.is_set():
                self.loading_file.set()
                clear_load_flag = lambda e: self.loading_file.clear()
                def response_handler(response):
                    if self.temp_file == None:
                        size = len(response.content)
                        delay = tools.get_delay(self)
                        self.print(tools.format_data(size, 2) + '  \t' + str(round(delay, 2)) + ' s    \t' + tools.format_data(size/delay, 2) + '/s')
                        fd, temp_file = tempfile.mkstemp('_e621dl.'+self.file_ext, str(self.id), tempfile.gettempdir() + config.TEMP_SUBD_DIR)
                        with open(temp_file, 'wb') as outfile:
                            outfile.write(response.content)
                        #self.print('Downloaded ' + str(self.id))
                        os.close(fd)
                        self.temp_file = temp_file
                    try:
                        file_handler((self, self.temp_file))
                        clear_load_flag(None)
                    except Exception as e:
                        self.print(e)
                tools.rec_delay(self)
                api.queue_request(self.file_url, response_handler=response_handler, error_handler=clear_load_flag)
            return None
        return self.file_image

    def clear_cache(self):
        status = True
        if not self.temp_preview == None:
            try:
                os.remove(self.temp_preview)
                self.temp_preview = None
            except: status = False
        if not self.temp_file == None:
            try:
                os.remove(self.temp_file)
            except Exception as e:
                print(e)
                status = False
        self.temp_file = None
        if not self.file_image == None:
            del self.file_image
        self.file_image = None
        return status

    def print(self, *args):
        if len(args) > 0:
            s = args[0]
            for e in args[1:]:
                s += ' ' + str(e)
            if not self._message == None:
                self._message += '\n' + s
            else:
                self._message = s

    def download(self, tgt_dir=config.DOWNLOADS):
        parser = download.load_parser()
        download.download_post(parser, self, tgt_dir)
        download.save_parser(parser)

    def reduce_data(self):
        for key in config.META_TAGS:
            yield (key, repr(self.data.get(key)).replace('%', '%%'))

    def open(self):
        try: os.system('start '+config.BASE_URL+'/post/show/'+str(self.id))
        except: print('Failed to open post url. <%s>' % self.id)

    @property
    def message(self):
        ret = self._message
        self._message = None
        return ret

    @property
    def artist(self):
        return self.data['artist']

    @artist.setter
    def artist(self, value):
        self.data['artist'] = value

    @property
    def author(self):
        return self.data['author']

    @author.setter
    def author(self, value):
        self.data['author'] = value

    @property
    def change(self):
        return self.data['change']

    @change.setter
    def change(self, value):
        self.data['change'] = value

    @property
    def children(self):
        return self.data['children']

    @children.setter
    def children(self, value):
        self.data['children'] = value

    @property
    def created_at(self):
        return self.data['created_at']

    @created_at.setter
    def created_at(self, value):
        self.data['created_at'] = value

    @property
    def creator_id(self):
        return self.data['creator_id']

    @creator_id.setter
    def creator_id(self, value):
        self.data['creator_id'] = value

    @property
    def description(self):
        return self.data['description']

    @description.setter
    def description(self, value):
        self.data['description'] = value

    @property
    def fav_count(self):
        return self.data['fav_count']

    @fav_count.setter
    def fav_count(self, value):
        self.data['fav_count'] = value

    @property
    def file_ext(self):
        return self.data['file_ext']

    @file_ext.setter
    def file_ext(self, value):
        self.data['file_ext'] = value

    @property
    def file_size(self):
        return self.data['file_size']

    @file_size.setter
    def file_size(self, value):
        self.data['file_size'] = value

    @property
    def file_url(self):
        return self.data['file_url']

    @file_url.setter
    def file_url(self, value):
        self.data['file_url'] = value

    @property
    def has_children(self):
        return self.data['has_children']

    @has_children.setter
    def has_children(self, value):
        self.data['has_children'] = value

    @property
    def has_comments(self):
        return self.data['has_comments']

    @has_comments.setter
    def has_comments(self, value):
        self.data['has_comments'] = value

    @property
    def has_notes(self):
        return self.data['has_notes']

    @has_notes.setter
    def has_notes(self, value):
        self.data['has_notes'] = value

    @property
    def height(self):
        return self.data['height']

    @height.setter
    def height(self, value):
        self.data['height'] = value

    @property
    def id(self):
        return self.data['id']

    @id.setter
    def id(self, value):
        self.data['id'] = value

    @property
    def locked_tags(self):
        return self.data['locked_tags']

    @locked_tags.setter
    def locked_tags(self, value):
        self.data['locked_tags'] = value

    @property
    def md5(self):
        return self.data['md5']

    @md5.setter
    def md5(self, value):
        self.data['md5'] = value

    @property
    def parent_id(self):
        return self.data['parent_id']

    @parent_id.setter
    def parent_id(self, value):
        self.data['parent_id'] = value

    @property
    def preview_height(self):
        return self.data['preview_height']

    @preview_height.setter
    def preview_height(self, value):
        self.data['preview_height'] = value

    @property
    def preview_url(self):
        return self.data['preview_url']

    @preview_url.setter
    def preview_url(self, value):
        self.data['preview_url'] = value

    @property
    def preview_width(self):
        return self.data['preview_width']

    @preview_width.setter
    def preview_width(self, value):
        self.data['preview_width'] = value

    @property
    def rating(self):
        return self.data['rating']

    @rating.setter
    def rating(self, value):
        self.data['rating'] = value

    @property
    def sample_height(self):
        return self.data['sample_height']

    @sample_height.setter
    def sample_height(self, value):
        self.data['sample_height'] = value

    @property
    def sample_url(self):
        return self.data['sample_url']

    @sample_url.setter
    def sample_url(self, value):
        self.data['sample_url'] = value

    @property
    def sample_width(self):
        return self.data['sample_width']

    @sample_width.setter
    def sample_width(self, value):
        self.data['sample_width'] = value

    @property
    def score(self):
        return self.data['score']

    @score.setter
    def score(self, value):
        self.data['score'] = value

    @property
    def source(self):
        return self.data['source']

    @source.setter
    def source(self, value):
        self.data['source'] = value

    @property
    def sources(self):
        return self.data['sources']

    @sources.setter
    def sources(self, value):
        self.data['sources'] = value

    @property
    def status(self):
        return self.data['status']

    @status.setter
    def status(self, value):
        self.data['status'] = value

    @property
    def tags(self):
        return self.data['tags']

    @tags.setter
    def tags(self, value):
        self.data['tags'] = value

    @property
    def width(self):
        return self.data['width']

    @width.setter
    def width(self, value):
        self.data['width'] = value
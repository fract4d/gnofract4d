# A type representing an image - this wraps the underlying C++ image type
# exposed via fract4dmodule and provides some higher-level options around it

import os.path

try:
    from . import fract4dcgmp as fract4dc
except ImportError as err:
    from . import fract4dc

file_types = {
    ".jpg" : fract4dc.FILE_TYPE_JPG,
    ".jpeg" : fract4dc.FILE_TYPE_JPG,
    ".png" : fract4dc.FILE_TYPE_PNG,
    ".tga" :fract4dc.FILE_TYPE_TGA
    }

def file_matches():
    return ["*" + x for x in list(file_types.keys())]

class T:
    FATE_SIZE = 4
    COL_SIZE = 3
    SOLID = 128
    OUT = 0
    IN = 32 | SOLID  # in pixels have solid bit set
    UNKNOWN = 255
    BLACK = [0,0,0]
    WHITE = [255,255,255]

    def __init__(self,xsize,ysize,txsize=-1,tysize=-1):
        self._img = fract4dc.image_create(xsize,ysize,txsize, tysize)
        self.update_bufs()
        self.writer = None
        self.fp = None
        
    def get_xsize(self):
        return self.get_dim(fract4dc.IMAGE_WIDTH)

    def get_ysize(self):
        return self.get_dim(fract4dc.IMAGE_HEIGHT)

    def get_total_xsize(self):
        return self.get_dim(fract4dc.IMAGE_TOTAL_WIDTH)

    def get_total_ysize(self):
        return self.get_dim(fract4dc.IMAGE_TOTAL_HEIGHT)

    def get_xoffset(self):
        return self.get_dim(fract4dc.IMAGE_XOFFSET)

    def get_yoffset(self):
        return self.get_dim(fract4dc.IMAGE_YOFFSET)
    
    def get_dim(self,dim):
        return fract4dc.image_dims(self._img)[dim]

    xsize = property(get_xsize)
    ysize = property(get_ysize)
    total_xsize = property(get_total_xsize)
    total_ysize = property(get_total_ysize)
    xoffset = property(get_xoffset)
    yoffset = property(get_yoffset)

    def get_suggest_string(self):
        k = list(file_types.keys())
        k.sort()
        available_types = ", ".join(k).upper()
        suggest_string = "Please use one of: " + available_types
        return suggest_string

    def lookup(self,x,y):
        return fract4dc.image_lookup(self._img,x,y)

    def file_type(self,name):
        ext = os.path.splitext(name)[1]
        if ext == "":
            raise ValueError(
                "No file extension in '%s'. Can't determine file format. %s" %
                (name, self.get_suggest_string()))
        
        type = file_types.get(ext.lower(), None)
        if type is None:
            raise ValueError(
                "Unsupported file format '%s'. %s" %
                (ext, self.get_suggest_string()))
        return type
    
    def save(self,name):
        self.start_save(name)
        self.save_tile()
        self.finish_save()

    def load(self,name):
        type = self.file_type(name)
        fract4dc.image_read(self._img, name,type)
        
    def start_save(self,name):
        ft = self.file_type(name)
        self.writer = fract4dc.image_writer_create(self._img, name, ft)
        fract4dc.image_save_header(self.writer)

    def save_tile(self):
        if self.writer is None:
            return
        fract4dc.image_save_tile(self.writer)

    def finish_save(self):
        fract4dc.image_save_footer(self.writer)
        self.writer = None
        
    def get_tile_list(self):
        x = 0
        y = 0
        base_xres = self.xsize
        base_yres = self.ysize
        tiles = []
        while y < self.total_ysize:
            while x < self.total_xsize:
                w = min(base_xres, self.total_xsize - x)
                h = min(base_yres, self.total_ysize - y)
                tiles.append((x,y,w,h))
                x += base_xres
            y += base_yres
            x = 0
        return tiles
    
    def set_offset(self,x,y):
        fract4dc.image_set_offset(self._img,x,y)
        
    def update_bufs(self):
        self.fate_buf = fract4dc.image_fate_buffer(self._img,0,0)
        self.image_buf = fract4dc.image_buffer(self._img,0,0)

    def resize_full(self,x,y):
        fract4dc.image_resize(self._img, x, y,x,y)
        self.update_bufs()

    def resize_tile(self,x,y):
        dims = fract4dc.image_dims(self._img)
        fract4dc.image_resize(
            self._img, x, y,
            dims[fract4dc.IMAGE_TOTAL_WIDTH],
            dims[fract4dc.IMAGE_TOTAL_HEIGHT])
        
    def clear(self):
        fract4dc.image_clear(self._img)
        
    def pos(self,x,y,size):
        return size * (y * self.xsize + x)

    def fate_buffer(self,x=0,y=0):
        return fract4dc.image_fate_buffer(self._img, x, y)

    def image_buffer(self,x=0,y=0):
        return fract4dc.image_buffer(self._img, x, y)
        
    def get_fate(self,x,y):
        n = self.fate_buf[self.pos(x,y,T.FATE_SIZE)]
        if n == T.UNKNOWN:
            return None
        elif n & T.SOLID:
            is_solid = True
        else:
            is_solid = False
        fate = n & ~T.SOLID
        return (is_solid, fate)

    def get_all_fates(self,x,y):
        pos = self.pos(x,y,T.FATE_SIZE)
        return list(self.fate_buf[pos:pos+T.FATE_SIZE])

    def get_color(self,x,y):
        pos = self.pos(x,y,T.COL_SIZE)
        return list(self.image_buf[pos:pos+T.COL_SIZE])

    def get_color_index(self,x,y,sub=0):
        return fract4dc.image_get_color_index(self._img,x,y,sub)
    
    def serialize(self):
        return ""

#Embedded file name: wx/lib/embeddedimage.py
import base64
import cStringIO
import wx
try:
    b64decode = base64.b64decode
except AttributeError:
    b64decode = base64.decodestring

class PyEmbeddedImage(object):

    def __init__(self, data, isBase64 = True):
        self.data = data
        self.isBase64 = isBase64

    def GetBitmap(self):
        return wx.BitmapFromImage(self.GetImage())

    def GetData(self):
        return self.data

    def GetIcon(self):
        icon = wx.EmptyIcon()
        icon.CopyFromBitmap(self.GetBitmap())
        return icon

    def GetImage(self):
        data = self.data
        if self.isBase64:
            data = b64decode(self.data)
        stream = cStringIO.StringIO(data)
        return wx.ImageFromStream(stream)

    getBitmap = GetBitmap
    getData = GetData
    getIcon = GetIcon
    getImage = GetImage
    Bitmap = property(GetBitmap)
    Icon = property(GetIcon)
    Image = property(GetImage)

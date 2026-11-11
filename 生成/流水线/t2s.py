import ctypes,sys
L=ctypes.CDLL('libicui18n.so.70'); U=ctypes.CDLL('libicuuc.so.70')
open_=L.utrans_openU_70; open_.restype=ctypes.c_void_p
open_.argtypes=[ctypes.c_wchar_p,ctypes.c_int32,ctypes.c_int,ctypes.c_void_p,ctypes.c_int32,ctypes.c_void_p,ctypes.POINTER(ctypes.c_int)]
tr=L.utrans_transUChars_70
tr.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.POINTER(ctypes.c_int32),ctypes.c_int32,ctypes.c_int32,ctypes.POINTER(ctypes.c_int32),ctypes.POINTER(ctypes.c_int)]
def u16(s): return s.encode('utf-16-le')
err=ctypes.c_int(0)
idb=u16('Hant-Hans')
idbuf=ctypes.create_string_buffer(idb)
open_.argtypes=[ctypes.c_void_p,ctypes.c_int32,ctypes.c_int,ctypes.c_void_p,ctypes.c_int32,ctypes.c_void_p,ctypes.POINTER(ctypes.c_int)]
T=open_(ctypes.cast(idbuf,ctypes.c_void_p),len(idb)//2,0,None,0,None,ctypes.byref(err))
assert err.value<=0,('open',err.value)
def conv(s):
    b=u16(s); n=len(b)//2; cap=n*2+16
    buf=ctypes.create_string_buffer(b+b'\0'*(cap*2-len(b)))
    tl=ctypes.c_int32(n); lim=ctypes.c_int32(n); e=ctypes.c_int(0)
    tr(T,ctypes.cast(buf,ctypes.c_void_p),ctypes.byref(tl),cap,0,ctypes.byref(lim),ctypes.byref(e))
    assert e.value<=0,('tr',e.value)
    return buf.raw[:tl.value*2].decode('utf-16-le')
if __name__=='__main__':
    print(conv(sys.argv[1]))

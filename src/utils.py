import bencodepy

def get_bt_files(bt):
    torrent = bencodepy.decode(bt)
    if b'files' in torrent[b'info']:
        name = torrent[b'info'][b'name'].decode("utf-8")
        lst = []
        for info in torrent[b'info'][b'files']:
            path = info[b'path'][0].decode("utf-8")
            if ".mp4" in path or ".mkv" in path:
                lst.append("%s/%s" % (name, path))
        return lst
    else:
        return [torrent[b'info'][b'name'].decode("utf-8")]
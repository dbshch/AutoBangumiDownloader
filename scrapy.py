import urllib.request
import urllib.parse
import re
import os
import bencodepy
import html
import xmlrpc.client
from config import *
from sql import *
from nyaa import *

heads=('User-agent','Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:73.0) Gecko/20100101 Firefox/73.0')

async def download_bt(site, url, download_name, bangumi_name, downloaded_ep, bid=0):
    aria_rpc = xmlrpc.client.ServerProxy(RPC_URI)
    dir_name = "%s/%s" % (VIDEO_DIR, bangumi_name)
    file_name = download_name
    if os.path.isdir(dir_name) == False:
        os.makedirs(dir_name)
    download_name = download_name.replace('[', r'\[')
    download_name = download_name.replace(']', r'\]')
    download_name = download_name.replace('.', r'\.')
    download_name = download_name.replace('(', r'\(')
    download_name = download_name.replace(')', r'\)')
    opener=urllib.request.build_opener()
    # opener=urllib.request.URLopener(proxies)
    opener.addheaders=[heads]
    urllib.request.install_opener(opener)
    data=opener.open(site + url).read().decode('utf-8','ignore')
    updated = []
    existEps = []
    if bid != 0:
        existEps = await getExistEp(bid)
    nyaa_magnets = await getNyaaMagnet(bangumi_name)
    for seq in range(downloaded_ep + 1, 55):
        if seq in existEps:
            continue
        res = filter_nyaa_bts(nyaa_magnets, seq)
        if len(res) > 0:
            opener=urllib.request.build_opener()
            bt_url = res[0][2]
            bt = opener.open(bt_url).read()
            torrent = bencodepy.decode(bt)
            bt_video_name = torrent[b'info'][b'name'].decode("utf-8")
            rpc_id = aria_rpc.aria2.addTorrent(RPC_TOKEN, xmlrpc.client.Binary(bt), [], {"dir":dir_name})
            updated.append((seq, "%s/%s/%s" % (VIDEO_DIR, bangumi_name, bt_video_name), rpc_id))
            continue
        f_name = file_name % seq
        name = download_name % seq
        regex4 = r'\<a href="(.+)" target="\_blank" rel="nofollow".+width=\"16\" height=\"16\" \/\>.+Raws.+%02d.+1920x1080.+\.torrent' % seq
        regex3 = r'\<a href="(.+)" target="\_blank" rel="nofollow".+width=\"16\" height=\"16\" \/\>.+Raws.+%02d.+1080p.+\.torrent' % seq
        regex2 = r'\<a href="(.+)" target="\_blank" rel="nofollow".+width=\"16\" height=\"16\" \/\>.+Raws.+%02d.+Baha.+1080p.+\.torrent' % seq
        regex = r'\<a href="(.+)" target="\_blank" rel="nofollow".+%s' % name
        x = re.findall(regex, data)
        if len(x) == 0:
            x = re.findall(regex2, data)
            if len(x) == 0:
                x = re.findall(regex3, data)
                if len(x) == 0:
                    x = re.findall(regex4, data)
                    if len(x) == 0:
                        continue
        torrent_site = site + x[0]
        dl_url = opener.open(torrent_site).read().decode('utf-8','ignore')
        download_re = r'\<a href="(.+)" target="\_blank" style="float:left;"\>\<span class="icon icon-download"\>'
        bt_url = site + re.findall(download_re, dl_url)[0]
        bt = opener.open(bt_url)
        bt = bt.read()
        video_name = "%s%02d" % (bangumi_name, seq)
        torrent = bencodepy.decode(bt)
        bt_video_name = torrent[b'info'][b'name'].decode("utf-8")
        ext = bt_video_name.split(".")[-1]
        rpc_id = aria_rpc.aria2.addTorrent(RPC_TOKEN, xmlrpc.client.Binary(bt), [], {"dir":dir_name})
        updated.append((seq, "%s/%s" % (dir_name, bt_video_name), rpc_id))
    return updated

def download_single_bt(site, torrent_url, bangumi_name):
    aria_rpc = xmlrpc.client.ServerProxy(RPC_URI)
    dir_name = "%s/%s" % (VIDEO_DIR, bangumi_name)
    if os.path.isdir(dir_name) == False:
        os.makedirs(dir_name)
    torrent_site = site + torrent_url
    opener=urllib.request.build_opener()
    opener.addheaders=[heads]
    dl_url = opener.open(torrent_site).read().decode('utf-8','ignore')
    download_re = r'\<a href="(.+)" target="\_blank" style="float:left;"\>\<span class="icon icon-download"\>'
    bt_url = site + re.findall(download_re, dl_url)[0]
    bt = opener.open(bt_url)
    bt = bt.read()
    rpc_id = aria_rpc.aria2.addTorrent(RPC_TOKEN, xmlrpc.client.Binary(bt), [], {"dir":dir_name})
    torrent = bencodepy.decode(bt)
    bt_video_name = torrent[b'info'][b'name'].decode("utf-8")
    ext = bt_video_name.split(".")[-1]
    video_path = "%s/%s/%s" % (VIDEO_DIR, bangumi_name, bt_video_name)
    # print(video_path)
    return (video_path, rpc_id)

def get_cover(site, bangumi_url):
    opener=urllib.request.build_opener()
    opener.addheaders=[heads]
    data=opener.open("%s%s" % (site, bangumi_url)).read().decode('utf-8','ignore')
    cover_regex = r'\<img src="(/upload/attach.+?)"'
    cover = re.findall(cover_regex, data)
    if len(cover) == 0:
        cover_regex = r'\<img src="(.+?)" style="max-width:871px;'
        cover = re.findall(cover_regex, data)
    cover_path = ""
    if len(cover) != 0:
        cover = html.unescape(cover[0])
        cover_file = opener.open('%s%s' % (site, cover))
        cover_path = "covers/%s" % cover.split("/")[-1]
        cover_path = cover_path.split("=")[-1]
        open(cover_path, 'wb').write(cover_file.read())
    return cover_path

def search(site, name):
    name = urllib.parse.quote_plus(name)
    opener=urllib.request.build_opener()
    opener.addheaders=[heads]
    data=opener.open("%s/search-index-keyword-%s.htm" % (site, name)).read().decode('utf-8','ignore')
    regex = r'\<td valign="middle" class="subject"\>(.+?)\</td\>'
    regex = r'\<a href="(.+?)" class=".+?"  target=".+?" title="(.+?)\<\/a\>'
    x = re.findall(regex, data)
    return x

def fetch_bts(site, url):
    opener=urllib.request.build_opener()
    opener.addheaders=[heads]
    data=opener.open("%s/%s" % (site, url)).read().decode('utf-8','ignore')
    cover_regex = r'\<img src="(/upload/attach.+?)"'
    cover = re.findall(cover_regex, data)
    if len(cover) == 0:
        cover_regex = r'\<img src="(.+?)" style="max-width:871px;'
        cover = re.findall(cover_regex, data)
    cover_path = ""
    if len(cover) != 0:
        cover = html.unescape(cover[0])
        cover_file = opener.open('%s%s' % (site, cover))
        cover_path = "covers/%s" % cover.split("/")[-1]
        cover_path = cover_path.split("=")[-1]
        open(cover_path, 'wb').write(cover_file.read())

    bt_regex = r'\<a href="(.+)" target="\_blank" rel="nofollow".+?\>(.+?.torrent).+'
    bts = re.findall(bt_regex, data)
    return (cover_path, bts)

def parse_bts(bts):
    single_bts = {}
    bt_patterns = {}
    tmp = {}
    for bt in bts:
        btn = bt[1]
        pattern_regex = re.compile(r'(?=([^0-9A-Za-z][0-9]{1,2}[^0-9A-Za-z]))')
        flg = 0
        if btn[1:11] == "SubsPlease":
            continue
        for m in pattern_regex.finditer(bt[1]):
            if len(m.group(1)) == 4 or len(m.group(1)) == 3:
                if m.start() > 2 and btn[m.start():m.start()+1] == "全":
                    continue
                kw = m.start() > 2 and btn[m.start()-1:m.start()+1]
                if kw == "Hi" or kw == "MP" or kw == "mp" or kw == "IG":
                    continue
                if btn[m.start()+len(m.group(1))-1:m.start()+len(m.group(1))] == "月":
                    continue
                if btn[m.start()+len(m.group(1))-1:m.start()+len(m.group(1))+2] == "bit":
                    continue
                if btn[m.start():m.start()+1] == "S" and btn[m.start()+3:m.start()+4] == "E":
                    continue
                if len(m.group(1)) == 4:
                    pat = "%s%s%s" % (btn[:m.start()+1], r'%02d', btn[m.start()+3:])
                else:
                    pat = "%s%s%s" % (btn[:m.start()+1], r'%d', btn[m.start()+2:])
                if pat not in bt_patterns:
                    bt_patterns[pat] = []
                bt_patterns[pat].append(m.group(1))
                tmp[bt[1]] = bt[0]
                flg = 1
            else:
                if btn[m.start():m.start()+1] != "[" or btn[m.start()+2:m.start()+3] != "]":
                    continue
                pat = "%s%s%s" % (btn[:m.start()+1], r'%d', btn[m.start()+2:])
                if pat not in bt_patterns:
                    bt_patterns[pat] = []
                bt_patterns[pat].append(m.group(1))
                tmp[bt[1]] = bt[0]
                flg = 1
            if flg == 0 and bt[1] not in single_bts:
                single_bts[bt[1]] = bt[0]
    bt_p = []
    for k in bt_patterns:
        if len(bt_patterns[k]) == 1 and bt_patterns[k][0] not in single_bts:
            bt_name = k % int(bt_patterns[k][0][1:-1])
            single_bts[bt_name] = tmp[bt_name]
        bt_p.append(k)
    return (single_bts, bt_patterns)
    
def fetch_bangumi_bts(site, url):
    opener=urllib.request.build_opener()
    opener.addheaders=[heads]
    data=opener.open("%s/%s" % (site, url)).read().decode('utf-8','ignore')

    bt_regex = r'\<a href="(.+)" target="\_blank" rel="nofollow".+?\>(.+?.torrent).+'
    bts = re.findall(bt_regex, data)
    return bts

from NyaaPy.nyaa import Nyaa
import re
import zhconv
from queue import PriorityQueue

priored_keywords = ["Lilith", "NC-Raws", "Baha", "Bili"]

def filter_nyaa_bts(bts, ep):
    filtered = []
    # priority = PriorityQueue()
    for bt in bts:
        pattern_regex = re.compile(r'(?=([^0-9][0-9]{1,2}[^0-9]))')
        flg = 0
        btn = bt[1]
        for m in pattern_regex.finditer(btn):
            if len(m.group(1)) == 4 or len(m.group(1)) == 3:
                if m.start() > 2 and btn[m.start():m.start()+1] == "全":
                    continue
                kw = m.start() > 2 and btn[m.start()-1:m.start()+1]
                if kw == "Hi" or kw == "MP" or kw == "mp":
                    continue
                if btn[m.start()+len(m.group(1))-1:m.start()+len(m.group(1))] == "月":
                    continue
                if btn[m.start()+len(m.group(1))-1:m.start()+len(m.group(1))+2] == "bit":
                    continue
                if btn[m.start():m.start()+1] == "S" and btn[m.start()+3:m.start()+4] == "E":
                    continue
                if int(m.group(1)[1:-1]) != ep:
                    continue
            else:
                continue
            if "1080" not in btn:
                continue
            if "合集" in btn:
                continue
            for kw in priored_keywords:
                if kw in btn:
                    filtered = [bt]
                    return filtered
            filtered.append(bt)
    return filtered


async def getNyaaMagnet(bangumi_name):
    nyaa = Nyaa()
    torrent_list = []
    page_num = 1
    bangumi_name = zhconv.convert(bangumi_name, 'zh-cn')
    while 1:
        search = nyaa.search(keyword=bangumi_name, category=1, subcategory=3, page=page_num)
        if len(search) == 0:
            break
        torrent_list += search
        page_num += 1
    bangumi_name = zhconv.convert(bangumi_name, 'zh-tw')
    while 1:
        search = nyaa.search(keyword=bangumi_name, category=1, subcategory=3, page=page_num)
        if len(search) == 0:
            break
        torrent_list += search
        page_num += 1
    names = []
    for torrent in torrent_list:
        names.append((str(torrent.magnet),str(torrent.name),str(torrent.download_url)))
    return names

async def main():
    name = "古见同学"
    res = await getNyaaMagnet(name)
    res = filter_nyaa_bts(res, 12)
    aria_rpc = xmlrpc.client.ServerProxy(RPC_URI)
    # rpc_id = aria_rpc.aria2.addUri(RPC_TOKEN, [res[0][0]], {"dir":"test"})
    opener=urllib.request.build_opener()
    bt_url = res[0][2]
    bt = opener.open(bt_url).read()
    torrent = bencodepy.decode(bt)
    bt_video_name = torrent[b'info'][b'name'].decode("utf-8")
    rpc_id = aria_rpc.aria2.addTorrent(RPC_TOKEN, xmlrpc.client.Binary(bt), [], {"dir":"test"})
    print(rpc_id)
    print(bt_video_name)

if __name__ == "__main__":
    import xmlrpc.client
    from config import *
    import asyncio
    import urllib.request
    import bencodepy
    import urllib.parse
    asyncio.run(main())
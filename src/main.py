import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.locks
import tornado.web
import os
from config import *
from scrapy import *
from sql import *
from datetime import datetime

async def addBangumi(url, pattern, name, cover):
    pattern = pattern.replace("'", r"\'")
    name = name.replace("'", r"\'")
    sql = "INSERT INTO `Bangumi`(`url`, `bt_pattern`, `bangumi_name`, `cover`) VALUES ('%s','%s', '%s', '%s')" % (url, pattern, name, cover)
    return await DBupdate(sql)

async def getLatestBangumis():
    return await DBquery("SELECT `bid`,`bangumi_name`,`updated`,`update_time`,`cover`,`direct` FROM `Bangumi` ORDER BY update_time DESC")

async def getUpdates():
    updates = await DBquery("SELECT `bangumi_name`,`ep`,`video_url`,`update_time` FROM Episodes ORDER BY update_time DESC")
    updates = [ (ep[0], ep[1], ep[2], '-'.join(str(ep[3]).split(' ')[0].split('-')[1:])) for ep in updates]
    return updates

async def getEpisodes(bid):
    s = xmlrpc.client.ServerProxy(RPC_URI)
    updates = await DBquery("SELECT `bangumi_name`,`ep`,`video_url`,`update_time`,`downloaded`,`epid` FROM Episodes WHERE bid=%d ORDER BY update_time DESC" % int(bid))
    eps = []
    for ep in updates:
        if (ep[4] != '1'):
            r = s.aria2.tellStatus(RPC_TOKEN, ep[4])
            progress = int(r['completedLength'])/int(r['totalLength'])
            if progress == 1:
                update_sql = "UPDATE Episodes SET `downloaded`='1' WHERE `epid`=%d" % int(ep[5])
                await DBupdate(update_sql)
            eps.append((ep[0], ep[1], ep[2], '-'.join(str(ep[3]).split(' ')[0].split('-')[1:]), int(progress * 100)))
        else:
            eps.append((ep[0], ep[1], ep[2], '-'.join(str(ep[3]).split(' ')[0].split('-')[1:]), 100))
    return eps

async def addEpisode(bname, bid, ep, path, rpc_id):
    bname = bname.replace("'", r"\'")
    path = path.replace("'", r"\'")
    sql = "INSERT INTO `Episodes`(`bangumi_name`, `bid`, `ep`, `video_url`, `downloaded`) VALUES ('%s',%d,%d,'%s','%s')" % (bname, bid, ep, path, rpc_id)
    await DBupdate(sql)
    now = datetime.now()
    time = now.strftime("%Y-%m-%d %H:%M:%S")
    update_sq = "UPDATE `Bangumi` SET `updated`=%d,`update_time`='%s' WHERE `bid`=%d" % (ep, time, bid)
    return await DBupdate(update_sq)

class IndexHandler(tornado.web.RequestHandler):
    async def get(self):
        bangumis = await getLatestBangumis()
        bangumi_data = []
        for b in bangumis:
            if b[5] == 0:
                url = await DBquery("SELECT `video_url` FROM Episodes WHERE `bid`=%d AND `ep`=%d" % (b[0], b[2]))
                bangumi_data.append(b + (url[0]))
            else:
                bangumi_data.append(b + ('',))
        cnt = len(bangumis)
        self.render("index2.html", cnt=cnt, bangumis=bangumi_data)


class BangumiHandler(tornado.web.RequestHandler):
    async def get(self, bid):
        b_info = await DBquery("SELECT `bangumi_name`,`direct` FROM Bangumi WHERE bid=%d" % int(bid))
        is_direct = b_info[0][1]
        if is_direct > 0:
            self.redirect("%svideo/%s/" % (SUB_URL, b_info[0][0]))
            return
        # updates = await DBquery("SELECT `bangumi_name`,`ep`,`video_url`,`update_time`,`downloaded` FROM Episodes WHERE bid=%d ORDER BY update_time DESC" % int(bid))
        # updates = [ (ep[0], ep[1], ep[2], '-'.join(str(ep[3]).split(' ')[0].split('-')[1:])) for ep in updates]
        updates = await getEpisodes(bid)
        self.render("bangumi.html", sub_url=SUB_URL, episodes=updates, bid=bid)


# class StatusHandler(tornado.web.RequestHandler):
#     async def get(self):
#         # print(bangumis)
#         self.redirect("/")
        # self.write(bangumis)


class SubmitHandler(tornado.web.RequestHandler):
    async def get(self):
        site = await DBquery("SELECT * FROM Info")
        site = site[0][0]
        bangumi_name = self.get_argument("bangumi_name")
        url = self.get_argument("url")
        download_name = self.get_argument("download_name")
        updated = await download_bt(site, url, download_name, bangumi_name, 0)
        print(updated)
        cover = get_cover(site, url)

        bid = await addBangumi(url, download_name, bangumi_name, cover)
        for (ep, video_url, rpc_id) in updated:
            await addEpisode(bangumi_name, bid, ep, video_url, rpc_id)
        self.redirect(SUB_URL)

class SearchHandler(tornado.web.RequestHandler):
    async def get(self):
        site = await DBquery("SELECT * FROM Info")
        site = site[0][0]
        bangumi_name = self.get_argument("bangumi_name")
        res = search(site, bangumi_name)
        self.render("search.html", sub_url=SUB_URL, results=res)

class ParseHandler(tornado.web.RequestHandler):
    async def get(self):
        site = await DBquery("SELECT * FROM Info")
        site = site[0][0]
        bangumi_name = self.get_argument("bangumi_name")
        url = self.get_argument("url")
        (cover_path, bts) = fetch_bts(site, url)
        (single_bts, bt_p) = parse_bts(bts)
        self.render("select_res.html", sub_url=SUB_URL,
            url=url, cover_path=cover_path, single_bts=single_bts, bt_p=bt_p)

class AddBTHandler(tornado.web.RequestHandler):
    async def get(self):
        site = await DBquery("SELECT * FROM Info")
        site = site[0][0]
        bangumi_name = self.get_argument("bangumi_name")
        url = self.get_argument("url")
        bangumi_url = self.get_argument("bangumi_url")
        cover = self.get_argument("cover")
        download_single_bt(site, url, bangumi_name)

        sql = "INSERT INTO `Bangumi`(`url`, `bt_pattern`, `bangumi_name`, `cover`, `ended`, `direct`) VALUES ('%s','%s', '%s', '%s', 1, 1)" % (bangumi_url, bangumi_name, bangumi_name, cover)
        await DBupdate(sql)
        self.redirect(SUB_URL)

class ManualAddHandler(tornado.web.RequestHandler):
    async def get(self, bid):
        bid = int(bid)
        site = await DBquery("SELECT * FROM Info")
        site = site[0][0]
        data = await DBquery("SELECT * FROM Bangumi WHERE `bid`=%d" % bid)
        cover_path = data[0][7]
        bts = fetch_bangumi_bts(site, data[0][1])
        self.render("manual.html", sub_url=SUB_URL, cover_path=cover_path, bts=bts, bid=bid)

class ManualAddBTHandler(tornado.web.RequestHandler):
    async def get(self):
        bid = int(self.get_argument("bid"))
        ep = int(self.get_argument("ep"))
        url = self.get_argument("url")
        site = await DBquery("SELECT * FROM Info")
        site = site[0][0]
        data = await DBquery("SELECT * FROM Bangumi WHERE `bid`=%d" % bid)
        (path, rpc_id) = download_single_bt(site, url, data[0][3])
        await addEpisode(data[0][3], bid, ep, path, rpc_id)
        self.redirect(SUB_URL)

class RefreshHandler(tornado.web.RequestHandler):
    async def get(self):
        await download_bangumi()
        self.redirect(SUB_URL)

# class BangumiEditHandler(tornado.web.RequestHandler):
#     async def get(self):
#         self.render("edit.html", bangumis=bangumis)

# class BangumiDeleteHandler(tornado.web.RequestHandler):
#     async def get(self):
#         bid = self.get_argument('bid')
#         DBupdate('DELETE FROM `Bangumi` WHERE `bid`=%d' % bid)
#         self.redirect("/edit")

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", IndexHandler),
            (r"/submit", SubmitHandler),
            (r"/add_bt", AddBTHandler),
            (r"/search", SearchHandler),
            (r"/parse", ParseHandler),
            (r"/refresh", RefreshHandler),
            (r"/bangumi/([0-9]+)", BangumiHandler),
            (r"/manual/([0-9]+)", ManualAddHandler),
            (r"/manual_add_bt", ManualAddBTHandler),
            # (r"/status", StatusHandler),
            # (r"/edit", BangumiEditHandler),
            # (r"/delete", BangumiDeleteHandler),
        ]
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            # xsrf_cookies=True,
            cookie_secret="temp",
            # login_url="/auth/login",
            debug=True,
        )
        super(Application, self).__init__(handlers, **settings)


async def main():
    # print(await getUpdates())
    # await download_bangumi()
    # await change_url()
    tornado.options.parse_command_line()

    app = Application()
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port)

    shutdown_event = tornado.locks.Event()
    await shutdown_event.wait()
    await pool.close()


async def change_url():
    data = await DBquery("SELECT epid, video_url FROM Episodes")
    for d in data:
        url = d[1]
        url = url[1:]
        url = url.replace("'", r"\'")
        await DBupdate("UPDATE Episodes SET video_url='%s' WHERE `epid`=%d" % (url, d[0]))

async def download_bangumi():
    site = await DBquery("SELECT * FROM Info")
    site = site[0][0]
    bangumis = await getBangumis()
    for data in bangumis:
        updated = await download_bt(site, data[1], data[2], data[3], data[4], data[0])
        for (ep, video_url, rpc_id) in updated:
            await addEpisode(data[3], data[0], ep, video_url, rpc_id)


if __name__ == "__main__":
    task = tornado.ioloop.PeriodicCallback(
            download_bangumi,
            REFRESH_INTERVAL)
    task.start()
    tornado.ioloop.IOLoop.current().run_sync(main)
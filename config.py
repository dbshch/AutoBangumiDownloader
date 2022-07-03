from tornado.options import define, options

RPC_TOKEN = "token:YOUR_ARIA_RPC_TOKEN"
RPC_URI = 'http://localhost:6800/rpc'
SQL_PASSWD = "YOUR_SQL_PASSWORD"
SUB_URL = "/"
VIDEO_DIR = "video"
SERVICE_PORT = 9001
REFRESH_INTERVAL = 4 * 3600 * 1000

define("port", default=SERVICE_PORT, type=int)

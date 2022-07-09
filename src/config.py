from tornado.options import define, options

RPC_TOKEN = "token:YOUR_ARIA_RPC_TOKEN"
RPC_URI = 'http://localhost:6800/rpc'   
SQL_PASSWD = "YOUR_SQL_PASSWORD"
SUB_URL = "/" # must start and end with "/"
VIDEO_DIR = "video"
COVERS_DIR = "covers"
SERVICE_PORT = 9001
REFRESH_INTERVAL = 4 * 3600 * 1000
USE_NYAA = False

define("port", default=SERVICE_PORT, type=int)

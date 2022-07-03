from config import *
import tormysql

pool = tormysql.ConnectionPool(
    max_connections = 20,
    idle_seconds = 7200,
    wait_connection_timeout = 3,
    host = "127.0.0.1",
    user = "root",
    passwd = SQL_PASSWD,
    db = "Bangumis",
    charset = "utf8"
)

async def DBupdate(sql):
    async with (await pool.Connection()) as conn:
        try:
            with conn.cursor() as cursor:
                await cursor.execute(sql)
                bid = cursor.lastrowid
        except Exception as e:
            print(e)
            await conn.rollback()
            return -1
        else:
            await conn.commit()
    return bid

async def DBquery(sql):
    async with await pool.Connection() as conn:
        with conn.cursor() as cursor:
            await cursor.execute(sql)
            return cursor.fetchall()

async def getBangumis():
    return await DBquery("SELECT * FROM `Bangumi` WHERE `ended`=0")

async def getExistEp(bid):
    sql = "SELECT `ep` FROM Episodes WHERE `bid`=%d" % int(bid)
    res = await DBquery(sql)
    eps = [ ep[0] for ep in res ]
    return eps

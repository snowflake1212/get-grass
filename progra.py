#/usr/sbin/python3
import asyncio
import random
import ssl
import json
import time
import uuid
import aiohttp
from aiohttp_socks import ProxyConnector
from loguru import logger

from fake_useragent import UserAgent

user_agent = UserAgent()
random_user_agent = user_agent.random

async def connect_to_wss(user_id, proxy_url=None):
    device_id = str(uuid.uuid4())
    logger.info(device_id)

    while True:
        try:
            await asyncio.sleep(random.randint(1, 10) / 10)

            custom_headers = {
                "User-Agent": random_user_agent
            }

            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            uri = "wss://proxy.wynd.network:4650/"

            # Mengatur konektor dengan atau tanpa proxy
            if proxy_url:
                connector = ProxyConnector.from_url(proxy_url, ssl=ssl_context)
            else:
                connector = aiohttp.TCPConnector(ssl=ssl_context)

            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.ws_connect(uri, headers=custom_headers) as websocket:

                    async def send_ping():
                        while True:
                            send_message = json.dumps(
                                {"id": str(uuid.uuid4()), "version": "1.0.0", "action": "PING", "data": {}}
                            )
                            logger.debug(send_message)
                            await websocket.send_str(send_message)
                            await asyncio.sleep(20)

                    await asyncio.sleep(1)
                    asyncio.create_task(send_ping())

                    while True:
                        response = await websocket.receive_str()
                        message = json.loads(response)
                        logger.info(message)

                        if message.get("action") == "AUTH":
                            auth_response = {
                                "id": message["id"],
                                "origin_action": "AUTH",
                                "result": {
                                    "browser_id": device_id,
                                    "user_id": user_id,
                                    "user_agent": custom_headers['User-Agent'],
                                    "timestamp": int(time.time()),
                                    "device_type": "extension",
                                    "version": "2.5.0"
                                }
                            }
                            logger.debug(auth_response)
                            await websocket.send_str(json.dumps(auth_response))

                        elif message.get("action") == "PONG":
                            pong_response = {"id": message["id"], "origin_action": "PONG"}
                            logger.debug(pong_response)
                            await websocket.send_str(json.dumps(pong_response))

        except Exception as e:
            logger.error(e)

async def main():
    _user_id = '0355d28d-bba9-46d3-a885-1fef3d97c36a'

    # Masukkan URL proxy SOCKS5 tanpa username dan password
    proxy_url = "socks5://142.54.226.214:4145"

    await connect_to_wss(_user_id, proxy_url)

if __name__ == '__main__':
    asyncio.run(main())

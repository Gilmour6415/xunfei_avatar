import asyncio
import json
import uuid
import base64
import time
from websockets import connect
from auth_util import AuthUtil
from avatar_ws_util import AvatarWsUtil

# 配置参数
avatar_url = "wss://avatar.cn-huadong-1.xf-yun.com/v1/interact"
api_key = "217147d0ec3fe9ae7ff72171dd68fd63"  # 在控制台-我的应用-虚拟人 获取
api_secret = "Y2M3ZTdmMjQ0N2JiNDkwNDE0NzVhMWU5"  # 在控制台-我的应用-虚拟人 获取
app_id = "3524f168"  # 在控制台-我的应用获取
avatar_id = "110017006"  # 授权开通的形象id
VCN = "x4_lingxiaoqi_oral"  # 发音人参数
TEXT = "欢迎来到讯飞开放平台"


# 构建请求URL


async def main():
    request_url = AuthUtil.assemble_request_url(avatar_url, api_key, api_secret)
    print(f"requestUrl: {request_url}")
    timestamp = int(time.time() * 1000)
    print(f"时间戳：{timestamp}")

    # async with connect(request_url) as websocket:
    avatar_ws_util = AvatarWsUtil(request_url)

    # veryfi if the websocket is connected [done]
    await avatar_ws_util.connect()

    # Send start frame
    await avatar_ws_util.start(build_start_request())

    # Start ping task
    asyncio.create_task(send_ping(avatar_ws_util))

    await asyncio.sleep(5)

    # Send text data
    text = "你好呀，请问你是谁，我能为您做些什么"
    await avatar_ws_util.send(build_text_request(text))
    await asyncio.sleep(2)

    # Text interaction protocol
    text1 = "合肥今天天气如何"
    await avatar_ws_util.send(build_text_interact_request(text1))

    text2 = "今天星期四"
    await avatar_ws_util.send(build_text_request0(text2))

    await asyncio.sleep(50)
    await avatar_ws_util.close()


async def send_ping(avatar_ws_util):
    """
    每5秒发送一个保活请求
    """
    while True:
        await avatar_ws_util.send(build_ping_request())
        await asyncio.sleep(5)


def build_start_request():
    header = {
        "app_id": app_id,
        "ctrl": "start",
        "request_id": str(uuid.uuid4()),
        "scene_id": "66397006335184896",
    }

    parameter = {
        "avatar": {
            "avatar_id": avatar_id,
            "stream": {"protocol": "rtmp", "fps": 25, "bitrate": 5000, "alpha": 0},
            "width": 900,
            "height": 1280,
        },
        "subtitle": {"subtitle": 1, "font_color": "#FFFFFF"},
    }

    payload = {
        "background": {
            "data": "NNnLYRoWX0vlByj2Eqq04imAZYQNJYfaFP8Qv+5H10nuGu4DJ4ukrCtUOR6hLq38RAweTVtYlrVUOoUimELMbtZr9uDLSpkAk0ul+uG8THywW+wMcOJxPaCrK4lNz2jgiO2KheWwd4+vx/spQunRBW4Ktl+1NJSsYJkGo654NPU1GZwcOINPBMzx5z3hXAKB3YP/I0nnjGaoVSm5jzwP1CBy0u+Knz4E12FCg/BAbxDkTRe75Mn0WzFfvF4Q0Qh7KCXnP0cz1Qyxa68gMFU8XVMDFIPkYfjVfvGUhNE7I0SS2NUqByXM7xTGfu9RmYu1A/Oi8lobsB7e2jlzrYTEAsRew2+ANCxwt93xUGv+bqc="
        }
    }

    print(
        "初始请求为:\n", {"header": header, "parameter": parameter, "payload": payload}
    )
    return {"header": header, "parameter": parameter, "payload": payload}


def build_text_request(text):
    header = {"app_id": app_id, "ctrl": "text_driver", "request_id": str(uuid.uuid4())}

    parameter = {
        "avatar_dispatch": {"interactive_mode": 1},
        "tts": {"vcn": VCN, "speed": 50, "pitch": 50, "volume": 50},
    }

    payload = {"text": {"content": text}}

    return {"header": header, "parameter": parameter, "payload": payload}


def build_text_request0(text):
    header = {"app_id": app_id, "ctrl": "text_driver", "request_id": str(uuid.uuid4())}

    parameter = {
        "avatar_dispatch": {"interactive_mode": 0},
        "tts": {"vcn": VCN, "speed": 50, "pitch": 50, "volume": 50},
    }

    payload = {"text": {"content": text}}

    return {"header": header, "parameter": parameter, "payload": payload}


def build_ping_request():
    """
    保活协议
    """
    header = {"app_id": app_id, "ctrl": "ping", "request_id": str(uuid.uuid4())}
    return {"header": header}


def build_text_interact_request(text):
    header = {
        "app_id": app_id,
        "ctrl": "text_interact",
        "request_id": str(uuid.uuid4()),
    }

    parameter = {"tts": {"vcn": VCN, "speed": 50, "pitch": 50, "volume": 100}}

    payload = {"text": {"content": text}}

    return {"header": header, "parameter": parameter, "payload": payload}


if __name__ == "__main__":
    asyncio.run(main())

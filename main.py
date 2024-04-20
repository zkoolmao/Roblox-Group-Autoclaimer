import websocket, json, threading, asyncio, re, requests
from modules.claim import *
from modules.console import Logger

with open("./data/config.json", "r") as f:
    data = json.load(f)

loop = asyncio.new_event_loop()

session_id = None
heartbeat_interval = 30
seq_num = ""
resumeURL = None
ws = None

groupsid = 0
groupsids = []

with open("./data/config.json", "r", encoding="utf-8") as f:
    data = json.load(f)

embed = {
    "embeds": [
        {
            "title": f"✅ Successfully started autoclaimer!",
            "description": "⭐ https://github.com/zkoolmao/Roblox-Group-Autoclaimer",
            "color": 5763719
        }
    ],
}

requests.post(data["webhook"], json=embed)

async def on_message(ws, message):
    global session_id, heartbeat_interval, daat2, seq_num, resumeURL, groupsid, groupsids

    try:
        data = json.loads(message)
    except json.JSONDecodeError:
        print("Error decoding JSON message:", message)
        return

    event_type = data.get('t')
    if event_type == 'READY':
        session_id = data.get('d', {}).get('session_id')
        resumeURL = data.get('d', {}).get('resume_gateway_url')
        Logger.info(f"Logged in as {data['d']['user']['username']}#{data['d']['user']['discriminator']}")
        heartbeatwrapper()
    elif data["op"] == 10:
        heartbeat_interval = data["d"]["heartbeat_interval"] / 1000
        seq_num = data['s']
    elif data["op"] == 7:
        reconnect()
    elif event_type == 'MESSAGE_CREATE':
        content: str = data["d"]["content"]
        user: str = data["d"]["author"]["username"]
        channel = data["d"]["channel_id"]
        if content != "":
            if "roblox.com/groups" in content:
                message_parts = content.split("/")
                group_id_index = message_parts.index("groups") + 1
                if group_id_index < len(message_parts):
                    numbers: int = re.findall(r'\d+', message_parts[group_id_index])
                    if numbers != groupsid:
                        groupsid = numbers
                        groupsids.append(numbers[0])
                        await main(numbers[0])


async def on_error(ws, error):
    print("Error:", error)

async def on_close(ws, close_status_code, close_msg):
    if close_status_code != 1000 and close_status_code != 1001: 
        await resume()
    elif close_status_code == 1000 or close_status_code == 1001:
        Logger.error(f"Unfixable error, reconnecting instead of resuming..")
        reconnect()
    else:
        Logger.error(f"Connection closed with status code {close_status_code}. Resuming session..")
        await resume()

async def on_open(ws):
    payload = {"op": 2, "d": {"token": token, "intents": 513 | (1 << 15) | (1 << 12) | (1 << 9), "properties": {"os": 'linux', "browser": 'chrome', "device": 'chrome'}}}
    ws.send(json.dumps(payload))

def on_open_wrapper(ws):
    loop.run_until_complete(on_open(ws))

def on_message_wrapper(ws, message):
    loop.run_until_complete(on_message(ws, message))

def on_close_wrapper(ws, close_status_code, close_msg):
   loop.run_until_complete(on_close(ws, close_status_code, close_msg))

def on_error_wrapper(ws, error):
    loop.run_until_complete(on_error(ws, error))

def heartbeatwrapper():
    threading.Thread(target=asyncio.run, args=(send_heartbeat(),)).start()

def resumewrapper(ws):
    loop.run_until_complete(resume(ws))

async def send_heartbeat():
    while True:
        await asyncio.sleep(heartbeat_interval)
        ws.send(json.dumps({"op": 1, "d": f"{seq_num}"}))

async def resume():
    ws = websocket.WebSocketApp(f"{resumeURL}",	on_message=on_message_wrapper, on_error=on_error_wrapper, on_close=on_close_wrapper)
    payload = {"op": 6, "d": {"token": token, "intents": 513 | (1 << 15) | (1 << 12) | (1 << 9), "session_id": session_id, "seq": 1337}}
    ws.send(json.dumps(payload))
    Logger.info("Successfully resumed")

def reconnect():
    ws = websocket.WebSocketApp("wss://gateway.discord.gg", on_message=on_message_wrapper, on_error=on_error_wrapper, on_close=on_close_wrapper)
    ws.on_open = on_open
    asyncio.run(ws.run_forever())

if __name__ == "__main__":
    token = data["token"]

    ws = websocket.WebSocketApp("wss://gateway.discord.gg", on_message=on_message_wrapper, on_error=on_error_wrapper, on_close=on_close_wrapper)
    ws.on_open = on_open_wrapper

    asyncio.run(ws.run_forever())
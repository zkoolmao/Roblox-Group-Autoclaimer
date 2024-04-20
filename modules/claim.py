import socket, ssl, time, random, requests, asyncio, threading, json, aiohttp
from datetime import datetime
from modules.console import Logger

Host = "groups.roblox.com"
Port = 443

ct = ssl.create_default_context()
cookie = ""
xcsrf = ""

with open("./data/config.json", "r", encoding="utf-8") as f:
    data = json.load(f)

shoutMessages = data.get("shoutMessages", [])
webhook = data.get("webhook", "")

async def fetch(session, url, headers=None):
    async with session.get(url, headers=headers) as response:
        return await response.json()

async def sendEmbed(webhook, embed):
    async with aiohttp.ClientSession() as session:
        async with session.post(webhook, json=embed) as response:
            if response.status != 204:
                Logger.error(f"Failed to send embed: {response.status}")

s = socket.create_connection((Host, 443))

async def joinclaim(id, cookie, xcsrf):
    with socket.create_connection((Host, 443)) as s:
        with ct.wrap_socket(s, server_hostname=Host) as so:
            xtoken = xcsrf
            headers = f"Host: {Host}\r\n" \
                f"Connection: keep-alive\r\n" \
                f"User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36\r\n" \
                f"Cookie: GuestData=UserID=-1458690174; .ROBLOSECURITY={cookie}; RBXEventTrackerV2=CreateDate=11/19/2023 12:07:42 PM&rbxid=5189165742&browserid=200781876902;\r\n" \
                f"x-csrf-token: {xtoken}\r\n" \
                f"Content-Type: application/json; charset=utf-8\r\n" \
                f"accept: accept-encoding\r\n\r\n"
                
            datajoin = f"POST /v1/groups/{id}/users HTTP/1.1\r\n{headers}"
            dataclaim = f"POST /v1/groups/{id}/claim-ownership HTTP/1.1\r\n{headers}"
                
            start_time = time.time()
            so.sendall(datajoin.encode())
            so.sendall(dataclaim.encode())
            response_join = so.recv(1024).decode()
            response_claim = so.recv(1024).decode()
            end_time = time.time()

            total_time = end_time - start_time
                
            return response_join, response_claim, total_time

def leaveGroup(groupid):
    global cookie, xcsrf
    headers = {"Content-Type": "application/json", "Cookie": f"GuestData=UserID=-1458690174; .ROBLOSECURITY={cookie}; RBXEventTrackerV2=CreateDate=11/19/2023 12:07:42 PM&rbxid=5189165742&browserid=200781876902;", "x-csrf-token": f"{xcsrf}"}
    response = requests.get("https://users.roblox.com/v1/users/authenticated", headers=headers)
    userid = response.json()["id"]
    response = requests.delete(f"https://groups.roblox.com/v1/groups/{groupid}/users/{userid}", headers=headers)
    return response

async def changeCookie():
    global cookie, xcsrf

    with open("./data/cookies.txt", "r") as f:
        data = f.read().splitlines()

    cookie = random.choice(data)
    try:
        xr = requests.post("https://auth.roblox.com/v2/logout", headers={"cookie": f".ROBLOSECURITY={cookie}"})
        if xr.status_code != 200:
            xcsrf = xr.headers.get("x-csrf-token")
    except:
        pass

async def xcsrfToken():
    while True:
        global xcsrf, cookie
        try:
            xr = requests.post("https://auth.roblox.com/v2/logout", headers={"cookie": f".ROBLOSECURITY={cookie}"})
            if xr.status_code != 200:
                xcsrf = xr.headers.get("x-csrf-token")
        except:
            pass

async def group_thumbnail(session, group_id):
    response = await fetch(session, f"https://thumbnails.roblox.com/v1/groups/icons?groupIds={group_id}&size=420x420&format=Png&isCircular=false")
    if "data" in response and response["data"]:
        return response["data"][0]["imageUrl"]
    else:
        return None

async def groupData(groupid, cookie):
    global xcsrf
    headers = {"Content-Type": "application/json", "Cookie": f"GuestData=UserID=-1458690174; .ROBLOSECURITY={cookie}; RBXEventTrackerV2=CreateDate=11/19/2023 12:07:42 PM&rbxid=5189165742&browserid=200781876902;", "x-csrf-token": f"{xcsrf}"}

    async with aiohttp.ClientSession() as session:
        today = datetime.now().strftime("%Y-%m-%d")
        try:
            response = await fetch(session, f"https://economy.roblox.com/v1/groups/{groupid}/currency", headers=headers)
            funds = response.get("robux", 0)
        except Exception as e:
            Logger.error(f"Error: {e}")
            funds = 0

        try:
            response = await fetch(session, f"https://economy.roblox.com/v1/groups/{groupid}/revenue/summary/{today}", headers=headers)
            pending_funds = response.get("pendingRobux", 0)
        except Exception as e:
            Logger.error(f"Error: {e}")
            pending_funds = 0

        try:
            response = await fetch(session, f"https://catalog.roblox.com/v1/search/items/details?Category=3&SortType=Relevance&CreatorTargetId={groupid}&ResultsPerPage=100&CreatorType=2", headers=headers)
            clothing = len(response.get("data", []))
        except Exception as e:
            Logger.error(f"Error: {e}")
            clothing = 0

        return {"funds": funds, "pending_funds": pending_funds, "clothing": clothing}

async def main(groupid):
    global cookie, xcsrf

    async with aiohttp.ClientSession() as session:
        join, claim, time = await joinclaim(groupid, cookie, xcsrf)
        claimstatus = claim.splitlines()[0]
        joinstatus = join.splitlines()[0]

        if "HTTP/1.1 200 OK" in joinstatus and "HTTP/1.1 200 OK" in claimstatus:
            Logger.info(f"Successfully joined and claimed group {groupid} in {time} seconds")
            shout_message = random.choice(shoutMessages)

            try:
                response = requests.patch(f"https://groups.roblox.com/v1/groups/{groupid}/status", headers={"Cookie": f"GuestData=UserID=-1458690174; .ROBLOSECURITY={cookie}; RBXEventTrackerV2=CreateDate=11/19/2023 12:07:42 PM&rbxid=5189165742&browserid=200781876902;", "X-CSRF-TOKEN": f"{xcsrf}"}, json={"message": shout_message})
                response.raise_for_status()
                Logger.info(f"Successfully changed shout to: {shout_message}")
            except Exception as e:
                Logger.error(f"Error: {e}")

            response = requests.get(f"https://groups.roblox.com/v1/groups/{groupid}")
            groupInfo = response.json()
            groupInfo2 = await groupData(groupid, cookie)

            groupName = groupInfo["name"]
            groupMembers = groupInfo["memberCount"]
            groupClothing = groupInfo2.get("clothing", [])
            groupPending = groupInfo2.get("pending_funds", [])
            groupFunds = groupInfo2.get("funds", [])

            embed = {
                "embeds": [
                    {
                        "title": f"✅ Successfully claimed group in {time} seconds!",
                        "url": f"https://roblox.com/groups/{str(groupid)}",
                        "description": "⭐ [Roblox Group Autoclaimer](https://github.com/zkoolmao/Roblox-Group-Autoclaimer)",
                        "color": 5763719,
                        "thumbnail": {"url": await group_thumbnail(session, groupid)},
                        "fields": [
                            {"name": "Group ID:", "value": str(groupid), "inline": True},
                            {"name": "Group Name:", "value": groupName, "inline": True},
                            {"name": "Group Members:", "value": str(groupMembers), "inline": True},
                            {"name": "Group Clothing:", "value": str(groupClothing), "inline": True},
                            {"name": "Group Funds:", "value": str(groupFunds), "inline": True},
                            {"name": "Pending Funds:", "value": str(groupPending), "inline": True}
                        ],
                    }
                ],
            }

            try:
                await sendEmbed(webhook, embed)
                Logger.info("Successfully sent embed.")
            except Exception as e:
                Logger.error(f"Error: {e}")

        elif "HTTP/1.1 200 OK" in joinstatus and "HTTP/1.1 403 Forbidden" in claimstatus or "HTTP/1.1 200 OK" in joinstatus and "HTTP/1.1 500 Internal Server Error" in claimstatus:
            Logger.error(f"Someone already claimed group {groupid}, leaving the group..")
            leave = leaveGroup(groupid)
            if leave.status_code == 200:
                Logger.info(f"Successfully left group {groupid}")
            else:
                Logger.error(f"Something happened while leaving group {groupid}")

        elif "HTTP/1.1 403 Forbidden" in joinstatus and "==" in claimstatus:
            Logger.error("Cookie probably flagged, changing cookies..")
            await changeCookie()
        elif "HTTP/1.1 403 Forbidden" in joinstatus and "HTTP/1.1 403 Forbidden" in claimstatus:
            Logger.error("XCSRF Token invalidated")
        elif "HTTP/1.1 429" in joinstatus or "HTTP/1.1 429" in claimstatus:
            Logger.error("Ratelimited, changing cookie..")
            await changeCookie()
        else:
            Logger.error(f"Failed to claim {groupid} | {joinstatus} | {claimstatus}")
            leaveGroup(groupid)

asyncio.run(changeCookie())
thread = threading.Thread(target=asyncio.run, args=(xcsrfToken(),))
thread.daemon = True
thread.start()
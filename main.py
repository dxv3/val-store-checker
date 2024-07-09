import asyncio
import sys
import requests
import riot_auth
import os
from dotenv import load_dotenv
import time

load_dotenv()
UNAME = os.getenv("USERNAME")
PASSWD = os.getenv("PASSWORD")
WEHBOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
REGION = os.getenv("REGIONN")

WATCHLIST = ["Xenohunter Knife"]

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
CREDS = UNAME, PASSWD

riot_auth.RiotAuth.RIOT_CLIENT_USER_AGENT = f"RiotClient/{requests.get('https://valorant-api.com/v1/version').json()['data']['riotClientBuild']} %s (Windows;10;;Professional, x64)"
print(f'Using User Agent "{riot_auth.RiotAuth.RIOT_CLIENT_USER_AGENT}"')
print("Getting Tokens....")
auth = riot_auth.RiotAuth()
asyncio.run(auth.authorize(*CREDS))

print(f"Access Token Type: {auth.token_type}\n")
print(f"Access Token: {auth.access_token}\n")
print(f"Entitlements Token: {auth.entitlements_token}\n")
print(f"User ID: {auth.user_id}")

asyncio.run(auth.reauthorize())

headers = {
    'Authorization': f'{auth.token_type} {auth.access_token}',
    'X-Riot-ClientPlatform': 'ew0KCSJwbGF0Zm9ybVR5cGUiOiAiUEMiLA0KCSJwbGF0Zm9ybU9TIjogIldpbmRvd3MiLA0KCSJwbGF0Zm9ybU9TVmVyc2lvbiI6ICIxMC4wLjE5MDQyLjEuMjU2LjY0Yml0IiwNCgkicGxhdGZvcm1DaGlwc2V0IjogIlVua25vd24iDQp9',
    'X-Riot-ClientVersion': f'{requests.get("https://valorant-api.com/v1/version").json()["data"]["riotClientVersion"]}',
    'X-Riot-Entitlements-JWT': f'{auth.entitlements_token}',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36',
}

response = requests.get(f"https://pd.{REGION}.a.pvp.net/store/v2/storefront/{auth.user_id}", headers=headers)

if response.status_code != 200:
    print(f"Error: Received status code {response.status_code} from store API")
    sys.exit(1)

try:
    store_data = response.json()
except requests.exceptions.JSONDecodeError:
    print("Error: Failed to decode JSON response")
    sys.exit(1)

if 'SkinsPanelLayout' not in store_data:
    print("Error: SkinsPanelLayout not found in response")
    sys.exit(1)

shop_items = store_data["SkinsPanelLayout"]["SingleItemOffers"]

for i in range(len(shop_items)):
    item_id = shop_items[i]
    itemdata_response = requests.get(f"https://valorant-api.com/v1/weapons/skinlevels/{item_id}")

    if itemdata_response.status_code != 200:
        print(f"Error retrieving data for item {item_id}: {itemdata_response.status_code}")
        continue

    try:
        itemdata = itemdata_response.json()
    except requests.exceptions.JSONDecodeError:
        print(f"Error decoding JSON for item {item_id}")
        continue

    if 'data' not in itemdata:
        print(f"Error: 'data' field not found in itemdata for item {item_id}")
        continue

    skin_name = itemdata["data"]["displayName"]
    skin_cost = store_data["SkinsPanelLayout"]["SingleItemStoreOffers"][i]["Cost"]["85ad13f7-3d1b-5128-9eb2-7cd8ee0b5741"]

    print(f'Got data for {skin_name}')

    webhook_data = {
        "embeds": [
            {
                "title": f'{skin_name} - {skin_cost} VP',
                "color": 13346551,
                "image": {
                    "url": f'{itemdata["data"]["displayIcon"]}'
                }
            }
        ],
        "attachments": []
        }

    webhook_response = requests.post(WEBHOOK_URL, json=webhook_data)
    if skin_name in WATCHLIST:
        WEGOTTHESKIN = {"content": f"@everyone {skin_name} in the store!!! {skin_cost} VP!",}
        time.sleep(1)
        webhook_response = requests.post(WEBHOOK_URL, json=WEGOTTHESKIN)
        time.sleep(0.3)
        webhook_response = requests.post(WEBHOOK_URL, json=WEGOTTHESKIN)
        time.sleep(0.3)
        webhook_response = requests.post(WEBHOOK_URL, json=WEGOTTHESKIN)
        time.sleep(0.3)
        webhook_response = requests.post(WEBHOOK_URL, json=WEGOTTHESKIN)
    print(f"Webhook response status: {webhook_response.status_code}")
    print(webhook_response.text)

print("Script completed.")

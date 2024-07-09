import asyncio
import sys
import requests
import riot_auth
import os
from dotenv import load_dotenv

load_dotenv()
UNAME = ""
PASSWD = ""
WEBHOOK_URL = ""
REGION = ""

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
CREDS = UNAME, PASSWD

try:
    version_response = requests.get('https://valorant-api.com/v1/version')
    version_response.raise_for_status()
    version_data = version_response.json()['data']
    riot_auth.RiotAuth.RIOT_CLIENT_USER_AGENT = f"RiotClient/{version_data['riotClientBuild']} %s (Windows;10;;Professional, x64)"
    print(f'Using User Agent "{riot_auth.RiotAuth.RIOT_CLIENT_USER_AGENT}"')
except requests.RequestException as e:
    print(f"Failed to get Riot client version: {e}")
    sys.exit(1)

print("Getting Tokens....")
auth = riot_auth.RiotAuth()

try:
    asyncio.run(auth.authorize(*CREDS))
    if not all([auth.token_type, auth.access_token, auth.entitlements_token, auth.user_id]):
        print("Failed to authorize. Please check your credentials and try again.")
        sys.exit(1)
except Exception as e:
    print(f"Failed to authorize: {e}")
    sys.exit(1)

print(f"Access Token Type: {auth.token_type}\n")
print(f"Access Token: {auth.access_token}\n")
print(f"Entitlements Token: {auth.entitlements_token}\n")
print(f"User ID: {auth.user_id}")

try:
    reauth_success = asyncio.run(auth.reauthorize())
    if not reauth_success:
        print("Reauthorization failed.")
        sys.exit(1)
except Exception as e:
    print(f"Failed to reauthorize: {e}")
    sys.exit(1)

headers = {
    'Authorization': f'{auth.token_type} {auth.access_token}',
    'X-Riot-ClientPlatform': 'ew0KCSJwbGF0Zm9ybVR5cGUiOiAiUEMiLA0KCSJwbGF0Zm9ybU9TIjogIldpbmRvd3MiLA0KCSJwbGF0Zm9ybU9TVmVyc2lvbiI6ICIxMC4wLjE5MDQyLjEuMjU2LjY0Yml0IiwNCgkicGxhdGZvcm1DaGlwc2V0IjogIlVua25vd24iDQp9',
    'X-Riot-ClientVersion': f'{version_data["riotClientVersion"]}',
    'X-Riot-Entitlements-JWT': f'{auth.entitlements_token}',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36',
}

try:
    response = requests.get(f"https://pd.{REGION}.a.pvp.net/store/v2/storefront/{auth.user_id}", headers=headers)
    response.raise_for_status()
    response_data = response.json()
    if 'SkinsPanelLayout' not in response_data:
        print("Unexpected response structure. 'SkinsPanelLayout' key not found.")
        print(response_data)
        sys.exit(1)
except requests.RequestException as e:
    print(f"Failed to get store data: {e}")
    sys.exit(1)

shop_items = [0, 1, 2, 3]

for i in shop_items:
    try:
        offer_id = response_data['SkinsPanelLayout']['SingleItemOffers'][i]
        item_response = requests.get(f"https://valorant-api.com/v1/weapons/skinlevels/{offer_id}")
        item_response.raise_for_status()
        item_data = item_response.json()["data"]
        print(f'Got data for {item_data["displayName"]}')

        webhook_data = {
            "embeds": [
                {
                    "title": f'{item_data["displayName"]} - {response_data["SkinsPanelLayout"]["SingleItemStoreOffers"][i]["Cost"]["85ad13f7-3d1b-5128-9eb2-7cd8ee0b5741"]}VP',
                    "color": 13346551,
                    "image": {
                        "url": f'{item_data["displayIcon"]}'
                    }
                }
            ],
            "attachments": []
        }

        if WEBHOOK_URL:
            webhook_response = requests.post(WEBHOOK_URL, json=webhook_data)
            if webhook_response.status_code == 204:
                print('Webhook sent successfully.')
            else:
                print(f"Failed to send webhook. Status code: {webhook_response.status_code}")
                print(f"Response: {webhook_response.text}")
        else:
            print('Webhook URL is not set.')

    except requests.RequestException as e:
        print(f"Failed to get item data or send webhook: {e}")
    except KeyError as e:
        print(f"Key error: {e}")

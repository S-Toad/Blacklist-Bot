
import discord
import os
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials

TOKEN = os.environ['BLACKLIST_BOT_TOKEN']  # Discord bot token
SHEET_KEY = '1uctYXKU7z0TXCXMZOdvMm3ryiVqxG2OuKF1zxMO5B8A'  # Unique ID for shitlist google sheet
JSON_FILE = os.environ['GOOGLE_API_JSON_FILE']  # JSON for google sheets API project
CHANNEL_ID = int(os.environ['BLACKLIST_BOT_CHANNEL_ID']) # Specific channel ID for #community-reports
REGEX_STR = 'https:\/\/steamcommunity.com\/\S+'

# Set up discord and google client
client = discord.Client()
scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name(JSON_FILE, scope)
google_client = gspread.authorize(creds)

@client.event
async def on_message(message):
    # If we're not in the right channel, return
    if message.channel.id != CHANNEL_ID:
        return
    
    # Scan for Steam URLs
    msg_str = message.content
    matches = re.findall(REGEX_STR, msg_str)
    print("Found %d matches" % len(matches))

    # Handle each url posted
    if matches:
        sheet = google_client.open_by_key(SHEET_KEY).sheet1
        for match in matches:
            print("Processing user: %s" % match)
            match_message = await get_record_msg(sheet, match)
            await message.channel.send(match_message)


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')


async def get_record_msg(sheet, steam_url):
    # Look for user in the google sheet
    user_record = find_record(sheet, steam_url)
    
    msg = ''
    if user_record:
        # If user was found, construct message using data from sheet
        name = user_record['NAME']
        msg += '**Name:** `' + name + '`'

        msg += '\n\n**Past Punishments:**'
        past_punishments = user_record['BAN LENGTH'].split(', ')
        for punishment in past_punishments:
            if 'P(M)' in punishment:
                punishment = "Permanent Ban (Moorland)"
            elif 'P(R)' in punishment or 'P' in punishment:
                punishment = "Permanent Ban (Ruby's)"
            elif 'M' in punishment:
                punishment = punishment.replace('M', ' Minutes')
            elif 'H' in punishment:
                punishment = punishment.replace('H', ' Hours')
            elif 'D' in punishment:
                punishment = punishment.replace('D', ' Days')

            msg += '\n- ' + punishment
        
        msg += '\n\n**Transgressions: **'
        crimes = user_record['TRANSGRESSIONS\n'].split(', ')
        for crime in crimes:
            msg += '\n- ' + crime
    else:
        # Otherwise let people know this man is clean
        msg = 'User has no previous punishments.'

    return msg

def find_record(sheet, steam_url):
    steam_id = ''.join(ch for ch in steam_url if ch.isdigit())
    steam_id = int(steam_id)

    for record in sheet.get_all_records():
        if 'PROFILE' in record:
            record_id =  ''.join(ch for ch in record['PROFILE'] if ch.isdigit())
            if len(record_id) != 0 and int(record_id) == steam_id:
                return record
    return None


if __name__ == "__main__":
    client.run(TOKEN)

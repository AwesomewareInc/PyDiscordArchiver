import discord, os, time, json
import urllib.request
import pathlib
from json import JSONEncoder

download_avatars = True				# should it download tupper avatars?
bots_only = False					# should it filter to bots only
check_category_name = True			# should it check the category of each channel to make sure it's in an "archives" channel
guild_id = -1						# guild ID. -1 to prompt the user.
channel_id = -1						# channel ID. -1 for all.
valid_channel_id_given = False		# whether to prompt for channel ID

messages = None
time_since_last_downloaded = 0

class Message:
	def __init__(self, id: str, avatar: str, author: str, channel: str, content: str, timestamp: str, fictional: bool) -> None:
		self.id = id
		self.avatar = avatar
		self.author = author
		self.channel = channel
		self.content = content
		self.timestamp = timestamp
		self.fictional = fictional
	def toJSON(self):
		return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)
	
class MessageEncoder(JSONEncoder):
	def default(self, o):
		return o.__dict__
	
def fucker(f):
	if str(type(f)) == "<class 'dict'>":
		return f["channel"]
	else:
		return f.channel
	
def fuck(f):
	if str(type(f)) == "<class 'dict'>":
		return f["id"]
	else:
		return f.id
	
def get_ids():
	return list(map(lambda f: fuck(f), messages))
def get_channels():
	return list(map(lambda f: fucker(f), messages))

async def main_bot(client):
	global channel_id
	global guild_id
	global valid_channel_id_given

	# ask for the guild id
	while guild_id <= -1:
		try:
			guild_id = int(input("Enter the ID of the server you want to look in: "))
		except:
			print("Invalid number")

	# ask for the channel id, and let us default to all of them.
	channel_id_str = ""
	while valid_channel_id_given == False:
		try:
			channel_id_str = input("Enter the ID of the channel you want to look in (blank for all): ")
			channel_id = int(channel_id_str)
		except:
			if(channel_id_str == ""):
				valid_channel_id_given = True
				channel_id = -1
			else:
				print("Invalid number given.")
		finally:
			valid_channel_id_given = True

	# ask what file to write to
	file_name = input("What file should this be saved to? .json will automatically be appended to whatever you enter:\n")
	await archive_guild(client,guild_id,channel_id,file_name+".json")
	await client.close()

async def archive_guild(client,guild_id,channel_id,file_name):
	global messages
	

	f = open(file_name,'r')
	try:
		messages = json.loads(f.read())
	except Exception as ex:
		print(ex)
		messages = []
		pass
	f.close()

	guild = client.get_guild(guild_id)
	if(channel_id == -1):
		for channel in guild.channels:
			if(channel.type == discord.ChannelType.text):
				await archive_channel(client,channel,file_name)
	else:
		await archive_channel(client,guild.get_channel(channel_id),file_name)

async def archive_channel(client,channel,file_name):
	global check_category_name
	global download_avatars
	global time_since_last_downloaded
	global messages

	if str(channel.name) in get_channels():
		print("skipping "+str(channel.name)+"; already archived.")
		return
	

	if check_category_name:
		if channel.category is not None:
			if "archives" not in channel.category.name.lower():
				return
		else: 
			return
	if "bios" in channel.name.lower():
		return
	# start 
	folder_name = file_name.replace(".json","",1)
	_ = pathlib.Path(folder_name).mkdir(parents=True,exist_ok=True)
	try:
		async for message in channel.history(limit=1000000):
			is_fictional = False
			if message.webhook_id:
				is_fictional = True
			if(is_fictional == True or bots_only == False):
					avatar = ""
					avatar_url = ""
					if download_avatars and is_fictional:
						if message.author.avatar is not None:
							avatar_url = message.author.avatar.url
							parts = avatar_url.split("/")
							parts_2 = parts[len(parts)-1].split("?")
							avatar = folder_name+"/"+parts_2[0]
							if not os.path.exists(avatar):
								while time_since_last_downloaded + 3 >= time.time():
									pass
								req = urllib.request.Request(
									avatar_url, 
									data=None, 
									headers={
										'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
									}
								)

								f2 = urllib.request.urlopen(req)
								f3 = open(avatar,"xb")
								f3.write(f2.read())
								f3.close()
								time_since_last_downloaded = time.time()
								
					msg_id = message.id
					channel = str(message.channel.name)
					author = str(message.author.name.replace("\"","'"))
					content = str(message.content.replace("\\","/",999999).replace("\"","'",999999).replace("\n","<br>",999999))
					timestamp = str(int(message.created_at.timestamp()))

					messages.append(Message(msg_id,avatar,author,channel,content,timestamp,is_fictional))
	except discord.errors.Forbidden:
		print("Channel "+channel.name+" is locked from the bot.")
		pass
	f = open(file_name,'w')
	f.write(json.dumps(messages,cls=MessageEncoder).replace("},","}\n").replace("[","").replace("]",""))
	f.close()
	print(format("parsed %d messages" % len(messages)))

client = discord.Client(
	intents=discord.Intents(
		message_content=True,
		guild_messages=True,
		guilds=True,
	)
)

@client.event
async def on_ready():
	await main_bot(client)

f = open("key","r")
if f is None:
	print("No key file found.")
else:
	client.run(f.read())

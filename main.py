import discord, os, time, json, re
import urllib.request
import pathlib
from json import JSONEncoder

download_avatars = True				# should it download tupper avatars?
bots_only = False					# should it filter to bots only
check_category_name = True			# should it check the category of each channel to make sure it's in an "archives" channel
guild_id = 554421097869606915					# guild ID. -1 to prompt the user.
channel_id = -1						# channel ID. -1 for all.
valid_channel_id_given = True		# whether to prompt for channel ID
file_name = "ddd_roleplay"						# file name. empty for prompt.

messages = None
time_since_last_downloaded = 0

class Channel:
	def __init__(self, id: str, name: str, category_id: str, archived: bool):
		self.obj_type = "channel"
		self.id = id
		self.name = name
		self.category_id = category_id
		self.archived = archived

class User:
	def __init__(self, id: str, name: str):
		self.obj_type = "user"
		self.id = id
		self.name = name

class Message:
	def __init__(self, id: str, avatar: str, author: str, channel: str, content: str, timestamp: str, fictional: bool, attachments: list[str]) -> None:
		self.obj_type = "message"
		self.id = id
		self.avatar = avatar
		self.author = author
		self.channel = channel
		self.content = content
		self.timestamp = timestamp
		self.fictional = fictional
		self.attachments = attachments
	def toJSON(self):
		return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)
	
class MessageEncoder(JSONEncoder):
	def default(self, o):
		return o.__dict__
	
def fucker(f):
	if str(type(f)) == "<class 'dict'>":
		if f["obj_type"] == "message":
			return f["channel"]
	else:
		if f.obj_type == "message":
			return f.channel
	return None

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
	global file_name

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
	if file_name == "":
		file_name = input("What file should this be saved to? .json will automatically be appended to whatever you enter:\n")
	await archive_guild(client,guild_id,channel_id,file_name+".json")
	await client.close()

async def archive_guild(client,guild_id,channel_id,file_name):
	global messages
	try:
		f = open(file_name,'r')
		messages = json.loads(f.read())
		f.close()
	except Exception as ex:
		print(ex)
		messages = []
		pass
	

	guild = client.get_guild(guild_id)
	for user in guild.members:
		messages.append(User(user.id,user.name))
		pass
	if(channel_id == -1):
		for channel in guild.channels:
			if(channel.type == discord.ChannelType.text):
				archived = True
				if check_category_name:
					if channel.category is not None:
						if "archives" in channel.category.name.lower() and "bios" not in channel.name:
							archived = True
						else:
							archived = False
					else: 
						archived = False
				messages.append(Channel(channel.id,channel.name,channel.category.name,archived))
				await archive_channel(client,channel,file_name)
	else:
		channel = guild.get_channel(channel_id)
		messages.append(Channel(channel.id,channel.name,str(channel.category.name),True))
		await archive_channel(client,channel,file_name)

async def archive_channel(client,channel,file_name):
	global check_category_name
	global download_avatars
	global time_since_last_downloaded
	global messages

	if str(channel.id) in get_channels():
		print("skipping "+str(channel.id)+"; already archived.")
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
					attachments = []
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
						for attachment in message.attachments:
							attachment_url = attachment.url
							attachment = folder_name+"/"+str(message.id)+"-"+attachment.filename
							attachments.append(attachment)
							if not os.path.exists(attachment):
								while time_since_last_downloaded + 3 >= time.time():
									pass
								req = urllib.request.Request(
									attachment_url, 
									data=None, 
									headers={
										'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
									}
								)

								f2 = urllib.request.urlopen(req)
								f3 = open(attachment,"xb")
								f3.write(f2.read())
								f3.close()
								time_since_last_downloaded = time.time()
								print("downloaded "+attachment)
						links = re.findall('((http)(.*?)(discord)(.*?)(/attachments/)(.*?)/(.*?)/(.*))([a-z0-9])', message.content)
						for link in links:
							attachment_url = link[0]
							attachment = folder_name+"/"+str(message.id)+"-"+link[len(link)-2]+link[len(link)-1]
							try:
								print(link, "\nmatched",attachment)
								attachments.append(attachment)
								if not os.path.exists(attachment):
									while time_since_last_downloaded + 3 >= time.time():
										pass
									req = urllib.request.Request(
										attachment_url, 
										data=None, 
										headers={
											'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
										}
									)

									f2 = urllib.request.urlopen(req)
									f3 = open(attachment,"xb")
									f3.write(f2.read())
									f3.close()
									time_since_last_downloaded = time.time()
									print("downloaded "+attachment)
							except Exception as ex:
								print("could not download",attachment+":",ex)
					msg_id = message.id
					channel = message.channel.id
					author = message.author.name.replace("\"","'")
					content = str(message.content.replace("\\","/").replace("\"","'").replace("\n","\\n"))
					timestamp = str(int(message.created_at.timestamp()))

					messages.append(Message(msg_id,avatar,author,channel,content,timestamp,is_fictional,attachments))
	except discord.errors.Forbidden:
		print("Channel "+channel.name+" is locked from the bot.")
		pass
	f = open(file_name,'w')
	fuck = json.dumps(messages,cls=MessageEncoder).replace("},","}\n")
	f.write(fuck[0:len(fuck)-1])
	f.close()
	print(format("parsed %d messages" % len(messages)))

client = discord.Client(
	intents=discord.Intents(
		message_content=True,
		guild_messages=True,
		guilds=True,
		members=True,
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

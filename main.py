import discord

client = discord.Client()
bots_only = False

@client.event
async def on_ready():
	guild_id = -1
	channel_id = -1

	# ask for the guild id
	while guild_id <= -1:
		try:
			guild_id = int(input("Enter the ID of the server you want to look in: "))
		except:
			print("Invalid number")

	# ask for the channel id, and let us default to all of them.
	valid_channel_id_given = False
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

	await archive_guild(guild_id,channel_id,file_name+".json")
	await client.close()

@client.event
async def archive_guild(guild_id,channel_id,file_name):
	# clear the file
	f = open(file_name,'w')
	f.write("")
	f.close()
	guild = client.get_guild(guild_id)
	if(channel_id == -1):
		for channel in guild.channels:
			if(channel.type == discord.ChannelType.text):
				await archive_channel(channel,file_name)
	else:
		await archive_channel(guild.get_channel(channel_id),file_name)

@client.event
async def archive_channel(channel,file_name):
	# start 
	f = open(file_name,'a')
	try:
		async for message in channel.history(limit=1000000):
			is_fictional = False
			if message.webhook_id:
				is_fictional = True
			if(is_fictional == True or bots_only == False):
					content = message.content.replace("\\","\\\\",999999).replace("\n"," ",999999).replace("\"","'",999999)
					f.write('{"author": "%s", "channel": "%s", "content": "%s", "timestamp": "%s", "fictional": "%s"}\n' % (message.author.name,message.channel.name,content,int(message.created_at.timestamp()),is_fictional))
	except discord.errors.Forbidden:
		print("Channel "+channel.name+" is locked from the bot.")
		pass
	f.close()

f = open("key","r")
if f is None:
	print("No key file found.")
else:
	client.run(f.read())
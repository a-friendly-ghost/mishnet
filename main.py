import discord , io , os , random , re , time , asyncio
from dotenv import load_dotenv

# load environment variables
load_dotenv()

# instantiate client
client = discord.Client()
clientUser = discord.ClientUser

async def webhook_get(channel: discord.TextChannel):
	try:
		for webhook in await channel.webhooks():
			if webhook.token: return webhook

		print('making webhook for '+channel.name)
		return await channel.create_webhook(
			name="mishnet webhook",
			reason="yeah"
		)
	except discord.HTTPException as e:
		messages = [
			"there has been a http error.",
			"oopsie doopsie! da http went fucky wucky! 3:",
			"oopsie woopsie our code kitty is hard at work.",
		]
		await channel.send(random.choice(messages))
		return None
	except discord.Forbidden as e:
		await channel.send("missing 'manage webhook' perms >:(")
		return None

async def bridge(channel , message , name , pfp):
	webhook = await webhook_get(channel)
	if not webhook:
		await message.channel.send('webhook error')
	await webhook.send(allowed_mentions=discord.AllowedMentions.none(), content=message, username=name, avatar_url=pfp)

def cut(string , length):
	return string[0:length-4] + '...'

@client.event
async def on_ready():
	print(f'{client.user} has connected to Discord!')
	global connected , hallowspeak
	mishserver = client.get_channel(915251024174940160)
	agonyserver = client.get_channel(746466196978794517)
	cpserver = client.get_channel(987001423977914428)
	ccjserver = client.get_channel(629816294870351884)
	hallowspeak = client.get_channel(986616150492323840)
	connected = [mishserver , agonyserver , cpserver , ccjserver , hallowspeak]

	global serverNames
	serverNames = {
		mishserver : 'mishserver',
		agonyserver : 'agonyserver',
		cpserver : 'conphon',
		ccjserver : 'ccj',
		hallowspeak : 'Hallowspeak'
	}

@client.event
async def on_message(message):

	if message.author.bot:
		return

	if message.channel in connected:
		if message.content == "perftest": startTime = time.perf_counter()
		sendList = [i for i in connected if i.guild != message.channel.guild]

		toSend = message.content + ' ' + ' '.join([i.url for i in message.attachments])
		name = message.author.name + ', from ' + serverNames[message.channel]
		pfp = message.author.avatar_url

		loop = asyncio.get_running_loop()
		for channel in sendList:
			loop.create_task(bridge(channel , toSend , name , pfp))

		if message.content == "perftest":
			endTime = time.perf_counter()
			toSend = "bridge time: " + str(endTime - startTime)
			for channel in connected:
				loop.create_task(bridge(channel, toSend, name, pfp))

	return

#start bot
client.run(os.getenv('TOKEN'))
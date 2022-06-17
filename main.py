import discord, io, os, random, sys, time, asyncio
from dotenv import load_dotenv
from message_associations import MessageAssociations

# load environment variables
load_dotenv()

# instantiate client
client = discord.Client()
associations = MessageAssociations()

@client.event
async def on_ready():
	print(f'{client.user} has connected to Discord!')
	global connected, hallowspeak
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
async def on_message(message: discord.Message):
	if message.author.bot:
		return

	if message.channel in connected:
		if message.content == "perftest": 
			startTime = time.perf_counter()
		
		target_channels = [i for i in connected if i.guild != message.channel.guild]
		to_send = message.content + ' ' + ' '.join([i.url for i in message.attachments])
		name = message.author.name + ', from ' + serverNames[message.channel]
		pfp = message.author.avatar_url

  		# run every message sending thingy in parallel
		await asyncio.gather(*[bridge(message , channel , to_send , name , pfp) for channel in target_channels])

		if message.content == "perftest":
			endTime = time.perf_counter()
			to_send = "bridge time: " + str(endTime - startTime)
			loop = asyncio.get_event_loop()
			for channel in connected:
				loop.create_task(bridge(message, channel, to_send, name, pfp))

async def bridge(original_message: discord.Message, target_channel: discord.TextChannel, to_send: str, name: str, pfp: discord.Asset):
	webhook = await get_webhook_for_channel(target_channel)
	copy_message = await webhook.send(
		allowed_mentions=discord.AllowedMentions.none(), 
		content=to_send, 
		username=name, 
		avatar_url=pfp, 
		wait=True,
	)
	assert copy_message is not None
	associations.add_copy(original_message, copy_message)

async def get_webhook_for_channel(channel: discord.TextChannel):
	# webhooks that we own have a non-None token attribute
	for webhook in await channel.webhooks():
		if webhook.token:
			return webhook

	print(f"Making webhook for {channel.name}...")
	return await channel.create_webhook(name="mishnet webhook", reason="yeah")

@client.event
async def on_message_delete(message: discord.Message):
	for associated_message in associations.retrieve_others(message):
		print(f"{associated_message=}")
		await associated_message.delete()

@client.event
async def on_error(event, *args, **kwargs):
	# FIXME: this is _the_ most horrible way to find the channel. please for the love of god fix this
	for arg in args:
		if hasattr(arg, "channel") and isinstance(arg.channel, discord.TextChannel):
			channel = arg.channel
			break
	else:
		# no channel to send error message to, cope
		return

	exception_type, exception_instance, traceback = sys.exc_info()
	messages = [
		"there has been a http error happening here in the code. yes",
		"oopsie doopsie! da http went fucky wucky!",
		"oopsie woopsie our code kitty is hard at work",
		"https://tenor.com/brsRI.gif",
		"amoung us",
	]
	await channel.send(f"{random.choice(messages)}: {str(exception_instance)}")

# start bot
client.run(os.getenv('TOKEN'))
import discord, io, os, random, sys, time, asyncio, re
from dotenv import load_dotenv
from message_associations import MessageAssociations
from typing import Union
import traceback

# load environment variables
load_dotenv()

# instantiate client
client = discord.Client()
global associations
associations = MessageAssociations()

@client.event
async def on_ready():
	print(f'{client.user} has connected to Discord!')

	mishserver = client.get_channel(915251024174940160)
	agonyserver = client.get_channel(746466196978794517)
	cpserver = client.get_channel(987001423977914428)
	ccjserver = client.get_channel(629816294870351884)
	hallowspeak = client.get_channel(986616150492323840)
	global mishnet1 , mishnet_channels
	mishnet1 = [mishserver , agonyserver , cpserver , ccjserver , hallowspeak]
	mishnet_channels = [mishnet1]

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
	if message.author.bot or message.channel not in mishnet1:
		return

	if message.content == "perftest": 
		startTime = time.perf_counter()

	for group in mishnet_channels: # feeling like this would be another application for the associations data structure, but we made it only work for storing messages
		if message.channel in group:
			mishnet_channel = group
	
	target_channels = [i for i in mishnet_channel if i.guild != message.channel.guild]
	name = message.author.name + ', from ' + serverNames[message.channel]
	pfp = message.author.avatar_url

 		# run every message sending thingy in parallel
	await asyncio.gather(*[bridge(message , channel , name , pfp) for channel in target_channels])

	if message.content == "perftest":
		endTime = time.perf_counter()
		to_send = "bridge time: " + str(endTime - startTime)
		loop = asyncio.get_event_loop()
		for channel in mishnet_channel:
			loop.create_task(bridge(message, channel, name, pfp, content_override=to_send)) # is this a bad way to do this

async def create_to_send(message: discord.Message, target_channel: discord.TextChannel) -> str:
	# i know this is not the most compact way to write this function, but it's the cleanest and nicest imo. optimise it if you want
	to_send = ''
	
	if message.reference:
		replied_message = await message.channel.fetch_message(message.reference.message_id)

		funny = random.randint(1,100)
		if funny == 1: # i'm really funny
			link_text = 'zelda'
		else:
			link_text = 'link'

		replied_partial_message = message.channel.get_partial_message(replied_message.id)
		link_url = 'link not found'
		for copy in associations.retrieve_others(replied_partial_message):
			if copy.channel.id == target_channel.id:
				link_url = copy.jump_url
				break

		to_send += f"> **{re.sub(', from .*', '', replied_message.author.name)}** [{link_text}]({link_url})" + '\n> ' + replied_message.content.replace('\n','\n> ') + '\n' # fstring cannot contain a backslash???
	
	to_send += message.content
	to_send += ' ' + ' '.join([attachment.url for attachment in message.attachments])
	return to_send

async def bridge(original_message: discord.Message, target_channel: discord.TextChannel, name: str, pfp: discord.Asset, content_override = False):
	webhook = await get_webhook_for_channel(target_channel)
	if content_override:
		to_send = content_override
	else:
		to_send = await create_to_send(original_message, target_channel)
	copy_message = await webhook.send(
		allowed_mentions=discord.AllowedMentions.none(), 
		content=to_send, 
		username=name, 
		avatar_url=pfp, 
		wait=True,
	)
	assert copy_message is not None
	associations.add_copy(original_message.channel.get_partial_message(original_message.id), target_channel.get_partial_message(copy_message.id))

async def get_webhook_for_channel(channel: discord.TextChannel):
	# webhooks that we own have a non-None token attribute
	for webhook in await channel.webhooks():
		if webhook.token:
			return webhook

	print(f"Making webhook for {channel.name}...")
	return await channel.create_webhook(name="mishnet webhook", reason="what are you a cop?")

@client.event
async def on_message_delete(message: discord.Message):
	if message.channel not in mishnet1:
		return

	original_partial_message = message.channel.get_partial_message(message.id)
	
	if original_partial_message not in associations.internal:
		return

	try:
		await asyncio.gather(*[associated_partial_message.delete() for associated_partial_message in associations.retrieve_others(original_partial_message)])
		# this is both to clean up the database, and also so that it can check whether the message has already been deleted, so it doesn't try to delete it again
		associations.internal.pop(original_partial_message)
	except discord.errors.NotFound:
		pass

@client.event
async def on_bulk_message_delete(messages: list[discord.Message]):
	for message in messages:
		for associated_message_id in associations.retrieve_others(message.id):
			associated_message = await message.channel.fetch_message(associated_message_id)
			await associated_message.delete()

@client.event
async def on_reaction_add(reaction: discord.Reaction, member: Union[discord.Member, discord.User]):
	if reaction.message.channel not in mishnet1:
		return

	if reaction.emoji == "❌":

		reacted_partial_message = reaction.message.channel.get_partial_message(reaction.message.id)

		if reacted_partial_message not in associations.internal:
			return

		# partialMessage:s don't have a .author attribute, so i need to convert it to a normal Message. how efficiential
		original_message = await associations.retrieve_others(reacted_partial_message)[0].fetch() # the first one in the value list is also the key
		if original_message.author.id != member.id: # message.author is a user, so i compare ids
			if isinstance(member, discord.Member) and discord.Permissions.manage_messages not in reaction.message.channel.permissions_for(member):
				return

		try:
			await asyncio.gather(*[associated_partial_message.delete() for associated_partial_message in [*associations.retrieve_others(reacted_partial_message), reacted_partial_message]])
			assert associations.retrieve_others(reacted_partial_message)[0] in associations.keys() # i think so
			associations.internal.pop(associations.retrieve_others(reacted_partial_message)[0]) 
			# this is both to clean up the database, and also so that it can check whether the message has already been deleted, so it doesn't try to delete it again
		except discord.errors.NotFound:
			pass

@client.event
async def on_message_edit(before , after):
	if before.channel not in mishnet1:
		return
	if before.author.bot:
		return

	assert before.id == after.id

	original_partial_message = before.channel.get_partial_message(before.id) # converts before (discord.Message) into a discord.PartialMessage

	try:
		for associated_partial_message in associations.retrieve_others(original_partial_message): # i don't know how to gather this
			webhook = await get_webhook_for_channel(associated_partial_message.channel)
			await webhook.edit_message(associated_partial_message.id, content=after.content)	
	except discord.errors.Forbidden as e: # idk why the error is happening so, cope # future mish here, i think i fixed this so this error will never happen, but idk can't be too safe
		print(e)
		pass

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

	exception_type, exception, exc_traceback = sys.exc_info()
	messages = [
		"oopsie doopsie! da http went fucky wucky! {}",
		"oopsie woopsie our code kitty is hard at work: {}",
		"when the exception is sus: {}",
		"exception messag {} e (sussy)" # added spaces around the exception, now it looks intentional
	]
	await channel.send(random.choice(messages).format(str(exception)))

 	# this is just hackish debugging
	traceback.print_exception(exception_type, exception, exc_traceback)

# start bot
client.run(os.getenv('TOKEN'))
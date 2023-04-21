import discord, io, os, random, sys, time, asyncio, re
from dotenv import load_dotenv
from imstupid import MessageAssociations, TheOriginalMessageHasAlreadyBeenDeletedYouSlowIdiotError
from typing import Union
from collections import Counter
import traceback

# load environment variables
load_dotenv()

# instantiate client
client = discord.Client(intents=discord.Intents.all())
associations = MessageAssociations()

mishnet_channels = None

@client.event
async def on_ready():
	print(f'{client.user} has connected to Discord!')

	mishserver = client.get_channel(915251024174940160)
	agonyserver = client.get_channel(746466196978794517)
	cpserver = client.get_channel(987001423977914428)
	ccjserver = client.get_channel(629816294870351884)
	hallowspeak = client.get_channel(986616150492323840)
	prolangs = client.get_channel(988876878582546472)
	meriakcottage = client.get_channel(1046824467055263824)
	noellecord = client.get_channel(1058818319890792588)
	digiserver = client.get_channel(1070736308806373457)
	merrycord = client.get_channel(1085661170637226124)
	ostracod = client.get_channel(1093661502084493422)
	osscord = client.get_channel(1099099975369101385)

	mishserver2 = client.get_channel(1006522289048784967)
	agonyserver2 = client.get_channel(1006237275664949349)
	cpserver2 = client.get_channel(1006522209872920618)
	ccjserver2 = client.get_channel(1055428091285086218)
	hallowspeak2 = client.get_channel(1006526679071596574)
	prolangs2 = client.get_channel(1006660045511086080)
	meriakcottage2 = client.get_channel(964755175770325002)
	noellecord2 = client.get_channel(1058818153192366171)
	digiserver2 = client.get_channel(1070736404155478137)
	merrycord2 = client.get_channel(1085661144573816842)
	ostracod2 = client.get_channel(1093661477111611443)
	osscord2 = client.get_channel(1099099944054444067)

	global mishnet1 , mishnet2 , mishnet_channels
	mishnet1 = [mishserver ,  agonyserver ,  cpserver ,  ccjserver ,  hallowspeak ,  prolangs ,  meriakcottage ,  noellecord ,  digiserver , merrycord , ostracod , osscord] # conlanging
	mishnet2 = [mishserver2 , agonyserver2 , cpserver2 , ccjserver2 , hallowspeak2 , prolangs2 , meriakcottage2 , noellecord2 , digiserver2 , merrycord2 , ostracod2 , osscord2] # general
	mishnet_channels = [mishnet1 , mishnet2]

	global serverNames
	serverNames = {
		mishserver : 'mishserver',
		agonyserver : 'agonyserver',
		cpserver : 'conphon',
		ccjserver : 'ccj',
		hallowspeak : 'Hallowspeak',
		prolangs : 'prolangs',
		meriakcottage : 'mɛriak cottage',
		noellecord : 'noellecord',
		digiserver : 'digiserver',
		merrycord : 'merrycord',
		ostracod : 'ostracod conlangs',
		osscord : 'osscord',

		mishserver2 : 'mishserver',
		agonyserver2 : 'agonyserver',
		cpserver2 : 'conphon',
		ccjserver2: 'ccj',
		hallowspeak2 : 'Hallowspeak',
		prolangs2 : 'prolangs',
		meriakcottage2 : 'mɛriak cottage',
		noellecord2 : 'noellecord',
		digiserver2 : 'digiserver',
		merrycord2 : 'merrycord',
		ostracod2 : 'ostracod conlangs',
		osscord2 : 'osscord'
	}

	global banlist
	kafka = 708095054748844082
	banlist = [kafka]

@client.event
async def on_message(message: discord.Message):

	while mishnet_channels == None:
		await asyncio.sleep(0.1)

	mishnet_channel = None
	for group in mishnet_channels: # feeling like this would be another application for the associations data structure, but we made it only work for storing messages
		if message.channel in group:
			mishnet_channel = group

	if not mishnet_channel:
		return

	if message.webhook_id: # avoids unnecessarily checking all this
		channelWebhooks = await message.channel.webhooks()
		for webhook in channelWebhooks:
			if webhook.id == message.webhook_id:
				if webhook.token:
					# this webhook is from mishnet
					return

	if message.author.id in banlist:
		try:
			await message.delete()
		except:
			pass
		return

	if message.content == "perftest": 
		startTime = time.perf_counter()
	
	target_channels = [i for i in mishnet_channel if i.guild != message.channel.guild]
	name = message.author.name + ', from ' + serverNames[message.channel]
	pfp = message.author.display_avatar.url
 	# run every message sending thingy in parallel
	duplicate_messages = await asyncio.gather(*[bridge(message , channel , name , pfp) for channel in target_channels])
	try:
		associations.set_duplicates(message, duplicate_messages)
	except TheOriginalMessageHasAlreadyBeenDeletedYouSlowIdiotError:
		# fuck shit piss delete them all again ig
		await asyncio.gather(*[message.delete() for message in duplicate_messages])

	if message.content == "perftest":
		endTime = time.perf_counter()
		to_send = "bridge time: " + str(endTime - startTime)
		loop = asyncio.get_event_loop()
		for channel in mishnet_channel:
			loop.create_task(bridge(message, channel, name, client.user.display_avatar.url, content_override=to_send)) # is this a bad way to do this

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

		# there is zero need to get the partial message here
		replied_partial_message = message.channel.get_partial_message(replied_message.id)
		link_url = replied_partial_message.jump_url
		
		reply_text = replied_message.content
		
		reply_text = re.sub(r"(?<!\]\()(?<!<)(https?:\/\/[^ \n]+)" , r"<\1>" , reply_text) # unembeds a link inside the quote block -- thank u taswelll for the help!
		# future mish: thank you taswelll for fixing your own code when it broke!

		reply_text += ' ' + ' '.join([f"<{attachment.url}>" for attachment in replied_message.attachments])

		# me on my way to modify code to make it less compact
		to_send += f'> **{re.sub(", from .*" , "" , replied_message.author.name)}** [{link_text}]({link_url})'
		to_send += ''.join([ ('\n> '+line) for line in reply_text.split('\n') ])
		to_send += '\n'

	to_send += message.content
	
	# cry about it
	to_send = re.sub(r"https://discord(?:app)?.com/channels/(\d+)/(\d+)/(\d+)", lambda x : next((copy.jump_url for copy in associations.retrieve_others( discord.PartialMessage(channel=client.get_channel(int(x.group(2))) , id=int(x.group(3))) ) if copy.channel.id == target_channel.id),"link not found"), to_send)
	# future mish here: i am crying about it actually thanks
	# future future mish here (multiple months later): what the actual fuck what was wrong with you (me)

	to_send += ' ' + ' '.join([attachment.url for attachment in message.attachments])
	
	if 'mishdebug' in to_send:
		to_send = '```' + repr(to_send.replace('```','')) + '```'
	
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
	return copy_message

async def get_webhook_for_channel(channel: discord.TextChannel):
	# webhooks that we own have a non-None token attribute
	for webhook in await channel.webhooks():
		if webhook.token:
			return webhook

	print(f"Making webhook for {channel.name}...")
	return await channel.create_webhook(name="mishnet webhook", reason="what are you a cop?")

@client.event
async def on_message_delete(message: discord.Message):
	# FIXME: factor into is_mishnet_channel()
	if message.channel not in [channel for group in mishnet_channels for channel in group]: # i actually fucking hate that this is how you do this
		return

	if message not in associations:
		associations.remove(message)
		return

 	# ensure we have original message (mod may have deleted duplicate message)
	original_message = associations.to_original(message)
	duplicates = associations.get_duplicates_of(original_message)

	# now we can remove it (AFTER fetching the duplicates, IDIOT)
	associations.remove(message)

	async def delete(message):
		try:
			await message.delete()
		except discord.errors.NotFound:
			pass
	await asyncio.gather(*[delete(duplicate) for duplicate in duplicates])

@client.event
async def on_bulk_message_delete(messages: list[discord.Message]):
	for message in messages:
		for associated_message_id in associations.retrieve_others(message.id):
			associated_message = await associated_message.channel.fetch_message(associated_message_id)
			await associated_message.delete()

def total_reactions(message: discord.Message) -> Counter[str]:
	counter = Counter[str]()
	all_message = associations.retrieve_others(message) + [message]
	for message in all_message:
		for reaction in message.reactions:
			counter[reaction.emoji] += reaction.count
	return counter

		# just for displaying data. no business logic allowed!!! >:(((
# why did you indent that linus
class SuperCoolReactionView(discord.ui.View):
	def __init__(self, reaction_counts: Counter[str]):
		super().__init__() # omg super() i learnt what that does like a week ago
		# add button for each reaction thingy
		# FIXME: what about max items?
		for emoji, count in reaction_counts.items():
			self.add_item(discord.ui.Button(label=count, emoji=emoji, disabled=True))

@client.event
async def on_reaction_add(reaction: discord.Reaction, member: Union[discord.Member, discord.User]):
	#FIXME: X-reaction is out of date. should mirror on_message_delete but doesn't
	
	print("reaction addded!!!!!dd")

	if reaction.message.channel not in [channel for group in mishnet_channels for channel in group]:
		return

	# FIXME: maybe we can just delete whatever message was reacted to, and then let the on_message_delete handler handle the rest?
	if reaction.emoji == "❌":
		reacted_partial_message = reaction.message.channel.get_partial_message(reaction.message.id)

		if reacted_partial_message not in associations:
			return

		# partialMessage's don't have a .author attribute, so i need to convert it to a normal Message. how efficiential
		original_message = await associations.to_original.fetch()
		if original_message.author.id != member.id: # message.author is a user, so i compare ids
			if isinstance(member, discord.Member) and discord.Permissions.manage_messages not in reaction.message.channel.permissions_for(member):
				return

		associations.remove(original_message)

		try:
			await asyncio.gather(*[associated_partial_message.delete() for associated_partial_message in [*associations.retrieve_others(reacted_partial_message), reacted_partial_message]])
			# this is both to clean up the database, and also so that it can check whether the message has already been deleted, so it doesn't try to delete it again
		except discord.errors.NotFound:
			pass

	print("mmm yes adding view")
	reactions = total_reactions(reaction.message)
	view = SuperCoolReactionView(reactions)
	messages = associations.retrieve_others(reaction.message) + [reaction.message]
	return await asyncio.gather(*[message.edit(view=view) for message in messages])

@client.event
async def on_message_edit(before , after):
	print('gay sex (debug)')
	if before.content == after.content: return
	# a message embedding counts triggers on message edit, which is cringe but this solves that

	if before.channel not in [channel for group in mishnet_channels for channel in group]: return
	if before.author.bot: return

	assert before.id == after.id

	original_partial_message = before.channel.get_partial_message(before.id) # converts before (discord.Message) into a discord.PartialMessage

	async def edit_copy(partial_message: discord.PartialMessage , after_message: discord.Message):
		webhook = await get_webhook_for_channel(partial_message.channel)
		toEdit = await create_to_send(after_message , partial_message.channel)
		return await webhook.edit_message(partial_message.id, content=toEdit)

	wait_time = 0
	while wait_time < 2:	
		try:
			duplicate_messages = associations.get_duplicates_of(original_partial_message)
			return await asyncio.gather(*[edit_copy(m , after) for m in duplicate_messages])
		except discord.errors.Forbidden as e: # idk why the error is happening so, cope # future mish here, i think i fixed this so this error will never happen, but idk can't be too safe
			await asyncio.wait(0.1)
			wait_time += 0.1
			print('edit waited')
	raise TimeoutError

# it goes here. fuck you
messages = [
	"oopsie doopsie! da code went fucky wucky! {}",
	"oopsie woopsie our code kitty is hard at work: {}",
	"when the exception is sus: {}",
	"the compiler explaining why {}:\nhttps://tenor.com/bGzoN.gif",
	"exception messag {} e (sussy)" # added spaces around the exception, now it looks intentional
]
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

	if channel  in [i for group in mishnet_channels for i in group]: # mishnet keeps clogging general
		await channel.send(random.choice(messages).format(str(exception)))

 	# this is just hackish debugging
	traceback.print_exception(exception_type, exception, exc_traceback)

# start bot
client.run(os.getenv('TOKEN'))
import discord, io, os, random, sys, time, asyncio, re
from dotenv import load_dotenv
from imstupid import MessageAssociations, TheOriginalMessageHasAlreadyBeenDeletedYouSlowIdiotError, get_mishnick_or_username
from typing import Union
from collections import Counter
import traceback
import psycopg

# load environment variables
load_dotenv()

# instantiate client
client = discord.Client(intents=discord.Intents.all())
associations = MessageAssociations()
prefix = 'mn!'

mishnet_channels = None

if sys.platform == 'win32':
	asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())	

# hello this is mish!
# note on the inconsistent terminology for folks reading through my shit code for some godforsaken reason
# a "mishnet general" and "mishnet conlanging" are mishnet channels
# just "channel" though refers to like, the discord channels, also called nodes when i remember to call them that

ready = False

async def get_webhook_for_channel(channel: discord.TextChannel):
	# webhooks that we own have a non-None token attribute
	for webhook in await channel.webhooks():
		if webhook.token:
			return webhook

	print(f"Making webhook for {channel.name}...")
	return await channel.create_webhook(name="mishnet webhook", reason="what are you a cop?")

@client.event
async def on_ready():
	print('on ready begin')

	print(f'{client.user} has connected to Discord!')

	# todo: store these more neatly
	# oh my god mish please do this -mish

	mishserver = client.get_channel(915251024174940160)
	agonyserver = client.get_channel(746466196978794517)
	cpserver = client.get_channel(987001423977914428)
	ccjserver = client.get_channel(629816294870351884)
	hallowspeak = client.get_channel(986616150492323840)
	prolangs = client.get_channel(988876878582546472)
	meriakcottage = client.get_channel(1046824467055263824)
	digiserver = client.get_channel(1070736308806373457)
	merrycord = client.get_channel(1085661170637226124)
	ostracod = client.get_channel(1093661502084493422)
	osscord = client.get_channel(1099099975369101385)
	conserver = client.get_channel(1114983071083667657)
	marciland = client.get_channel(1115636041475440750)
	primistan = client.get_channel(1118593147451211776)
	kathycord = client.get_channel(1118827288641941535)

	mishserver2 = client.get_channel(1006522289048784967)
	agonyserver2 = client.get_channel(1006237275664949349)
	cpserver2 = client.get_channel(1006522209872920618)
	ccjserver2 = client.get_channel(1055428091285086218)
	hallowspeak2 = client.get_channel(1006526679071596574)
	prolangs2 = client.get_channel(1006660045511086080)
	meriakcottage2 = client.get_channel(964755175770325002)
	digiserver2 = client.get_channel(1070736404155478137)
	merrycord2 = client.get_channel(1085661144573816842)
	ostracod2 = client.get_channel(1093661477111611443)
	osscord2 = client.get_channel(1099099944054444067)
	conserver2 = client.get_channel(1114983094630490133)
	marciland2 = client.get_channel(1115635971216650271)
	primistan2 = client.get_channel(1118593123426250872)
	kathycord2 = client.get_channel(1118827217691099226)

	global mishnet1 , mishnet2 , mishnet_channels
	mishnet1 = [mishserver ,  agonyserver ,  cpserver ,  ccjserver ,  hallowspeak ,  prolangs ,  meriakcottage ,  digiserver , merrycord , ostracod , osscord , conserver , marciland , primistan , kathycord] # conlanging
	mishnet2 = [mishserver2 , agonyserver2 , cpserver2 , ccjserver2 , hallowspeak2 , prolangs2 , meriakcottage2 , digiserver2 , merrycord2 , ostracod2 , osscord2 , conserver2 , marciland2 , primistan2 , kathycord2] # general
	mishnet_channels = [mishnet1 , mishnet2]

	print('all channels gotten')

	global serverNames
	serverNames = {
		mishserver : 'mishserver',
		agonyserver : 'agonyserver',
		cpserver : 'conphon',
		ccjserver : 'ccj',
		hallowspeak : 'Hallowspeak',
		prolangs : 'prolangs',
		meriakcottage : 'mɛriak cottage',
		digiserver : 'digiserver',
		merrycord : 'merrycord',
		ostracod : 'ostracod conlangs',
		osscord : 'osscord',
		conserver : 'conserver',
		marciland : 'marciland' ,
		primistan : 'primistan',
		kathycord : 'kathycord',

		mishserver2 : 'mishserver',
		agonyserver2 : 'agonyserver',
		cpserver2 : 'conphon',
		ccjserver2: 'ccj',
		hallowspeak2 : 'Hallowspeak',
		prolangs2 : 'prolangs',
		meriakcottage2 : 'mɛriak cottage',
		digiserver2 : 'digiserver',
		merrycord2 : 'merrycord',
		ostracod2 : 'ostracod conlangs',
		osscord2 : 'osscord',
		conserver2 : 'conserver',
		marciland2 : 'marciland',
		primistan2 : 'primistan',
		kathycord2 : 'kathycord'
	}

	global webhooks
	webhooks = {}
	for mishnet_channel in mishnet_channels:
		for node in mishnet_channel:
			webhooks[node] = await get_webhook_for_channel(node)

	print('all webhooks cached')

	global banlist
	kafka = 708095054748844082
	mimubot = 493716749342998541
	dmitrij = 239165690232307713
	echo = 472692106150805505
	yuphph = 127243394559770624
	banlist = [kafka, mimubot, dmitrij, echo, yuphph]

	global ready
	ready = True
	print('on ready end')

async def get_replied_message(original_message: discord.Message) -> discord.Message:

	replied_message_reference = original_message.reference
	if replied_message_reference:
		return await original_message.channel.fetch_message(replied_message_reference.message_id)
	
	if original_message.embeds:
		embed_desc = original_message.embeds[0].description
		if embed_desc:
			regex_result = re.search(r"\[(?:Reply to:|\(click to see attachment\))\]\(https://discord(?:app)?.com/channels/(\d+)/(\d+)/(\d+)\)" , embed_desc)
			if regex_result:
				return await original_message.channel.fetch_message(regex_result.group(3)) # create_to_send() will do the job of translating this into the version of the message from each server, does not need to be done heres
		
	return None

def prune_replies(content: str, length_limit: int) -> str:

	def find_depth(line):
		depth = 0
		for index in range(0, len(line)+1, 2):
			if line[index:index+2] == '> ':
				depth += 1
			else:
				return depth

	lines_depths = [ ( line , find_depth(line) ) for line in content.split('\n') ]
	max_depth = max([i[1] for i in lines_depths])
	for current_depth in range(max_depth , 0 , -1): # goes from max_depth to *1*, not to 0, because uhhhhhhhhhhhhhhhhhhhhhhhh
		if len( '\n'.join([i[0] for i in lines_depths]) ) < length_limit:
			break
		else:
			prune_position = next(index for index , i in enumerate(lines_depths) if i[1] == current_depth)
			lines_depths = [ (line , depth) for (line , depth) in lines_depths if depth < current_depth ]
			lines_depths.insert(prune_position , (f"{'> '*current_depth}{max_depth-current_depth+1} more replies" , current_depth) ) # this cannot be inserted at the end because it is part of the message's length
	
	return '\n'.join([i[0] for i in lines_depths])

async def create_to_send(content: str, target_channel: discord.TextChannel, replied_message, stickers) -> str:
	# i know this is not the most compact way to write this function, but it's the cleanest and nicest imo. optimise it if you want
	to_send = ''
	
	if replied_message:
		funny = random.randint(1,100)
		if funny == 1: # i'm really funny
			link_text = 'zelda'
		else:
			link_text = 'link'

		link_url = replied_message.jump_url
		reply_text = replied_message.content
		
		reply_text = re.sub(r"(?<!\]\()(?<!<)(https?:\/\/[^ \n]+)" , r"<\1>" , reply_text) # unembeds a link inside the quote block -- thank u taswelll for the help!
		# future mish: thank you taswelll for fixing your own code when it broke!

		reply_text += ' ' + ' '.join([f"[(🖼️)](<{attachment.url}>)" for attachment in replied_message.attachments])

		# me on my way to modify code to make it less compact
		repliee_name = await get_mishnick_or_username(conn, replied_message.author)
		to_send += f'> **{re.sub(r", from .*" , "" , repliee_name)}** [{link_text}]({link_url})' # removes server from user's name
		to_send += ''.join([ ('\n> '+line) for line in reply_text.split('\n') ])
		to_send += '\n'

	if content.startswith('> '): # separates reply quote blocks and quote blocks already in the message
		to_send += '\n'

	to_send += content

	to_send += ' ' + ' '.join(sticker.url for sticker in stickers)

	# cry about it
	to_send = re.sub(r"https://discord(?:app)?.com/channels/(\d+)/(\d+)/(\d+)", lambda x : next((copy.jump_url for copy in associations.retrieve_others( discord.PartialMessage(channel=client.get_channel(int(x.group(2))) , id=int(x.group(3))) ) if copy.channel.id == target_channel.id),"link not found"), to_send)
	# future mish here: i am crying about it actually thanks
	# future future mish here (multiple months later): what the actual fuck what was wrong with you (me)
	
	if 'mishdebug' in to_send:
		to_send = '```' + repr(to_send.replace('```','')) + '```'

	if len(to_send) > 2000:
		to_send = prune_replies(to_send , 2000)
	
	return to_send

async def bridge(
		content, 
		target_channel: discord.TextChannel, 
		replied_message, 
		name: str, 
		pfp: discord.Asset, 
		attachment_files,
		stickers,
		ping: bool, 
		):
	
	webhook = webhooks[target_channel]

	to_send = await create_to_send(content, target_channel, replied_message, stickers)
	attachments_to_files = await asyncio.gather(*[attachment.to_file(spoiler=attachment.is_spoiler()) for attachment in message.attachments])

	copy_message = await webhook.send(
		allowed_mentions = discord.AllowedMentions.all() if ping else discord.AllowedMentions.none(),
		content = to_send, 
		username = name, 
		avatar_url = pfp, 
		wait = True,
		files = attachments_to_files if attachments_to_files != [] else discord.utils.MISSING # i hate this
	)
	
	return copy_message

@client.event
async def on_message(message: discord.Message):

	while ready == False:
		await asyncio.sleep(0.1)

	# ensure not bridging bridged messages themselves or responding to bridged commands
	if message.webhook_id: # avoids unnecessarily checking all this
		channelWebhooks = await message.channel.webhooks()
		for webhook in channelWebhooks:
			if webhook.id == message.webhook_id:
				if webhook.token:
					# this webhook is from mishnet
					return

	# commands

	if message.content.startswith(prefix+'help') or message.content.startswith(prefix+'info'):
		await message.channel.send(f"""
		__mishnet commands:__
		{prefix}help - sends this message (alias: {prefix}info)
		{prefix}perftest - tests bridge performance time
		{prefix}nick [nick here] - changes your mishnet nickname (alias: {prefix}nickname)
		{prefix}nick - tells you how other servers see your name (aliases: {prefix}nicktest , {prefix}nickname)
		{prefix}clearnick - resets your mishnet nickname to use your username
		the []s aren't part of the command
		""")
	
	if message.content == prefix + "uwu": #vitally important command
		await message.channel.send('uwu')

	# oh my god please write a separate function for aliases
	if message.content == prefix+"nick" or message.content == prefix+"nickname" or message.content == prefix+"nicktest": # nick(test) command
		other_server_name = await get_mishnick_or_username(conn, message.author)
		await message.channel.send(f"hi!!! your name will be seen by people on other servers as {other_server_name} ! :D")

	elif message.content.startswith(prefix+"nick") or message.content.startswith(prefix+"nickname"): # nick(change) command
		nick = message.content.replace(prefix+"nick ",'').replace(prefix+"nickname",'') # this is a bad (ugly) way to do this i think i should write a function

		if len(nick) > 32:
			await message.channel.send('sorry, a mishnet nickname can only be a maximum of 32 characters long')
		
		async with conn.cursor(row_factory=psycopg.rows.dict_row) as cursor:
			await cursor.execute('SELECT user_id, nickname FROM nicknames WHERE user_id = %s' , [message.author.id])
			record = await cursor.fetchone()
			if record:
				await cursor.execute(f"UPDATE nicknames SET nickname=%s WHERE user_id=%s" , [nick,message.author.id])
			else:
				await cursor.execute(f"INSERT INTO nicknames (user_id, nickname) VALUES (%s, %s)" , [message.author.id,nick])

		await conn.commit()
		await message.channel.send(f'hello {nick}! i have set your mishnet (me) nickname as `{nick}` c:')

	if message.content.startswith(prefix+"clearnick"):
		async with conn.cursor(row_factory=psycopg.rows.dict_row) as cursor:
			await cursor.execute('SELECT user_id, nickname FROM nicknames WHERE user_id = %s' , [message.author.id])
			record = await cursor.fetchone()
			if record:
				await cursor.execute(f"DELETE FROM nicknames WHERE user_id=%s",[message.author.id])
				await message.channel.send(f'your mishnet nickname has been cleared, {message.author.name}! it will now show up to others as your discord username ^-^')
			else:
				await message.channel.send(f'{message.author.name}, your mishnet nickname is already the default (your username) ! :p')
		await conn.commit()

	# bridge

	mishnet_channel = next( (channel_group for channel_group in mishnet_channels if message.channel in channel_group) , None ) # feeling like this would be another application for the associations data structure, but we made it only work for storing messages
	if not mishnet_channel:
		return	

	if message.author.id in banlist:
		try:
			return await message.delete()
		except:
			return message.channel.send('error: mishnet does not have message deletion perms in this server, and so it cannot stop banned users')

	if message.content == prefix + "perftest": 
		startTime = time.perf_counter()
	
	target_channels = [i for i in mishnet_channel if i.guild != message.channel.guild]

	name = await get_mishnick_or_username(conn, message.author) + ', from ' + serverNames[message.channel]

	pfp = message.author.display_avatar.url
	# run every message sending thingy in parallel
	replied_message = await get_replied_message(message)
	duplicate_messages = await asyncio.gather(*[bridge(message.content , channel , replied_message , name , pfp , None , message.stickers , False) for channel in target_channels])
	try:
		associations.set_duplicates(message, duplicate_messages)
	except TheOriginalMessageHasAlreadyBeenDeletedYouSlowIdiotError:
		# fuck shit piss delete them all again ig
		await asyncio.gather(*[message.delete() for message in duplicate_messages])

	if message.content == prefix + "perftest":
		endTime = time.perf_counter()
		bridge_time = "bridge time: " + str(endTime - startTime)
		await message.channel.send(f"{bridge_time}s")

	return

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
	return await delete(original_message)

@client.event
async def on_bulk_message_delete(messages: list[discord.Message]):
	for message in messages:
		for associated_message_id in associations.retrieve_others(message.id):
			associated_message = await associated_message.channel.fetch_message(associated_message_id)
			await associated_message.delete()

def total_reactions(message: discord.Message) -> Counter[str]: # DEVELOPMENT ON HOLD
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

		original_message = associations.to_original(reaction.message)
		if original_message.author.id != member.id: # message.author is a User, so i compare ids
			if isinstance(member, discord.Member) and discord.Permissions.manage_messages not in reaction.message.channel.permissions_for(member):
				return

		return await reaction.message.delete()
	
	if reaction.emoji == "🔔":

		original_message = associations.to_original(reaction.message)
	
		name = await get_mishnick_or_username(conn, member) + ', from ' + serverNames[reaction.message.channel]
		pfp = member.display_avatar.url
		
		mishnet_channel = next(group for group in mishnet_channels if original_message.channel in group)
		
		messages = await asyncio.gather(*[bridge(
				content = original_message.author.mention, 
				target_channel = channel, 
				replied_message = original_message, 
				name = name, 
				pfp = pfp, 
				attachment_files = [], 
				stickers = [], 
				ping = (channel == original_message.channel)
			) for channel in mishnet_channel])
		
		# ew
		main = next(i for i in messages if i.channel == reaction.message.channel)
		duplicates = [i for i in messages if i.channel != reaction.message.channel]
		associations.set_duplicates(main, duplicates)

	print("mmm yes adding view")
	reactions = total_reactions(reaction.message)
	view = SuperCoolReactionView(reactions)
	messages = associations.retrieve_others(reaction.message) + [reaction.message]
	return await asyncio.gather(*[message.edit(view=view) for message in messages])

@client.event
async def on_message_edit(before , after):
	if before.content == after.content: return
	# a message embedding counts triggers on message edit, which is cringe but this solves that

	if before.channel not in [channel for group in mishnet_channels for channel in group]: return
	if before.author.bot: return

	assert before.id == after.id

	original_partial_message = before.channel.get_partial_message(before.id) # converts before (discord.Message) into a discord.PartialMessage

	async def edit_copy(partial_to_edit: discord.PartialMessage , after_message: discord.Message, replied_message):
		wait_time = 0
		delay = 0.2
		while wait_time < 5:
			try:
				webhook = webhooks[partial_to_edit.channel]
				toEdit = await create_to_send(after_message.content , partial_to_edit.channel, replied_message, after.stickers)
				return await webhook.edit_message(partial_to_edit.id, content=toEdit)
			except:
				exception_type, exception, exc_traceback = sys.exc_info()
				traceback.print_exception(exception_type, exception, exc_traceback)
				await asyncio.sleep(delay)
				wait_time += delay
		# should raise an error here
		
	async def get_duplicates_timeout():
		wait_time = 0
		delay = 0.2
		while wait_time < 5:
			try:
				duplicates = associations.get_duplicates_of(original_partial_message)
				if duplicates == None:
					pass
				else:
					return duplicates
			except:
				exception_type, exception, exc_traceback = sys.exc_info()
				traceback.print_exception(exception_type, exception, exc_traceback)
				await asyncio.sleep(delay)
				wait_time += delay
		# should raise an error here

	#todo: fix this code repetition
	
	duplicate_messages = await get_duplicates_timeout()
	replied_message = await get_replied_message(after)
	return await asyncio.gather(*[edit_copy(m , after, replied_message) for m in duplicate_messages])

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
		# specific errors
		if str(exception).split()[0] == "429": # timeout error
			await channel.send('hiiii sorryyyy there was a timeout errorrr :c u may want to check if your message or your edit went through')
		else:
			await channel.send(random.choice(messages).format(str(exception)))

 	# this is just hackish debugging
	print('on error exception:')
	traceback.print_exception(exception_type, exception, exc_traceback)

# start bot
async def start_everything():
	print('starting')

	global conn
	conn = await psycopg.AsyncConnection.connect(f"dbname=mishnet port={os.getenv('PORT')} user={os.getenv('DBUSER')} password={os.getenv('PASSWORD')}")

	print('database connected')

	await client.start(os.getenv('TOKEN'))

asyncio.run(start_everything())

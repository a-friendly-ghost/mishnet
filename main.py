import discord, io, os, random, sys, time, asyncio, re, datetime
from dotenv import load_dotenv
from imstupid import MessageAssociations, TheOriginalMessageHasAlreadyBeenDeletedYouSlowIdiotError, get_mishnick_or_username
from typing import Union
from collections import Counter, OrderedDict
import traceback
import psycopg

# load environment variables
load_dotenv()

# instantiate client
client = discord.Client(intents=discord.Intents.all())
associations = MessageAssociations()
prefix = 'mn!'

poll_start = 'poll:'
poll_lock = asyncio.Lock()

commands = f"""
__mishnet commands:__
- {prefix}help - sends this message (alias: {prefix}info)
- {prefix}perftest - tests bridge performance time
- {prefix}nick [nick here] - changes your mishnet nickname (alias: {prefix}nickname)
- {prefix}nick - tells you how other servers see your name (aliases: {prefix}nicktest , {prefix}nickname)
- {prefix}clearnick - resets your mishnet nickname to use your username
- {prefix}poll [optional text] - creates a poll message
- {prefix}rules - sends the rules of mishnet
- {prefix}servers - sends a description of each server connected to mishnet
- {prefix}telephone - sends a jump link to the latest telephone game entry
- {prefix}telephoneprefix - tells you the prefix used to mark telephone messages (alias: {prefix}tpprefix)
- {prefix}telephoneprefix [prefix here] - sets the telephone prefix. admin required (alias: {prefix}tpprefix)
- {prefix}shutthefuckup [userid] - bans a user from mishnet
the []s aren't part of the command
__reaction functions:__
- :x: - deletes a bridged message
- :bell: - pings the person reacted to
"""

rules = """
the mishnet rules are a combination of the rules of mishnet's connected servers, alongside what i (mish) consider to be right and wrong
- no bigotry of any kind, such as on the basis of race, nationality, religion, gender, sexual orientation, ability, etc
- respect your fellow mishnet users, including their wishes regarding not seeing particular things, words, or topics
- no explicit or shocking images or videos
if you see someone breaking these rules or doing something you consider wrong, please ping me personally. if i am not online, ping one of the mods of the server you are in
breaking a rule will result in recieving a warn; three warns will result in being banned from mishnet
please remember that given the wide range of mishnet, not all members may be familiar with what makes you uncomfortable, even if it seems obvious from your perspective
"""

serverdescs = """
this is a list of every connected server along with a brief description of them
- mishserver - my (mish) personal friend server
- agonyserver - another friend server i am in
- conphon - the server for the r/conlangphonologies subreddit, though moreso its own community with little actual link to the subreddit at all
- ccj - the server for the r/conlangcirclejerk subreddit, though moreso its own community with little actual link to the subreddit at all
- hallowspeak - the server for my conlanging project Hallowspeak
- prolangs - the server for elemenopi's webcomic Prolangs, about humanised versions of popular conlangs
- meriakcottage - idk
- merrycord - merrybot (also known as evie)'s personal friend server
- ostracod - the server about the conlangs and other projects made by ostracod, creator of vötgil among others
- marciland - server, created by marci, of one of the main friend groups across mishnet after their individual servers became no longer useable
- kathycord - i really don't know man. made by katherine
- open book - a server focused around the idea that conlanging and worldbuilding is an artform like any other, created by creativitytheemotion
"""

mishnet_channels = None

if sys.platform == 'win32':
	asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())	

# hello this is mish!
# note on the inconsistent terminology for folks reading through my shit code for some godforsaken reason
# a "mishnet general" and "mishnet conlanging" are mishnet channels
# just "channel" though refers to like, the discord channels, also called nodes when i remember to call them that

ready = False

telephoneprefix = open('telephoneprefix.txt','r').read()
latesttelephone = open('telephonelatest.txt','r').read()
banlist = []
with open('banlist.txt','r') as banfile:
	for line in banfile.readlines():
		if int(line) not in banlist:
			banlist.append(int(line))
with open('banlist.txt','w') as banfile:
	banfile.write('\n'.join(banlist))

async def get_webhook_for_channel(channel: discord.TextChannel):
	# webhooks that we own have a non-None token attribute
	for webhook in await channel.webhooks():
		if webhook.token:
			return webhook

	print(f"Making webhook for {channel.name}...")
	return await channel.create_webhook(name="mishnet webhook", reason="what are you a cop?")

# shows the typing indicator based on the list of currently typing users
async def manage_typing_indicator():
	# TODO: async this
	for group in mishnet_channels:
		for channel in group:
			show_typing = True if len([user for node , userlist in users_typing.items() if node != channel and node in group for user in userlist]) > 0 else False
			if show_typing:
				async with channel.typing():
					await asyncio.sleep(1)
	return


@client.event
async def on_ready():
	print('on ready begin')

	print(f'{client.user} has connected to Discord!')

	# todo: store these more neatly
	# oh my god mish please do this -mish

	# these are stored here right now, because i need to do more database work to store them there, but i can't do it myself (i don't know how)

	mishserver = client.get_channel(915251024174940160)
	agonyserver = client.get_channel(746466196978794517)
	cpserver = client.get_channel(987001423977914428)
	ccjserver = client.get_channel(629816294870351884)
	hallowspeak = client.get_channel(986616150492323840)
	prolangs = client.get_channel(988876878582546472)
	meriakcottage = client.get_channel(1046824467055263824)
	merrycord = client.get_channel(1124169206427045979)
	ostracod = client.get_channel(1093661502084493422)
	marciland = client.get_channel(1115636041475440750)
	kathycord = client.get_channel(1118827288641941535)
	openbook = client.get_channel(1139256333540012082)

	mishserver2 = client.get_channel(1006522289048784967)
	agonyserver2 = client.get_channel(1006237275664949349)
	cpserver2 = client.get_channel(1006522209872920618)
	ccjserver2 = client.get_channel(1055428091285086218)
	hallowspeak2 = client.get_channel(1006526679071596574)
	prolangs2 = client.get_channel(1006660045511086080)
	meriakcottage2 = client.get_channel(964755175770325002)
	merrycord2 = client.get_channel(1124169171568164986)
	ostracod2 = client.get_channel(1093661477111611443)
	marciland2 = client.get_channel(1115635971216650271)
	kathycord2 = client.get_channel(1118827217691099226)
	openbook2 = client.get_channel(1139256312488808488)

	global mishnet1 , mishnet2 , mishnet_channels
	mishnet1 = [mishserver ,  agonyserver ,  cpserver ,  ccjserver ,  hallowspeak ,  prolangs ,  meriakcottage , merrycord , ostracod , marciland , kathycord , openbook] # conlanging
	mishnet2 = [mishserver2 , agonyserver2 , cpserver2 , ccjserver2 , hallowspeak2 , prolangs2 , meriakcottage2 , merrycord2 , ostracod2 , marciland2 , kathycord2 , openbook2] # general
	mishnet_channels = [mishnet1 , mishnet2]

	print('all channels gotten')

	# this part will also be much cleaner once the database is sorted
	global serverNames
	serverNames = {
		mishserver : 'mishserver',
		agonyserver : 'agonyserver',
		cpserver : 'conphon',
		ccjserver : 'ccj',
		hallowspeak : 'Hallowspeak',
		prolangs : 'prolangs',
		meriakcottage : 'mɛriak cottage',
		merrycord : 'merrycord',
		ostracod : 'ostracod conlangs',
		marciland : 'marciland' ,
		kathycord : 'kathycord',
		openbook : 'open book',

		mishserver2 : 'mishserver',
		agonyserver2 : 'agonyserver',
		cpserver2 : 'conphon',
		ccjserver2: 'ccj',
		hallowspeak2 : 'Hallowspeak',
		prolangs2 : 'prolangs',
		meriakcottage2 : 'mɛriak cottage',
		merrycord2 : 'merrycord',
		ostracod2 : 'ostracod conlangs',
		marciland2 : 'marciland',
		kathycord2 : 'kathycord',
		openbook2 : 'open book'
	}

	# put all the webhooks in a dict for faster retrieval
	global webhooks
	webhooks = {}
	for mishnet_channel in mishnet_channels:
		for node in mishnet_channel:
			webhooks[node] = await get_webhook_for_channel(node)

	print('all webhooks cached')

	print('banlist stored')

	# set up users typing structure thing
	global users_typing
	users_typing = {}
	for mishnet_channel in mishnet_channels:
		for node in mishnet_channel:
			users_typing[node] = []

	print('typing dict initialised')

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

async def create_to_send(content: str, target_channel: discord.TextChannel, original_guild: discord.Guild, replied_message, stickers) -> str:
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
		
		if reply_text.replace('\n','') == commands.replace('\n',''): # reasons
			reply_text = '`mishnet command list'
		if reply_text.replace('\n','') == rules.replace('\n',''):
			reply_text = '`mishnet rules`'
		if reply_text.replace('\n','') == serverdescs.replace('\n',''):
			reply_text = '`mishnet server descriptions`'
		
		reply_text = re.sub(r"(?<!\]\()(?<!<)(https?:\/\/[^ \n]+)" , r"<\1>" , reply_text) # unembeds a link inside the quote block -- thank u taswelll for the help!
		# future mish: thank you taswelll for fixing your own code when it broke!

		reply_text += ' ' + ' '.join([f"[(📎)](<{attachment.url}>)" for attachment in replied_message.attachments]) # the image emoji didn't render on ios

		# me on my way to modify code to make it less compact
		repliee_name = await get_mishnick_or_username(conn, replied_message.author)
		repliee_name = repliee_name.replace('_','\_').replace('*','\*') # avoids usernames with _s and *s showing up as markdown formatting
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

	# replaces channel links with "channel name in server name"
	channel_links = re.findall(r"(?<=<#)\d+(?=>)" , to_send)
	for match in channel_links:
		linked_channel = await client.fetch_channel(match)
		if linked_channel.guild != target_channel.guild: # avoids redundant replacing link with itself
			group = next((i for i in mishnet_channels if linked_channel in i), None)
			if group: # im silly
				equivalent_channel = next(channel for channel in group if channel.guild.id == target_channel.guild.id)
				to_send = to_send.replace(f"<#{match}>" , f"<#{equivalent_channel.id}>")
			else:
				# linked channel is not a mishnet channel
				to_send = to_send.replace(f"<#{match}>" , f"`#{linked_channel.name} in {linked_channel.guild.name}`") # replace with mishnet name for server once channels are endatabased

	# replaces role pings with "role name role in server name"
	role_pings = re.findall(r"(?<=<@&)\d+(?=>)" , to_send)
	for match in role_pings:
		pinged_role = next(i for i in original_guild.roles if i.id == int(match))
		to_send = to_send.replace(f"<@&{match}>" , f"`@{pinged_role.name} role in {original_guild}`")
	
	# just for debugging
	if 'mishdebug' in to_send:
		to_send = '```' + repr(to_send.replace('```','')) + '```'

	# removes tracking junk from youtube urls
	to_send = re.sub(r"(https?://(?:youtube\.com/watch\?v=[^&]*|youtu\.be/[^?]*)).si=[^&]*(&t=.*)?","\g<1>\g<2>",to_send)

	if len(to_send) > 1000 and replied_message:
		to_send = prune_replies(to_send , 1000)
	
	return to_send

async def bridge(
	content, 
	target_channel: discord.TextChannel, 
	original_guild: discord.Guild,
	replied_message, 
	name: str, 
	pfp: discord.Asset, 
	attachments: list[discord.Attachment],
	stickers,
	ping: bool
):
	
	webhook = webhooks[target_channel]

	to_send = await create_to_send(content, target_channel, original_guild, replied_message, stickers)
	attachments_to_files = await asyncio.gather(*[attachment.to_file(spoiler=attachment.is_spoiler()) for attachment in attachments])

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

	global telephoneprefix, latesttelephone

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
		await message.channel.send(commands)
	
	if message.content == prefix + "uwu": #vitally important command
		await message.channel.send('uwu')

	# TODO: oh my god please write a separate function for aliases
	if message.content == prefix+"nick" or message.content == prefix+"nickname" or message.content == prefix+"nicktest": # nick(test) command
		other_server_name = await get_mishnick_or_username(conn, message.author)
		await message.channel.send(f"hi!!! your name is currently seen by people on other servers as {other_server_name} ! :D")

	elif message.content.startswith(prefix+"nick") or message.content.startswith(prefix+"nickname"): # nick(change) command
		nick = message.content.replace(prefix+"nick ",'').replace(prefix+"nickname",'') # TODO: this is a bad (ugly) way to do this i think i should write a function

		if len(nick) > 32:
			await message.channel.send('sorry, a mishnet nickname can only be a maximum of 32 characters long')
		else:
			async with conn.cursor(row_factory=psycopg.rows.dict_row) as cursor:
				await cursor.execute('SELECT user_id, nickname FROM nicknames WHERE user_id = %s' , [message.author.id])
				record = await cursor.fetchone()
				if record:
					await cursor.execute("UPDATE nicknames SET nickname=%s WHERE user_id=%s" , [nick,message.author.id])
				else:
					await cursor.execute("INSERT INTO nicknames (user_id, nickname) VALUES (%s, %s)" , [message.author.id,nick])

			await conn.commit()
			await message.channel.send(f'hello {nick}! i have set your mishnet (me) nickname as `{nick}` c:')

	if message.content.startswith(prefix+"clearnick"):
		async with conn.cursor(row_factory=psycopg.rows.dict_row) as cursor:
			await cursor.execute('SELECT user_id, nickname FROM nicknames WHERE user_id = %s' , [message.author.id])
			record = await cursor.fetchone()
			if record:
				await cursor.execute("DELETE FROM nicknames WHERE user_id=%s",[message.author.id])
				await message.channel.send(f'your mishnet nickname has been cleared, {message.author.name}! it will now show up to others as your discord username ^-^')
			else:
				await message.channel.send(f'{message.author.name}, your mishnet nickname is already the default (your username) ! :p')
		await conn.commit()

	if message.content.startswith(prefix + 'poll'):
		await message.channel.send(poll_start + message.content.replace(prefix+'poll',''))

	if message.content == prefix + 'rules':
		await message.channel.send(rules)

	if message.content == prefix + 'servers':
		await message.channel.send(serverdescs)

	if message.content.startswith(prefix+'shutthefuckup '):
		if message.author.guild_permissions.administrator:
			try:
				to_ban = int(message.content.replace(prefix+'shutthefuckup ',''))
			except:
				await message.channel.send('invalid arguments')
			with open('banlist.txt','a') as balls:
				balls.write(f'\n{to_ban}')
			banlist.append(int(to_ban))
			await message.channel.send(f'banned user {to_ban}')
		else:
			await message.channel.send('you do not have permissions')

	# this is bad code. why would you write it in this way
	if message.content.startswith(prefix + 'telephoneprefix') or message.content.startswith(prefix + 'tpprefix'):
		if message.content.replace(prefix + 'telephoneprefix' , '').replace(prefix + 'tpprefix' , '') == '':
			await message.channel.send(f"the current prefix used for the mishnet telephone game is\n{telephoneprefix}")
		elif message.content.startswith(prefix + 'telephoneprefix ') or message.content.startswith(prefix + 'tpprefix '):
			if message.author.guild_permissions.administrator:
				telephoneprefix = message.content.replace(prefix + 'telephoneprefix ' , '').replace(prefix + 'tpprefix ' , '')
				with open('telephoneprefix.txt','w') as prefixfile:
					prefixfile.write(telephoneprefix)
				await message.channel.send(f'telephone prefix set to {telephoneprefix}')
			else:
				await message.channel.send('you do not have perms to do this')

	if message.content == prefix + 'telephone':
		to_send = re.sub(r"https://discord(?:app)?.com/channels/(\d+)/(\d+)/(\d+)", lambda x : next((copy.jump_url for copy in associations.retrieve_others( discord.PartialMessage(channel=client.get_channel(int(x.group(2))) , id=int(x.group(3))) ) if copy.channel.id == message.channel.id),"link not found"), latesttelephone)
		await message.channel.send(f'the latest telephone message is {to_send}')
	
	if message.content.startswith(telephoneprefix):
		latesttelephone = message.jump_url
		with open('telephonelatest.txt','w') as latest:
			latest.write(latesttelephone)

	# bridge
	# bridging code will be moved to the whole queue operation once i try to tackle that

	global users_typing

	if message.content == prefix + "perftest": 
		startTime = time.perf_counter()

	mishnet_channel = next( (channel_group for channel_group in mishnet_channels if message.channel in channel_group) , None ) # feeling like this would be another application for the associations data structure, but we made it only work for storing messages
	if not mishnet_channel:
		return

	# typing indicator runs out immediately when message is sent
	if message.author in users_typing[message.channel]:
		users_typing[message.channel].remove(message.author)

	await manage_typing_indicator()

	if message.author.id in banlist:
		try:
			return await message.delete()
		except:
			return message.channel.send('error: mishnet does not have message deletion perms in this server, and so it cannot stop banned users')
	
	target_channels = [i for i in mishnet_channel if i.guild != message.channel.guild]

	name = await get_mishnick_or_username(conn, message.author) + ', from ' + serverNames[message.channel]
	pfp = message.author.display_avatar.url
	replied_message = await get_replied_message(message)

	# run every message sending thingy in parallel
	duplicate_messages = await asyncio.gather(*[bridge(
			content = message.content,
			target_channel = channel,
			original_guild = message.channel.guild,
			replied_message = replied_message,
			name = name,
			pfp = pfp,
			attachments = message.attachments,
			stickers = message.stickers,
			ping = False
		) for channel in target_channels])
	
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
			print(f'could not delete in {message.guild.name}')
			pass

	await asyncio.gather(*[delete(duplicate) for duplicate in duplicates])
	return await delete(original_message)

@client.event
async def on_bulk_message_delete(messages: list[discord.Message]):
	for message in messages:
		for associated_message_id in associations.retrieve_others(message.id):
			associated_message = await associated_message.channel.fetch_message(associated_message_id)
			await associated_message.delete()

class SuperCoolReactionView(discord.ui.View):
	def __init__(self, reaction_counts: Counter[str]):
		super().__init__() # omg super() i learnt what that does like a week ago
		# add button for each reaction thingy
		# FIXME: what about max items?
		for emoji, count in reaction_counts.items():
			self.add_item(discord.ui.Button(label=count, emoji=emoji, disabled=True))

async def alter_poll(original_message: discord.Message , reaction: discord.Reaction , count: int):

	global poll_lock
	await poll_lock.acquire()

	# need to re-get the message (cannot use reaction.message) because the content can change between the call and acquiring the lock
	# need to check original message specifically because the lock waits for the original to be edited, but not for the duplicates to be edited
	reaction_message = await original_message.channel.fetch_message(original_message.id)

	# parse existing message back into a dictionary
	# this ensures reacts stay in the same order
	poll_reactions = {i.split()[0] : int(i.split()[1]) for i in re.sub(f"{poll_start}.*(?:\n)?" , "" , reaction_message.content).split(' - ') if i != ''} # lol

	if isinstance(reaction.emoji , discord.Emoji): # class for custom emotes
		emote = f"<:{reaction.emoji.name}:{reaction.emoji.id}>"
	else:
		emote = reaction.emoji
	
	if emote in poll_reactions.keys():
		poll_reactions[emote] += count
	else:
		poll_reactions[emote] = 1 

	poll_text = re.search(f"{poll_start}(.*)(?:\n)?" , reaction_message.content).group(1)

	to_edit = poll_start + poll_text + '\n' + ' - '.join([f"{emote} {count}" for emote , count in poll_reactions.items() if count > 0])
	await original_message.edit(content=to_edit)
	poll_lock.release()
	return # idk why this is here instead of above

async def update_reactions(message: discord.Message):
	all_messages = await asyncio.gather(*[partial.fetch() for partial in associations.get_duplicates_of(message)]) + [message]
	all_reactions = {}
	for message in all_messages:
		for react in message.reactions:
			if react.emoji in all_reactions.keys():
				old_count = all_reactions[react.emoji]
				all_reactions[react.emoji] = old_count + react.count
			else:
				all_reactions[react.emoji] = react.count 

	view = SuperCoolReactionView(all_reactions)
	messages_to_edit = associations.retrieve_others(message)
	return await asyncio.gather(*[message.edit(view=view) for message in messages_to_edit])

@client.event
async def on_reaction_add(reaction: discord.Reaction, member: Union[discord.Member, discord.User]):

	if member.id in banlist:
		return

	global poll_lock

	if reaction.message.channel not in [channel for group in mishnet_channels for channel in group]:
		return
	
	partial_message = reaction.message.channel.get_partial_message(reaction.message.id) # converts to partial message
	original_message = await associations.to_original(partial_message).fetch()

	if original_message.author.id == client.user.id and reaction.message.content.startswith(poll_start):
		await alter_poll(original_message , reaction , 1)
		return

	if reaction.emoji == "❌":

		if original_message.author.id != member.id: # message.author is a User, so i compare ids
			if isinstance(member, discord.Member) and discord.Permissions.manage_messages not in reaction.message.channel.permissions_for(member):
				return

		return await reaction.message.delete()
	
	if reaction.emoji == "🔔":
	
		name = await get_mishnick_or_username(conn, member) + ', from ' + serverNames[reaction.message.channel]
		pfp = member.display_avatar.url
		
		mishnet_channel = next(group for group in mishnet_channels if original_message.channel in group)
		
		messages = await asyncio.gather(*[bridge(
				content = f"{original_message.author.mention} username: `{original_message.author.name}`", 
				target_channel = channel, 
				original_guild = original_message.channel.guild,
				replied_message = original_message,
				name = name, 
				pfp = pfp, 
				attachments = [], 
				stickers = [], 
				ping = (channel == original_message.channel)
			) for channel in mishnet_channel])
		
		# ew
		main = next(i for i in messages if i.channel == reaction.message.channel)
		duplicates = [i for i in messages if i.channel != reaction.message.channel]
		associations.set_duplicates(main, duplicates)

	return await update_reactions(original_message)

@client.event
async def on_reaction_remove(reaction: discord.Reaction, member: Union[discord.Member, discord.User]):

	global poll_lock

	if reaction.message.channel not in [channel for group in mishnet_channels for channel in group]:
		return
	
	partial_message = reaction.message.channel.get_partial_message(reaction.message.id) # converts to partial message
	original_message = await associations.to_original(partial_message).fetch()

	if original_message.author.id == client.user.id and reaction.message.content.startswith(poll_start):
		await alter_poll(original_message , reaction , -1)
		return
		
	return await update_reactions(original_message)

@client.event
async def on_message_edit(before , after):
	if before.content == after.content: return
	# a message embedding counts triggers on message edit, which is cringe but this solves that

	if before.channel not in [channel for group in mishnet_channels for channel in group]: return
	
		# ensure not editing bridged messages themselves or responding to bridged commands
	if before.webhook_id: # avoids unnecessarily checking all this
		channelWebhooks = await before.channel.webhooks()
		for webhook in channelWebhooks:
			if webhook.id == before.webhook_id:
				if webhook.token:
					# this webhook is from mishnet
					return
	assert before.id == after.id

	original_partial_message = before.channel.get_partial_message(before.id) # converts before (discord.Message) into a discord.PartialMessage

	async def edit_copy(partial_to_edit: discord.PartialMessage , after_message: discord.Message, replied_message):
		wait_time = 0
		delay = 0.2
		while wait_time < 5:
			try:
				webhook = webhooks[partial_to_edit.channel]
				toEdit = await create_to_send(after_message.content , partial_to_edit.channel, after_message.guild, replied_message, after.stickers)
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
	if not duplicate_messages: return # edit done before bot started ? idk
	replied_message = await get_replied_message(after)
	return await asyncio.gather(*[edit_copy(m , after, replied_message) for m in duplicate_messages])

@client.event
async def on_typing(channel, user, when):
	if channel not in [channel for group in mishnet_channels for channel in group]: return
	if user.id == client.user.id: return
	
	global users_typing
	if user not in users_typing[channel]:
		users_typing[channel].append(user)

	await asyncio.sleep(10)
	users_typing[channel].remove(user)
	return await manage_typing_indicator()

# it goes here. fuck you
messages = [
	"oopsie doopsie! da code went fucky wucky! {}",
	"oopsie woopsie our code kitty is hard at work: {}",
	"when the exception is sus: {}",
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

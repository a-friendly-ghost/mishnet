import discord

# FIXME: make this persistent using some database and functions to modify it easily

class MessageAssociations:
    """class w a dictionary holding lists of bridged messages that are the same or sth idk"""

    internal: dict[discord.PartialMessage, list[discord.PartialMessage]]

    def __init__(self):
        self.internal = {}

    def add_copy(self, original_partial_msg: discord.PartialMessage, copy_partial_msg: discord.PartialMessage):
        if original_partial_msg not in self.internal.keys(): # makes sure the original message is also added to the value list, but only once
            self.internal[original_partial_msg] = [original_partial_msg]

        assert isinstance(self.internal[original_partial_msg], list)
        if copy_partial_msg not in self.internal[original_partial_msg]:
            self.internal[original_partial_msg].append(copy_partial_msg)
        else:
            pass # i don't know why this ever happens, so instead of solving what causes it, i blocked it from happening

    def retrieve_others(self, original_or_copy_partial: discord.PartialMessage) -> list[discord.PartialMessage]:
        for associations_list in self.internal.values():
            assert isinstance(associations_list, list)
            if original_or_copy_partial in associations_list:
                return [partial_message for partial_message in associations_list if partial_message.id != original_or_copy_partial.id]
        
        return []
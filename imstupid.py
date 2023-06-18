from collections import defaultdict
from discord import PartialMessage, Member
import psycopg, asyncio, inspect, traceback, sys

class TheOriginalMessageHasAlreadyBeenDeletedYouSlowIdiotError(Exception):
    pass

class MishnetTimeout(Exception):
    pass

# FIXME: do we need to compare by ids?

class MessageAssociations:
    _internal: dict[PartialMessage, list[PartialMessage]]
    _to_be_removed: list[PartialMessage]

    def __init__(self):
        self._internal = dict[PartialMessage, list[PartialMessage]]()
        self._to_be_removed = list[PartialMessage]()
    
    def set_duplicates(self, original_message: PartialMessage, duplicate_messages: list[PartialMessage]):
        """Call this when you've just finished bridging a message"""
        if original_message in self._to_be_removed:
            self._to_be_removed.remove(original_message)
            raise TheOriginalMessageHasAlreadyBeenDeletedYouSlowIdiotError()
        else:
            self._internal[original_message] = duplicate_messages
    
    def get_duplicates_of(self, original_message: PartialMessage):
        """Fetch all duplicates of some message (e.g. if the original has been deleted/edited)"""
        return self._internal[original_message]
    
    def retrieve_others(self, original_or_duplicate_message: PartialMessage):
        if original_or_duplicate_message in self._internal.keys():
            return self.get_duplicates_of(original_or_duplicate_message)
        else:
            for original, duplicates in self._internal.items():
                if original_or_duplicate_message in duplicates:
                    return [partial_message for partial_message in duplicates if partial_message.id != original_or_duplicate_message.id] + [original]
        
        return [] # this is for when you try to reply to a message before the last bot restart.
        # it needs to return an empty list so that next() shoves it to the default value of "link not found"

    def to_original(self, original_or_duplicate: PartialMessage):
        for original, duplicates in self._internal.items():
            if original == original_or_duplicate or original_or_duplicate in duplicates:
                return original

    def __contains__(self, original_message: PartialMessage):
        return self._internal.__contains__(original_message)

    def remove(self, original_message: PartialMessage):
        """Call this when an original message has been deleted. Handles out-of-sync-ness."""
        if original_message in self._internal:
            del self._internal[original_message]
        else:
            self._to_be_removed.append(original_message)

async def get_mishnick_or_username(connection: psycopg.AsyncConnection, author: Member):
    async with connection.cursor(row_factory=psycopg.rows.dict_row) as cursor:
        await cursor.execute('SELECT user_id, nickname FROM nicknames WHERE user_id = %s' , [author.id])
        record = await cursor.fetchone()
        if record == None:
            return author.name
        else:
            return record["nickname"]
                
    #it should probably raise an error here
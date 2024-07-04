
from typing import Union

from discord import CategoryChannel, DirectoryChannel, ForumChannel, StageChannel, TextChannel, VoiceChannel


VocalGuildChannel = Union[VoiceChannel, StageChannel]
NonCategoryChannel = Union[VocalGuildChannel, ForumChannel, TextChannel, DirectoryChannel]
GuildChannel = Union[NonCategoryChannel, CategoryChannel]

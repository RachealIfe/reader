import dataclasses
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from typing import Dict
from typing import Iterable
from typing import List
from typing import NamedTuple
from typing import Optional
from typing import Sequence
from typing import Tuple
from typing import Type
from typing import TypeVar
from typing import Union


_T = TypeVar('_T')


class _namedtuple_compat:

    """Add namedtuple-like methods to a dataclass."""

    @classmethod
    def _make(cls: Type[_T], iterable: Iterable[Any]) -> _T:
        iterable = tuple(iterable)
        attrs_len = len(dataclasses.fields(cls))
        if len(iterable) != attrs_len:
            raise TypeError(
                'Expected %d arguments, got %d' % (attrs_len, len(iterable))
            )
        return cls(*iterable)

    _replace = dataclasses.replace

    _asdict = dataclasses.asdict


# Public API


@dataclass(frozen=True)
class Feed(_namedtuple_compat):

    """Data type representing a feed."""

    #: The URL of the feed.
    url: str

    #: The date the feed was last updated.
    updated: Optional[datetime] = None

    #: The title of the feed.
    title: Optional[str] = None

    #: The URL of a page associated with the feed.
    link: Optional[str] = None

    #: The author of the feed.
    author: Optional[str] = None

    #: User-defined feed title.
    user_title: Optional[str] = None


@dataclass(frozen=True)
class Entry(_namedtuple_compat):

    """Data type representing an entry."""

    #: Entry identifier.
    id: str

    # Entries returned by the parser always have updated set.
    # I tried modeling this through typing, but it's too complicated.

    #: The date the entry was last updated.
    updated: Optional[datetime]

    #: The title of the entry.
    title: Optional[str] = None

    #: The URL of a page associated with the entry.
    link: Optional[str] = None

    #: The author of the feed.
    author: Optional[str] = None

    #: The date the entry was first published.
    published: Optional[datetime] = None

    #: A summary of the entry.
    summary: Optional[str] = None

    #: Full content of the entry.
    #: A sequence of :class:`Content` objects.
    content: Sequence['Content'] = ()

    #: External files associated with the entry.
    #: A sequence of :class:`Enclosure` objects.
    enclosures: Sequence['Enclosure'] = ()

    #: Whether the entry was read or not.
    read: bool = False

    #: Whether the entry is important or not.
    important: bool = False

    #: The entry's feed.
    feed: Optional[Feed] = None


@dataclass(frozen=True)
class Content(_namedtuple_compat):

    """Data type representing a piece of content."""

    #: The content value.
    value: str

    #: The content type.
    type: Optional[str] = None

    #: The content language.
    language: Optional[str] = None


@dataclass(frozen=True)
class Enclosure(_namedtuple_compat):

    """Data type representing an external file."""

    #: The file URL.
    href: str

    #: The file content type.
    type: Optional[str] = None

    #: The file length.
    length: Optional[int] = None


# Typing support


FeedInput = Union[str, Feed]
EntryInput = Union[Tuple[str, str], Entry]


def feed_argument(feed: FeedInput) -> str:
    # Giving away some duck typing for type checking (catching AttributeError
    # is not enough for mypy, see https://github.com/python/mypy/issues/8056).
    if isinstance(feed, Feed):
        return feed.url
    if isinstance(feed, str):
        return feed
    raise ValueError('feed')


def entry_argument(entry: EntryInput) -> Tuple[str, str]:
    # Giving away some duck typing for type checking.
    if isinstance(entry, Entry):
        if isinstance(entry.feed, Feed):
            return entry.feed.url, entry.id
    if isinstance(entry, tuple) and len(entry) == 2:
        feed_url, entry_id = entry
        if isinstance(feed_url, str) and isinstance(entry_id, str):
            return entry
    raise ValueError('entry')


# Private API
# https://github.com/lemon24/reader/issues/111


class ParsedFeed(NamedTuple):

    feed: Feed
    http_etag: Optional[str]
    http_last_modified: Optional[str]


class ParseResult(NamedTuple):

    parsed_feed: ParsedFeed
    entries: Iterable[Entry]

    # compatibility

    @property
    def feed(self) -> Feed:
        return self.parsed_feed.feed

    @property
    def http_etag(self) -> Optional[str]:
        return self.parsed_feed.http_etag

    @property
    def http_last_modified(self) -> Optional[str]:
        return self.parsed_feed.http_last_modified


class FeedForUpdate(NamedTuple):

    url: str
    updated: Optional[datetime]
    http_etag: Optional[str]
    http_last_modified: Optional[str]
    stale: bool
    last_updated: datetime


class EntryForUpdate(NamedTuple):

    updated: datetime


class FeedUpdateIntent(NamedTuple):

    url: str
    feed: Optional[Feed]
    http_etag: Optional[str]
    http_last_modified: Optional[str]
    last_updated: datetime


class EntryUpdateIntent(NamedTuple):
    """An entry with additional data to be passed to Storage
    when updating a feed.

    """

    #: The feed URL.
    url: str

    #: The entry.
    entry: Entry

    #: The time at the start of updating this feed (start of update_feed
    #: in update_feed, the start of each feed update in update_feeds).
    last_updated: datetime

    #: The time at the start of updating this batch of feeds (start of
    #: update_feed in update_feed, start of update_feeds in update_feeds);
    #: None if the entry already exists.
    first_updated_epoch: Optional[datetime]

    #: The index of the entry in the feed (zero-based).
    feed_order: int


class UpdatedEntry(NamedTuple):

    entry: Entry
    new: bool


class UpdateResult(NamedTuple):

    #: The entries that were updated.
    entries: Iterable[UpdatedEntry]


# https://github.com/python/typing/issues/182
JSONValue = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]
JSONType = Union[Dict[str, JSONValue], List[JSONValue]]


# TODO: these should probably be in storage.py (along with some of the above)


class EntryFilterOptions(NamedTuple):

    """Options for filtering the results of the "get entry" storage methods."""

    feed_url: Optional[str] = None
    entry_id: Optional[str] = None
    read: Optional[bool] = None
    important: Optional[bool] = None
    has_enclosures: Optional[bool] = None

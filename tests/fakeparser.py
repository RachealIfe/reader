import threading
from collections import OrderedDict

from reader import Feed
from reader import ParseError
from reader.exceptions import _NotModified
from reader.types import entry_argument
from reader.types import EntryData
from reader.types import ParsedFeed


def _make_feed(number, updated=None, **kwargs):
    return Feed(
        f'{number}',
        updated,
        kwargs.pop('title', f'Feed #{number}'),
        kwargs.pop('link', f'http://www.example.com/{number}'),
        **kwargs,
    )


def _make_entry(feed_number, number, updated, **kwargs):
    return EntryData(
        f'{feed_number}',
        # evals to tuple
        f'{feed_number}, {number}',
        updated,
        kwargs.pop('title', f'Entry #{number}'),
        kwargs.pop('link', f'http://www.example.com/entries/{number}'),
        **kwargs,
    )


class Parser:
    def __init__(self, feeds=None, entries=None):
        self.feeds = feeds or {}
        self.entries = entries or {}
        self.http_etag = None
        self.http_last_modified = None

    @classmethod
    def from_parser(cls, other):
        return cls(other.feeds, other.entries)

    def feed(self, number, updated=None, **kwargs):
        feed = _make_feed(number, updated, **kwargs)
        self.feeds[number] = feed
        self.entries.setdefault(number, OrderedDict())
        return feed

    def entry(self, feed_number, number, updated, **kwargs):
        entry = _make_entry(feed_number, number, updated, **kwargs)
        self.entries[feed_number][number] = entry
        return entry

    def __call__(self, url, http_etag, http_last_modified):
        for feed_number, feed in self.feeds.items():
            if feed.url == url:
                break
        else:
            raise RuntimeError("unkown feed: {}".format(url))
        return ParsedFeed(
            feed,
            self.entries[feed_number].values(),
            self.http_etag,
            self.http_last_modified,
        )


class BlockingParser(Parser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.in_parser = threading.Event()
        self.can_return_from_parser = threading.Event()

    def __call__(self, *args, **kwargs):
        self.in_parser.set()
        self.can_return_from_parser.wait()
        return super().__call__(*args, **kwargs)


class FailingParser(Parser):
    def __call__(self, *args, **kwargs):
        raise ParseError(None)


class _NotModifiedParser(Parser):
    def __call__(self, *args, **kwargs):
        raise _NotModified(None)


class ParserThatRemembers(Parser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.calls = []

    def __call__(self, url, http_etag, http_last_modified):
        self.calls.append((url, http_etag, http_last_modified))
        return super().__call__(url, http_etag, http_last_modified)

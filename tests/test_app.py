from datetime import datetime

import pytest
import requests
import wsgiadapter
import mechanicalsoup

from reader import Reader
from reader.app import create_app

from fakeparser import Parser


@pytest.mark.slow
def test_mark_as_read_unread(tmpdir):
    db_path = str(tmpdir.join('db.sqlite'))

    parser = Parser()
    feed = parser.feed(1, datetime(2010, 1, 1))
    entry = parser.entry(1, 1, datetime(2010, 1, 1))

    reader = Reader(db_path)
    reader._parse = parser

    reader.add_feed(feed.url)
    reader.update_feeds()

    app = create_app(db_path)

    session = requests.Session()
    session.mount('http://app/', wsgiadapter.WSGIAdapter(app))
    browser = mechanicalsoup.StatefulBrowser(session)
    browser.open('http://app/')

    assert len(browser.get_current_page().select('.entry form')) == 1

    form = browser.select_form('.entry form')
    response = browser.submit_selected(form.form.find('button', text='mark as read'))
    assert response.status_code == 200
    assert len(browser.get_current_page().select('.entry form')) == 0

    response = browser.follow_link(browser.find_link(text='read'))
    assert response.status_code == 200
    assert len(browser.get_current_page().select('.entry form')) == 1

    form = browser.select_form('.entry form')
    response = browser.submit_selected(form.form.find('button', text='mark as unread'))
    assert response.status_code == 200
    assert len(browser.get_current_page().select('.entry form')) == 0

    response = browser.follow_link(browser.find_link(text='unread'))
    assert response.status_code == 200
    assert len(browser.get_current_page().select('.entry form')) == 1


@pytest.mark.slow
def test_mark_all_as_read_unread(tmpdir):
    db_path = str(tmpdir.join('db.sqlite'))

    parser = Parser()
    feed = parser.feed(1, datetime(2010, 1, 1))
    entry = parser.entry(1, 1, datetime(2010, 1, 1))

    reader = Reader(db_path)
    reader._parse = parser

    reader.add_feed(feed.url)
    reader.update_feeds()

    app = create_app(db_path)

    session = requests.Session()
    session.mount('http://app/', wsgiadapter.WSGIAdapter(app))
    browser = mechanicalsoup.StatefulBrowser(session)
    browser.open('http://app/', params={'feed': feed.url})

    assert len(browser.get_current_page().select('.entry form')) == 1

    form = browser.select_form('#update-entries')
    form.set_checkbox({'really-mark-all-as-read': True})
    response = browser.submit_selected(form.form.find('button', text='mark all as read'))
    assert response.status_code == 200
    assert len(browser.get_current_page().select('.entry form')) == 0

    response = browser.follow_link(browser.find_link(text='read'))
    assert response.status_code == 200
    assert len(browser.get_current_page().select('.entry form')) == 1

    form = browser.select_form('form#update-entries')
    form.set_checkbox({'really-mark-all-as-unread': True})
    response = browser.submit_selected(form.form.find('button', text='mark all as unread'))
    assert response.status_code == 200
    assert len(browser.get_current_page().select('.entry form')) == 0

    response = browser.follow_link(browser.find_link(text='unread'))
    assert response.status_code == 200
    assert len(browser.get_current_page().select('.entry form')) == 1


@pytest.mark.slow
def test_add_delete_feed(tmpdir):
    db_path = str(tmpdir.join('db.sqlite'))

    parser = Parser()
    feed = parser.feed(1, datetime(2010, 1, 1))
    entry = parser.entry(1, 1, datetime(2010, 1, 1))

    reader = Reader(db_path)
    reader._parse = parser

    app = create_app(db_path)

    session = requests.Session()
    session.mount('http://app/', wsgiadapter.WSGIAdapter(app))
    browser = mechanicalsoup.StatefulBrowser(session)
    browser.open('http://app/')

    response = browser.follow_link(browser.find_link(text='feeds'))
    assert response.status_code == 200
    assert len(browser.get_current_page().select('.feed form')) == 0

    form = browser.select_form('form#top-bar')
    form.input({'feed-url': feed.url})
    response = browser.submit_selected(form.form.find('button', text='add feed'))
    assert response.status_code == 200
    assert len(browser.get_current_page().select('.feed form')) == 1

    # because we don't have a title at this point
    feed_link = browser.find_link(text=feed.url)

    response = browser.follow_link(feed_link)
    assert response.status_code == 200
    assert len(browser.get_current_page().select('.entry form')) == 0

    reader.update_feeds()

    browser.refresh()
    assert len(browser.get_current_page().select('.entry form')) == 1

    response = browser.follow_link(browser.find_link(text='feeds'))
    assert response.status_code == 200

    form = browser.select_form('.feed form')
    form.set_checkbox({'really-delete-feed': True})
    response = browser.submit_selected(form.form.find('button', text='delete feed'))
    assert response.status_code == 200
    assert len(browser.get_current_page().select('.feed form')) == 0

    response = browser.follow_link(browser.find_link(text='entries'))
    assert response.status_code == 200
    assert len(browser.get_current_page().select('.entry form')) == 0

    response = browser.follow_link(feed_link)
    assert response.status_code == 404


@pytest.mark.slow
def test_delete_feed_from_entries_page_redirects(tmpdir):
    db_path = str(tmpdir.join('db.sqlite'))

    parser = Parser()
    feed = parser.feed(1, datetime(2010, 1, 1))
    entry = parser.entry(1, 1, datetime(2010, 1, 1))

    reader = Reader(db_path)
    reader._parse = parser

    reader.add_feed(feed.url)
    reader.update_feeds()

    app = create_app(db_path)

    session = requests.Session()
    session.mount('http://app/', wsgiadapter.WSGIAdapter(app))
    browser = mechanicalsoup.StatefulBrowser(session)
    browser.open('http://app/', params={'feed': feed.url})

    form = browser.select_form('form#update-entries')
    form.set_checkbox({'really-delete-feed': True})
    response = browser.submit_selected(form.form.find('button', text='delete feed'))
    assert response.status_code == 200
    assert browser.get_url() == 'http://app/'
    assert len(browser.get_current_page().select('.entry form')) == 0


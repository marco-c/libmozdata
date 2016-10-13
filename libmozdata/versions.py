# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

try:
    from urllib.request import urlopen
except ImportError:
    from urllib import urlopen

from os.path import commonprefix
import json
import re
from datetime import timedelta
from icalendar import Calendar
from . import utils

__versions = None
__version_dates = None
__stability_version_dates = None


def __get_major(v):
    return int(v.split('.')[0])


def __getVersions():
    """Get the versions number for each channel

    Returns:
        dict: versions for each channel
    """
    resp = urlopen('https://product-details.mozilla.org/1.0/firefox_versions.json')
    data = json.loads(resp.read().decode('utf-8'))
    resp.close()

    aurora = data['FIREFOX_AURORA']
    nightly = data['FIREFOX_NIGHTLY'] if 'FIREFOX_NIGHTLY' in data else '%d.0a1' % (__get_major(aurora) + 1)
    esr = data['FIREFOX_ESR_NEXT']
    if not esr:
        esr = data['FIREFOX_ESR']
    if esr.endswith('esr'):
        esr = esr[:-3]

    return {'release': data['LATEST_FIREFOX_VERSION'],
            'beta': data['LATEST_FIREFOX_RELEASED_DEVEL_VERSION'],
            'aurora': str(aurora),
            'nightly': nightly,
            'esr': esr}


def __getVersionDates():
    resp = urlopen('https://product-details.mozilla.org/1.0/firefox_history_major_releases.json')
    data = json.loads(resp.read().decode('utf-8'))
    resp.close()

    data = dict([(v, utils.get_moz_date(d)) for v, d in data.items()])

    resp = urlopen('https://www.google.com/calendar/ical/mozilla.com_2d37383433353432352d3939%40resource.calendar.google.com/public/basic.ics')
    calendar = Calendar.from_ical(resp.read().decode('utf-8'))
    resp.close()

    for component in calendar.walk():
        if component.name == 'VEVENT':
            match = re.search('Firefox ([0-9]+) Release', component.get('summary'))
            if match:
                version = match.group(1) + '.0'
                if version not in data:
                    data[version] = utils.get_moz_date(utils.get_date_str(component.decoded('dtstart')))

    return data


def __getStabilityVersionDates():
    resp = urlopen('https://product-details.mozilla.org/1.0/firefox_history_stability_releases.json')
    data = json.loads(resp.read().decode('utf-8'))
    resp.close()

    return dict([(v, utils.get_moz_date(d)) for v, d in data.items()])


def get(base=False):
    """Get current version number by channel

    Returns:
        dict: containing version by channel
    """
    global __versions
    if not __versions:
        __versions = __getVersions()

    if base:
        res = {}
        for k, v in __versions.items():
            res[k] = __get_major(v)
        return res

    return __versions


def __getMatchingVersion(version, versions_dates):
    date = None
    longest_match = []
    longest_match_v = None
    for v, d in versions_dates:
        match = commonprefix([v.split('.'), str(version).split('.')])
        if len(match) > 0 and (len(match) > len(longest_match) or (len(match) == len(longest_match) and int(v[-1]) <= int(longest_match_v[-1]))):
            longest_match = match
            longest_match_v = v
            date = d

    return date


def getMajorDate(version):
    global __version_dates
    if not __version_dates:
        __version_dates = __getVersionDates()

    return __getMatchingVersion(version, __version_dates.items())


def getDate(version):
    global __version_dates, __stability_version_dates
    if not __version_dates:
        __version_dates = __getVersionDates()
    if not __stability_version_dates:
        __stability_version_dates = __getStabilityVersionDates()

    return __getMatchingVersion(version, list(__version_dates.items()) + list(__stability_version_dates.items()))


def __getCloserDate(date, versions_dates, negative=False):
    def diff(d):
        return d - date

    return min([(v, d) for v, d in versions_dates if negative or diff(d) > timedelta(0)], key=lambda i: abs(diff(i[1])))


def getCloserMajorRelease(date, negative=False):
    global __version_dates
    if not __version_dates:
        __version_dates = __getVersionDates()

    return __getCloserDate(date, __version_dates.items(), negative)


def getCloserRelease(date, negative=False):
    global __version_dates, __stability_version_dates
    if not __version_dates:
        __version_dates = __getVersionDates()
    if not __stability_version_dates:
        __stability_version_dates = __getStabilityVersionDates()

    return __getCloserDate(date, list(__version_dates.items()) + list(__stability_version_dates.items()), negative)

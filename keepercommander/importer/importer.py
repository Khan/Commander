#  _  __
# | |/ /___ ___ _ __  ___ _ _ ®
# | ' </ -_) -_) '_ \/ -_) '_|
# |_|\_\___\___| .__/\___|_|
#              |_|
#
# Keeper Commander
# Copyright 2018 Keeper Security Inc.
# Contact: ops@keepersecurity.com
#
import os.path
import importlib
import logging

from typing import Iterable, Union, Optional

PathDelimiter = '\\'


def importer_for_format(format):
    full_name = 'keepercommander.importer.' + format
    module = importlib.import_module(full_name)
    if hasattr(module, 'Importer'):
        return module.Importer
    raise Exception('Cannot resolve importer for format {}'.format(format))


def exporter_for_format(format):
    full_name = 'keepercommander.importer.' + format
    module = importlib.import_module(full_name)
    if hasattr(module, 'Exporter'):
        return module.Exporter
    raise Exception('Cannot resolve exporter for format {}'.format(format))


def strip_path_delimiter(name, delimiter=PathDelimiter):
    folder = name.strip()
    if folder == delimiter:
        return ''
    if len(folder) > 1:
        if folder[:1] == delimiter and folder[:2] != delimiter*2:
            folder = folder[1:].strip()
    if len(folder) > 1:
        if folder[-1:] == delimiter and folder[-2:] != delimiter*2:
            folder = folder[:-1].strip()
    return folder


def path_components(path, delimiter=PathDelimiter):
    # type: (str, str) -> Iterable[str]
    p = path.strip()
    pos = 0
    while pos < len(p):
        idx = p.find(delimiter, pos)
        if idx >= 0:
            if idx+1 < len(p):
                if p[idx+1] == delimiter:
                    pos = idx + 2
                    continue
            comp = p[:idx].strip()
            p = p[idx+1:].strip()
            pos = 0
            if len(comp) > 0:
                yield comp.replace(2*delimiter, delimiter)
        else:
            p = strip_path_delimiter(p, delimiter=delimiter)
            if len(p) > 0:
                yield p.replace(2*delimiter, delimiter)
                p = ''


class Permission:
    def __init__(self):
        self.uid = None
        self.name = None
        self.manage_users = None
        self.manage_records = None


class SharedFolder:
    def __init__(self):
        self.uid = None
        self.path = None
        self.manage_users = None
        self.manage_records = None
        self.can_edit = None
        self.can_share = None
        self.permissions = None  # type: [Permission]


class Attachment:
    def __init__(self):
        self.file_id = None
        self.name = None
        self.size = None
        self.key = None
        self.mime = None

    def open(self):
        raise NotImplemented

class Folder:
    def __init__(self):
        self.uid = None
        self.domain = None # type: Optional[str]
        self.path = None # type: Optional[str]
        self.can_edit = None
        self.can_share = None


class Record:
    def __init__(self):
        self.uid = None
        self.title = None
        self.login = None
        self.password = None
        self.login_url = None
        self.notes = None
        self.custom_fields = {}
        self.folders = None     # type: [Folder]
        self.attachments = None # type: [Attachment]


class BaseImporter:
    def execute(self, name):
        # type: (BaseImporter, str) -> Iterable[Union[Record, SharedFolder]]

        yield from self.do_import(name)

    def do_import(self, filename):
        # type: (BaseImporter, str) -> Iterable[Union[Record, SharedFolder]]
        raise NotImplemented()

    def extension(self):
        return ''


class BaseFileImporter(BaseImporter):
    def execute(self, name):
        # type: (BaseFileImporter, str) -> Iterable[Union[Record, SharedFolder]]

        path = os.path.expanduser(name)
        if not os.path.isfile(path):
            ext = self.extension()
            if ext:
                path = path + '.' + ext

        if not os.path.isfile(path):
            raise Exception('File \'{0}\' does not exist'.format(name))

        yield from self.do_import(path)


class BaseExporter:
    def execute(self, filename, records):
        # type: (BaseExporter, str, [Union[Record, SharedFolder]]) -> None

        if filename:
            filename = os.path.expanduser(filename)
            if filename.find('.') < 0:
                ext = self.extension()
                if ext:
                    filename = filename + '.' + ext
        elif not self.supports_stdout():
            logging.error("stdout is not supported for this file format")
            return

        self.do_export(filename, records)

    def do_export(self, filename, records):
        # type: (BaseExporter, str, [Union[Record, SharedFolder]]) -> None
        raise NotImplemented()

    def has_shared_folders(self):
        return False

    def has_attachments(self):
        return False

    def extension(self):
        return ''

    def supports_stdout(self):
        return False

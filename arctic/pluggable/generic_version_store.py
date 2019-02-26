import logging

import bson
import six

from .._util import indent
from ..exceptions import NoDataFoundException, ArcticException
from arctic.pluggable._pickle_store import PickleStore
from arctic.store.versioned_item import VersionedItem

logger = logging.getLogger(__name__)

VERSION_STORE_TYPE = 'VersionStore'
_TYPE_HANDLERS = []


def register_versioned_storage(storageClass, storage_args=tuple(), storage_kwargs=None):
    add_handler(_TYPE_HANDLERS, storageClass, storage_args, storage_kwargs)


def add_handler(type_handlers, storageClass, storage_args=tuple(), storage_kwargs=None):
    storage_kwargs = storage_kwargs or {}
    existing_instances = [i for i, v in enumerate(type_handlers) if str(v.__class__) == str(storageClass)]
    store = storageClass(*storage_args, **storage_kwargs)
    if existing_instances:
        for i in existing_instances:
            type_handlers[i] = store
    else:
        type_handlers.insert(0, store)
    return storageClass

_default_bson_handler = PickleStore()

class GenericVersionStore(object):

    def __init__(self, library_name, backing_store, bson_handler=_default_bson_handler, type_handlers=None):
        self.library_name = library_name
        self._backing_store = backing_store
        self._bson_handler = bson_handler
        if type_handlers:
            self.type_handlers = []
            for th in type_handlers:
                add_handler(self.type_handlers, th)
        else:
            self.type_handlers = _TYPE_HANDLERS


    def __str__(self):
        return """<%s at %s>
%s""" % (self.__class__.__name__, hex(id(self)), indent(str(self.library_name), 4))

    def __repr__(self):
        return str(self)

    def list_symbols(self, all_symbols=False, snapshot=None, regex=None, **kwargs):
        """
        Return the symbols in this library.

        Parameters
        ----------
        all_symbols : `bool`
            If True returns all symbols under all snapshots, even if the symbol has been deleted
            in the current version (i.e. it exists under a snapshot... Default: False
        snapshot : `str`
            Return the symbols available under the snapshot.
        regex : `str`
            filter symbols by the passed in regular expression
        kwargs :
            kwarg keys are used as fields to query for symbols with metadata matching
            the kwargs query

        Returns
        -------
        String list of symbols in the library
        """
        return self._backing_store.list_symbols(self.library_name)

    def has_symbol(self, symbol, as_of=None):
        """
        Return True if the 'symbol' exists in this library AND the symbol
        isn't deleted in the specified as_of.

        It's possible for a deleted symbol to exist in older snapshots.

        Parameters
        ----------
        symbol : `str`
            symbol name for the item
        as_of : `str` or int or `datetime.datetime`
            Return the data as it was as_of the point in time.
            `int` : specific version number
            `str` : snapshot name which contains the version
            `datetime.datetime` : the version of the data that existed as_of the requested point in time
        """
        try:
            version = self._backing_store.read_version(self.library_name, symbol, as_of)
        except NoDataFoundException:
            version = None
        return version is not None

    def read_audit_log(self, symbol=None, message=None):
        """
        Return the audit log associated with a given symbol

        Parameters
        ----------
        symbol : `str`
            symbol name for the item
        """
        raise NotImplementedError()

    def list_versions(self, symbol=None, snapshot=None, latest_only=False):
        """
        Return a list of versions filtered by the passed in parameters.

        Parameters
        ----------
        symbol : `str`
            Symbol to return versions for.  If None returns versions across all
            symbols in the library.
        snapshot : `str`
            Return the versions contained in the named snapshot
        latest_only : `bool`
            Only include the latest version for a specific symbol

        Returns
        -------
        List of dictionaries describing the discovered versions in the library
        """
        raise NotImplementedError()

    def _read_handler(self, version, symbol):
        handler = None
        for h in self.type_handlers:
            if h.can_read(version, symbol):
                handler = h
                break
        if handler is None:
            handler = self._bson_handler
        return handler

    def _write_handler(self, version, symbol, data, **kwargs):
        handler = None
        for h in self.type_handlers:
            if h.can_write(version, symbol, data, **kwargs):
                handler = h
                break
        if handler is None:
            version['type'] = 'default'
            handler = self._bson_handler
        return handler

    def read(self, symbol, as_of=None, version_id=None, snapshot_id=None, date_range=None, **kwargs):
        """
        Read data for the named symbol.  Returns a VersionedItem object with
        a data and metadata element (as passed into write).

        Parameters
        ----------
        symbol : `str`
            symbol name for the item
        as_of : `datetime.datetime`
            Return the data as it was as_of at that point in time.
        version_id : `str`
            Return the specific version
        snapshot_id : `str`
            Return the specific version contained in the referenced snapshot
        date_range: `arctic.date.DateRange`
            DateRange to read data for.  Applies to Pandas data, with a DateTime index
            returns only the part of the data that falls in the DateRange.

        Returns
        -------
        VersionedItem namedtuple which contains a .data and .metadata element
        """
        _version = self._backing_store.read_version(self.library_name, symbol, as_of, version_id, snapshot_id)
        return self._do_read(symbol, _version, date_range=date_range, **kwargs)

    def get_info(self, symbol, as_of=None):
        """
        Reads and returns information about the data stored for symbol

        Parameters
        ----------
        symbol : `str`
            symbol name for the item
        as_of : `str` or int or `datetime.datetime`
            Return the data as it was as_of the point in time.
            `int` : specific version number
            `str` : snapshot name which contains the version
            `datetime.datetime` : the version of the data that existed as_of the requested point in time

        Returns
        -------
        dictionary of the information (specific to the type of data)
        """
        version = self._backing_store.read_version(self.library_name, symbol, as_of)
        handler = self._read_handler(version, symbol)
        if handler and hasattr(handler, 'get_info'):
            return handler.get_info(version)
        return {}

    def _do_read(self, symbol, version, from_version=None, **kwargs):
        if version.get('deleted'):
            raise NoDataFoundException("No data found for %s in library %s" % (symbol, self._arctic_lib.get_name()))
        handler = self._read_handler(version, symbol)
        data = handler.read(self._backing_store, self.library_name, version, symbol, from_version=from_version, **kwargs)
        return VersionedItem(symbol=symbol, library=self.library_name, version=version['version'],
                             metadata=version.pop('metadata', None), data=data)

    def read_metadata(self, symbol, as_of=None, allow_secondary=None):
        """
        Return the metadata saved for a symbol.  This method is fast as it doesn't
        actually load the data.

        Parameters
        ----------
        symbol : `str`
            symbol name for the item
        as_of : `str` or int or `datetime.datetime`
            Return the data as it was as_of the point in time.
            `int` : specific version number
            `str` : snapshot name which contains the version
            `datetime.datetime` : the version of the data that existed as_of the requested point in time
        allow_secondary : `bool` or `None`
            Override the default behavior for allowing reads from secondary members of a cluster:
            `None` : use the settings from the top-level `Arctic` object used to query this version store.
            `True` : allow reads from secondary members
            `False` : only allow reads from primary members
        """
        _version = self._backing_store.read_version(self.library_name, symbol, as_of)
        return VersionedItem(symbol=symbol, library=self.library_name, version=_version['version'],
                             metadata=_version.pop('metadata', None), data=None)

    def _insert_version(self, version):
        try:
            self._backing_store.write_version(self.library_name, version['symbol'], version)
        except DuplicateKeyError as err:
            logger.exception(err)
            raise OperationFailure("A version with the same _id exists, force a clean retry")


    def append(self, symbol, data, metadata=None, prune_previous_version=True, upsert=True, **kwargs):
        """
        Append 'data' under the specified 'symbol' name to this library.
        The exact meaning of 'append' is left up to the underlying store implementation.

        Parameters
        ----------
        symbol : `str`
            symbol name for the item
        data :
            to be persisted
        metadata : `dict`
            an optional dictionary of metadata to persist along with the symbol.
        prune_previous_version : `bool`
            Removes previous (non-snapshotted) versions from the database.
            Default: True
        upsert : `bool`
            Write 'data' if no previous version exists.
        """
        raise NotImplementedError()

    def write(self, symbol, data, metadata=None, prune_previous_version=True, **kwargs):
        """
        Write 'data' under the specified 'symbol' name to this library.

        Parameters
        ----------
        symbol : `str`
            symbol name for the item
        data :
            to be persisted
        metadata : `dict`
            an optional dictionary of metadata to persist along with the symbol.
            Default: None
        prune_previous_version : `bool`
            Removes previous (non-snapshotted) versions from the database.
            Default: True
        kwargs :
            passed through to the write handler

        Returns
        -------
        VersionedItem named tuple containing the metadata and version number
        of the written symbol in the store.
        """
        _id = bson.ObjectId()
        version = {'_id': _id, 'symbol': symbol, 'metadata': metadata}

        previous_version = self._backing_store.read_version(self.library_name, symbol)

        handler = self._write_handler(version, symbol, data, **kwargs)
        handler.write(self._backing_store, self.library_name, version, symbol, data, previous_version, **kwargs)

        #if prune_previous_version and previous_version:
        #     self._prune_previous_versions(symbol)

        # self._publish_change(symbol, version)

        # Insert the new version into the version DB
        self._insert_version(version)

        logger.debug('Finished writing versions for %s', symbol)

        return VersionedItem(symbol=symbol, library=self.library_name, version=version['version'],
                             metadata=version.pop('metadata', None), data=None)

    def write_metadata(self, symbol, metadata, prune_previous_version=True, **kwargs):
        """
        Write 'metadata' under the specified 'symbol' name to this library.
        The data will remain unchanged. A new version will be created.
        If the symbol is missing, it causes a write with empty data (None, pickled, can't append)
        and the supplied metadata.
        Returns a VersionedItem object only with a metadata element.
        Fast operation: Zero data/segment read/write operations.

        Parameters
        ----------
        symbol : `str`
            symbol name for the item
        metadata : `dict` or `None`
            dictionary of metadata to persist along with the symbol
        prune_previous_version : `bool`
            Removes previous (non-snapshotted) versions from the database.
            Default: True
        kwargs :
            passed through to the write handler (only used if symbol does not already exist or is deleted)

        Returns
        -------
        `VersionedItem`
            VersionedItem named tuple containing the metadata of the written symbol's version document in the store.
        """
        raise NotImplementedError()

    def restore_version(self, symbol, as_of, prune_previous_version=True):
        """
        Restore the specified 'symbol' data and metadata to the state of a given version/snapshot/date.
        Returns a VersionedItem object only with a metadata element.
        Fast operation: Zero data/segment read/write operations.

        Parameters
        ----------
        symbol : `str`
            symbol name for the item
        as_of : `str` or `int` or `datetime.datetime`
            Return the data as it was as_of the point in time.
            `int` : specific version number
            `str` : snapshot name which contains the version
            `datetime.datetime` : the version of the data that existed as_of the requested point in time
        prune_previous_version : `bool`
            Removes previous (non-snapshotted) versions from the database.
            Default: True

        Returns
        -------
        `VersionedItem`
            VersionedItem named tuple containing the metadata of the written symbol's version document in the store.
        """
        # if version/snapshot/data supplied in "as_of" does not exist, will fail fast with NoDataFoundException
        raise NotImplementedError()

    def delete(self, symbol):
        """
        Delete all versions of the item from the current library which aren't
        currently part of some snapshot.

        Parameters
        ----------
        symbol : `str`
            symbol name to delete
        """
        raise self._backing_store.delete_symbol(self.library_name, symbol)

    def snapshot(self, snap_name, metadata=None, skip_symbols=None, versions=None):
        """
        Snapshot versions of symbols in the library.  Can be used like:

        Parameters
        ----------
        snap_name : `str`
            name of the snapshot
        metadata : `dict`
            an optional dictionary of metadata to persist along with the symbol.
        skip_symbols : `collections.Iterable`
            optional symbols to be excluded from the snapshot
        versions: `dict`
            an optional dictionary of versions of the symbols to be snapshot
        """
        self._backing_store.snapshot(self.library_name, snap_name, metadata=None, skip_symbols=None, versions=None)


    def delete_snapshot(self, snap_name):
        """
        Delete a named snapshot

        Parameters
        ----------
        symbol : `str`
            The snapshot name to delete
        """
        self._backing_store.delete_snapshot(self.library_name, snap_name)


    def list_snapshots(self):
        """
        List the snapshots in the library

        Returns
        -------
        string list of snapshot names
        """
        raise self._backing_store.list_snapshots(self.library_name)


    def stats(self):
        """
        Return storage statistics about the library

        Returns
        -------
        dictionary of storage stats
        """
        raise NotImplementedError()

    def _fsck(self, dry_run):
        """
        Run a consistency check on this VersionStore library.
        """
        raise NotImplementedError()

    def _cleanup_orphaned_chunks(self, dry_run):
        """
        Fixes any chunks who have parent pointers to missing versions.
        Removes the broken parent pointer and, if there are no other parent pointers for the chunk,
        removes the chunk.
        """
        raise NotImplementedError()

    def _cleanup_orphaned_versions(self, dry_run):
        """
        Fixes any versions who have parent pointers to missing snapshots.
        Note, doesn't delete the versions, just removes the parent pointer if it no longer
        exists in snapshots.
        """
        raise NotImplementedError()

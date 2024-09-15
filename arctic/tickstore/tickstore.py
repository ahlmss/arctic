from __future__ import print_function

import copy
import logging
from datetime import datetime as dt, timedelta

import numpy as np
import pandas as pd
import pymongo
from bson.binary import Binary
from pymongo import ReadPreference
from pymongo.errors import OperationFailure

try:
    from pandas.core.frame import _arrays_to_mgr
except ImportError:
    # Deprecated since pandas 0.23.4
    from pandas.core.internals.construction import arrays_to_mgr as _arrays_to_mgr

try:
    from pandas.api.types import infer_dtype
except ImportError:
    from pandas.lib import infer_dtype

from ..date import DateRange, to_pandas_closed_closed, mktz, datetime_to_ms, ms_to_datetime, CLOSED_CLOSED, to_dt, utc_dt_to_local_dt
from ..decorators import mongo_retry
from ..exceptions import OverlappingDataException, NoDataFoundException, UnorderedDataException, UnhandledDtypeException, ArcticException
from .._util import indent

try:
    from lz4.block import compress as lz4_compress, decompress as lz4_decompress
    lz4_compressHC = lambda _str: lz4_compress(_str, mode='high_compression')
except ImportError as e:
    from lz4 import compress as lz4_compress, compressHC as lz4_compressHC, decompress as lz4_decompress


PD_VER = pd.__version__
logger = logging.getLogger(__name__)

# Example-Schema:
# --------------
# {ID: ObjectId('52b1d39eed5066ab5e87a56d'),
#  SYMBOL: u'symbol'
#  INDEX: Binary('...', 0),
#  IMAGE_DOC: { IMAGE:  {
#                          'ASK': 10.
#                          ...
#                        }
#              's': <sequence_no>
#              't': DateTime(...)
#             }
#  COLUMNS: {
#   'ACT_FLAG1': {
#        DATA: Binary('...', 0),
#        DTYPE: u'U1',
#        ROWMASK: Binary('...', 0)},
#   'ACVOL_1': {
#        DATA: Binary('...', 0),
#        DTYPE: u'float64',
#        ROWMASK: Binary('...', 0)},
#               ...
#    }
#  START: DateTime(...),
#  END: DateTime(...),
#  END_SEQ: 31553879L,
#  SEGMENT: 1386933906826L,
#  SHA: 1386933906826L,
#  VERSION: 3,
# }

TICK_STORE_TYPE = 'TickStoreV3'

ID = '_id'
SYMBOL = 'sy'
INDEX = 'i'
START = 's'
END = 'e'
START_SEQ = 'sS'
END_SEQ = 'eS'
SEGMENT = 'se'
SHA = 'sh'
IMAGE_DOC = 'im'
IMAGE = 'i'

COLUMNS = 'cs'
DATA = 'd'
DTYPE = 't'
IMAGE_TIME = 't'
ROWMASK = 'm'

COUNT = 'c'
VERSION = 'v'

META = 'md'

CHUNK_VERSION_NUMBER = 3


class TickStore(object):

    @classmethod
    def initialize_library(cls, arctic_lib, **kwargs):
        TickStore(arctic_lib)._ensure_index()

    @mongo_retry
    def _ensure_index(self):
        collection = self._collection
        collection.create_index([(SYMBOL, pymongo.ASCENDING),
                                 (START, pymongo.ASCENDING)], background=True)
        collection.create_index([(START, pymongo.ASCENDING)], background=True)

        self._metadata.create_index([(SYMBOL, pymongo.ASCENDING)], background=True, unique=True)

    def __init__(self, arctic_lib, chunk_size=100000):
        """
        Parameters
        ----------
        arctic_lib : ArcticLibraryBinding
            Arctic Library
        chunk_size : int
            Number of ticks to store in a document before splitting to another document.
            if the library was obtained through get_library then set with: self._chuck_size = 10000
        """
        self._arctic_lib = arctic_lib
        # Do we allow reading from secondaries
        self._allow_secondary = self._arctic_lib.arctic._allow_secondary
        self._chunk_size = chunk_size
        self._reset()

    @mongo_retry
    def _reset(self):
        # The default collections
        self._collection = self._arctic_lib.get_top_level_collection()
        self._metadata = self._collection.metadata

    def __getstate__(self):
        return {'arctic_lib': self._arctic_lib}

    def __setstate__(self, state):
        return TickStore.__init__(self, state['arctic_lib'])

    def __str__(self):
        return """<%s at %s>
%s""" % (self.__class__.__name__, hex(id(self)), indent(str(self._arctic_lib), 4))

    def __repr__(self):
        return str(self)

    def delete(self, symbol, date_range=None):
        """
        Delete all chunks for a symbol.

        Which are, for the moment, fully contained in the passed in
        date_range.

        Parameters
        ----------
        symbol : `str`
            symbol name for the item
        date_range : `date.DateRange`
            DateRange to delete ticks in
        """
        query = {SYMBOL: symbol}
        date_range = to_pandas_closed_closed(date_range)
        if date_range is not None:
            assert date_range.start and date_range.end
            query[START] = {'$gte': date_range.start}
            query[END] = {'$lte': date_range.end}
        else:
            # delete metadata on complete deletion
            self._metadata.delete_one({SYMBOL: symbol})
        return self._collection.delete_many(query)

    def list_symbols(self, date_range=None):
        return self._collection.distinct(SYMBOL)

    def _mongo_date_range_query(self, symbol, date_range):
        # Handle date_range
        if not date_range:
            date_range = DateRange()

        # We're assuming CLOSED_CLOSED on these Mongo queries
        assert date_range.interval == CLOSED_CLOSED

        # Since we only index on the start of the chunk,
        # we do a pre-flight aggregate query to find the point where the
        # earliest relevant chunk starts.

        start_range = {}
        first_dt = last_dt = None
        if date_range.start:
            assert date_range.start.tzinfo
            start = date_range.start

            # If all chunks start inside of the range, we default to capping to our
            # range so that we don't fetch any chunks from the beginning of time
            start_range['$gte'] = start

            match = self._symbol_query(symbol)
            match.update({'s': {'$lte': start}})

            result = self._collection.aggregate([
                # Only look at the symbols we are interested in and chunks that
                # start before our start datetime
                {'$match': match},
                # Throw away everything but the start of every chunk and the symbol
                {'$project': {'_id': 0, 's': 1, 'sy': 1}},
                # For every symbol, get the latest chunk start (that is still before
                # our sought start)
                {'$group': {'_id': '$sy', 'start': {'$max': '$s'}}},
                {'$sort': {'start': 1}},
            ])
            # Now we need to get the earliest start of the chunk that still spans the start point.
            # Since we got them sorted by start, we just need to fetch their ends as well and stop
            # when we've seen the first such chunk
            try:
                for candidate in result:
                    chunk = self._collection.find_one({'s': candidate['start'], 'sy': candidate['_id']}, {'e': 1})
                    if chunk['e'].replace(tzinfo=mktz('UTC')) >= start:
                        start_range['$gte'] = candidate['start'].replace(tzinfo=mktz('UTC'))
                        break
            except StopIteration:
                pass

        # Find the end bound
        if date_range.end:
            # If we have an end, we are only interested in the chunks that start before the end.
            assert date_range.end.tzinfo
            last_dt = date_range.end
        else:
            logger.info("No end provided.  Loading a month for: {}:{}".format(symbol, first_dt))
            if not first_dt:
                first_doc = self._collection.find_one(self._symbol_query(symbol),
                                                      projection={START: 1, ID: 0},
                                                      sort=[(START, pymongo.ASCENDING)])
                if not first_doc:
                    raise NoDataFoundException()

                first_dt = first_doc[START]
            last_dt = first_dt + timedelta(days=30)
        if last_dt:
            start_range['$lte'] = last_dt

        # Return chunks in the specified range
        if not start_range:
            return {}
        return {START: start_range}

    def _symbol_query(self, symbol):
        if isinstance(symbol, str):
            query = {SYMBOL: symbol}
        elif symbol is not None:
            query = {SYMBOL: {'$in': symbol}}
        else:
            query = {}
        return query

    def _read_preference(self, allow_secondary):
        """ Return the mongo read preference given an 'allow_secondary' argument
        """
        allow_secondary = self._allow_secondary if allow_secondary is None else allow_secondary
        return ReadPreference.NEAREST if allow_secondary else ReadPreference.PRIMARY

    def read(self, symbol, date_range=None, columns=None, include_images=False, allow_secondary=None,
             _target_tick_count=0):
        """
        Read data for the named symbol.  Returns a VersionedItem object with
        a data and metdata element (as passed into write).

        Parameters
        ----------
        symbol : `str`
            symbol name for the item
        date_range : `date.DateRange`
            Returns ticks in the specified DateRange
        columns : `list` of `str`
            Columns (fields) to return from the tickstore
        include_images : `bool`
            Should images (/snapshots) be included in the read
        allow_secondary : `bool` or `None`
            Override the default behavior for allowing reads from secondary members of a cluster:
            `None` : use the settings from the top-level `Arctic` object used to query this version store.
            `True` : allow reads from secondary members
            `False` : only allow reads from primary members

        Returns
        -------
        pandas.DataFrame of data
        """
        perf_start = dt.now()
        rtn = {}
        column_set = set()

        multiple_symbols = not isinstance(symbol, str)

        date_range = to_pandas_closed_closed(date_range)
        query = self._symbol_query(symbol)
        query.update(self._mongo_date_range_query(symbol, date_range))

        if columns:
            projection = dict([(SYMBOL, 1),
                               (INDEX, 1),
                               (START, 1),
                               (VERSION, 1),
                               (IMAGE_DOC, 1)] +
                              [(COLUMNS + '.%s' % c, 1) for c in columns])
            column_set.update([c for c in columns if c != 'SYMBOL'])
        else:
            projection = dict([(SYMBOL, 1),
                               (INDEX, 1),
                               (START, 1),
                               (VERSION, 1),
                               (COLUMNS, 1),
                               (IMAGE_DOC, 1)])

        column_dtypes = {}
        ticks_read = 0
        data_coll = self._collection.with_options(read_preference=self._read_preference(allow_secondary))
        for b in data_coll.find(query, projection=projection).sort([(START, pymongo.ASCENDING)],):
            data = self._read_bucket(b, column_set, column_dtypes,
                                     multiple_symbols or (columns is not None and 'SYMBOL' in columns),
                                     include_images, columns)
            for k, v in data.items():
                try:
                    rtn[k].append(v)
                except KeyError:
                    rtn[k] = [v]
            # For testing
            ticks_read += len(data[INDEX])
            if _target_tick_count and ticks_read > _target_tick_count:
                break

        if not rtn:
            raise NoDataFoundException("No Data found for {} in range: {}".format(symbol, date_range))
        rtn = self._pad_and_fix_dtypes(rtn, column_dtypes)

        index = pd.DatetimeIndex(np.concatenate(rtn[INDEX]).astype('datetime64[ms]'), tz='UTC')
        if columns is None:
            columns = [x for x in rtn.keys() if x not in (INDEX, 'SYMBOL')]
        if multiple_symbols and 'SYMBOL' not in columns:
            columns = ['SYMBOL', ] + columns

        if len(index) > 0:
            arrays = [np.concatenate(rtn[k]) for k in columns]
        else:
            arrays = [[] for _ in columns]

        if multiple_symbols:
            sort = np.argsort(index, kind='mergesort')
            index = index[sort]
            arrays = [a[sort] for a in arrays]

        t = (dt.now() - perf_start).total_seconds()
        logger.info("Got data in %s secs, creating DataFrame..." % t)
        if pd.__version__.startswith("0.") or pd.__version__.startswith("1.0"):
            mgr = _arrays_to_mgr(arrays, columns, index, columns, dtype=None)
        else:
            # 4th argument removed + new argument typ is mandatory
            mgr = _arrays_to_mgr(arrays, columns, index, dtype=None, typ="array")

        rtn = pd.DataFrame(mgr)
        # Present data in the user's default TimeZone
        rtn.index = rtn.index.tz_convert(mktz())

        t = (dt.now() - perf_start).total_seconds()
        ticks = len(rtn)
        rate = int(ticks / t) if t != 0 else float("nan")
        logger.info("%d rows in %s secs: %s ticks/sec" % (ticks, t, rate))
        if not rtn.index.is_monotonic_increasing:
            logger.error("TimeSeries data is out of order, sorting!")
            rtn = rtn.sort_index(kind='mergesort')
        if date_range:
            # FIXME: support DateRange.interval...
            rtn = rtn.loc[date_range.start:date_range.end]
        return rtn

    def read_metadata(self, symbol):
        """
        Read metadata for the specified symbol

        Parameters
        ----------
        symbol : `str`
            symbol name for the item

        Returns
        -------
        dict
        """
        return self._metadata.find_one({SYMBOL: symbol})[META]

    def _pad_and_fix_dtypes(self, cols, column_dtypes):
        # Pad out Nones with empty arrays of appropriate dtypes
        rtn = {}
        index = cols[INDEX]
        full_length = len(index)
        for k, v in cols.items():
            if k != INDEX and k != 'SYMBOL':
                col_len = len(v)
                if col_len < full_length:
                    v = ([None, ] * (full_length - col_len)) + v
                    assert len(v) == full_length
                for i, arr in enumerate(v):
                    if arr is None:
                        #  Replace Nones with appropriate-length empty arrays
                        v[i] = self._empty(len(index[i]), column_dtypes.get(k))
                    else:
                        # Promote to appropriate dtype only if we can safely cast all the values
                        # This avoids the case with strings where None is cast as 'None'.
                        # Casting the object to a string is not worthwhile anyway as Pandas changes the
                        # dtype back to objectS
                        if (i == 0 or v[i].dtype != v[i - 1].dtype) and np.can_cast(v[i].dtype, column_dtypes[k],
                                                                                    casting='safe'):
                            v[i] = v[i].astype(column_dtypes[k], casting='safe')

            rtn[k] = v
        return rtn

    def _set_or_promote_dtype(self, column_dtypes, c, dtype):
        existing_dtype = column_dtypes.get(c)
        if existing_dtype is None or existing_dtype != dtype:
            # Promote ints to floats - as we can't easily represent NaNs
            if np.issubdtype(dtype, int):
                dtype = np.dtype('f8')
            column_dtypes[c] = np.promote_types(column_dtypes.get(c, dtype), dtype)

    def _prepend_image(self, document, im, rtn_length, column_dtypes, column_set, columns):
        image = im[IMAGE]
        first_dt = im[IMAGE_TIME]
        if not first_dt.tzinfo:
            first_dt = first_dt.replace(tzinfo=mktz('UTC'))
        document[INDEX] = np.insert(document[INDEX], 0, np.uint64(datetime_to_ms(first_dt)))
        for field in image:
            if field == INDEX:
                continue
            if columns and field not in columns:
                continue
            if field not in document or document[field] is None:
                col_dtype = np.dtype(str if isinstance(image[field], str) else 'f8')
                document[field] = self._empty(rtn_length, dtype=col_dtype)
                column_dtypes[field] = col_dtype
                column_set.add(field)
            val = image[field]
            document[field] = np.insert(document[field], 0, document[field].dtype.type(val))
        # Now insert rows for fields in document that are not in the image
        for field in set(document).difference(set(image)):
            if field == INDEX:
                continue
            logger.debug("Field %s is missing from image!" % field)
            if document[field] is not None:
                val = np.nan
                document[field] = np.insert(document[field], 0, document[field].dtype.type(val))
        return document

    def _read_bucket(self, doc, column_set, column_dtypes, include_symbol, include_images, columns):
        rtn = {}
        if doc[VERSION] != 3:
            raise ArcticException("Unhandled document version: %s" % doc[VERSION])
        # np.cumsum copies the read-only array created with frombuffer
        rtn[INDEX] = np.cumsum(np.frombuffer(lz4_decompress(doc[INDEX]), dtype='uint64'))
        doc_length = len(rtn[INDEX])
        column_set.update(doc[COLUMNS].keys())

        # get the mask for the columns we're about to load
        union_mask = np.zeros((doc_length + 7) // 8, dtype='uint8')
        for c in column_set:
            try:
                coldata = doc[COLUMNS][c]
                # the or below will make a copy of this read-only array
                mask = np.frombuffer(lz4_decompress(coldata[ROWMASK]), dtype='uint8')
                union_mask = union_mask | mask
            except KeyError:
                rtn[c] = None
        union_mask = np.unpackbits(union_mask)[:doc_length].astype('bool')
        rtn_length = np.sum(union_mask)

        rtn[INDEX] = rtn[INDEX][union_mask]
        if include_symbol:
            rtn['SYMBOL'] = [doc[SYMBOL], ] * rtn_length

        # Unpack each requested column in turn
        for c in column_set:
            try:
                coldata = doc[COLUMNS][c]
                dtype = np.dtype(coldata[DTYPE])
                # values ends up being copied by pandas before being returned to the user. However, we
                # copy it into a bytearray here for safety.
                values = np.frombuffer(bytearray(lz4_decompress(coldata[DATA])), dtype=dtype)
                self._set_or_promote_dtype(column_dtypes, c, dtype)
                rtn[c] = self._empty(rtn_length, dtype=column_dtypes[c])
                # unpackbits will make a copy of the read-only array created by frombuffer
                rowmask = np.unpackbits(np.frombuffer(lz4_decompress(coldata[ROWMASK]),
                                        dtype='uint8'))[:doc_length].astype('bool')
                rowmask = rowmask[union_mask]
                rtn[c][rowmask] = values
            except KeyError:
                rtn[c] = None

        if include_images and doc.get(IMAGE_DOC, {}).get(IMAGE, {}):
            rtn = self._prepend_image(rtn, doc[IMAGE_DOC], rtn_length, column_dtypes, column_set, columns)
        return rtn

    def _empty(self, length, dtype):
        if dtype is not None and dtype == np.float64:
            rtn = np.empty(length, dtype)
            rtn[:] = np.nan
            return rtn
        else:
            return np.empty(length, dtype=np.object_)

    def stats(self):
        """
        Return storage statistics about the library

        Returns
        -------
        dictionary of storage stats
        """
        res = {}
        db = self._collection.database
        conn = db.connection
        res['sharding'] = {}
        try:
            sharding = conn.config.databases.find_one({'_id': db.name})
            if sharding:
                res['sharding'].update(sharding)
            res['sharding']['collections'] = list(conn.config.collections.find(
                                                  {'_id': {'$regex': '^' + db.name + r"\..*"}}))
        except OperationFailure:
            # Access denied
            pass
        res['dbstats'] = db.command('dbstats')
        res['chunks'] = db.command('collstats', self._collection.name)
        res['totals'] = {'count': res['chunks']['count'],
                         'size': res['chunks']['size'],
                         }
        return res

    def _assert_nonoverlapping_data(self, symbol, start, end):
        #
        # Imagine we're trying to insert a tick bucket like:
        #      |S------ New-B -------------- E|
        #  |---- 1 ----| |----- 2 -----| |----- 3 -----|
        #
        # S = New-B Start
        # E = New-B End
        # New-B overlaps with existing buckets 1,2,3
        #
        # All we need to do is find the bucket who's start is immediately before (E)
        # If that document's end is > S, then we know it overlaps
        # with this bucket.
        doc = self._collection.find_one({SYMBOL: symbol,
                                         START: {'$lt': end}
                                         },
                                        projection={START: 1,
                                                    END: 1,
                                                    '_id': 0},
                                        sort=[(START, pymongo.DESCENDING)])
        if doc:
            if not doc[END].tzinfo:
                doc[END] = doc[END].replace(tzinfo=mktz('UTC'))
            if doc[END] > start:
                raise OverlappingDataException(
                    "Document already exists with start:{} end:{} in the range of our start:{} end:{}".format(
                        doc[START], doc[END], start, end))

    def write(self, symbol, data, initial_image=None, metadata=None):
        """
        Writes a list of market data events.

        Parameters
        ----------
        symbol : `str`
            symbol name for the item
        data : list of dicts or a pandas.DataFrame
            List of ticks to store to the tick-store.
            if a list of dicts, each dict must contain a 'index' datetime
            if a pandas.DataFrame the index must be a Timestamp that can be converted to a datetime.
            Index names will not be preserved.
        initial_image : dict
            Dict of the initial image at the start of the document. If this contains a 'index' entry it is
            assumed to be the time of the timestamp of the index
        metadata: dict
            optional user defined metadata - one per symbol
        """
        pandas = False
        # Check for overlapping data
        if isinstance(data, list):
            start = data[0]['index']
            end = data[-1]['index']
        elif isinstance(data, pd.DataFrame):
            start = data.index[0].to_pydatetime()
            end = data.index[-1].to_pydatetime()
            pandas = True
        else:
            raise UnhandledDtypeException("Can't persist type %s to tickstore" % type(data))
        self._assert_nonoverlapping_data(symbol, to_dt(start), to_dt(end))

        if pandas:
            buckets = self._pandas_to_buckets(data, symbol, initial_image)
        else:
            buckets = self._to_buckets(data, symbol, initial_image)
        self._write(buckets)

        if metadata:
            self._metadata.replace_one({SYMBOL: symbol},
                                       {SYMBOL: symbol, META: metadata},
                                       upsert=True)

    def _write(self, buckets):
        start = dt.now()
        mongo_retry(self._collection.insert_many)(buckets)
        t = (dt.now() - start).total_seconds()
        ticks = len(buckets) * self._chunk_size
        rate = int(ticks / t) if t != 0 else float("nan")
        logger.debug("%d buckets in %s: approx %s ticks/sec" % (len(buckets), t, rate))

    def _pandas_to_buckets(self, x, symbol, initial_image):
        rtn = []
        for i in range(0, len(x), self._chunk_size):
            bucket, initial_image = TickStore._pandas_to_bucket(x[i:i + self._chunk_size], symbol, initial_image)
            rtn.append(bucket)
        return rtn

    def _to_buckets(self, x, symbol, initial_image):
        rtn = []
        for i in range(0, len(x), self._chunk_size):
            bucket, initial_image = TickStore._to_bucket(x[i:i + self._chunk_size], symbol, initial_image)
            rtn.append(bucket)
        return rtn

    @staticmethod
    def _to_ms(date):
        if isinstance(date, dt):
            if not date.tzinfo:
                logger.warning('WARNING: treating naive datetime as UTC in write path')
            return datetime_to_ms(date)
        return date

    @staticmethod
    def _str_dtype(dtype):
        """
        Represent dtypes without byte order, as earlier Java tickstore code doesn't support explicit byte order.
        """
        assert dtype.byteorder != '>'
        if dtype.kind == 'i':
            assert dtype.itemsize == 8
            return 'int64'
        elif dtype.kind == 'f':
            assert dtype.itemsize == 8
            return 'float64'
        elif dtype.kind == 'U':
            return 'U%d' % (dtype.itemsize / 4)
        else:
            raise UnhandledDtypeException("Bad dtype '%s'" % dtype)

    @staticmethod
    def _ensure_supported_dtypes(array):
        # We only support these types for now, as we need to read them in Java
        if array.dtype.kind == 'i':
            array = array.astype('<i8')
        elif array.dtype.kind == 'f':
            array = array.astype('<f8')
        elif array.dtype.kind in ('O', 'U', 'S'):
            if array.dtype.kind == 'O' and infer_dtype(array) not in ['unicode', 'string', 'bytes']:
                # `string` in python2 and `bytes` in python3
                raise UnhandledDtypeException("Casting object column to string failed")
            try:
                array = array.astype(np.unicode_)
            except (UnicodeDecodeError, SystemError):
                # `UnicodeDecodeError` in python2 and `SystemError` in python3
                array = np.array([s.decode('utf-8') for s in array])
            except:
                raise UnhandledDtypeException("Only unicode and utf8 strings are supported.")
        else:
            raise UnhandledDtypeException("Unsupported dtype '%s' - only int64, float64 and U are supported" % array.dtype)
        # Everything is little endian in tickstore
        if array.dtype.byteorder != '<':
            array = array.astype(array.dtype.newbyteorder('<'))
        return array

    @staticmethod
    def _pandas_compute_final_image(df, image, end):
        # Compute the final image with forward fill of df applied to the image
        final_image = copy.copy(image)
        last_values = df.ffill().tail(1).to_dict()
        last_dict = {i: list(a.values())[0] for i, a in last_values.items()}
        final_image.update(last_dict)
        final_image['index'] = end
        return final_image

    @staticmethod
    def _pandas_to_bucket(df, symbol, initial_image):
        rtn = {SYMBOL: symbol, VERSION: CHUNK_VERSION_NUMBER, COLUMNS: {}, COUNT: len(df)}
        end = to_dt(df.index[-1].to_pydatetime())
        if initial_image:
            if 'index' in initial_image:
                start = min(to_dt(df.index[0].to_pydatetime()), initial_image['index'])
            else:
                start = to_dt(df.index[0].to_pydatetime())
            image_start = initial_image.get('index', start)
            rtn[IMAGE_DOC] = {IMAGE_TIME: image_start, IMAGE: initial_image}
            final_image = TickStore._pandas_compute_final_image(df, initial_image, end)
        else:
            start = to_dt(df.index[0].to_pydatetime())
            final_image = {}
        rtn[END] = end
        rtn[START] = start

        logger.warning("NB treating all values as 'exists' - no longer sparse")
        rowmask = Binary(lz4_compressHC(np.packbits(np.ones(len(df), dtype='uint8')).tobytes()))

        index_name = df.index.names[0] or "index"
        if PD_VER < '0.23.0':
            recs = df.to_records(convert_datetime64=False)
        else:
            recs = df.to_records()

        for col in df:
            array = TickStore._ensure_supported_dtypes(recs[col])
            col_data = {
                DATA: Binary(lz4_compressHC(array.tobytes())),
                ROWMASK: rowmask,
                DTYPE: TickStore._str_dtype(array.dtype),
            }
            rtn[COLUMNS][col] = col_data
        rtn[INDEX] = Binary(
            lz4_compressHC(np.concatenate(
                ([recs[index_name][0].astype('datetime64[ms]').view('uint64')],
                 np.diff(
                     recs[index_name].astype('datetime64[ms]').view('uint64')))).tobytes()))
        return rtn, final_image

    @staticmethod
    def _to_bucket(ticks, symbol, initial_image):
        rtn = {SYMBOL: symbol, VERSION: CHUNK_VERSION_NUMBER, COLUMNS: {}, COUNT: len(ticks)}
        data = {}
        rowmask = {}
        start = to_dt(ticks[0]['index'])
        end = to_dt(ticks[-1]['index'])
        final_image = copy.copy(initial_image) if initial_image else {}
        for i, t in enumerate(ticks):
            if initial_image:
                final_image.update(t)
            for k, v in t.items():
                try:
                    if k != 'index':
                        rowmask[k][i] = 1
                    else:
                        v = TickStore._to_ms(v)
                        if data[k][-1] > v:
                            raise UnorderedDataException("Timestamps out-of-order: %s > %s" % (
                                ms_to_datetime(data[k][-1]), t))
                    data[k].append(v)
                except KeyError:
                    if k != 'index':
                        rowmask[k] = np.zeros(len(ticks), dtype='uint8')
                        rowmask[k][i] = 1
                    data[k] = [v]

        rowmask = dict([(k, Binary(lz4_compressHC(np.packbits(v).tobytes())))
                        for k, v in rowmask.items()])
        for k, v in data.items():
            if k != 'index':
                v = np.array(v)
                v = TickStore._ensure_supported_dtypes(v)
                rtn[COLUMNS][k] = {DATA: Binary(lz4_compressHC(v.tobytes())),
                                   DTYPE: TickStore._str_dtype(v.dtype),
                                   ROWMASK: rowmask[k]}

        if initial_image:
            image_start = initial_image.get('index', start)
            if image_start > start:
                raise UnorderedDataException("Image timestamp is after first tick: %s > %s" % (
                    image_start, start))
            start = min(start, image_start)
            rtn[IMAGE_DOC] = {IMAGE_TIME: image_start, IMAGE: initial_image}
        rtn[END] = end
        rtn[START] = start
        rtn[INDEX] = Binary(lz4_compressHC(np.concatenate(([data['index'][0]], np.diff(data['index']))).tobytes()))
        return rtn, final_image

    def max_date(self, symbol):
        """
        Return the maximum datetime stored for a particular symbol

        Parameters
        ----------
        symbol : `str`
            symbol name for the item
        """
        res = self._collection.find_one({SYMBOL: symbol}, projection={ID: 0, END: 1},
                                        sort=[(START, pymongo.DESCENDING)])
        if res is None:
            raise NoDataFoundException("No Data found for {}".format(symbol))
        return utc_dt_to_local_dt(res[END])

    def min_date(self, symbol):
        """
        Return the minimum datetime stored for a particular symbol

        Parameters
        ----------
        symbol : `str`
            symbol name for the item
        """
        res = self._collection.find_one({SYMBOL: symbol}, projection={ID: 0, START: 1},
                                        sort=[(START, pymongo.ASCENDING)])
        if res is None:
            raise NoDataFoundException("No Data found for {}".format(symbol))
        return utc_dt_to_local_dt(res[START])

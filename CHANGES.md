## Changelog

### 1.83.1 (2024-04-08) 
 * Release: #1022 fixes for pandas 2 and latest numpy
 * Compatibility: unpin pandas and numpy
 * Compatibility: update pinning to pymongo<4
 * Compatibility: tested on python 3.11

### 1.82.2 (2024-02-01) 
 * Release: #1022 Prepare release 1.82.2 
 * Perf: #1021 Improve performance of Tickstore read 
 * Bugfix: #1019 Remove failing requirements.txt versions
 * Docs: #1019 Updated links to ArcticDB website and docs
 * Docs: #1017 Fix doc for chunkstore's list_symbols

### 1.82.1 (2023-10-09)
 * Release: #1014 Prepare release 1.82.1
 * Bugfix: #1013 Fix serialized tz name for index timezones of dateutil.timezone.tzutc()
 * Bugfix: #1013 Fix serialized tz name for single-level index timezones of dateutil.timezone.gettz("UTC")
  
### 1.82.0 (2023-07-24)
 * Release: #1012 version 1.82.0
 * Compatibility: update pinning from pandas<1.1, to pandas<2
 * Compatibility: update pinning from numpy<1.19 to numpy<2
 * Build: specify which version of python/numpy/pandas to test
 * Bugfix: #887 #928 resolve import error on pandas.Panel, Panel was removed in pandas 1.0
 * Bugfix: fix pandas get_timezone() argument cannot be None
 * Bugfix: fix np.float/np.int/np.book depreciations
 * Bugfix: fix numpy tostring() is deprecated. Use tobytes() instead.
 * Bugfix: numpy.testing.utils is deprecated
 * Bugfix: pandas.util.testing is deprecated
 * Cleanup: remove async_benchmark

### 1.81.2 (2023-05-11)
  * Feature: #1000, #1001, #1002, #1003, #1007, #1008 ArcticDB docs, links etc
  * Bugfix:  #1009 force CircleCI to install tzlocal==4.2

### 1.81.1 (2023-03-13)
  * Feature: #996 release wheel to pypi as well as tar.gz, egg.

### 1.81.0 (2023-03-10)
  * Bugfix:  #979 fix circleci mongo install
  * Feature: #980 get testpack running with mongod 4.4.18
  * Bugfix:  #985 suppress FutureWarning for Panel import
  * Bugfix:  #989 VersionStore slow snapshot delete add new index
  * Bugfix:  #806, #990 DateTimeIndex tz serialization

### 1.80.5 (2022-09-05)
  * Feature: #950 remove all traces of python 2.7 and six package
  * Feature: #959 add python 3.8 support
  * Feature: #962 pin pandas<1.1.0, numpy<1.19.0

### 1.80.4 (2022-01-25)
  * Bugfix:  #940 fix rows per chunk causing divide by zero
  * Feature: #943 check markdown rendering of README.md and CHANGES.md in build
  * Bugfix:  #946 move test dependencies to tests_require

### 1.80.3 (2022-01-20)
  * Feature: #941 use named index for VersionStore to avoid 127 max fully qualified index name
  * Bugfix:  #935, #936 fixed README.md rendering which was preventing pypi upload

### 1.80.2 (2022-01-10)
  * Bugfix: #932 revert serialization-optimization (#909, #910)

### 1.80.1 (2021-12-09)
  * Bugfix: #855 use IXSCAN for list\_symbols which speeds up snapshotting (actually #856)
  * Bugfix: #926 avoid pathologically slow count_documents() call with pymongo > 3.6.0

### 1.80.0 (2021-10-28)
  * Feature: #919 Add CircleCI badge to README.md
  * Feature: #917 Add CircleCI build
  * Bugfix:  #910 Fix column subsetting bug
  * Bugfix:  #909 Speedup FrameToArray serialiser for ChunkStore by removing intermediate DataFrame construction
  * Bugfix:  #902 Chunkstore-read-speedup
  * Bugfix:  #872 Do not spam if not permissioned on cache db
  * Bugfix:  #874 Pickle protocol 5 not supported in 3.7 and below
  * Bugfix:       Handle uninitialized cache object
  * Feature: #897 Pin numpy 1.18.4
  * Feature: #897 Pin pandas 1.0.3
  * Bugfix:  #881 Fix for issue #815
  * Bugfix:  #875 Fix flake8 errors

### 1.79.4 (2020-12-01)
  * Bugfix: Update code to work with latest version of pandas
  * Bugfix: Fix missing column handling in numpy serializer

### 1.79.3 (2019-12-6)
  * Bugfix: #832 Bytes to unicode for pd.Series
  * Feature: #825 Max BSON size configurable
  * Bugfix: #823 Don't retry bulk write errors
  * Feature: #802 kwargs passed through to iterators in chunkstore

### 1.79.2 (2019-05-21)
  * Feature: Allow list_library caching to be tunable via a settings collection.
  * Bugfix: #777: Handle empty columns in dataframes

### 1.79.1 (2019-05-03)
  * Bugfix: Pandas convert multiindexes to unicode if flag set.

### 1.79 (2019-05-02)
  * Bugfix: #765 Pandas data columns require encoding to convert to unicode.

### 1.78 (2019-05-02)
  * Bugfix: Use the default encoding (ascii) instead of bytes for unpickling.

### 1.77 (2019-05-01)
  * Bugfix: pypandoc not rendering README correctly for PYPI
  * Bugfix: #744 get_info on an empty dataframe raises an exception
  * Bugfix: #751 Handle unpickling py2 datetime and other object types with latin1
  * Bugfix: #598 Add an option to convert py2 str to py3 str (unicode type) on read.

### 1.74 (2019-02-28)
  * Bugfix: #712 Pandas deprecation warning in chunkstore serializer
  * BugFix: #670 Lots of pycodestyle fixes
  * BugFix: #691 Fix arrays_to_mgr for pandas 0.23.4+
  * BugFix: #698 Fix no handler in logging warning
  * BugFix: #705 Use sort_index instead of sortlevel\_
  * BugFix: #710: Initialize SEGMENT_SHA in versions for writes and appends
  * Feature: #669 Experimental initial implementation of async arctic
  * Feature: #704 Do not enable sharding by default in BSONStore.
  * Feature: #688 Remove Chunkstore check for issue #422
  * Feature: #717 Add a best effort cache for list_libraries
  * Bugfix: #722 Exception while reading a column from chunkstore with a column missing in the chunk

### 1.73 (2018-11-27)
  * Bugfix: #658 Write/append errors for Panel objects from older pandas versions
  * Feature: #653 Add version meta-info in arctic module
  * Feature: #663 Include arctic numerical version in the metadata of the version document
  * Feature: #650 Implemented forward pointers for chunks in VersionStore (modes: enabled/disabled/hybrid)

### 1.72 (2018-11-06)
  * Feature: #577 Added implementation for incremental serializer for numpy records
  * Bugfix: #648 Fix issue with Timezone aware Pandas types, which don't contain hasobject attribute

### 1.71  (2018-11-05)
  * Bugfix: #645 Fix write errors for Pandas DataFrame that has mixed object/string types in multi-index column

### 1.70 (2018-10-30)
  * Bugfix: #157 Assure that serialized dataframes remain value-equivalent (e.g. avoid NaN --> 'nan' in mixed string columns)
  * Bugfix: #608 Ensure Arctic performs well with MongoDB 3.6 (sorting)
  * Bugfix: #629 Column kwarg no longer modified
  * Bugfix: #641 DateRange.intersection open/closed range fix
  * Feature: #493 Can pass kwargs when calling MongoClient, e.g. for ssl
  * Feature: #590 Faster write handler selection for DataFrames with objects  
  * Feature: #604 Improved handling handling for pickling serialization decidions


### 1.69 (2018-09-12)
  * Docs: VersionStore documentation
  * Bugfix: Issue #612 ThreadPool should be created by process using it
  * Feature: Upsert option on appends in ChunkStore

### 1.68 (2018-08-17)
  * Feature: #553 Compatibility with both the new and old LZ4 API
  * Feature: #571 Removed the Cython LZ4 code, use the latest python-lz4
  * Feature: #557 Threadpool based compression. Speed imrpovement and tuning benchmarks.
  * Bugfix: fix tickstore unicode handling, support both unicode and utf-8 arrays
  * Bugfix: #591 Fix tickstore reads not returning index with localized timezone
  * Feature: #595 add host attribute to VersionedItem.
  * Bugfix: #594 Enable sharding on chunkstore

### 1.67.1 (2018-07-11)
  * Bugfix: #579 Fix symbol corruption due to restore_version and append
  * Bugfix: #584 Fix list_versions for a snapshot after deleting symbols in later versions

### 1.67 (2018-05-24)
  * Bugfix: #561 Fix PickleStore read corruption after write_metadata

### 1.66 (2018-05-21)
  * Bugfix: #168 Do not allow empty string as a column name
  * Bugfix: #483 Remove potential floating point error from datetime_to_ms
  * Bugfix: #271 Log when library doesnt exist on delete
  * Feature: MetaDataStore: added list_symbols with regexp, as_of and metadata fields matching filters
  * Feature: Support for serialization of DataFrames in Pandas 0.23.x

### 1.65 (2018-04-16)
  * Bugfix: #534 VersionStore: overwriting a symbol with different dtype (but same data format) does not
                 raise exceptions anymore
  * Bugfix: #531 arctic_prune_versions: clean broken snapshot references before pruning
  * Bugfix: setup.py develop in a conda environment on Mac
  * Feature: #490 add support to numpy 1.14

### 1.63 (2018-04-06)
  * Bugfix: #521 Clang 6.0 compiler support on macOS
  * Feature: #510 VersionStore: support multi column in pandas DataFrames

### 1.62 (2018-3-14)
  * Bugfix: #517 VersionStore: append does not duplicate data in certain corner cases
  * Bugfix: #519 VersionStore: list_symbols speed improvement and fix for memory limit exceed

### 1.61 (2018-3-2)
  * Feature: #288 Mapping reads and writes over chunks in chunkstore
  * Bugfix: #508 VersionStore: list_symbols and read now always returns latest version
  * Bugfix: #512 Improved performance for list_versions
  * Bugfix: #515 VersionStore: _prune_previous_versions now retries the cleanup operation

### 1.60 (2018-2-13)
  * Bugfix: #503 ChunkStore: speedup check for -1 segments
  * Feature: #504 Increasing number of libraries in Arctic to 5000.

### 1.59 (2018-2-6)
  * Bugfix: Increase performance of invalid segment check in chunkstore
  * Bugfix: #501 Fix the spurious data integrity exceptions at write path, due to moving chunks form the balancer

### 1.58 (2018-1-15)
  * Bugfix: #491 roll back the use of frombuffer to fromstring, fixes the read-only ndarray issue

### 1.57 (2018-1-11)
  * Feature: #206 String support for tickstore
  * Bugfix: #486 improve mongo_retry robustness with failures for version store write/append

### 1.56 (2017-12-21)
  * Bugfix: #468 Re-adding compatibility for pandas 0.20.x
  * Bugfix: #476 Ensure we re-auth when a new MongoClient is created after fork

### 1.55 (2017-12-14)
  * Bugfix:  #439 fix cursor timeouts in chunkstore iterator
  * Bugfix:  #450 fix error in chunkstore delete when chunk range produces empty df
  * Bugfix:  #442 fix incorrect segment values in multi segment chunks in chunkstore
  * Feature: #457 enchances fix for #442 via segment_id_repair tool
  * Bugfix:  #385 exceptions during quota statistics no longer kill a write
  * Feature: PR#161 TickStore.max_date now returns a datetime in the 'local' timezone
  * Feature: #425 user defined metadata for tickstore
  * Feature: #464 performance improvement by avoiding unnecessary re-authentication
  * Bugfix:  #250 Added multiprocessing safety, check for initialized MongoClient after fork.
  * Feature: #465 Added fast operations for write only metadata and restore symbol to a version 

### 1.54 (2017-10-18)
  * Bugfix:  #440 Fix read empty MultiIndex+tz Series

### 1.53 (2017-10-06)
  * Perf:    #408 Improve memory performance of version store's serializer
  * Bugfix   #394 Multi symbol read in chunkstore
  * Bugfix:  #407 Fix segment issue on appends in chunkstore
  * Bugfix:  Inconsistent returns on MetadataStore.append
  * Bugfix:  #412 pandas deprecation and #289 improve exception report in numpy record serializer
  * Bugfix:  #420 chunkstore ignoring open interval date ranges
  * Bugfix:  #427 chunkstore metadata not being correctly replaced during symbol overwrite
  * Bugfix:  #431 chunkstore iterators do not handle multi segment chunks correctly

### 1.51 (2017-08-21)
  * Bugfix:  #397 Remove calls to deprecated methods in pymongo
  * Bugfix:  #402 Append to empty DF fails in VersionStore

### 1.50 (2017-08-18)
  * Feature: #396 MetadataStore.read now supports as_of argument
  * Bugfix:  #397 Pin pymongo==3.4.0

### 1.49 (2017-08-02)
  * Feature: #392 MetadataStore
  * Bugfix:  #384 sentinels missing time data on chunk start/ends in ChunkStore
  * Bugfix:  #382 Remove dependency on cython being pre-installed
  * Bugfix:  #343 Renaming libraries/collections within a namespace/database
  
### 1.48 (2017-06-26)
  * BugFix: Rollback #363, as it breaks multi-index dataframe
  * Bugfix:  #372 OSX build improvements

### 1.47 (2017-06-19)
  * Feature: Re-introduce #363 `concat` flag, essentially undo-ing 1.45
  * BugFix: #377 Fix broken `replace_one` on BSONStore and add `bulk_write`

### 1.46 (2017-06-13)
  * Feature: #374 Shard BSONStore on `_id` rather than `symbol`

### 1.45 (2017-06-09)
  * BugFix: Rollback #363, which can cause ordering issues on append

### 1.44 (2017-06-08)
  * Feature: #364 Expose compressHC from internal arctic LZ4 and remove external LZ4 dependency
  * Feature: #363 Appending older data (compare to what's exist in library) will raise. Use `concat=True` to append only the
             new bits
  * Feature: #371 Expose more functionality in BSONStore
  
### 1.43 (2017-05-30)
  * Bugfix:  #350 remove deprecated pandas calls
  * Bugfix:  #360 version incorrect in empty append in VersionStore
  * Feature: #365 add generic BSON store

### 1.42 (2017-05-12)
  * Bugfix: #346 fixed daterange subsetting error on very large dateframes in version store
  * Bugfix: #351 $size queries can't use indexes, use alternative queries

### 1.41 (2017-04-20)
  * Bugfix: #334 Chunk range param with pandas object fails in chunkstore.get_chunk_ranges
  * Bugfix: #339 Depending on lz4<=0.8.2 to fix build errors
  * Bugfix: #342 fixed compilation errors on Mac OSX
  * Bugfix: #344 fixed data corruption problem with concurrent appends

### 1.40 (2017-03-03)
  * BugFix: #330 Make Arctic._lock reentrant 

### 1.39 (2017-03-03)
  * Feature:  #329 Add reset() method to Arctic 

### 1.38 (2017-02-22)
  * Bugfix:  #324 Datetime indexes must be sorted in chunkstore
  * Feature: #290 improve performance of tickstore column reads

### 1.37 (2017-1-31)
  * Bugfix:  #300 to_datetime deprecated in pandas, use to_pydatetime instead
  * Bugfix:  #309 formatting change for DateRange ```__str__```
  * Feature: #313 set and read user specified metadata in chunkstore
  * Feature: #319 Audit log support in ChunkStor
  * Bugfix:  #216 Tickstore write fails with named index column


### 1.36 (2016-12-13)
  
  * Feature: Default to hashed based sharding
  * Bugfix: retry socket errors during VersionStore snapshot operations

### 1.35 (2016-11-29)

  * Bugfix:  #296 Cannot compress/decompress empty string

### 1.34 (2016-11-29)

  * Feature: #294 Move per-chunk metadata for chunkstore to a separate collection
  * Bugfix:  #292 Account for metadata size during size chunking in ChunkStore
  * Feature: #283 Support for all pandas frequency strings in ChunkStore DateChunker
  * Feature: #286 Add has_symbol to ChunkStore and support for partial symbol matching in list_symbols

### 1.33 (2016-11-07)
  
  * Feature:    #275 Tuple range object support in DateChunker
  * Bugfix:     #273 Duplicate columns breaking serializer
  * Feature:    #267 Tickstore.delete returns deleted data
  * Dependency: #266 Remove pytest-dbfixtures in favor of pytest-server-fixtures

### 1.32 (2016-10-25)
  
  * Feature: #260 quota support on Chunkstore
  * Bugfix: #259 prevent write of unnamed columns/indexes
  * Bugfix: #252 pandas 0.19.0 compatibility fixes
  * Bugfix: #249 open ended range reads on data without index fail
  * Bugfix: #262 VersionStore.append must check data is written correctly during repack
  * Bugfix: #263 Quota: Improve the error message when near soft-quota limit
  * Perf:   #265 VersionStore.write / append don't aggressively add indexes on each write
  
### 1.31 (2016-09-29)
  
  * Bugfix: #247 segmentation read fix in chunkstore
  * Feature: #243 add get_library_type method
  * Bugfix: more cython changes to handle LZ4 errors properly
  * Feature: #239 improve chunkstore's get_info method

### 1.30 (2016-09-26)

  * Feature: #235 method to return chunk ranges on a symbol in ChunkStore
  * Feature: #234 Iterator access to ChunkStore
  * Bugfix: #236 Cython not handling errors from LZ4 function calls
  
### 1.29 (2016-09-20)

  * Bugfix: #228 Mongo fail-over during append can leave a Version in an inconsistent state
  * Feature: #193 Support for different Chunkers and Serializers by symbol in ChunkStore
  * Feature: #220 Raise exception if older version of arctic attempts to read unsupported pickled data
  * Feature: #219 and #220 Support for pickling large data (>2GB)
  * Feature: #204 Add support for library renaming
  * Feature: #209 Upsert capability in ChunkStore's update method
  * Feature: #207 Support DatetimeIndexes in DateRange chunker
  * Bugfix:  #232 Don't raise during VersionStore #append(...) if the previous append failed

### 1.28 (2016-08-16)

  * Bugfix: #195 Top level tickstore write with list of dicts now works with timezone aware datetimes

### 1.27 (2016-08-05)

  * Bugfix: #187 Compatibility with latest version of pytest-dbfixtures
  * Feature: #182 Improve ChunkStore read/write performance
  * Feature: #162 Rename API for ChunkStore
  * Feature: #186 chunk_range on update
  * Bugfix: #189 range delete does not update symbol metadata

### 1.26 (2016-07-20)

  * Bugfix: Faster TickStore querying for multiple symbols simultaneously
  * Bugfix: TickStore.read now respects `allow_secondary=True`
  * Bugfix: #147 Add get_info method to ChunkStore
  * Bugfix: Periodically re-cache the library.quota to pick up any changes
  * Bugfix: #166 Add index on SHA for ChunkStore
  * Bugfix: #169 Dtype mismatch in chunkstore updates
  * Feature: #171 allow deleting of values within a date range in ChunkStore
  * Bugfix: #172 Fix date range bug when querying dates in the middle of chunks
  * Bugfix: #176 Fix overwrite failures in Chunkstore
  * Bugfix: #178 - Change how start/end dates are populated in the DB, also fix append so it works as expected.
  * Bugfix: #43 - Remove dependency on hardcoded Linux timezone files

### 1.25 (2016-05-23)

  * Bugfix: Ensure that Tickstore.write doesn't allow out of order messages
  * Bugfix: VersionStore.write now allows writing 'None' as a value

### 1.24 (2016-05-10)
  
  * Bugfix: Backwards compatibility reading/writing documents with previous versions of Arctic

### 1.22 (2016-05-09)
  
  * Bugfix: #109 Ensure stable sort during Arctic read
  * Feature: New benchmark suite using ASV
  * Bugfix: #129 Fixed an issue where some chunks could get skipped during a multiple-symbol TickStore read
  * Bugfix: #135 Fix issue with different datatype returned from pymongo in python3
  * Feature: #130 New Chunkstore storage type

### 1.21 (2016-03-08)

  * Bugfix: #106 Fix Pandas Panel storage for panels with different dimensions

### 1.20 (2016-02-03)

  * Feature: #98 Add initial_image as optional parameter on tickstore write()
  * Bugfix: #100 Write error on end field when writing with pandas dataframes

### 1.19 (2016-01-29)

  * Feature: Add python 3.3/3.4 support
  * Bugfix: #95 Fix raising NoDataFoundException across multiple low level libraries

### 1.18 (2016-01-05)

  * Bugfix: #81 Fix broken read of multi-index DataFrame written by old version of Arctic
  * Bugfix: #49 Fix strifying tickstore

### 1.17 (2015-12-24)

  * Feature: Add timezone suppport to store multi-index dataframes
  * Bugfix:  Fixed broken sdist releases

### 1.16 (2015-12-15)

  * Feature: ArticTransaction now supports non-audited 'transactions': `audit=False`

```
with ArcticTransaction(Arctic('hostname')['some_library'], 'symbol', audit=False) as at:
...
```

     This is useful for batch jobs which read-modify-write and don't want to clash with
     concurrent writers, and which don't require keeping all versions of a symbol.

### 1.15 (2015-11-25)

  * Feature: get_info API added to version_store.

### 1.14 (2015-11-25)
### 1.12 (2015-11-12)

  * Bugfix: correct version detection for Pandas >= 0.18.
  * Bugfix: retrying connection initialisation in case of an AutoReconnect failure.

### 1.11 (2015-10-29)

  * Bugfix: Improve performance of saving multi-index Pandas DataFrames
    by 9x
  * Bugfix: authenticate should propagate non-OperationFailure exceptions
    (e.g. ConnectionFailure) as this might be indicative of socket failures
  * Bugfix: return 'deleted' state in VersionStore.list_versions() so that
    callers can pick up on the head version being the delete-sentinel.

### 1.10 (2015-10-28)

  * Bugfix: VersionStore.read(date_range=...) could do the wrong thing with
    TimeZones (which aren't yet supported for date_range slicing.).

### 1.9 (2015-10-06)

  * Bugfix: fix authentication race condition when sharing an Arctic
    instance between multiple threads.

### 1.8 (2015-09-29)

  * Bugfix: compatibility with both 3.0 and pre-3.0 MongoDB for
    querying current authentications

### 1.7 (2015-09-18)

  * Feature: Add support for reading a subset of a pandas DataFrame
    in VersionStore.read by passing in an arctic.date.DateRange
  * Bugfix: Reauth against admin if not auth'd against a library a
    specific library's DB.  Sometimes we appear to miss admin DB auths.
    This is to workaround that until we work out what the issue is.

### 1.6 (2015-09-16)

  * Feature: Add support for multi-index Bitemporal DataFrame storage.
    This allows persisting data and changes within the DataFrame making it
    easier to see how old data has been revised over time.
  * Bugfix: Ensure we call the error logging hook when exceptions occur

### 1.5 (2015-09-02)

  * Always use the primary cluster node for 'has_symbol()', it's safer

### 1.4 (2015-08-19)

  * Bugfixes for timezone handling, now ensures use of non-naive datetimes
  * Bugfix for tickstore read missing images

### 1.3 (2015-08-011)

  * Improvements to command-line control scripts for users and libraries
  * Bugfix for pickling top-level Arctic object

### 1.2 (2015-06-29)

  * Allow snapshotting a range of versions in the VersionStore, and
    snapshot all versions by default.

### 1.1 (2015-06-16)

  * Bugfix for backwards-compatible unpickling of bson-encoded data
  * Added switch for enabling parallel lz4 compression

### 1.0 (2015-06-14)

  *  Initial public release

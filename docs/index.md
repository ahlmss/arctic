!!! important "Important"
    ## ArcticDB

    [ArcticDB](https://arcticdb.io/#arctic1) is a ground-up rewrite of Arctic.<br>
    The old Arctic, described below, is in maintenance mode.<br>
    ArcticDB uses a very similar api to Arctic and is much faster.
    
    Take a look:<br>
    [Website](https://arcticdb.io/#arctic1), [Docs](https://docs.arcticdb.io/latest/#arctic1), [GitHub](https://github.com/man-group/arcticdb)

# Arctic Introduction

## Arctic

Arctic is a timeseries / dataframe database that sits atop MongoDB. Arctic supports serialization of a number of datatypes for storage in the mongo document model.

## Why use Arctic? 

Some of the reasons to use Arctic are:-

* Serializes a number of data types eg. Pandas DataFrames, Numpy arrays, Python objects via pickling etc. so you don't have to handle different datatypes manually. 
* Uses LZ4 compression by default on the client side to get big savings on network / disk.  
* Allows you to version different stages of an object and snapshot the state (In some ways similar to git), and allows you to freely experiment and then just revert back the snapshot. [VersionStore only] 
* Does the chunking (breaking a Dataframe to smaller parts) for you. 
* Adds a concept of Users and per User Libraries which can build on Mongo's auth. 
* Has different types of Stores, each with its own benefits. Eg. Versionstore allows you to version and snapshot stuff, TickStore is for storage and highly efficient retrieval of streaming data, ChunkStore allows you to chunk and efficiently retrieve ranges of chunks. If nothing suits you, feel free to use vanilla Mongo commands with BSONStore.
* Restricts data access to Mongo and thus prevents ad hoc queries on unindexed / unsharded collections

Head over to the FAQs and James's presentation given below for more details. 

## Basic Operations

Arctic provides a [wrapper](../arctic/arctic.py) for handling connections to Mongo. The `Arctic` class is what actually connects to Arctic.

```
>>> conn = Arctic('127.0.0.1')
```

There are a number of operations that are possible with just this connection handle. The most basic ones are `list_libraries` and `initiailize_library`.

Arctic divides data into different libraries. These could be different users, different markets, different geographic regions, etc. Library names are strings and are entirely user defined.

```
>>> conn.list_libraries()
    []
```

In this case, there are no libraries on the system, so one can be initialized.

```
>>> conn.initialize_library('library_name')
>>> conn.list_libraries()
    [u'library_name']
```

`initialize_library` has an optional named arg, `lib_type` that defaults to `VersionStore` (more on Arctic storage engine types later).

Once a library is initialized, you can access it like so:

```
>>> lib = conn['library_name']
```

With this handle to the library, we can begin to store and retrieve data from Arctic.

(note, most of the storage engines support the same basic methods (`read`, `write`, etc), but each have their own set of unique methods as well)

`write` in its most basic form takes an Arctic `symbol` and the data. The `symbol` is a user defined key that is used to store/retrieve the data. The `data` in most cases is a Pandas DataFrame, though some storage engines support other types (all support dataframes, and some support dicts and pickleable objects).

`read` as you might expect takes the `symbol` to read back the data. The different storage engines have different parameters that allow you to subset the data (more on this later).

```
>>> data = pd.DataFrame(.....)
>>> lib.write('symbolname', data)
>>> df = lib.read('symbolname')
>>> df
                data
date
2016-01-01       1
2016-01-02       2
2016-01-03       3
```


Other basic methods:

* `library.list_symbols()`
    - Does what you might expect - lists all the symbols in the given library
```['US_EQUITIES', 'EUR_EQUITIES', ...]```
* `arctic.get_quota(library_name)`, `arctic.set_quota(library_name, quota_in_bytes)`
   - Arctic internally sets quotas on libraries so they do not consume too much space.    You can check and set quotas with these two methods. Note these operate on the       `Arctic` object, not on libraries


## Arctic Storage Engines

Arctic is designed to be very extensible and currently supports a numer of different use cases. To understand what Arctic is capable of, one must understand the storage models it uses. Arctic currently supports three storage engines

* [TickStore](tickstore.md)
* [VersionStore](versionstore.md)
* [Chunkstore](chunkstore.md)

Each one has various features and is designed to support specific and general use cases.


## Arctic configuration settings

There is a large number of configuration knobs which tune Arctic's performance, and enable/disable various (experimental) features.

For more details refer to the [Arctic configuration guide](configuration.md).

## Presentations

### Video

- [2015 All Your Base : Building a time series database: 10^12 rows and counting](https://vimeo.com/album/3660528/video/145842301)
- [2014 PyData : Python and MongoDB as a Platform for Financial Market Data](https://www.youtube.com/watch?v=FVyIxdxsyok)
- [2014 MongoDB World : Replacing Traditional Technologies with MongoDB: A Single Platform for All Financial Data at AHL](https://www.mongodb.com/presentations/replacing-traditional-technologies-mongodb-single-platform-all-financial-data-ahl)

### Slides

- [2015 All Your Base : Building a time series database: 10^12 rows and counting](http://www.slideshare.net/JamesBlackburn1/building-a-time-series-database?ref=http://lanyrd.com/2015/all-your-base/sdrydc/)
- [2015 PyData : Arctic: High-performance IoT and financial data storage with Python and MongoDB](http://www.slideshare.net/JamesBlackburn1/2015-pydata-highperformance-iot-and-financial-data-storage-with-python-and-mongodb)
- [2014 PyData : Python and MongoDB as a Platform for Financial Market Data](http://www.slideshare.net/JamesBlackburn1/mongodb-and-python-as-a-market-data-platform)
- [2014 MongoDB World : Replacing Traditional Technologies with MongoDB: A Single Platform for All Financial Data at AHL](http://www.slideshare.net/mongodb/replacing-traditional-technologies-with-mongodb-a-single-platform-for-all-financial-data-at-ahl?ref=https://www.mongodb.com/presentations/replacing-traditional-technologies-mongodb-single-platform-all-financial-data-ahl)

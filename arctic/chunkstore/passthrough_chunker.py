from pandas import DataFrame, Series

from ._chunker import Chunker, START, END


class PassthroughChunker(Chunker):
    TYPE = 'passthru'

    def to_chunks(self, df, chunk_size):
        """
        pass thru chunker of the dataframe/series

        returns
        -------
        ("NA", "NA", dataframe/series)
        """
        if len(df) > 0:
            yield "NA", "NA", df

    def to_range(self, start, end):
        """
        returns a RangeObject from start/end sentinels.

        returns
        -------
        string
        """
        return "NA"

    def chunk_to_str(self, chunk_id):
        """
        Converts parts of a chunk range (start or end) to a string

        returns
        -------
        string
        """
        return "NA"

    def to_mongo(self, range_obj):
        """
        returns mongo query against range object.
        since range object is not valid, returns empty dict

        returns
        -------
        string
        """
        return {'$and': [{START: "NA"}, {END: "NA"}]}

    def filter(self, data, range_obj):
        """
        ensures data is properly subset to the range in range_obj.
        since range object is not valid, returns data

        returns
        -------
        data
        """
        return data

    def exclude(self, data, range_obj):
        """
        Removes data within the bounds of the range object.
        Since range object is not valid for this chunk type,
        returns nothing

        returns
        -------
        empty dataframe or series
        """
        if isinstance(data, DataFrame):
            return DataFrame()
        else:
            return Series()

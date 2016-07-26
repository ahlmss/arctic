import logging
import numpy as np
import numpy.ma as ma
import pandas as pd

from bson import Binary, SON

from .._compress import compress, decompress


class NumpyArrayConverter(object):
    """
    Converts a Numpy ndarray to and from PyMongo SON representation:

        {
         type:        '<i8',          # Numpy dtype (str)
         length:      20,             # Numpy array length
         values:      '\x00\x00bb...' # Compressed bytes
        }
    """

    def docify(self, arr, meta=None):
        """
        Convert a Numpy ndarray to SON.

        Parameters
        ----------
        arr:  ndarray
            The numpy array to encode
        meta: dict
            Optional additional key value pairs to include in the SON
        """
        arr, mask = self._convert_types(arr)
        son = SON(meta,
                  type=arr.dtype.str,
                  length=len(arr),
                  values=Binary(compress(arr.tostring())))
        if mask is not None:
            son['mask'] = Binary(compress(mask.tostring()))
        return son

    def objify(self, doc):
        """
        Decode a Pymongo SON object into an Numpy ndarray
        """
        arr_data = decompress(doc['values'])
        arr = np.fromstring(arr_data, doc['type'])

        if 'mask' in doc:
            mask_data = decompress(doc['mask'])
            mask = np.fromstring(mask_data, 'bool')
            arr = ma.masked_array(arr, mask)

        return arr

    def _convert_types(self, a):
        """
        Converts object arrays of strings to numpy string arrays
        """
        # No conversion for scalar type
        if a.dtype != 'object':
            return a, None

        # We can't infer the type of an empty array, so just
        # assume strings
        if len(a) == 0:
            return a.astype('U1'), None

        # Compute a mask of missing values. Replace NaNs and Nones with
        # empty strings so that type inference has a chance.
        mask = pd.isnull(a)
        if mask.sum() > 0:
            a = a.copy()
            np.putmask(a, mask, '')
        else:
            mask = None

        if pd.lib.infer_dtype(a) == 'mixed':
            a = np.array([s.encode('ascii') for s in a])
            a = a.astype('O')

        type_ = pd.lib.infer_dtype(a)
        if type_ in ['unicode', 'string']:
            max_len = pd.lib.max_len_string_array(a)
            return a.astype('U{:d}'.format(max_len)), mask
        else:
            raise ValueError('Cannot store arrays with {} dtype'.format(type_))


class FrameConverter(object):
    """
    Converts a Pandas Dataframe to and from PyMongo SON representation:

        {
         columns: [col1, col2, col3],
         data: {
          col1: { <numpy array representation>,
          col2: { <numpy array representation>,
          col3: { <numpy array representation>,
         }
        }
    """

    def __init__(self):
        self.converter = NumpyArrayConverter()

    def docify(self, df):
        """
        Convert a Pandas DataFrame to SON.

        Parameters
        ----------
        df:  DataFrame
            The Pandas DataFrame to encode
        """
        doc = SON({'data': {}}, columns=[str(c) for c in df.columns])
        for c in df:
            meta = {'name': str(c)}
            try:
                doc['data'][str(c)] = self.converter.docify(df[c].values, meta)
            except Exception as e:
                typ = pd.lib.infer_dtype(df[c])
                msg = "Column '{}' type is {}".format(str(c), typ)
                logging.info(msg)
                raise e
        return doc

    def objify(self, doc, columns=None):
        """
        Decode a Pymongo SON object into an Pandas DataFrame
        """
        cols = columns or doc['columns']
        data = {c: self.converter.objify(doc['data'][c]) for c in cols}
        return pd.DataFrame(data, columns=cols)[cols]


class NumpyString(object):
    def __init__(self):
        self.converter = FrameConverter()

    def serialize(self, df):
        if isinstance(df, pd.Series):
            dtype = 'series'
            df = df.to_frame()
        else:
            dtype = 'dataframe'

        if df.index.names != [None]:
            index = df.index.names
            df = df.reset_index()
            ret = self.converter.docify(df)
            ret['index'] = index
            ret['type'] = dtype
            return ret
        ret = self.converter.docify(df)
        ret['type'] = dtype
        return ret

    def deserialize(self, data, columns=None):
        if data == []:
            return pd.DataFrame()

        if isinstance(data, list):
            if columns and 'index' in data[0]:
                columns.extend(data[0]['index'])
                df = pd.concat([self.converter.objify(d, columns) for d in data])
            else:
                df = pd.concat([self.converter.objify(d, columns) for d in data], ignore_index=True)
            dtype = data[0]['type']
            if 'index' in data[0]:
                df = df.set_index(data[0]['index'])
        else:
            df = self.converter.objify(data, columns)
            dtype = data['type']
            if 'index' in data:
                df = df.set_index(data['index'])
        if dtype == 'series':
            return df[df.columns[0]]
        return df

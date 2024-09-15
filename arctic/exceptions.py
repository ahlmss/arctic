class ArcticException(Exception):
    pass


class NoDataFoundException(ArcticException):
    pass


class UnhandledDtypeException(ArcticException):
    pass


class LibraryNotFoundException(ArcticException):
    pass


class DuplicateSnapshotException(ArcticException):
    pass


class StoreNotInitializedException(ArcticException):
    pass


class OptimisticLockException(ArcticException):
    pass


class QuotaExceededException(ArcticException):
    pass


class UnsupportedPickleStoreVersion(ArcticException):
    pass


class DataIntegrityException(ArcticException):
    """
    Base class for data integrity issues.
    """
    pass


class ArcticSerializationException(ArcticException):
    pass


class ConcurrentModificationException(DataIntegrityException):
    pass


class UnorderedDataException(DataIntegrityException):
    pass


class OverlappingDataException(DataIntegrityException):
    pass


class AsyncArcticException(ArcticException):
    pass


class RequestDurationException(AsyncArcticException):
    pass


class ChunkStoreOutstandingTransaction(ArcticException):
    pass

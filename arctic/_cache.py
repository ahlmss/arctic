import logging
from datetime import datetime, timedelta

from pymongo.errors import OperationFailure

logger = logging.getLogger(__name__)

CACHE_COLL = 'cache'
CACHE_DB = 'meta_db'
CACHE_SETTINGS = 'settings'
CACHE_SETTINGS_KEY = 'cache'
"""
Sample settings collection entry:
meta_db.settings.insertOne({"type": "cache", "enabled": true, "cache_expiry": 600})
meta_db.settings.find(): { "_id" : ObjectId("5cd5388b9fddfbe6e968f11b"), "type": "cache", "enabled" : false, "cache_expiry" : 600 }
"""
DEFAULT_CACHE_EXPIRY = 3600


class Cache:
    def __init__(self, client, cache_expiry=DEFAULT_CACHE_EXPIRY, cache_db=CACHE_DB, cache_col=CACHE_COLL):
        self._client = client
        self._cachedb = client[cache_db]
        self._cachecol = None
        try:
            if cache_col not in self._cachedb.list_collection_names():
                self._cachedb.create_collection(cache_col).create_index("date", expireAfterSeconds=cache_expiry)
        except OperationFailure as op:
            logging.debug("This is fine if you are not admin. The collection should already be created for you: %s", op)

        self._cachecol = self._cachedb[cache_col]

    def _get_cache_settings(self):
        try:
            return self._cachedb[CACHE_SETTINGS].find_one({'type': CACHE_SETTINGS_KEY})
        except OperationFailure as op:
            logging.debug("Cannot access %s in db: %s. Error: %s" % (CACHE_SETTINGS, CACHE_DB, op))
        return None

    def set_caching_state(self, enabled):
        """
        Used to enable or disable the caching globally
        :return:
        """
        if not isinstance(enabled, bool):
            logging.error("Enabled should be a boolean type.")
            return

        if (CACHE_SETTINGS not in self._cachedb.list_collection_names()) or self._cachedb[CACHE_SETTINGS].count() == 0:
            logging.info("Creating %s collection for cache settings" % CACHE_SETTINGS)
            self._cachedb[CACHE_SETTINGS].insert_one({
                'type': CACHE_SETTINGS_KEY,
                'enabled': enabled,
                'cache_expiry': DEFAULT_CACHE_EXPIRY
            })
        else:
            self._cachedb[CACHE_SETTINGS].update_one({'type': CACHE_SETTINGS_KEY}, {'$set': {'enabled': enabled}})
            logging.info("Caching set to: %s" % enabled)

    def _is_not_expired(self, cached_data, newer_than_secs):
        # Use the expiry period in the settings (or the default) if not overriden by the function argument.
        if newer_than_secs:
            expiry_period = newer_than_secs
        else:
            cache_settings = self._get_cache_settings()
            expiry_period = cache_settings['cache_expiry'] if cache_settings else DEFAULT_CACHE_EXPIRY

        return datetime.utcnow() < cached_data['date'] + timedelta(seconds=expiry_period)

    def get(self, key, newer_than_secs=None):
        """

        :param key: Key for the dataset. eg. list_libraries.
        :param newer_than_secs: None to indicate use cache if available. Used to indicate what level of staleness
        in seconds is tolerable.
        :return: None unless if there is non stale data present in the cache.
        """
        try:
            if not self._cachecol:
                # Collection not created or no permissions to read from it.
                return None
            cached_data = self._cachecol.find_one({"type": key})
            # Check that there is data in cache and it's not stale.
            if cached_data and self._is_not_expired(cached_data, newer_than_secs):
                return cached_data['data']
        except OperationFailure as op:
            # Fallback to uncached version without spamming.
            logging.debug("Could not read from cache due to: %s. Ask your admin to give read permissions on %s:%s",
                          op, CACHE_DB, CACHE_COLL)

        return None

    def set(self, key, data):
        try:
            self._cachecol.update_one(
                {"type": key},
                {"$set": {"type": key, "date": datetime.utcnow(), "data": data}},
                upsert=True
            )
        except OperationFailure as op:
            logging.debug("This operation is to be run with admin permissions. Should be fine: %s", op)

    def append(self, key, append_data):
        try:
            self._cachecol.update_one(
                {'type': key},
                {
                    # Add to set will not add the same library again to the list unlike set.
                    '$addToSet': {'data': append_data},
                    '$setOnInsert': {'type': key, 'date': datetime.utcnow()}
                },
                upsert=True
            )
        except OperationFailure as op:
            logging.debug("Admin is required to append to the cache: %s", op)

    def delete_item_from_key(self, key, item):
        try:
            self._cachecol.update(
                {'type': key},
                {"$pull": {"data": item}}
            )
        except OperationFailure as op:
            logging.debug("Admin is required to remove from cache: %s", op)

    def update_item_for_key(self, key, old, new):
        # This op is not atomic, but given the rarity of renaming a lib, it should not cause issues.
        self.delete_item_from_key(key, old)
        self.append(key, new)

    def is_caching_enabled(self, cache_enabled_in_env):
        cache_settings = self._get_cache_settings()
        # Explicitly setting the setting takes precedence over env.
        if cache_settings:
            return cache_settings['enabled']
        return cache_enabled_in_env

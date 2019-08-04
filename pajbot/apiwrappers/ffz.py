from pajbot.apiwrappers.base import BaseApi
from pajbot.apiwrappers.response_cache import ClassInstanceListSerializer
from pajbot.models.emote import Emote


class FFZApi(BaseApi):
    def __init__(self, redis):
        super().__init__(base_url="https://api.frankerfacez.com/v1/", redis=redis)

    @staticmethod
    def parse_sets(emote_sets):
        emotes = []
        for emote_set in emote_sets.values():
            for emote in emote_set["emoticons"]:
                # FFZ returns relative URLs (e.g. //cdn.frankerfacez.com/...)
                # so we fill in the scheme if it's missing :)
                urls = {size: FFZApi.fill_in_url_scheme(url) for size, url in emote["urls"].items()}
                emotes.append(Emote(code=emote["name"], provider="ffz", id=emote["id"], urls=urls))

        return emotes

    def fetch_global_emotes(self):
        """Returns a list of global FFZ emotes in the standard Emote format."""
        response = self.get("/set/global")

        # FFZ returns a number of global sets but only a subset of them should be available
        # in all channels, those are available under "default_sets", e.g. a list of set IDs like this:
        # [ 3, 6, 7, 14342 ]
        global_set_ids = response["default_sets"]
        global_sets = {str(set_id): response["sets"][str(set_id)] for set_id in global_set_ids}

        return self.parse_sets(global_sets)

    def get_global_emotes(self, force_fetch=None):
        return self.cache.cache_fetch_fn(
            redis_key="api:ffz:global-emotes",
            fetch_fn=lambda: self.fetch_global_emotes(),
            serializer=ClassInstanceListSerializer(Emote),
            expiry=60 * 60,
            force_fetch=force_fetch,
        )

    def fetch_channel_emotes(self, channel_name):
        """Returns a list of channel-specific FFZ emotes in the standard Emote format."""
        response = self.get(["room", channel_name])
        return self.parse_sets(response["sets"])

    def get_channel_emotes(self, channel_name, force_fetch=None):
        return self.cache.cache_fetch_fn(
            redis_key="api:ffz:channel-emotes:{}".format(channel_name),
            fetch_fn=lambda: self.fetch_channel_emotes(channel_name),
            serializer=ClassInstanceListSerializer(Emote),
            expiry=60 * 60,
            force_fetch=force_fetch,
        )

from libtrustbridge.repos.miniorepo import MinioRepo


class ChannelRepo(MinioRepo):
    DEFAULT_BUCKET = 'channel'

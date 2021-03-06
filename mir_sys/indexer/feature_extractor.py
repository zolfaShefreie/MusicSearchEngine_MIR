import os

from mir_sys.elasticsearch.queries import Queries
from mir_sys.utils.audio_downloader import Downloader, DOWNLOAD_PATH
from mir_sys.utils.generate_fingerprint import FingerprintGenerator


class FeatureExtractor:
    queries = Queries()
    LIMIT = 20
    MAX_TRY_SONG = 5

    @classmethod
    def get_ids(cls) -> list:
        """
        check for songs that should download
        :return: a list of ids and seen status
        """
        ids = cls.queries.get_unseen_songs(cls.LIMIT)
        if not ids:
            return cls.queries.get_no_feature_songs(cls.LIMIT, cls.MAX_TRY_SONG)
        return ids

    @classmethod
    def save_fingerprint(cls, song_id: str, fingerprints: list):
        """
        :param fingerprints:
        :param song_id:
        :return:
        """
        complete_fingerprints = "".join(fingerprints)
        unique_fingerprints = set(fingerprints)
        cls.queries.update_obj(obj_id=song_id, index_name="songs",
                               obj={'fingerprint': complete_fingerprints})
        cls.queries.update_song_list(list(unique_fingerprints), song_id)

    @classmethod
    def run(cls) -> int:
        """
        :return: length of elements that function work on them
        """
        ids = cls.get_ids()
        cls.queries.increase_effort_song(ids)
        Downloader.download_manager(ids)
        for song_id in ids:
            path = f"{DOWNLOAD_PATH}{song_id}.wav"
            if os.path.exists(path):
                cls.save_fingerprint(song_id, FingerprintGenerator.generate_fingerprint(dir_or_samples=path))
        return len(ids)

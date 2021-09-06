from collections import Counter
import itertools

from mir_sys.utils.generate_fingerprint import FingerprintGenerator
from mir_sys.utils.custom_base64 import NumBase64
from mir_sys.utils.util_classes import FingerprintSim, hamming_distance
from mir_sys.elasticsearch.queries import Queries

MAX_BIT = 24


class Retriever:

    MAX_NUM_BLOCK = 5

    def __init__(self):
        self.fingerprints = None
        self.query_hash_table = dict()

    def get_fingerprint(self, sample_or_dir):
        self.fingerprints = FingerprintGenerator.generate_fingerprint(sample_or_dir)

    @classmethod
    def get_fingerprint_songs(cls, fingerprint: str, rel_fingerprints: list) -> list:
        """
        :param fingerprint:
        :param rel_fingerprints:
        :return: return a list of songs
        """
        fingerprints_query = rel_fingerprints + [fingerprint]
        results = Queries.search_ids(fingerprints_query, "fingerprints")
        songs = set()
        for each in results:
            songs.update(set(each['songs']))
        return list(songs)

    def fill_hash_table(self):
        """
        create hast table for query
        """
        fingerprint_set = set(self.fingerprints)
        for fingerprint in fingerprint_set:
            rel_fingerprints = FingerprintSim.create_rel_fingerprints(fingerprint)
            songs = self.get_fingerprint_songs(fingerprint, rel_fingerprints)
            self.query_hash_table[fingerprint] = {"rels": rel_fingerprints, "songs": songs}

    def make_block_search(self) -> list:
        """
        set score for songs based on repeat in fingerprint list and then block them
        :return: block list
        """
        songs = [song for fingerprint in self.fingerprints
                 for song in self.query_hash_table[fingerprint]['songs']]
        song_score = dict(Counter(songs))

        # initial block list
        blocks = [list() for i in range(self.MAX_NUM_BLOCK)]

        for song in song_score:
            score = song_score[song]/len(self.fingerprints)
            for i in range(1, self.MAX_NUM_BLOCK+1):
                if score < ((1/self.MAX_NUM_BLOCK) * i):
                    blocks[i].append(song)

        return blocks

    def make_regex_dict(self) -> dict:
        """
        :return:
        """
        fingerprint_regex = dict()
        for fingerprint in self.query_hash_table:
            regex = r"".join([each + "|" for each in self.query_hash_table[fingerprint]]).rstrip("|")
            fingerprint_regex[fingerprint] = r"({}|{})".format(fingerprint, regex)
        return fingerprint_regex

    # def make_positions_fingerprint(self) -> dict:
    #     """
    #     work with positions to make dict for make range fingerprint before and after
    #     :return:
    #     """
    #     positions = dict()
    #     length = len(self.fingerprints)
    #     reversed_fingerprints = list(reversed(self.fingerprints))
    #     for each in set(self.fingerprints):
    #         first_index, last_index = self.fingerprints.index(each), length - reversed_fingerprints.index(each) -1
    #         if first_index == last_index:
    #             positions[each] = (first_index, length-(first_index+1))
    #         else:
    #             positions[each] = (first_index, last_index, length-(first_index+1), length-(last_index+1))
    #     return positions

    def make_positions_fingerprint(self) -> list:
        """
        work with positions to make dict for make range fingerprint before and after
        :return:
        """
        positions = list()
        length = len(self.fingerprints)
        for i in range(length):
            positions.append((i, length-i-1))
        return positions

    def mack_regex(self) -> str:
        """
        :return: regex
        """
        fingerprint_regex_dict = self.make_regex_dict()
        range_list = self.make_positions_fingerprint()

        regex = r"(?=((.{4})*("
        for i in range(len(self.fingerprints)):
            regex += r"(.{}){}{}(.{}){}|".format(str({4}), str({range_list[i][0]}),
                                                 fingerprint_regex_dict[self.fingerprints[i]],
                                                 str({4}), str({range_list[i][1]}))
        regex.rstrip("|")
        regex += r")(.{4})*))"
        return regex

    @classmethod
    def find_matches_in_song(cls, song_fingerprint: str, regex: str) -> list:
        pass

    def search_in_songs(self, songs: list):
        pass

    @staticmethod
    def hamming_distance(match_fingerprint: str, query_fingerprint: str):
        """
        :param match_fingerprint:
        :param query_fingerprint:
        :return: return hamming distance of two fingerprint
        """
        match_binary = NumBase64.decode_to_binary(match_fingerprint)
        query_binary = NumBase64.decode_to_binary(query_fingerprint)
        xor = bin(int(match_binary, 2) ^ int(query_binary, 2)).lstrip("0b")
        distance = 0
        for each in xor:
            if each == "1":
                distance += 1
        return distance/len(query_binary)

    def retrieve(self, sample_or_dir):
        pass



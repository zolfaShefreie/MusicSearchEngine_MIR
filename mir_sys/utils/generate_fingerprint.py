from keras.models import model_from_json
from keras import backend as K
from keras.layers import Activation
from keras.utils.generic_utils import get_custom_objects
from django.conf import settings
import librosa
import os
import numpy as np


MUSICBRAINZ_CONF = getattr(settings, 'MUSIC_BRAINS', {})


def binary_activation(x):
    return K.cast(K.greater(x, 0), K.floatx())


get_custom_objects().update({'binary_activation': Activation(binary_activation)})


class FingerprintGenerator:
    SAMPLE_RATE = 16000
    HOP_LENGTH = int(SAMPLE_RATE * 0.1)
    N_FFT = int(SAMPLE_RATE * 0.2)
    DIFF = 1
    ALLOW_DURATION = 10000
    SPECIAL_VALUE = -10
    FRAME_SEC_INDEXES = [librosa.time_to_frames(i, SAMPLE_RATE, n_fft=N_FFT, hop_length=HOP_LENGTH)
                         for i in range(1, ALLOW_DURATION, DIFF)]

    MAX_FRAME_NUM = max([FRAME_SEC_INDEXES[i + 1] - FRAME_SEC_INDEXES[i] for i in range(len(FRAME_SEC_INDEXES) - 1)])

    # load model
    json_file = open('./drive/MyDrive/fingerprint_model/encoder_model.json', 'r')
    loaded_model_json = json_file.read()
    json_file.close()
    MODEL = model_from_json(loaded_model_json, {'binary_activation': Activation(binary_activation)})
    # load weights into new model
    MODEL.load_weights("./drive/MyDrive/fingerprint_model/encoder_model.h5")

    @classmethod
    def get_samples_of_audio(cls, file_path: str, remove_file=True) -> np.array:
        """
        get samples from audio file(signals)
        :param file_path: the path of audio file
        :param remove_file: a bool for delete file after get samples or not
        :return: samples
        """
        if os.path.exists(file_path):
            x, sr = librosa.load(file_path, cls.SAMPLE_RATE, res_type="kaiser_fast")
            if remove_file:
                os.remove(file_path)
            return x
        return None

    @classmethod
    def get_chroma_feature(cls, samples: np.array) -> np.ndarray:
        """
        :param samples:
        :return: chroma feature matrix
        """
        return librosa.feature.chroma_stft(samples,
                                           sr=cls.SAMPLE_RATE,
                                           n_fft=cls.N_FFT,
                                           hop_length=cls.HOP_LENGTH)

    @classmethod
    def add_padding(cls, feature: np.array) -> np.array:
        """
        :param feature: a matrix of feature values
        :return: a matrix with padding
        """
        full_matrix = np.full((cls.MAX_FRAME_NUM, 12), cls.SPECIAL_VALUE, dtype=np.float32)
        full_matrix[:feature.shape[0], :feature.shape[1]] = feature
        return full_matrix

    @classmethod
    def split_features(cls, feature: np.ndarray) -> np.ndarray:
        """
        split a matrix to many matrix
        :param feature:
        :return: an array of feature matrix
        """
        split_feature = np.split(feature, [each for each in cls.FRAME_SEC_INDEXES if each < len(feature)])
        return np.array([cls.add_padding(each) for each in split_feature])




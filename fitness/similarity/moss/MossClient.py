import mosspy
import re
import yaml
import logging

from fitness.similarity.SimilarityClient import SimilarityClient

try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen


class MossClient(SimilarityClient):

    def __init__(self, *args, **kwargs):
        with open("config.yml", 'r') as f:
            config = yaml.load(f)
            self.userid = config['moss_user_id']

    def get_scores(self, original_file, refactored_files):
        similarity_values = list()
        for file in refactored_files:
            similarity_values.append(self.get_binary_score(original_file, file))

        return similarity_values

    def get_binary_score(self, original_file, refactored_file):

        m = mosspy.Moss(self.userid, "python")

        m.addFile(original_file)
        m.addFile(refactored_file)

        url = m.send()
        logging.debug('Report URL: {}'.format(url))

        return self.parse_response(url)

    def parse_response(self, url):
        response = urlopen(url)
        content = response.read()

        p = re.compile('\([0-9]+%\)')
        scores = [int(score[1:-2]) for score in p.findall(str(content))]

        assert len(scores) == 2

        # simply use refactored file's match score with regard to original file
        return scores[1]



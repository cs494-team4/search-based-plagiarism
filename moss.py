import mosspy
import re
import yaml
import logging

try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen


def get_score(original_file, refactored_file):
    with open("config.yml", 'r') as f:
        config = yaml.load(f)
        userid = config['moss_user_id']

    m = MossClient(userid, "python")

    m.addFile(original_file)
    m.addFile(refactored_file)

    url = m.send()
    logging.debug('Report URL: {}'.format(url))

    return m.parse_score(url)


class MossClient(mosspy.Moss):
    def parse_score(self, url):
        response = urlopen(url)
        content = response.read()

        p = re.compile('\([0-9]+%\)')
        scores = [int(score[1:-2]) for score in p.findall(str(content))]

        assert len(scores) == 2

        # simply use refactored file's match score with regard to original file
        return scores[1]

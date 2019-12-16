from fitness.similarity.SimilarityClient import SimilarityClient

from .pycode_similar import *


class PyCodeSimClient(SimilarityClient):
    def get_scores(self, original_file, refactored_files):
        def get_file(value):
            return open(value, 'rb')

        files = [original_file] + refactored_files

        pycode_list = [(f.name, f.read())
                       for f in map(get_file, files)]

        try:
            results = detect([c[1] for c in pycode_list])
        except NoFuncException as ex:
            print('error: can not find functions from {}.'.format(
                pycode_list[ex.source][0]))
            return

        scores = []
        for index, func_ast_diff_list in results:
            # print('ref: {}'.format(pycode_list[0][0]))
            # print('candidate: {}'.format(pycode_list[index][0]))
            sum_total_count = sum(
                func_diff_info.total_count for func_diff_info in func_ast_diff_list)
            sum_plagiarism_count = sum(
                func_diff_info.plagiarism_count for func_diff_info in func_ast_diff_list)
            print('{:.2f} % ({}/{}) of ref code structure is plagiarized by candidate.'.format(
                sum_plagiarism_count / float(sum_total_count) * 100,
                sum_plagiarism_count,
                sum_total_count))

            scores.append(sum_plagiarism_count / float(sum_total_count) * 100)

        return scores

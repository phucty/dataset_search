import numpy as np
from pyNTCIREVAL import metrics
import math
from collections import defaultdict
import setting as st
import io_worker as iw
import logging


def ndcg(rank_predict, rank_gt, max_ranking=st.EVAL_LIMIT, logbase=2):
    if len(set(rank_predict)) == 1 and rank_predict[0] == 0:
        return 0.

    metric = metrics.nDCG(rank_gt, st.EVAL_REF_LEVEL, logb=logbase, cutoff=max_ranking)
    labeled_ranked_list = [(doc_id, doc_score) for doc_id, doc_score in enumerate(rank_predict)]
    result = metric.compute(labeled_ranked_list)
    if math.isnan(result):
        result = 0.
    return result


def nerr(rank_predict, rank_gt, max_ranking=st.EVAL_LIMIT):
    metric = metrics.nERR(rank_gt, st.EVAL_REF_LEVEL, cutoff=max_ranking)
    labeled_ranked_list = [(doc_id, doc_score) for doc_id, doc_score in enumerate(rank_predict)]
    result = metric.compute(labeled_ranked_list)
    if math.isnan(result):
        result = 0
    return result


def q_measure(rank_predict, rank_gt, max_ranking=st.EVAL_LIMIT, beta=1.):
    metric = metrics.QMeasure(rank_gt, st.EVAL_REF_LEVEL, beta=beta, cutoff=max_ranking)
    labeled_ranked_list = [(doc_id, doc_score) for doc_id, doc_score in enumerate(rank_predict)]
    result = metric.compute(labeled_ranked_list)
    if math.isnan(result):
        result = 0.
    return result


def run_eval(predict_file, lang=st.LANG_EN, cutoff=st.EVAL_LIMIT):
    iw.print_status("Lang: %s, Eval %s" % (lang, predict_file))
    lang = lang.lower()
    if lang == st.LANG_EN:
        SIZE_DATA = st.SIZE_DATA_EN
    elif lang == st.LANG_JP:
        SIZE_DATA = st.SIZE_DATA_JP
    else:
        iw.print_status("Error: Incorrect languages, \"e\" for English data, \"j\" for Japanese data")
        return

    if not predict_file:
        iw.print_status("Error: Invalid prediction")
        return

    DIR_TRAIN_QRELS = './data/data_search_%s_train_qrels.txt' % lang
    DIR_TRAIN_TOPICS = './data/data_search_%s_train_topics.tsv' % lang

    # Get query id and text
    queries = defaultdict()
    for line in iw.load_text_obj(DIR_TRAIN_TOPICS):
        line = line.split("\t")
        if len(line) == 2:
            query_id, query_text = line[0], line[1].replace("\n", "")
            queries[query_id] = query_text

    queries_gt = defaultdict()
    for line in iw.load_text_obj(DIR_TRAIN_QRELS):
        line = line.split()
        if len(line) == 3:
            query_id, table_id, score = line[0], line[1], line[2]
            if score == "L2":
                score = 2
            elif score == "L1":
                score = 1
            else:
                score = 0
            if not queries_gt.get(query_id):
                queries_gt[query_id] = defaultdict(int)
            queries_gt[query_id][table_id] = score

    res_queries = defaultdict(list)
    for line in iw.load_text_obj(predict_file):
        line = line.split(" ")
        res_queries[line[0]].append(line[2])

    m_nDCG = []
    m_nERR = []
    m_q_measure = []
    missing = 0
    for q_id, response in res_queries.items():
        q_text = queries.get(q_id, "")
        iw.print_status("\n%s\t%s" % (q_id, q_text))

        rank_predict = []
        rank_gt = [0] * st.REL_LEVEL_NUM
        for q_value in queries_gt[q_id].values():
            rank_gt[q_value] += 1

        gt_rel = sum([_rank_gt for _rank_gt in rank_gt[1:]])

        rank_gt[0] = SIZE_DATA - gt_rel
        iw.print_status(rank_gt)

        p_rel = 0
        iw.print_status("Responds: %d" % (len(response)))
        for hit_i, hit in enumerate(response):
            hit_rel = queries_gt[q_id].get(hit, 0)
            rank_predict.append(hit_rel)
            if hit_rel:
                p_rel += 1
                iw.print_status("  %d. %d - %s" % (hit_i + 1, hit_rel, hit))
        missing += (gt_rel - p_rel)
        # iw.print_status("Missing: %d" % (gt_rel - p_rel))

        q_nDCG = ndcg(rank_predict, rank_gt, cutoff)
        q_nERR = nerr(rank_predict, rank_gt, cutoff)
        q_q_measure = q_measure(rank_predict, rank_gt, cutoff)
        iw.print_status("nDCG@%d: %.4f\tnERR@%d: %.4f\tQ@%d: %4f" % (cutoff, q_nDCG,
                                                                     cutoff, q_nERR,
                                                                     cutoff, q_q_measure))
        m_nDCG.append(0 if not q_nDCG else q_nDCG)
        m_nERR.append(0 if not q_nERR else q_nERR)
        m_q_measure.append(0 if not q_q_measure else q_q_measure)

    iw.print_status("Final:")
    iw.print_status("nDCG@%d\tnERR@%d\tQ measure@%d" % (cutoff, cutoff, cutoff))
    iw.print_status("%.4f\t%.4f\t%4f" % (np.mean(m_nDCG), np.mean(m_nERR), np.mean(m_q_measure)))
    # iw.print_status("Missing: %d" % missing)


if __name__ == "__main__":
    if st.IS_LOG:
        iw.create_dir(st.DIR_LOG)
        logging.basicConfig(filename=st.DIR_LOG, format='%(message)s', level=logging.INFO)

    run_eval(lang="e", predict_file="results/anserini/en-rm3+bm25.txt", cutoff=10)
    # run_eval(lang="e", predict_file="results/elastic_search/en-bm25.txt", cutoff=10)
    # run_eval(lang="j", predict_file="results/anserini/ja-bm25.txt", cutoff=10)
    # run_eval(lang="j", predict_file="results/elastic_search/ja-bm25.txt", cutoff=10)

    iw.print_status("Done")


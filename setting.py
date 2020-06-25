import time
LANG_JP = "j"
LANG_EN = "e"
SIZE_DATA_JP = 1338402
SIZE_DATA_EN = 46615
DIR_LOG = "./log/log_%s.txt" % (str(time.time()))


# Main Setting --------------------------------------------------------------------------------------------------------
# Cut off limit for evaluation if nDCG@10 please set 10
EVAL_LIMIT = 1000

# L0, L1, L2
REL_LEVEL_NUM = 3
EVAL_REF_LEVEL = [i for i in range(1, REL_LEVEL_NUM)]


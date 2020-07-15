#!/usr/bin/env python3
import sys, argparse, os
import glob
import pandas as pd 
import numpy as np

boundaries = set(['/', '//', '{H}', '{PBC}', "+"])
noises = ["[SPOKEN NOISE]", "<inaudible>"]

def add_tags(tsvfile, tagfile):
    df = pd.read_csv(tsvfile, sep="\t")
    sents_with_tags = open(tagfile).readlines()
    sents_tokens = [x.split() for x in sents_with_tags]
    list_df = []
    tok_id = 0
    for i, sent in enumerate(sents_tokens):
        for tok_tag in sent:
            token, tag = tok_tag.split("_")
            list_df.append({'sent_id': i,
                'token': token,
                'tok_id': tok_id,
                'tag': tag})
            tok_id += 1
        tok_id = 0
    tag_df = pd.DataFrame(list_df)
    merged_df = pd.merge(df, tag_df, on=['sent_id', 'tok_id', 'token'], how='outer')
    print(merged_df[merged_df.isna().any(axis=1)])
    assert not merged_df.isnull().values.any()
    return merged_df

def write_sents(merged_df, outfile_txt):
    prev_sent = 0
    with open(outfile_txt, 'w') as f:
        for i, row in merged_df.iterrows():
            this_sent = row.sent_id
            if this_sent != prev_sent:
                f.write('\n')
                prev_sent = this_sent
            s = row.token + "\t" + row.tag + "\t" + str(row.disf) + "\n"
            f.write(s)
    return
            
if __name__ == '__main__':
    pa = argparse.ArgumentParser(description="Annotate transcriptions")
    pa.add_argument('--tsvfile', type=str, \
        default="annotations_tokens_v5_split.tsv", \
        help="input filename (token level)")
    pa.add_argument('--tagfile', type=str, \
        default="slash_units_tags_v5_split.txt", \
        help="POS-tagged file")
    pa.add_argument('--outfile_tsv', type=str, \
        default="merged_v4.tsv", \
        help="merged file")
    pa.add_argument('--outfile_txt', type=str, \
        default="to_dfl_v5.txt", \
        help="file to do disfluency detection")

    args = pa.parse_args()
    tsvfile = args.tsvfile
    tagfile = args.tagfile
    outfile_tsv = args.outfile_tsv
    outfile_txt = args.outfile_txt
    merged_df = add_tags(tsvfile, tagfile)
    merged_df.to_csv(outfile_tsv, sep="\t", index=False)
    write_sents(merged_df, outfile_txt)
    
    exit(0)



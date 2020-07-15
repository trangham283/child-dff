#!/usr/bin/env python3
import sys, argparse, os
import glob
import pandas as pd 
import numpy as np
from difflib import SequenceMatcher


def map_times(df):
    map_dict = {}
    for filename, df_file in df.groupby('filename'):
        num = 0
        times = set(df_file.time)
        for i, t in enumerate(sorted(times)):
            map_dict[(filename, t)] = filename + '-' + str(i+1)
    return map_dict

def check_tokens(x1, x2):
    sseq = SequenceMatcher(None, x1, x2)
    for info in sseq.get_opcodes():
        tag, i1, i2, j1, j2 = info
        #if tag != 'equal':
        #    print(tag, x1[i1:i2], "-->", x2[j1:j2])
        if i2-i1 != j2-j1:
            print(tag, x1[i1:i2], "-->", x2[j1:j2])

def check_all(df, time_df):
    utt_ids = set(df.utt_id)
    for utt_id in utt_ids:
        print(utt_id)
        x1 = df[df.utt_id == utt_id].token.to_list()
        x1 = [x for x in x1 if x != '<inaudible>']
        x2 = time_df[time_df.utt_id == utt_id].word.to_list()
        x2 = [x for x in x2 if x != "<SPOKEN_NOISE>"]
        x2 = [x.lower() for x in x2]
        check_tokens(x1, x2)

def assign_idx(df):
    new_df = []
    for utt_id, df_utt in df.groupby('utt_id'):
        df_utt = df_utt.assign(word_idx=range(len(df_utt)))
        new_df.append(df_utt)
    return pd.concat(new_df)

def add_times(tsvfile, alifile):
    df = pd.read_csv(tsvfile, sep="\t")
    inaudibles = set(df[df.token == '<inaudible>']['sent_id']) # 121 sents
    map_dict = map_times(df)
    df['utt_id'] = df.apply(lambda x: map_dict[(x['filename'],x['time'])],axis=1)

    time_df = pd.read_csv(alifile, sep=" ", 
            names=['utt_id','channel','start_time','duration', 'word'], 
            header=None, index_col=False)
    
    df_new = df[df.token != "<inaudible>"]
    df_new = assign_idx(df_new)
    df_time = time_df[time_df.word != "<SPOKEN_NOISE>"]
    df_time['word'] = df_time.word.apply(lambda x: x.lower())
    df_time = assign_idx(df_time)
    #check_all(df_new, df_time)
    merged_df = pd.merge(df_time, df_new, on=['utt_id', 'word_idx'])
    merged_df = merged_df[~merged_df['sent_id'].isin(inaudibles)]
    merged_df['start_time'] = merged_df['start_time']*3
    merged_df['duration'] = merged_df['duration']*3
    merged_df['sframe'] = merged_df['start_time']*100
    merged_df['eframe'] = merged_df['sframe'] + merged_df['duration']*100
    merged_df['sframe'] = merged_df['sframe'].apply(int)
    merged_df['eframe'] = merged_df['eframe'].apply(int)
    merged_df = merged_df.drop(columns=['channel', 'word', 'word_idx'])

    #print(merged_df[merged_df.isna().any(axis=1)])
    #assert not merged_df.isnull().values.any()
    return merged_df

# F0_dir = "F0"
def get_feats(merged_df, utt_id):
    f0_file = "F0/" + utt_id + '.f0'
    f0 = open(f0_file).readlines()
    f0 = [float(x.strip()) for x in f0]
    this_df = merged_df[merged_df.utt_id == utt_id]

    # example sentence    
    sent_id = 2233
    sent_df = this_df[this_df.sent_id == sent_id]
    pause_after = sent_df.sframe.diff().to_list()
    nan = pause_after.pop(0)
    pause_after.append(nan)
    sent_df = sent_df.assign(diff = pause_after)
    sent_df['pause_after'] = sent_df['diff'] - sent_df['dframe']
    
    sent_f0 = f0[sframe:eframe]
    

if __name__ == '__main__':
    pa = argparse.ArgumentParser(description="Annotate transcriptions")
    pa.add_argument('--tsvfile', type=str, \
        default="annotations_with_levels.tsv", \
        help="input filename (token level)")
    pa.add_argument('--alifile', type=str, \
        default="alignments-jibo.txt", \
        help="time alignment file")
    pa.add_argument('--outfile_tsv', type=str, \
        default="merged_time.tsv", \
        help="merged file")

    args = pa.parse_args()
    tsvfile = args.tsvfile
    alifile = args.alifile
    outfile_tsv = args.outfile_tsv
    merged_df = add_times(tsvfile, alifile)
    merged_df.to_csv(outfile_tsv, sep="\t", index=False)
    
    exit(0)



#!/usr/bin/env python3
import sys, argparse, os
import glob
import pandas as pd 
import numpy as np
from collections import Counter

boundaries = set(['/', '//', '{H}', '{PBC}', "+"])
noises = ["[SPOKEN NOISE]", "<inaudible>"]

def annotate_boundaries(text_file, sent_id, split_contractions=False):
    basename = os.path.basename(text_file).split("_")[0]
    lines = open(text_file).readlines()
    lines = [x.strip() for x in lines]
    lines = [x for x in lines if x]
    lines = lines[1:] # first line is always file name

    list_row = []
    disf_spans = []
    disf_done = []
    for line in lines:
        # replace square brackets to not confuse it with disf annotations
        all_toks = line.replace("[inaudible]", "<inaudible>")
        # separate brackets from words for easier annotations
        all_toks = all_toks.replace('[', ' [ ').replace(']', ' ] ')
        all_toks = all_toks.replace("’",  "'").replace("‘", "'")
        all_toks = all_toks.replace('+', ' + ')
        if split_contractions:
            all_toks = all_toks.replace("n't", " n't")
            all_toks = all_toks.replace("'s", " 's")
            all_toks = all_toks.replace("'d", " 'd")
            all_toks = all_toks.replace("'ll", " 'll")
            all_toks = all_toks.replace("'ve", " 've")
            all_toks = all_toks.replace("'re", " 're")
            all_toks = all_toks.replace("'m", " 'm")
            all_toks = all_toks.replace("cannot", "can not")
            all_toks = all_toks.replace("gonna", "gon na")
            all_toks = all_toks.replace("wanna", "wan na")
            all_toks = all_toks.replace("gotta", "got ta")
            all_toks = all_toks.replace("dunno", "du n no")
            all_toks = all_toks.replace("don'", "don '")
        all_toks = all_toks.split()
        time = all_toks[0]
        tokens = all_toks[1:]
        idx = 0
        glob_id = 0
        filler = 0
        boundary = 'None'
        level = 0

        while tokens:
            tok = tokens.pop(0)
            if tok == '{F':
                filler = 1
                continue
            if "}" in tok and tok not in boundaries:
                tok = tok.replace("}", '')
                list_row.append({
                    'filename': basename, 
                    'time': time[1:-1],
                    'sent_id': sent_id,
                    'tok_id': idx,
                    'glob_id': glob_id,
                    'token': tok.lower(),
                    'filler': filler,
                    'boundary': boundary,
                    'disf': 0,
                    'level': level
                    })
                idx += 1
                glob_id += 1
                filler = 0
                assert "/" not in tok
                assert "+" not in tok
                assert "{" not in tok
                continue
            if tok in boundaries:
                b = list_row[-1]['boundary'] 
                if sum([x in b for x in boundaries]) > 0:
                    list_row[-1]['boundary'] = list_row[-1]['boundary']+"_"+tok
                else:
                    list_row[-1]['boundary'] = tok
                if tok == '+':
                    disf_spans[-1]['+'].append(glob_id)
                if '/' in tok or '//' in tok:
                    sent_id += 1
                    idx = 0
                continue
            if tok == '[':
                disf_spans.append({'time': time[1:-1], 'open': glob_id, '+': []})
                level += 1
                continue                
            if tok == "]":
                disf_spans[-1]['close'] = glob_id
                disf_done.append(disf_spans.pop())
                level -= 1
                continue
            
            if not tok: continue # account for restarts
            assert "/" not in tok
            assert "+" not in tok
            assert "{" not in tok
            list_row.append({
                'filename': basename, 
                'sent_id': sent_id,
                'time': time[1:-1],
                'tok_id': idx,
                'glob_id': glob_id,
                'token': tok.lower(),
                'filler': filler,
                'boundary': boundary,
                'disf': 0,
                'level': level
                })
            idx += 1
            glob_id += 1
    return pd.DataFrame(list_row), disf_done, disf_spans, sent_id

def build_df(files1, dir1, split_contractions=False):
    list_df = []
    sent_id = 0
    for f1 in files1:
        basename = os.path.basename(f1)
        ff = basename.split("_")[0]
        print(basename)
        df1, disf1, sp1, sent_id = annotate_boundaries(f1, sent_id, split_contractions)
        df1['BE'] = 0
        df1['nested'] = 0
        # assert that stack is fully popped
        assert not sp1

        for span in disf1:
            #print(span)
            time = span['time']
            start = span['open']
            end = span['+'][-1]
            mask = (df1['time']==time) & (df1['glob_id']<end) & (df1['glob_id']>=start)
            df1.loc[mask, 'disf'] = 1
            mbe = (df1['time']==time) & (df1['glob_id']==start)
            df1.loc[mbe, 'BE'] = 1

        disf_df = pd.DataFrame(disf1)
        for time, df_time in disf_df.groupby('time'):
            df_time = df_time.sort_values('open')
            pairs = zip(df_time.open, df_time.close)
            ranges = []
            nested_ranges = []
            for s, e in pairs:
                if not ranges:
                    ranges.append([s,e])
                    continue
                prev_s, prev_e = ranges[-1]
                if s < prev_e:
                    ranges[-1][1] = max(e, prev_e)
                    if not nested_ranges:
                        nested_ranges.append(ranges[-1])
                    elif nested_ranges[-1][0] == ranges[-1][0]:
                        nested_ranges[-1] = ranges[-1]
                    else:
                        nested_ranges.append(ranges[-1])
                else:
                    ranges.append([s,e])

            for open_idx, close_idx in nested_ranges:
                mask = (df1['time']==time) & (df1['glob_id']<=close_idx) & (df1['glob_id']>=open_idx)
                df1.loc[mask, 'nested'] = 1

        list_df.append(df1)
    all_df = pd.concat(list_df)
    return all_df

            
if __name__ == '__main__':
    pa = argparse.ArgumentParser(description="Annotate transcriptions")
    pa.add_argument('--dir1', type=str, \
        default="Transcriptions_MT_V5", help="directory of transcription files")
    pa.add_argument('--outfile', type=str, \
        default="annotations_with_levels_split_v6.tsv", help="output filename")
    pa.add_argument('--split', type=int, \
        default=0, help="split contractions flag")

    args = pa.parse_args()
    dir1 = args.dir1
    outfile = args.outfile
    split_contractions = bool(args.split)
    files1 = glob.glob(dir1 + "/*.txt")
    all_df = build_df(files1, dir1, split_contractions)
    all_df.to_csv(outfile, sep="\t", index=False)
    exit(0)



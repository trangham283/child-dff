# child-dff
Here are some example steps for marking annotations:

1. Mark boundary and disfluencies of a set of transcriptions:
   On a terminal:
   `python mark_annotations.py --dir1 sample_data --outfile sample_data.tsv --split 0`

   This will produce the tab-separated file `sample_data.tsv`
   You can read this in excel, or use the pandas package in python.
   In the python console:
   `df = pd.read_csv('sample_data.tsv', sep="\t")`

   To avoid seeing ellipsis, you can try to just show first 5 lines like:
   `df.head(5)`. To see what columns there are, you can type `df.columns`.

   It's a very useful package, so I recommend reading through a tutorial, 
   e.g. this one: https://pandas.pydata.org/pandas-docs/stable/getting_started/10min.html

2. Add time info, which requires having an alignment file:
   Here, it's the `sample_alignments.txt` file, a subset of full alignments given to 
   me by Gary.

   You can add the timing info like this:
   `python add_time_alignments.py --tsvfile sample_data.tsv --alifile sample_alignments.txt --outfile_tsv sample_merged_time.tsv`

   Similar to step 1, this produces `sample_merged_time.tsv`, another tab-separated file and you can also view it as in step 1. 





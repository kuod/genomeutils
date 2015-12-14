#!/usr/bin/env python 
"""
translate the CDS region predicted by trsk program 
"""

import os 
import sys 
import filecmp
import numpy as np 
import pandas as pd 
from Bio import SeqIO 
from Bio.SeqRecord import SeqRecord
from Bio.Seq import Seq
from Bio.Alphabet import SingleLetterAlphabet
from gfftools import GFFParser, helper
from signal_labels import generate_genome_seq_labels as seqlab
import pdb
import os
import re

def translate_trsk_genes(gtf_file, fas_file, out_seq_fname, max_orf_opt = False):
    """ translate the trsk genes to protein sequence @args gtf_file: genome annotation file @type gtf_file: str
    @args fas_file: genome sequence file
    @type fas_file: str
    @args out_seq_fname: output file in fasta format 
    @type out_seq_fname: str
    """
    
    if filecmp.cmp(gtf_file, fas_file):
        exit("Do the two files are exactly same? Please check that!")

    ## reading the TSkim file to get the features 
    sys.stdout.write('reading genome features from %s\n' % gtf_file)
    anno_db = GFFParser.Parse(gtf_file) 
    total_genes = len(anno_db) 

    ## genome sequence file reading 
    sys.stdout.write('reading genome sequence from %s\n' % fas_file)
    seqlab.chrom_name_consistency(fas_file, anno_db) 
    cds_idx = []
    if not max_orf_opt:
        for idp, feat in enumerate(anno_db):
            if not feat['cds_exons'][0].any():
                cds_idx.append(idp)
    else:
        for idp, feat in enumerate(anno_db):
            if not feat['exons'][0].any():
                cds_idx.append(idp)
    anno_db = np.delete(anno_db, cds_idx)
    genes_with_cds = 0

    fasFH = helper.open_file(fas_file)
    out_seq_fh = open(out_seq_fname, 'w')
    for rec in SeqIO.parse(fasFH, 'fasta'):
        for idx, feature in enumerate(anno_db):
            if rec.id == feature['chr']:
                cds_seq = ''
                if len(feature['cds_exons'][0]) == 0:
                    max_orf_opt = True
                if not max_orf_opt:
                    for ex in feature['cds_exons'][0]:
                        cds_seq += rec.seq[ex[0] - 1:ex[1]]

                    if feature['strand'] == '-':
                        cds_seq = cds_seq.reverse_complement()
                    if cds_seq:
                        prt_seq = SeqRecord(cds_seq.translate(), id=feature['name'], description='protein sequence')
                        out_seq_fh.write(prt_seq.format('fasta'))
                else:
                    start = int(feature['exons'][0][0][0])
                    end = int(feature['exons'][0][0][1] + 1)
                    cds_seq += rec.seq[start:end]
                    if feature['strand'] == '-':
                        cds_seq = cds_seq.reverse_complement()
                    cds_seq = find_max_orf(cds_seq)
                    if cds_seq:
                        genes_with_cds += 1
                        prt_seq = SeqRecord(cds_seq.translate(), id=feature['name'], description='protein sequence')
                        out_seq_fh.write(prt_seq.format('fasta'))

    fasFH.close()
    out_seq_fh.close()

    sys.stdout.write('total genes fetched: %d\n' % total_genes)
    sys.stdout.write('total genes translated: %d\n' % genes_with_cds)
    sys.stdout.write('protein sequence stored at %s\n' % out_seq_fname)


def trsk_gene_len_dist(gtf_file, out_file="hist_cds_len.pdf"):
    """
    plotting the histograms bases on the genes and CDS length
    """
    import matplotlib.pyplot as plt 

    anno_db = GFFParser.Parse(gtf_file) 

    cds_idx = [] # deleting the empty cds lines  
    for idp, feat in enumerate(anno_db):
        if not feat['cds_exons'][0].any():
            cds_idx.append(idp) 

    anno_db = np.delete(anno_db, cds_idx) 
    
    trans_len = np.zeros((len(anno_db), 2))
    genes = [] 

    for idx, feat in enumerate(anno_db):
        cds_len = 0 
        for exc in feat['cds_exons'][0]:
            cds_len += exc[1]-exc[0]

        trans_len[idx, 0] = feat['stop']-feat['start']
        trans_len[idx, 1] = cds_len
        genes.append(feat['name'])
    
    ## gene, cds length information 
    df_len_dis_genes = pd.DataFrame(trans_len, columns=['gene_len', 'cds_len'], index=genes)

    ## plotting the gene length based on the bins of gene length  
    gene_length = trans_len[:,0] ## gene length from the matrix 

    freq, bins = np.histogram(gene_length, bins=10, range=None, normed=False, weights=None)
    bins = np.delete(bins, 10) 

    df_gene_len_bin = pd.DataFrame(freq, columns=['gene_frequency'], index=bins) 
    plt.figure() 
    df_gene_len_bin.plot(kind="bar")
    #plt.savefig()

    ## plotting the cds length distribution
    cds_length = trans_len[:,1] ## cds length distribution 
    freq, bins = np.histogram(cds_length, bins=10, range=None, normed=False, weights=None)
    bins = np.delete(bins, 10) 
    df_cds_len_bin = pd.DataFrame(freq, columns=['cds_frequency'], index=bins) 
    plt.figure() 
    df_cds_len_bin.plot(kind="bar")
    plt.savefig(out_file) 

def find_max_orf(seq):
    """ find optimal start and end for concatenated exons
    @args seq: biopython alphabet object

    Returns:
    False   bool    Longest ORF was less than 100 nt
    Seq     BioPython Seq Object    Longest start to end substring in seq
    """
    seq = str(seq)
    start_arr = np.array([ m.start() for m in re.finditer('ATG', seq) ])
    taa_list = np.array([ m.start() for m in re.finditer('TAA', seq) ])
    tag_list = np.array([ m.start() for m in re.finditer('TAG', seq) ])
    tga_list = np.array([ m.start() for m in re.finditer('TGA', seq) ])
    end_arr = np.sort(np.hstack((taa_list, tag_list, tga_list)))
    if len(start_arr) == 0 or len(end_arr) == 0:
        return False
    max_dist = 0
    max_start = -1
    max_end = -1
    start_arr_orf = [ int(x % 3) for x in start_arr ]
    end_arr_orf = [ int(x % 3) for x in end_arr ]
    for frame_ind in [0, 1, 2]:
        start_mask = np.array([ val == frame_ind for val in start_arr_orf ])
        start_frame = start_arr[start_mask]
        end_mask = np.array([ val == frame_ind for val in end_arr_orf ])
        end_frame = end_arr[end_mask]
        if len(start_frame) != 0 and len(end_frame) != 0:
            for start in np.sort(start_frame):
                seen_end = False
                for end in np.sort(end_frame):
                    if end < start or seen_end:
                        next
                    else:
                        seen_end = True
                        dist = end - start
                        if dist > max_end:
                            max_start = start
                            max_end = end
                            max_dist = dist
                            next
                        next

    if max_dist < 100:
        return False
    else:
        return Seq(seq[int(max_start):int(max_end) + 3], SingleLetterAlphabet())

if __name__=="__main__":
    gname = "hs_chr22.gff"
    fas = "hg19.fa"
    out = "out_protein_seq.fa"
    translate_trsk_genes(gname, fas, out) 

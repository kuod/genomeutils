#!/usr/bin/env python 
"""
filter out gene models from annotation file based on the splice-site consensus into account and length of the ORF 

Program requires genome annotation in gtf/gff and genome sequence file in fasta format. 

Requirement:
    numpy
    gfftools
    biopython 
"""

from __future__ import division
import sys 
import numpy 
import collections
from Bio import SeqIO 
from gfftools import GFFParser, helper 


def filter_gene_models(gff_name, fas_file, outFile):
    """
    check the sequence consistency/quality of predicted fragment

    @args gff_name: result file gff format from TranscriptSkimmer
    @type gff_name: str
    @args fas_file: genome sequence in fasta format
    @type fas_file: str 
    @args outFile: filtered gene output file 
    @type outFile: str 
    """
    
    print 'using genome sequence file %s' % fas_file
    print 'using genome annotation file %s' % gff_name
    print 
    ## getting the genome annotation from GFF file 
    gff_content = GFFParser.Parse(gff_name)
    
    ## getting the spliced transcripts from the predicted gene list 
    transcripts_region = collections.defaultdict(list)
    for gene_recd in gff_content:
        spliced_transcript = collections.defaultdict(list)

        for idx, sub_rec in enumerate(gene_recd['transcripts']):
            
            try:
                exon_cnt = len(gene_recd['exons'][idx])
            except:
                continue

            ## skipping the single-exon transcripts 
            if exon_cnt > 1: 
                for idk, ex in enumerate(gene_recd['exons'][idx]):
                    if idk == 0:
                        ex[0] = None 
                    if exon_cnt-1 == idk:
                        ex[1] = None

                    spliced_transcript[(gene_recd['name'], sub_rec[0], gene_recd['strand'])].append(ex)

        transcripts_region[gene_recd['chr']].append(spliced_transcript)

    print "check for the splice site consensus for predicted transcripts"
    ## check for splice site consensus sequence of predicted transcripts 
    get_gene_models = collections.defaultdict()
    for fas_rec in SeqIO.parse(fas_file, "fasta"):
        if fas_rec.id in transcripts_region:
            for details in transcripts_region[fas_rec.id]:
                for genes, regions in details.items():

                    acc_cons_cnt = 0 
                    don_cons_cnt = 0 

                    for region in regions:
                        if genes[-1] == '+':
                            ## acceptor splice site 
                            if not numpy.isnan(region[0]):
                                acc_seq = fas_rec.seq[int(region[0])-3:int(region[0])-1]
                                if str(acc_seq).upper() == "AG":
                                    acc_cons_cnt += 1 

                            if not numpy.isnan(region[1]):
                                don_seq = fas_rec.seq[int(region[1]):int(region[1])+2]
                                if str(don_seq).upper() == "GT":
                                    don_cons_cnt +=1 

                        elif genes[-1] == '-':
                            ## donor splice site 
                            if not numpy.isnan(region[0]):
                                don_seq = fas_rec.seq[int(region[0])-3:int(region[0])-1]
                                don_seq = don_seq.reverse_complement()
                                if str(don_seq).upper() == "GT":
                                    don_cons_cnt +=1 
                            
                            if not numpy.isnan(region[1]):
                                acc_seq = fas_rec.seq[int(region[1]):int(region[1])+2]
                                acc_seq = acc_seq.reverse_complement()
                                if str(acc_seq).upper() == "AG":
                                    acc_cons_cnt += 1 
                    ## check for half of the consensus sites 
                    if acc_cons_cnt > (len(regions)/2) and don_cons_cnt > (len(regions)/2):
                        get_gene_models[(fas_rec.id, genes[0], genes[1], genes[2])] = 1   
    
    gff_cont = GFFParser.Parse(gff_name)

    ## filter out the best gene models based on the consensus 
    print "writing the fine tuned transctipts to the the file"
    out_fh = open(outFile, "w")
    for recd in gff_cont:
        trans_indices = [] 

        for idx, sub_rec in enumerate(recd['transcripts']):
            if (recd['chr'], recd['name'], sub_rec[0], recd['strand']) in get_gene_models:
                trans_indices.append(idx)

        if trans_indices:
            chr_name = recd['chr']
            strand = recd['strand']
            start = recd['start']
            stop = recd['stop']
            source = recd['source']
            ID = recd['name']
            Name = recd['gene_info']['Name']
            Name = ID if Name != None else Name  
            out_fh.write('%s\t%s\tgene\t%d\t%d\t.\t%s\t.\tID=%s;Name=%s\n' % (chr_name, source, start, stop, strand, ID, Name))
                
            for idz, tid in enumerate(recd['transcripts']):
                if idz in trans_indices:

                    t_start = recd['exons'][idz][0][0]
                    t_stop = recd['exons'][idz][-1][-1]
                    t_type = recd['transcript_type'][idz] 

                    out_fh.write('%s\t%s\t%s\t%d\t%d\t.\t%s\t.\tID=%s;Parent=%s\n' % (chr_name, source, t_type, t_start, t_stop, strand, tid[0], ID))
                    
                    for ex_cod in recd['utr5_exons'][idz]:
                        out_fh.write('%s\t%s\tfive_prime_UTR\t%d\t%d\t.\t%s\t.\tParent=%s\n' % (chr_name, source, ex_cod[0], ex_cod[1], strand, tid[0])) 
                    for ex_cod in recd['cds_exons'][idz]:
                        out_fh.write('%s\t%s\tCDS\t%d\t%d\t.\t%s\t%d\tParent=%s\n' % (chr_name, source, ex_cod[0], ex_cod[1], strand, ex_cod[2], tid[0])) 
                    for ex_cod in recd['utr3_exons'][idz]:
                        out_fh.write('%s\t%s\tthree_prime_UTR\t%d\t%d\t.\t%s\t.\tParent=%s\n' % (chr_name, source, ex_cod[0], ex_cod[1], strand, tid[0]))
                    for ex_cod in recd['exons'][idz]:
                        out_fh.write('%s\t%s\texon\t%d\t%d\t.\t%s\t.\tParent=%s\n' % (chr_name, source, ex_cod[0], ex_cod[1], strand, tid[0])) 
    out_fh.close()
    return out_fname


if __name__ == "__main__":
    try:
        gff_name = sys.argv[1]
        fas_file = helper.open_file(sys.argv[2]) 
    except:
        print __doc__
        sys.exit(-1) 

    outfile = "filter_genes.gff"
    filter_gene_models(gff_name, fas_file, outfile)

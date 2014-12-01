#!/usr/bin/env python 
"""
generating standard genome indices. 

Usage: 
import prepare_data as pd 
pd.create_star_genome_index.__doc__

Requirement:
    STAR aligner: https://github.com/alexdobin/STAR 
    gfftools: https://github.com/vipints/genomeutils/tree/master/gfftools 
"""

import os 
import re
import sys 
import shutil
import subprocess 
from gfftools import helper
from gfftools import GFFParser


def create_star_genome_index(fasta_file, out_dir, genome_anno=None, num_workers=1, onematelength=100):
    """
    Creating STAR genome index with or without using genome annotation

    @args fasta_file: reference genome sequence file .fasta format 
    @type fasta_file: str 
    @args out_dir: genome index binary file storage place  
    @type out_dir: str 
    @args genome_anno: genome annotation file (optional) 
    @type genome_anno: str 
    @args num_workers: number of threads to run (default value = 1)
    @type num_workers: int 
    @args onematelength: One Mate Length (default value=100) 
    @type num_workers: int 
    """
    
    if not genome_anno:
        cli_cmd = 'STAR --runMode genomeGenerate --genomeDir %s --genomeFastaFiles %s --runThreadN %d' % (out_dir, fasta_file, num_workers) 
    else:
        ## check for the file type  
        gff_hand = helper.open_file(genome_anno)
    
        for rec in gff_hand:
            rec = rec.strip('\n\r')

            # skip empty line fasta identifier and commented line
            if not rec or rec[0] in  ['#', '>']:
                continue
            # skip the genome sequence 
            if not re.search('\t', rec):
                continue

            parts = rec.split('\t')
            assert len(parts) >= 8, rec

            ftype, tags = GFFParser.attribute_tags(parts[-1])
            break 

        gff_hand.close() 

        ## according to the file type 
        if ftype:
            cli_cmd = 'STAR --runMode genomeGenerate --genomeDir %s --genomeFastaFiles %s --runThreadN %d --sjdbGTFfile %s --sjdbGTFtagExonParentTranscript Parent --sjdbOverhang %d' % (out_dir, fasta_file, num_workers, genome_anno, onematelength) 
        else:
            cli_cmd = 'STAR --runMode genomeGenerate --genomeDir %s --genomeFastaFiles %s --runThreadN %d --sjdbGTFfile %s --sjdbOverhang %d' % (out_dir, fasta_file, num_workers, genome_anno, onematelength) 

    ## create downloadpath if doesnot exists 
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    
    ## start the index job 
    try:
        process = subprocess.Popen(cli_cmd, shell=True) 
        process.wait()
    except:
        print "error"
        sys.exit(-1)

    print 
    print "STAR genome index files are stored at %s" % out_dir
    print 


if __name__=="__main__":
    print __doc__
    
"""
"""
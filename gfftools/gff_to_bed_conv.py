#!/usr/bin/env python
"""
Convert genome annotation data in GFF/GTF to a 12 column BED format. 
BED format typically represents the transcript models. 

Usage: python gff_to_bed_conv.py in.gff > out.bed  
"""

import sys
import re

def stop_err(fmsg):
    
    sys.stderr.write('%s\n' % fmsg)
    sys.exit(-1)

def WriteBED(tinfo, einfo, bed_fh):
    """BED writter"""
    
    for contig_id, feature in tinfo.items():
        for tid, tloc in feature.items():
            if tid in einfo: # get corresponding exon info 
                exon_cnt, exon_len, exon_cod, fex, rstart = 0, '', '', 0, None
                if tloc[-1] == '-':
                    if einfo[tid][0][1] > einfo[tid][-1][1]:einfo[tid].sort()
                for ex_ele in einfo[tid]:
                    if ex_ele[0] != contig_id:continue
                    exon_cnt += 1
                    exon_len += str(int(ex_ele[2])-int(ex_ele[1])+1) + ','
                    if fex == 0: # calculate the relative exon start 
                        exon_cod += '0,'
                        fex = 1
                        rstart = int(ex_ele[1])
                    else:
                        exon_cod += str(int(ex_ele[1])-rstart) + ','
                if exon_len:
                    pline = [str(contig_id),
                            tloc[0],
                            tloc[1],
                            tid,
                            tloc[2],
                            tloc[-1],
                            tloc[0],
                            tloc[1],
                            '0',
                            str(exon_cnt),
                            exon_len,
                            exon_cod]
                    bed_fh.write('\t'.join(pline) + '\n')
    bed_fh.close()

def ParseAnno(gff_fh):
    """Reading GFF3 file to get feature annotation"""

    tinfo, einfo = dict(), dict()
    features = ['transcript', 'scRNA', 'mRNA', 'ncRNA', 'miRNA', 'rRNA', 'snoRNA', 'snRNA', 'tRNA', 'pseudogenic_transcript'] ## TODO: Growing list of RNA species. 

    for gff_line in gff_fh:
        gff_line = gff_line.strip('\n\r').split('\t')
        if re.match(r'#', gff_line[0]) or re.match(r'>', gff_line[0]) or len(gff_line) == 1:continue ## not considering commented and FASTA  lines from GFF
        if '' in gff_line:continue ## empty fields in any line ? 
        assert len(gff_line) == 9, '\t'.join(gff_line) ## a valid GFF line contains only 9 tab-delimited fields

        if gff_line[2] in features:
            tid = None
            for ele in gff_line[-1].split(';'):
                if re.search(r'ID=', ele):
                    tid = re.search(r'ID=(.+)', ele).group(1)
                    break
            if gff_line[0] in tinfo:
                tinfo[gff_line[0]][tid] = (gff_line[3], gff_line[4], gff_line[5], gff_line[6])
            else:
                tinfo[gff_line[0]] = {tid:(gff_line[3], gff_line[4], gff_line[5], gff_line[6])}
        elif gff_line[2] == 'exon':
            pid = None
            for ele in gff_line[-1].split(';'):
                if re.search(r'Parent=', ele):
                    pid = re.search(r'Parent=(.+)', ele).group(1)
                    break
            if pid in einfo:
                einfo[pid].append((gff_line[0], int(gff_line[3]), int(gff_line[4])))
            else:
                einfo[pid] = [(gff_line[0], int(gff_line[3]), int(gff_line[4]))]
    gff_fh.close()
    return tinfo, einfo

def __main__():

    cmd_arg = OptionParser()
    cmd_arg.add_option('', '-q', dest='query_file', help='Data in GFF3 file')
    cmd_arg.add_option('', '-o', dest='result_file', help='BED file name')

    options, args = cmd_arg.parse_args()
    if len(sys.argv) < 2:cmd_arg.print_help();sys.exit(-1)

    if options.query_file != None and options.result_file != None: 
        try:
            gff_fh = open(options.query_file, 'rU')
        except Exception, erm:
            stop_err('Error reading query file ' + str(erm))
        
        tinfo, einfo = ParseAnno(gff_fh) ## get transcript annotation from GFF3 file 
        try:
            bed_fh = open(options.result_file, 'w')
        except Exception, erm:
            stop_err('Error writing result file ' + str(erm))
        WriteBED(tinfo, einfo, bed_fh) ## BED writter 

if __name__ == "__main__": __main__() 

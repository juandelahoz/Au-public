#!/usr/bin/python
import argparse, sys, os, time, re, gzip, locale
from shutil import rmtree, copy, copytree
from multiprocessing import cpu_count, Pool
from tempfile import mkdtemp, gettempdir
from subprocess import Popen, PIPE
from Bio.Range import BedStream
from Bio.Format.GPD import GPDStream

# read count
version = 0.9

locale.setlocale(locale.LC_ALL,'en_US')

def main(args):

  if not args.output and not args.portable_output:
    sys.stderr.write("ERROR: must specify some kind of output\n")
    sys.exit()

  ## Check and see if directory for outputs exists
  if args.output:
    if os.path.isdir(args.output):
      sys.stderr.write("ERROR: output directory already exists.  Remove it to write to this location.\n")
      sys.exit()

  # Create the output HTML
  make_html(args)

  udir = os.path.dirname(os.path.realpath(__file__))
  if args.output:
    copytree(args.tempdir,args.output)
    cmd = 'python '+udir+'/make_solo_html.py '+args.output+'/report.html'
    sys.stderr.write(cmd+"\n")
    p = Popen(cmd.split(),stdout=PIPE)
    with open(args.output+'/portable_report.html','w') as of:
      for line in p.stdout:
        of.write(line)
    p.communicate()

  if args.portable_output:
    cmd = 'python '+udir+'/make_solo_html.py '+args.tempdir+'/report.html'
    sys.stderr.write(cmd+"\n")
    p = Popen(cmd.split(),stdout=PIPE)
    with open(args.portable_output,'w') as of:
      for line in p.stdout:
        of.write(line)
    p.communicate()

  ## Temporary working directory step 3 of 3 - Cleanup
  #if not args.specific_tempdir:
  #  rmtree(args.tempdir)


def make_html(args):
  global version
  #read in our alignment data
  mydate = time.strftime("%Y-%m-%d")
  a = {}
  with open(args.tempdir+'/data/alignment_stats.txt') as inf:
    for line in inf:
      (name,numstr)=line.rstrip().split("\t")
      a[name]=int(numstr)

  #read in our special read analysis
  special = {}
  with open(args.tempdir+'/data/special_report') as inf:
    for line in inf:
      f = line.rstrip().split("\t")
      if f[0] not in special: special[f[0]] = []
      special[f[0]].append(f[1:])
  #read in our error data
  e = {}
  with open(args.tempdir+'/data/error_stats.txt') as inf:
    for line in inf:
      (name,numstr)=line.rstrip().split("\t")
      e[name]=int(numstr)

  # read in our coverage data
  coverage_data = {}
  coverage_data['genome_total'] = 0
  with open(args.tempdir+'/data/chrlens.txt') as inf:
    for line in inf:
      f = line.rstrip().split("\t")
      coverage_data['genome_total']+=int(f[1])
  inf = gzip.open(args.tempdir+'/data/depth.sorted.bed.gz')
  coverage_data['genome_covered'] = 0
  bs = BedStream(inf)
  for rng in bs:
    f = line.rstrip().split("\t")
    coverage_data['genome_covered'] += rng.length()
  inf.close()
  inf = open(args.tempdir+'/data/beds/exon.bed')
  coverage_data['exons_total'] = 0
  bs = BedStream(inf)
  for rng in bs:
    f = line.rstrip().split("\t")
    coverage_data['exons_total'] += rng.length()
  inf.close()
  inf = open(args.tempdir+'/data/beds/intron.bed')
  coverage_data['introns_total'] = 0
  bs = BedStream(inf)
  for rng in bs:
    f = line.rstrip().split("\t")
    coverage_data['introns_total'] += rng.length()
  inf.close()
  inf = open(args.tempdir+'/data/beds/intergenic.bed')
  coverage_data['intergenic_total'] = 0
  bs = BedStream(inf)
  for rng in bs:
    f = line.rstrip().split("\t")
    coverage_data['intergenic_total'] += rng.length()
  inf.close()
  inf = gzip.open(args.tempdir+'/data/exondepth.bed.gz')
  coverage_data['exons_covered'] = 0
  bs = BedStream(inf)
  for rng in bs:
    f = line.rstrip().split("\t")
    coverage_data['exons_covered'] += rng.length()
  inf.close()
  inf = gzip.open(args.tempdir+'/data/introndepth.bed.gz')
  coverage_data['introns_covered'] = 0
  bs = BedStream(inf)
  for rng in bs:
    f = line.rstrip().split("\t")
    coverage_data['introns_covered'] += rng.length()
  inf.close()
  inf = gzip.open(args.tempdir+'/data/intergenicdepth.bed.gz')
  coverage_data['intergenic_covered'] = 0
  bs = BedStream(inf)
  for rng in bs:
    f = line.rstrip().split("\t")
    coverage_data['intergenic_covered'] += rng.length()
  inf.close()
  
  #get our coverage counts
  #get reference gene and transcript counts first
  tx_to_gene = {}
  if args.annotation:
    ref_genes = {}
    ref_transcripts = {}
    with open(args.annotation) as inf:
      gs = GPDStream(inf)  
      for gpd in gs:
        tx_to_gene[gpd.get_transcript_name()] = gpd.get_gene_name()
        ref_genes[gpd.get_gene_name()] = [0,0]
        ref_transcripts[gpd.get_transcript_name()] = [0,0]
    inf = gzip.open(args.tempdir+'/data/annotbest.txt.gz')
    for line in inf:
      f = line.rstrip().split("\t")
      gene = f[2]
      tx = f[3]
      if f[4]=='partial': ref_genes[gene][0] += 1
      elif f[4]=='full': ref_genes[gene][1] += 1
      if f[4]=='partial': ref_transcripts[tx][0] += 1
      elif f[4]=='full': ref_transcripts[tx][1] += 1
    inf.close()

  #get our locus count
  inf = gzip.open(args.tempdir+'/data/loci.bed.gz')
  locuscount = 0
  for line in inf:
    locuscount += 1
  inf.close()

  #get our annotation counts
  genefull = 0
  geneany = 0
  txfull = 0
  txany = 0
  inf = gzip.open(args.tempdir+'/data/annotbest.txt.gz')
  genes_f = {}
  genes_a = {}
  txs_f = {}
  txs_a = {}
  for line in inf:
    f = line.rstrip().split("\t")
    g = f[2]
    t = f[3]
    if g not in genes_a: genes_a[g] = 0
    genes_a[g]+=1
    if t not in txs_a: txs_a[t] = 0
    txs_a[t]+=1
    if f[4] == 'full':
      if g not in genes_f: genes_f[g] = 0
      genes_f[g]+=1
      if t not in txs_f: txs_f[t] = 0
      txs_f[t]+=1
  inf.close()
  genefull = len(genes_f.keys())
  geneany = len(genes_a.keys())
  txfull = len(txs_f.keys())
  txany = len(txs_a.keys())
  
  #Get evidence counts for bias
  bias_tx_count = None
  bias_read_count = None
  with open(args.tempdir+'/data/bias_counts.txt') as inf:
    for line in inf:
      f = line.rstrip().split("\t")
      bias_tx_count = int(f[0])
      bias_read_count = int(f[1])

  #make our css directory
  if not os.path.exists(args.tempdir+'/css'):
    os.makedirs(args.tempdir+'/css')
  udir = os.path.dirname(os.path.realpath(__file__))
  #copy css into that directory
  copy(udir+'/../data/mystyle.css',args.tempdir+'/css/mystyle.css')
  of = open(args.tempdir+'/report.html','w')
  ostr = '''
<!DOCTYPE html>
<html>
<head>
<link rel="stylesheet" type="text/css" href="css/mystyle.css">
<title>Long Read Alignment and Error Report</title>
</head>
<body>
<div>
  <div class="top_block">
    <div>
    Generated on:
    </div>
    <div class="input_value">'''
  of.write(ostr)
  of.write(mydate)
  ostr = '''
    </div>
  </div>
  <div class="top_block">
    <div>
    Version:
    </div>
    <div class="input_value">'''
  of.write(ostr)
  of.write(str(version))
  ostr = '''
    </div>
  </div>
  <div class="top_block">
    <div>Execution parmeters:</div>
    <div class="input_value">
    <a href="data/params.txt">params.txt</a>
    </div>
  </div>
  <div class="clear"></div>
  <div class="top_block">
    <div>Long read alignment and error report for:</div>
    <div class="input_value" id="filename">'''
  of.write(ostr+"\n")
  of.write(args.input)
  ostr = '''
    </div>  
  </div>
</div>
<div class="clear"></div>
<hr>
<div class="result_block">
  <div class="subject_title">
    <table><tr><td class="c1">Alignment analysis</td><td class="c2"><span class="highlight">'''
  of.write(ostr)
  reads_aligned = perc(a['ALIGNED_READS'],a['TOTAL_READS'],1)
  of.write(reads_aligned)
  ostr = '''
  </span></td><td class="c2"><span class="highlight2">reads aligned</span></td><td class="c2"><span class="highlight">'''
  of.write(ostr)
  bases_aligned = perc(a['ALIGNED_BASES'],a['TOTAL_BASES'],1)
  of.write(bases_aligned)
  ostr = '''
  </span></td><td class="c2"><span class="highlight2">bases aligned <i>(of aligned reads)</i></span></td></tr></table>
  </div>
  <div class="one_third left">
    <table class="data_table">
        <tr class="rhead"><td colspan="3">Read Stats</td></tr>'''
  of.write(ostr+"\n")
  total_read_string = '<tr><td>Total reads</td><td>'+str(addcommas(a['TOTAL_READS']))+'</td></td><td></td></tr>'
  of.write(total_read_string+"\n")
  unaligned_read_string = '<tr><td>- Unaligned reads</td><td>'+str(addcommas(a['UNALIGNED_READS']))+'</td></td><td>'+perc(a['UNALIGNED_READS'],a['TOTAL_READS'],1)+'</td></tr>'
  of.write(unaligned_read_string+"\n")
  aligned_read_string = '<tr><td>- Aligned reads</td><td>'+str(addcommas(a['ALIGNED_READS']))+'</td></td><td>'+perc(a['ALIGNED_READS'],a['TOTAL_READS'],1)+'</td></tr>'
  of.write(aligned_read_string+"\n")
  single_align_read_string = '<tr><td>--- Single-align reads</td><td>'+str(addcommas(a['SINGLE_ALIGN_READS']))+'</td></td><td>'+perc(a['SINGLE_ALIGN_READS'],a['TOTAL_READS'],1)+'</td></tr>'
  of.write(single_align_read_string+"\n")
  gapped_align_read_string = '<tr><td>--- Gapped-align reads</td><td>'+str(addcommas(a['GAPPED_ALIGN_READS']))+'</td></td><td>'+perc(a['GAPPED_ALIGN_READS'],a['TOTAL_READS'],2)+'</td></tr>'
  of.write(gapped_align_read_string+"\n")
  gapped_align_read_string = '<tr><td>--- Chimeric reads</td><td>'+str(addcommas(a['CHIMERA_ALIGN_READS']))+'</td></td><td>'+perc(a['CHIMERA_ALIGN_READS'],a['TOTAL_READS'],2)+'</td></tr>'
  of.write(gapped_align_read_string+"\n")
  gapped_align_read_string = '<tr><td>----- Trans-chimeric reads</td><td>'+str(addcommas(a['TRANSCHIMERA_ALIGN_READS']))+'</td></td><td>'+perc(a['TRANSCHIMERA_ALIGN_READS'],a['TOTAL_READS'],2)+'</td></tr>'
  of.write(gapped_align_read_string+"\n")
  gapped_align_read_string = '<tr><td>----- Self-chimeric reads</td><td>'+str(addcommas(a['SELFCHIMERA_ALIGN_READS']))+'</td></td><td>'+perc(a['SELFCHIMERA_ALIGN_READS'],a['TOTAL_READS'],2)+'</td></tr>'
  of.write(gapped_align_read_string+"\n")
  ostr='''
        <tr class="rhead"><td colspan="3">Base Stats <i>(of aligned reads)</i></td></tr>'''
  of.write(ostr+"\n")
  total_bases_string = '<tr><td>Total bases</td><td>'+str(addcommas(a['TOTAL_BASES']))+'</td></td><td></td></tr>'
  of.write(total_bases_string+"\n")
  unaligned_bases_string = '<tr><td>- Unaligned bases</td><td>'+str(addcommas(a['UNALIGNED_BASES']))+'</td><td>'+perc(a['UNALIGNED_BASES'],a['TOTAL_BASES'],1)+'</td></tr>'
  of.write(unaligned_bases_string+"\n")
  aligned_bases_string = '<tr><td>- Aligned bases</td><td>'+str(addcommas(a['ALIGNED_BASES']))+'</td><td>'+perc(a['ALIGNED_BASES'],a['TOTAL_BASES'],1)+'</td></tr>'
  of.write(aligned_bases_string+"\n")
  single_align_bases_string = '<tr><td>--- Single-aligned bases</td><td>'+str(addcommas(a['SINGLE_ALIGN_BASES']))+'</td><td>'+perc(a['SINGLE_ALIGN_BASES'],a['TOTAL_BASES'],1)+'</td></tr>'
  of.write(single_align_bases_string+"\n")
  gapped_align_bases_string = '<tr><td>--- Other-aligned bases</td><td>'+str(addcommas(a['GAPPED_ALIGN_BASES']))+'</td><td>'+perc(a['GAPPED_ALIGN_BASES'],a['TOTAL_BASES'],2)+'</td></tr>'
  of.write(gapped_align_bases_string+"\n")
  ostr = '''
    </table>
    <table class="right">
          <tr><td>Unaligned</td><td><div id="unaligned_leg" class="legend_square"></div></td></tr>
          <tr><td>Trans-chimeric alignment</td><td><div id="chimeric_leg" class="legend_square"></div></td></tr>
          <tr><td>Self-chimeric alignment</td><td><div id="selfchimeric_leg" class="legend_square"></div></td></tr>
          <tr><td>Gapped alignment</td><td><div id="gapped_leg" class="legend_square"></div></td></tr>
          <tr><td>Single alignment</td><td><div id="single_leg" class="legend_square"></div></td></tr>
    </table>
  </div>
  <div class="two_thirds left">
    <div class="rhead">Summary [<a href="plots/alignments.pdf">pdf</a>]</div>
    <img src="plots/alignments.png">
  </div>   
  <div class="clear"></div>
  <div class="one_half right">
    <div class="rhead">Exon counts of best alignments [<a href="plots/exon_size_distro.pdf">pdf</a>]</div>
    <img src="plots/exon_size_distro.png">
  </div>
'''
  of.write(ostr)
  if len(special['GN']) > 1:
    ostr = '''
  <div class="one_half left">
    <table class="one_half data_table">
      <tr class="rhead"><td colspan="5">Long read name information</td></tr>
      <tr><td>Type</td><td>Sub-type</td><td>Reads</td><td>Aligned</td><td>Fraction</td></tr>
'''
    of.write(ostr)
    for f in [x for x in special['GN'] if x[0] != 'Unclassified' or int(x[2])>0]:
      of.write('      <tr><td>'+f[0]+'</td><td>'+f[1]+'</td><td>'+addcommas(int(f[2]))+'</td><td>'+addcommas(int(f[3]))+'</td><td>'+perc(int(f[3]),int(f[2]),2)+'</td><tr>'+"\n")
    ostr = '''
    </table>
'''
    of.write(ostr)
    if 'PB' in special:
      # We have pacbio specific report
      pb = {}
      for f in special['PB']: pb[f[0]]=f[1]
      ostr = '''
      <div class="rhead">PacBio SMRT Cells [<a href="/plots/pacbio.pdf">pdf</a>]</div>
      <img src="plots/pacbio.png">
      <table class="horizontal_legend right">
        <tr><td>Aligned</td><td><div class="legend_square pacbio_aligned_leg"></div></td><td>Unaligned</td><td><div class="legend_square pacbio_unaligned_leg"></div></td></tr>
      </table>
      <table class="data_table one_half">
        <tr class="rhead"><td colspan="4">PacBio Stats</td></tr>
'''
      of.write(ostr)
      of.write('      <tr><td>Total Cell Count</td><td colspan="3">'+addcommas(int(pb['Cell Count']))+'</td></tr>')
      of.write('      <tr><td>Total Molecule Count</td><td colspan="3">'+addcommas(int(pb['Molecule Count']))+'</td></tr>')
      of.write('      <tr><td>Total Molecules Aligned</td><td colspan="3">'+addcommas(int(pb['Aligned Molecule Count']))+' ('+perc(pb['Aligned Molecule Count'],pb['Molecule Count'],2)+')</td></tr>')
      of.write('      <tr class="rhead"><td>Per-cell Feature</td><td>Min</td><td>Avg</td><td>Max</td></tr>')
      of.write('      <tr><td>Reads</td><td>'+addcommas(int(pb['Min Reads Per Cell']))+'</td><td>'+addcommas(int(pb['Avg Reads Per Cell']))+'</td><td>'+addcommas(int(pb['Max Reads Per Cell']))+'</td></tr>')
      of.write('      <tr><td>Molecules</td><td>'+addcommas(int(pb['Min Molecules Per Cell']))+'</td><td>'+addcommas(int(pb['Avg Molecules Per Cell']))+'</td><td>'+addcommas(int(pb['Max Molecules Per Cell']))+'</td></tr>')
      of.write('      <tr><td>Aligned Molecules</td><td>'+addcommas(int(pb['Min Aligned Molecules Per Cell']))+'</td><td>'+addcommas(int(pb['Avg Aligned Molecules Per Cell']))+'</td><td>'+addcommas(int(pb['Max Aligned Molecules Per Cell']))+'</td></tr>')
      ostr = '''        
      </table>
'''
      of.write(ostr)
    ostr = '''
  </div>
'''
    of.write(ostr)
  ostr = '''
</div>
<div class="clear"></div>
<hr>
<div class="result_block">
  <div class="subject_title">Annotation Analysis</div>
  <div class="one_half left">
    <div class="rhead">Distribution of reads among genomic features [<a href="plots/read_genomic_features.pdf">pdf</a>]</div>
    <img src="plots/read_genomic_features.png">
    <table class="one_half right horizontal_legend">
      <tr>
      <td>Exons</td><td><div class="exon_leg legend_square"></div></td><td></td>
      <td>Introns</td><td><div class="intron_leg legend_square"></div></td><td></td>
      <td>Intergenic</td><td><div class="intergenic_leg legend_square"></div></td><td></td>
      </tr>
    </table>
  </div>
  <div class="one_half right">
    <div class="rhead">Distribution of annotated reads [<a href="plots/annot_lengths.pdf">pdf</a>]</div>
    <img src="plots/annot_lengths.png">
    <table class="one_half right horizontal_legend">
      <tr>
      <td>Partial annotation</td><td><div class="partial_leg legend_square"></div></td><td></td>
      <td>Full-length</td><td><div class="full_leg legend_square"></div></td><td></td>
      <td>Unannotated</td><td><div class="unannotated_leg legend_square"></div></td><td></td>
      </tr>
    </table>
  </div>
  <div class="clear"></div>
  <div class="one_half right">
    <div class="rhead">Distribution of identified reference transcripts [<a href="plots/transcript_distro.pdf">pdf</a>]</div>
    <img src="plots/transcript_distro.png">
    <table class="one_half right horizontal_legend">
      <tr>
      <td>Partial annotation</td><td><div class="partial_leg legend_square"></div></td><td></td>
      <td>Full-length</td><td><div class="full_leg legend_square"></div></td><td></td>
      </tr>
    </table>
  </div>
  <div class="one_half left">
    <table class="data_table one_half">
      <tr class="rhead"><td colspan="5">Annotation Counts</td></tr>
      <tr><td>Feature</td><td>Evidence</td><td>Reference</td><td>Detected</td><td>Percent</td></tr>
'''
  of.write(ostr)
  cnt = len([x for x in ref_genes.keys() if sum(ref_genes[x])>0])
  of.write('      <tr><td>Genes</td><td>Any match</td><td>'+addcommas(len(ref_genes.keys()))+'</td><td>'+addcommas(cnt)+'</td><td>'+perc(cnt,len(ref_genes.keys()),2)+'</td></tr>'+"\n")
  cnt = len([x for x in ref_genes.keys() if ref_genes[x][1]>0])
  of.write('      <tr><td>Genes</td><td>Full-length</td><td>'+addcommas(len(ref_genes.keys()))+'</td><td>'+addcommas(cnt)+'</td><td>'+perc(cnt,len(ref_genes.keys()),2)+'</td></tr>'+"\n")
  cnt = len([x for x in ref_transcripts.keys() if sum(ref_transcripts[x])>0])
  of.write('      <tr><td>Transcripts</td><td>Any match</td><td>'+addcommas(len(ref_transcripts.keys()))+'</td><td>'+addcommas(cnt)+'</td><td>'+perc(cnt,len(ref_transcripts.keys()),2)+'</td></tr>'+"\n")
  cnt = len([x for x in ref_transcripts.keys() if ref_transcripts[x][1]>0])
  of.write('      <tr><td>Transcripts</td><td>Full-length</td><td>'+addcommas(len(ref_transcripts.keys()))+'</td><td>'+addcommas(cnt)+'</td><td>'+perc(cnt,len(ref_transcripts.keys()),2)+'</td></tr>'+"\n")
  ostr = '''
    </table>
    <table class="data_table one_half">
      <tr class="rhead"><td colspan="4">Top Genes</td></tr>
      <tr><td>Gene</td><td>Partial</td><td>Full-length</td><td>Total Reads</td></tr>
'''
  of.write(ostr)
  # get our top genes
  vs = reversed(sorted(ref_genes.keys(),key=lambda x: sum(ref_genes[x]))[-5:])
  for v in vs:
    of.write('      <tr><td>'+v+'</td><td>'+addcommas(ref_genes[v][0])+'</td><td>'+addcommas(ref_genes[v][1])+'</td><td>'+addcommas(sum(ref_genes[v]))+'</td></tr>'+"\n")
  ostr='''
    </table>
    <table class="data_table one_half">
      <tr class="rhead"><td colspan="5">Top Transcripts</td></tr>
      <tr><td>Transcript</td><td>Gene</td><td>Partial</td><td>Full-length</td><td>Total Reads</td></tr>
'''
  of.write(ostr)
  vs = reversed(sorted(ref_transcripts.keys(),key=lambda x: sum(ref_transcripts[x]))[-5:])
  for v in vs:
    of.write('      <tr><td>'+v+'</td><td>'+tx_to_gene[v]+'</td><td>'+addcommas(ref_transcripts[v][0])+'</td><td>'+addcommas(ref_transcripts[v][1])+'</td><td>'+addcommas(sum(ref_transcripts[v]))+'</td></tr>'+"\n")  
  ostr = '''
    </table>
  </div>
  <div class="clear"></div>
</div>
<hr>
<div class="subject_title">Coverage analysis &nbsp;&nbsp;&nbsp;&nbsp;<span class="highlight">'''
  of.write(ostr+"\n")
  of.write(perc(coverage_data['genome_covered'],coverage_data['genome_total'],2)+"\n")
  ostr = '''
  </span> <span class="highlight2">reference sequences covered</span>
</div>
<div class="result_block">
  <div class="one_half left">
    <div class="rhead">Coverage of reference sequences [<a href="plots/covgraph.pdf">pdf</a>]</div>
    <img src="plots/covgraph.png">
  </div>
  <div class="one_half left">
    <div class="rhead">Coverage distribution [<a href="plots/perchrdepth.pdf">pdf</a>]</div>
    <img src="plots/perchrdepth.png">
  </div>
  <div class="clear"></div>
  <div class="one_half left">
    <table class="data_table one_half">
      <tr class="rhead"><td colspan="4">Coverage statistics</td></tr>
      <tr><td>Feature</td><td>Feature (bp)<td>Coverage (bp)</td><td>Fraction</td><tr>
'''
  of.write(ostr)
  of.write('    <tr><td>Genome</td><td>'+addcommas(coverage_data['genome_total'])+'</td><td>'+addcommas(coverage_data['genome_covered'])+'</td><td>'+perc(coverage_data['genome_covered'],coverage_data['genome_total'],2)+'</td></tr>')
  of.write('    <tr><td>Exons</td><td>'+addcommas(coverage_data['exons_total'])+'</td><td>'+addcommas(coverage_data['exons_covered'])+'</td><td>'+perc(coverage_data['exons_covered'],coverage_data['exons_total'],2)+'</td></tr>')
  of.write('    <tr><td>Introns</td><td>'+addcommas(coverage_data['introns_total'])+'</td><td>'+addcommas(coverage_data['introns_covered'])+'</td><td>'+perc(coverage_data['introns_covered'],coverage_data['introns_total'],2)+'</td></tr>')
  of.write('    <tr><td>Intergenic</td><td>'+addcommas(coverage_data['intergenic_total'])+'</td><td>'+addcommas(coverage_data['intergenic_covered'])+'</td><td>'+perc(coverage_data['intergenic_covered'],coverage_data['intergenic_total'],2)+'</td></tr>')
  ostr = '''
    </table>
  </div>
  <div class="one_half right">
    <div class="rhead">Annotated features coverage [<a href="plots/feature_depth.pdf">pdf</a>]</div>
    <img src="plots/feature_depth.png">
    <table class="one_third right">
      <tr><td>Genome</td><td><div class="legend_square genome_cov_leg"></div></td>
          <td>Exons</td><td><div class="legend_square exon_cov_leg"></div></td>
          <td>Introns</td><td><div class="legend_square intron_cov_leg"></div></td>
          <td>Intergenic</td><td><div class="legend_square intergenic_cov_leg"></div></td></tr>
    </table>
  </div>
  <div class="one_half left">
    <div class="rhead">Bias in alignment to reference transcripts [<a href="plots/bias.pdf">pdf</a>]</div>
    <table>
  '''
  of.write(ostr)
  of.write('<tr><td colspan="2">Evidence from:</td></tr>')
  of.write('<tr><td>Total Transcripts</td><td>'+str(addcommas(bias_tx_count))+'</td></tr>'+"\n")
  of.write('<tr><td>Total reads</td><td>'+str(addcommas(bias_read_count))+'</td></tr>'+"\n")
  ostr='''
    </table>
    <img src="plots/bias.png">
  </div>
  <div class="clear"></div>
</div>
<hr>
<div class="subject_title"><table><tr><td class="c1">Rarefraction analysis</td><td class="c2"><span class="highlight">'''
  of.write(ostr)
  of.write(str(addcommas(geneany))+"\n")
  ostr = '''
  </span></td><td class="c3"><span class="highlight2">Genes detected</span></td><td class="c4"><span class="highlight">'''
  of.write(ostr)
  of.write(str(addcommas(genefull))+"\n")
  ostr = '''
  </span></td><td class="c5"><span class="highlight2">Full-length genes</span></td></tr></table>
</div>
<div class="result_block">
  <div class="one_half left">
    <div class="rhead">Gene detection rarefraction [<a href="plots/gene_rarefraction.pdf">pdf</a>]</div>
    <img src="plots/gene_rarefraction.png">
  </div>
  <div class="one_half left">
    <div class="rhead">Transcript detection rarefraction [<a href="plots/transcript_rarefraction.pdf">pdf</a>]</div>
    <img src="plots/transcript_rarefraction.png">
  </div>
  <div class="clear"></div>
  <div class="one_half left">
    <table class="data_table one_third">
      <tr><td class="rhead" colspan="3">Rarefraction stats</td></tr>
      <tr class="bold"><td>Feature</td><td>Criteria</td><td>Count</td></tr>'''
  of.write(ostr+"\n")
  of.write('<tr><td>Gene</td><td>full-length</td><td>'+str(addcommas(genefull))+'</td></tr>')
  of.write('<tr><td>Gene</td><td>any match</td><td>'+str(addcommas(geneany))+'</td></tr>')
  of.write('<tr><td>Transcript</td><td>full-length</td><td>'+str(addcommas(txfull))+'</td></tr>')
  of.write('<tr><td>Transcript</td><td>any match</td><td>'+str(addcommas(txany))+'</td></tr>')
  of.write('<tr><td>Locus</td><td></td><td>'+str(addcommas(locuscount))+'</td></tr>')
  ostr='''
    </table>
    <table id="rarefraction_legend">
      <tr><td>Any match</td><td><div class="rareany_leg legend_square"></div></td></tr>
      <tr><td>full-length</td><td><div class="rarefull_leg legend_square"></div></td></tr>
      <tr><td class="about" colspan="2">vertical line height indicates 5%-95% CI of simulation</td></tr>
    </table>
  </div>
  <div class="one_half left">
    <div class="rhead">Locus detection rarefraction [<a href="plots/gene_rarefraction.pdf">pdf</a>]</div>
    <img src="plots/locus_rarefraction.png">
  </div>
</div>
<div class="clear"></div>
<hr>
<div class="subject_title">Error pattern analysis &nbsp;&nbsp;&nbsp;&nbsp;<span class="highlight">'''
  of.write(ostr+"\n")
  error_rate = perc(e['ANY_ERROR'],e['ALIGNMENT_BASES'],3)
  of.write(error_rate)
  ostr='''
  </span> <span class="highlight2">error rate</span></div>
<div class="subject_subtitle">&nbsp; &nbsp; &nbsp; based on aligned segments</div>
<div class="result_block">
  <div class="full_length right">
    <div class="rhead">Error rates, given a target sequence [<a href="plots/context_plot.pdf">pdf</a>]</div>
    <img src="plots/context_plot.png">
  </div>
  <div class="clear"></div>
  <table class="data_table one_third left">
      <tr class="rhead"><td colspan="3">Alignment stats</td></tr>'''
  of.write(ostr+"\n")
  best_alignments_sampled_string = '<tr><td>Best alignments sampled</td><td>'+str(e['ALIGNMENT_COUNT'])+'</td><td></td></tr>'
  of.write(best_alignments_sampled_string+"\n")
  ostr = '''
      <tr class="rhead"><td colspan="3">Base stats</td></tr>'''
  of.write(ostr+"\n")
  bases_analyzed_string = '<tr><td>Bases analyzed</td><td>'+str(addcommas(e['ALIGNMENT_BASES']))+'</td><td></td></tr>'
  of.write(bases_analyzed_string+"\n")
  correctly_aligned_string = '<tr><td>- Correctly aligned bases</td><td>'+str(addcommas(e['ALIGNMENT_BASES']-e['ANY_ERROR']))+'</td><td>'+perc((e['ALIGNMENT_BASES']-e['ANY_ERROR']),e['ALIGNMENT_BASES'],1)+'</td></tr>'
  of.write(correctly_aligned_string+"\n")
  total_error_string = '<tr><td>- Total error bases</td><td>'+str(addcommas(e['ANY_ERROR']))+'</td><td>'+perc(e['ANY_ERROR'],e['ALIGNMENT_BASES'],3)+'</td></tr>'
  of.write(total_error_string+"\n")
  mismatched_string = '<tr><td>--- Mismatched bases</td><td>'+str(addcommas(e['MISMATCHES']))+'</td><td>'+perc(e['MISMATCHES'],e['ALIGNMENT_BASES'],3)+'</td></tr>'
  of.write(mismatched_string+"\n")
  deletion_string = '<tr><td>--- Deletion bases</td><td>'+str(addcommas(e['ANY_DELETION']))+'</td><td>'+perc(e['ANY_DELETION'],e['ALIGNMENT_BASES'],3)+'</td></tr>'
  of.write(deletion_string+"\n")
  complete_deletion_string = '<tr><td>----- Complete deletion bases</td><td>'+str(addcommas(e['COMPLETE_DELETION']))+'</td><td>'+perc(e['COMPLETE_DELETION'],e['ALIGNMENT_BASES'],3)+'</td></tr>'
  of.write(complete_deletion_string+"\n")
  homopolymer_deletion_string = '<tr><td>----- Homopolymer deletion bases</td><td>'+str(addcommas(e['HOMOPOLYMER_DELETION']))+'</td><td>'+perc(e['HOMOPOLYMER_DELETION'],e['ALIGNMENT_BASES'],3)+'</td></tr>'
  of.write(homopolymer_deletion_string+"\n")
  insertion_string = '<tr><td>--- Insertion bases</td><td>'+str(addcommas(e['ANY_INSERTION']))+'</td><td>'+perc(e['ANY_INSERTION'],e['ALIGNMENT_BASES'],3)+'</td></tr>'
  of.write(insertion_string+"\n")
  complete_insertion_string = '<tr><td>----- Complete insertion bases</td><td>'+str(addcommas(e['COMPLETE_INSERTION']))+'</td><td>'+perc(e['COMPLETE_INSERTION'],e['ALIGNMENT_BASES'],3)+'</td></tr>'
  of.write(complete_insertion_string+"\n")
  homopolymer_insertion_string = '<tr><td>----- Homopolymer insertion bases</td><td>'+str(addcommas(e['HOMOPOLYMER_INSERTION']))+'</td><td>'+perc(e['HOMOPOLYMER_INSERTION'],e['ALIGNMENT_BASES'],3)+'</td></tr>'
  of.write(homopolymer_insertion_string+"\n")
  ostr = '''
  </table>
  <div class="one_half left">
    <div class="rhead">Alignment-based error rates [<a href="plots/alignment_error_plot.pdf">pdf<a/>]</div>
    <img class="square_image" src="plots/alignment_error_plot.png">
  </div>
</div>
<div class="clear"></div>
<hr>
<div id="raw_data">
<table class="header_table">
  <tr><td class="rhead" colspan="4">Raw data</td></tr>
  <tr>
    <td>Read lengths:</td>
    <td class="raw_files"><a href="data/lengths.txt.gz">lengths.txt.gz</a></td>
  </tr>
  <tr>
    <td>Best genePred:</td>
    <td class="raw_files"><a href="data/best.sorted.gpd.gz">best.sorted.gpd.gz</a></td>
  </tr>
  <tr>
    <td>Gapped genePred:</td>
    <td class="raw_files"><a href="data/gapped.gpd.gz">gapped.gpd.gz</a></td>
  </tr>
  <tr>
    <td>Trans-chimeric genePred:</td>
    <td class="raw_files"><a href="data/chimera.gpd.gz">chimera.gpd.gz</a></td>
  </tr>
  <tr>
    <td>Self-chimeric genePred:</td>
    <td class="raw_files"><a href="data/technical_chimeras.gpd.gz">technical_chimeras.gpd.gz</a></td>
  </tr>
  <tr>
    <td>Other-chimeric genePred:</td>
    <td class="raw_files"><a href="data/technical_atypical_chimeras.gpd.gz">techinical_atypical_chimeras.gpd.gz</a></td>
  </tr>
  <tr>
    <td>Reference sequence lengths:</td>
    <td class="raw_files"><a href="data/chrlens.txt">chrlens.txt</a></td>
  </tr>
  <tr>
    <td>Coverage bed:</td>
    <td class="raw_files"><a href="data/depth.sorted.bed.gz">depth.sorted.bed.gz</a></td>
  </tr>
  <tr>
    <td>Loci basics bed:</td>
    <td class="raw_files"><a href="data/loci.bed.gz">loci.bed.gz</a></td>
  </tr>
  <tr>
    <td>Locus read data bed:</td>
    <td class="raw_files"><a href="data/loci-all.bed.gz">loci-all.bed.gz</a></td>
  </tr>
  <tr>
    <td>Locus rarefraction:</td>
    <td class="raw_files"><a href="data/locus_rarefraction.txt">locus_rarefraction.txt</a></td>
  </tr>
  <tr>
    <td>Read annotations:</td>
    <td class="raw_files"><a href="data/annotbest.txt.gz">annotbest.txt.gz</a></td>
  </tr>
  <tr>
    <td>Gene any match rarefraction:</td>
    <td class="raw_files"><a href="data/gene_rarefraction.txt">gene_rarefraction.txt</a></td>
  </tr>
  <tr>
    <td>Gene full-length rarefraction:</td>
    <td class="raw_files"><a href="data/gene_full_rarefraction.txt">gene_full_rarefraction.txt</a></td>
  </tr>
  <tr>
    <td>Transcript any match rarefraction:</td>
    <td class="raw_files"><a href="data/transcript_rarefraction.txt">transcript_rarefraction.txt</a></td>
  </tr>
  <tr>
    <td>Transcript full-length rarefraction:</td>
    <td class="raw_files"><a href="data/transcript_full_rarefraction.txt">transcript_full_rarefraction.txt</a></td>
  </tr>
  <tr>
    <td>Alignments stats raw report:</td>
    <td class="raw_files"><a href="data/alignment_stats.txt">alignment_stats.txt</a></td>
  </tr>
  <tr>
    <td>Alignment errors data:</td>
    <td class="raw_files"><a href="data/error_data.txt">error_data.txt</a></td>
  </tr>
  <tr>
    <td>Alignment error report:</td>
    <td class="raw_files"><a href="data/error_stats.txt">error_stats.txt</a></td>
  </tr>
  <tr>
    <td>Contextual errors data:</td>
    <td class="raw_files"><a href="data/context_error_data.txt">context_error_data.txt</a></td>
  </tr>
</table>
</div>
</body>
</html>
  '''
  of.write(ostr)

#Pre: numerator and denominator
#Post: percentage string
def perc(num,den,decimals=0):
  s = "{0:."+str(decimals)+"f}%"
  return s.format(100*float(num)/float(den))

def addcommas(val):
  return locale.format("%d",val,grouping=True)


def mycall(cmd,lfile):
  ofe = open(lfile+'.err','w')
  ofo = open(lfile+'.out','w')
  p = Popen(cmd.split(),stderr=ofe,stdout=ofo)
  p.communicate()
  ofe.close()
  ofo.close()
  return

def do_inputs():
  # Setup command line inputs
  parser=argparse.ArgumentParser(description="Create an output report",formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument('input',help="INPUT FILE or '-' for STDIN")
  parser.add_argument('-o','--output',help="OUTPUT Folder or STDOUT if not set")
  parser.add_argument('--portable_output',help="OUTPUT file in a portable html format")
  group1 = parser.add_mutually_exclusive_group(required=True)
  group1.add_argument('-r','--reference',help="Reference Fasta")
  group1.add_argument('--no_reference',action='store_true',help="No Reference Fasta")
  parser.add_argument('--annotation',help="Reference annotation genePred")
  parser.add_argument('--threads',type=int,default=1,help="INT number of threads to run. Default is system cpu count")
  # Temporary working directory step 1 of 3 - Definition
  parser.add_argument('--tempdir',required=True,help="This temporary directory will be used, but will remain after executing.")

  ### Parameters for alignment plots
  parser.add_argument('--min_aligned_bases',type=int,default=50,help="for analysizing alignment, minimum bases to consider")
  parser.add_argument('--max_query_overlap',type=int,default=10,help="for testing gapped alignment advantage")
  parser.add_argument('--max_target_overlap',type=int,default=10,help="for testing gapped alignment advantage")
  parser.add_argument('--max_query_gap',type=int,help="for testing gapped alignment advantge")
  parser.add_argument('--max_target_gap',type=int,default=500000,help="for testing gapped alignment advantage")
  parser.add_argument('--required_fractional_improvement',type=float,default=0.2,help="require gapped alignment to be this much better (in alignment length) than single alignment to consider it.")
  
  ### Parameters for locus analysis
  parser.add_argument('--min_depth',type=float,default=1.5,help="require this or more read depth to consider locus")
  parser.add_argument('--min_coverage_at_depth',type=float,default=0.8,help="require at leas this much of the read be covered at min_depth")
  parser.add_argument('--min_exon_count',type=int,default=2,help="Require at least this many exons in a read to consider assignment to a locus")

  ### Params for alignment error plot
  parser.add_argument('--alignment_error_scale',nargs=6,type=float,help="<ins_min> <ins_max> <mismatch_min> <mismatch_max> <del_min> <del_max>")
  parser.add_argument('--alignment_error_max_length',type=int,default=100000,help="The maximum number of alignment bases to calculate error from")
  
  ### Params for context error plot
  parser.add_argument('--context_error_scale',nargs=6,type=float,help="<ins_min> <ins_max> <mismatch_min> <mismatch_max> <del_min> <del_max>")
  parser.add_argument('--context_error_stopping_point',type=int,default=1000,help="Sample at least this number of each context")
  args = parser.parse_args()

  # Temporary working directory step 2 of 3 - Creation
  setup_tempdir(args)
  return args

def setup_tempdir(args):
  if not os.path.exists(args.tempdir):
    os.makedirs(args.tempdir.rstrip('/'))
  if not os.path.exists(args.tempdir):
    sys.stderr.write("ERROR: Problem creating temporary directory\n")
    sys.exit()
  return 

def external(args):
  main(args)

if __name__=="__main__":
  #do our inputs
  args = do_inputs()
  main(args)

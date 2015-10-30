import random, re
import SequenceBasics

class RandomBiallelicTranscriptomeEmitter:
  def __init__(self,transcriptome1,transcriptome2):
    self.transcriptome1 = transcriptome1
    self.transcriptome2 = transcriptome2
    self.em = RandomTranscriptomeEmitter(transcriptome1)
    self.transcriptome1_rho = {}
    # initialize rho to 0.5
    for n in transcriptome1.transcript_names:
      self.transcriptome1_rho[n] = 0.5

  def emit(self):
    [unique_name, name, seq] = self.em.emit()
    rnum = random.random()
    if rnum < self.transcriptome1_rho[unique_name]:
      return [unique_name, name, seq]
    return [unique_name,name, self.transcriptome2.transcripts[unique_name]]

  def emit_long_read(self):
    [unique_name, name, seq] = self.em.emit_long_read()
    rnum = random.random()
    if rnum < self.transcriptome1_rho[unique_name]:
      return [unique_name, name, seq]
    seq = self.transcriptome2.transcripts[unique_name]
    return [unique_name, name, random_flip(seq)]

  def emit_short_read(self,read_length):
    vals = self.em.emit_short_read(read_length)
    if not vals: return None
    [unique_name, name, seq] = vals
    rnum = random.random()
    if rnum < self.transcriptome1_rho[unique_name]:
      return [unique_name, name, seq]
    seq = random_fragment(self.transcriptome2.transcripts[unique_name],read_length)
    return [unique_name, name, random_flip(seq)]
    
def random_flip(seq):
  if random.random() < 0.5:
    return seq
  return SequenceBasics.rc(seq)

class RandomBiallelicGenomeEmitter:
  def __init__(self,genomefasta,vcffile):
    self.var_by_chr = {}
    with open(vcffile) as inf:
      for line in inf:
        line = line.rstrip()
        if re.match('^#',line): continue
        f = line.split("\t")
        chrom = f[0]
        pos = int(f[1])
        reference = f[3]
        alternate = f[4]
        if not chrom in self.var_by_chr:
          self.var_by_chr[chrom] = {}
        self.var_by_chr[chrom][pos] = {}
        self.var_by_chr[chrom][pos]['ref'] = reference
        self.var_by_chr[chrom][pos]['alt'] = alternate
    self.ref_genome = SequenceBasics.read_fasta_into_hash(genomefasta)

  def emit_genomes(self):
    phase = ''
    genome1 = ''
    genome2 = ''
    phase += "#Chromosome  Genome1Allele  Genome2Allele\n"
    for chrom in self.var_by_chr:
      if chrom not in self.ref_genome: continue
      seq_1 = list(self.ref_genome[chrom][:].upper()) #copy the chromosome
      seq_2 = list(self.ref_genome[chrom][:].upper())
      for pos in self.var_by_chr[chrom]:
        entry = self.var_by_chr[chrom][pos]
        rnum = random.random()
        if rnum < 0.5:
          seq_1[pos-1] = entry['ref']
          seq_2[pos-1] = entry['alt']
          phase += chrom + "\t" + str(pos) + "\t" + entry['ref'] + "\t" + entry['alt'] + "\n"
        else:
          seq_1[pos-1] = entry['alt']
          seq_2[pos-1] = entry['ref']
          phase += chrom + "\t" + str(pos) + "\t" + entry['alt'] + "\t" + entry['ref'] + "\n"
      genome1 += ">"+chrom+"\n"+''.join(seq_1)+"\n"
      genome2 += ">"+chrom+"\n"+''.join(seq_2)+"\n"
    return [genome1, genome2, phase]

class RandomTranscriptomeEmitter:
  def __init__(self,in_transcriptome):
    self.transcriptome = in_transcriptome
    self.transcript_names = self.transcriptome.transcript_names.keys()
    self.force_uniform_random = False

  def emit(self):
    lastname = self.transcriptome.get_uniform_random()
    if self.transcriptome.expression and not self.force_uniform_random:
      lastname = self.transcriptome.get_random_by_expression()
    return [lastname, self.transcriptome.transcript_names[lastname], self.transcriptome.transcripts[lastname]]

  def emit_long_read(self):
    [lastname, temp1, seq] = self.emit()
    seq = self.transcriptome.transcripts[lastname]
    rnum2 = random.random()
    if rnum2 < 0.5: seq = SequenceBasics.rc(seq)
    return [lastname, self.transcriptome.transcript_names[lastname], seq]

  def emit_short_read(self,read_length):
    [lastname, originalname, seq] = self.emit()
    seq = random_fragment(self.transcriptome.transcripts[lastname],read_length)
    return [lastname,originalname,random_flip(seq)]

def random_fragment(seq,frag_length):
  if frag_length > len(seq):
    return None
  startpoint = random.randint(0,len(seq)-frag_length)
  return seq[startpoint:startpoint+frag_length]

# emits a random nucleotide sequence
# user can set parameters one at a time as desired
#
# - set parameters
# set_gc_content(float default 0.5)
# set_sequence_length_range(min_len,max_len)
# set_sequence_length(length)
#
# emit()  - outputs the sequence
#
class RandomSequenceEmitter:
  def __init__(self):
    # some random settings
    self.sequence_length_min = 200
    self.sequence_length_max = 200
    self.gc_content = 0.5

  def emit(self):
    thislen = random.randint(self.sequence_length_min,self.sequence_length_max)
    o = ''
    for i in range(0,thislen): o += random_nucleotide_gc(self.gc_content)
    return o

  def set_length_range(self,minl,maxl):
    self.sequence_length_min = minl
    self.sequence_length_max = maxl

  def set_length(self,onelen):
    self.sequence_length_min = onelen
    self.sequence_length_max = onelen

  def set_gc_content(self,gc_content):
    self.gc_content = gc_content

def random_nucleotide_gc(gc_content):
  if random.random() < float(gc_content):
    if random.random() < 0.5: return 'G'
    return 'C'
  else:
    if random.random() < 0.5: return 'A'
    return 'T'

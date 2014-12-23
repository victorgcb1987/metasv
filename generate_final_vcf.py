#!/usr/bin/python

import argparse
import pybedtools
import pysam
import vcf
import logging

def convert_metasv_bed_to_vcf(bedfile = None, vcf_out = None, vcf_template = None, sample = None):
  vcf_template_reader = vcf.Reader(open(vcf_template, "r"))
  vcf_writer = vcf.Writer(open(vcf_out, "w"), vcf_template_reader)

  for interval in pybedtools.BedTool(bedfile):
    chrom = interval.chrom
    pos = interval.start
    end = interval.end

    sub_names = interval.name.split(":")
    sub_lengths = map(int, interval.fields[5].split(":"))

    sub_types = map(lambda x: x.split(",")[0], sub_names)
    sub_methods = [name.split(",")[2] for name in sub_names]
    svmethods = (";".join([name.split(",")[2] for name in sub_names])).split(";")

    index_to_use = 0
    should_ignore = False
    if "DEL" in sub_types:
      index_to_use = sub_types.index("DEL")
      svmethods_s = set(svmethods) - set(["SC"])
      if len(svmethods_s) == 1: continue
    elif "INV" in sub_types:
      index_to_use = sub_types.index("INV")
      svmethods_s = set(svmethods) - set(["SC"])
      if len(svmethods_s) == 1: continue
    elif "INS" in sub_types and "SC" in sub_methods:
      index_to_use = sub_methods.index("SC")

    svlen = sub_lengths[index_to_use]
    if sub_types[index_to_use] == "DEL":
      svlen = -svlen

    sv_type = sub_types[index_to_use]
    if sv_type == "INS":
      if end != pos + 1: continue
      end = pos
    sv_id = "."
    ref = "."
    alt = ["<%s>" % (sv_type)]
    qual = "."
    sv_filter = "."
    info = {"END": end, "SVLEN": svlen, "SVTYPE": sv_type, "SVMETHOD": svmethods}
    sv_format = "GT"
    sample_indexes = [0]
    samples = [vcf.model._Call(None, sample, ["1/1"])]
    vcf_record = vcf.model._Record(chrom, pos, sv_id, ref, alt, qual, sv_filter, info, sv_format, sample_indexes, samples)

    vcf_writer.write_record(vcf_record)

  vcf_writer.close()
  pysam.tabix_index(vcf_out, force = True, preset = "vcf")

if __name__ == "__main__":
  parser = argparse.ArgumentParser("Convert MetaSV final BED to VCF", formatter_class = argparse.ArgumentDefaultsHelpFormatter)

  parser.add_argument("--sample", help = "Sample name", required = True)
  parser.add_argument("--bed", help = "MetaSV final BED", required = True)
  parser.add_argument("--vcf", help = "Final VCF to output", required = True)
  parser.add_argument("--vcf_template", help = "VCF template", required = True)

  args = parser.parse_args()

  convert_metasv_bed_to_vcf(bedfile = args.bed, vcf_out = args.vcf, vcf_template = args.vcf_template, sample = args.sample)
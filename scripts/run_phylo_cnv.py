#!/usr/bin/python

# PhyloCNV - estimation of single-nucleotide-variants and gene-copy-number from shotgun sequence data
# Copyright (C) 2015 Stephen Nayfach
# Freely distributed under the GNU General Public License (GPLv3

__version__ = '0.0.2'

import argparse, sys, os

#def print_copyright(args):
#	# print out copyright information
#	print ("-------------------------------------------------------------------------")
#	print ("PhyloCNV - estimating the abundance, gene-content, and phylogeny of microbes from metagenomes")
#	print ("version %s; github.com/snayfach/PhyloCNV" % __version__)
#	print ("Copyright (C) 2015 Stephen Nayfach")
#	print ("Freely distributed under the GNU General Public License (GPLv3)")
#	print ("-------------------------------------------------------------------------")

def get_program():
	""" Get program specified by user (species, genes, or snvs) """
	if len(sys.argv) == 1 or sys.argv[1] in ['-h', '--help']:
		print('')
		print('Usage: phylo_cnv.py command [options]')
		print('')
		print('Commands:')
		print('\tspecies\t rapidly estimate the abundance of genome-clusters')
		print('\tgenes\t map reads to pangenomes of abundant genome-clusters')
		print('\tsnvs\t map reads to representative genomes and call SNVs')
		quit()
	elif sys.argv[1] not in ['species', 'genes', 'snvs']:
		sys.exit("Unrecognized command: '%s'" % sys.argv[1])
		quit()
	else:
		return sys.argv[1]

def get_arguments(program):
	""" Get arguments for specified program """
	if program == 'species':
		args = species_arguments()
	elif program == 'genes':
		args = pangenome_arguments()
	elif program == 'snvs':
		args = snv_arguments()
	else:
		sys.error("Unrecognized program: '%s'" % program)
	return args

def check_arguments(program, args):
	""" Run program specified by user (species, genes, or snvs) """
	if program == 'species':
		check_species(args)
	elif program == 'genes':
		check_genes(args)
	elif program == 'snvs':
		check_snvs(args)
	else:
		sys.error("Unrecognized program: '%s'" % program)

def run_program(program, args):
	""" Run program specified by user (species, genes, or snvs) """
	if program == 'species':
		from phylo_cnv import species
		species.estimate_abundance(args)
	elif program == 'genes':
		from phylo_cnv import cnvs
		cnvs.run_pipeline(args)
	elif program == 'snvs':
		from phylo_cnv import snvs
		snvs.run_pipeline(args)
	else:
		sys.error("Unrecognized program: '%s'" % program)
		
def species_arguments():
	""" Get arguments for metagenomic species profiling """
	parser = argparse.ArgumentParser(usage='phylo_cnv.py species [options]')
	parser.add_argument('program', help=argparse.SUPPRESS)
	parser.add_argument('-v', '--verbose', action='store_true', default=False)
	parser.add_argument('-1', type=str, dest='m1', help='FASTA/FASTQ file containing 1st mate if paired or unpaired reads', required=True)
	parser.add_argument('-2', type=str, dest='m2', help='FASTA/FASTQ file containing 2nd mate if paired')
	parser.add_argument('-o', type=str, dest='out', help='Path to output file', required=True)
	parser.add_argument('-k', dest='keep_temp', default=False, action='store_true', help='Keep temporary files, including BLAST output')
	parser.add_argument('-m', action='store_true', default=False, dest='norm', help='Estimate cellular relative abundance. Requires running MicrobeCensus and takes 20-30 minutes longer to complete.')
	parser.add_argument('-s', type=str, dest='speed', default='fast', choices=['fast','sensitive'], help='Alignment speed/sensitivity (fast)')
	parser.add_argument('-n', type=int, dest='reads', help='# reads to use from input file(s) (use all)')
	parser.add_argument('-t', dest='threads', default=1, help='Number of threads to use')
	args = vars(parser.parse_args())
	return args

def check_species(args):
	for arg in ['m1', 'm2']:
		if args[arg] and not os.path.isfile(args[arg]):
			sys.exit("\nInput file does not exist: '%s'" % args[arg])
	if not os.path.isdir(os.path.dirname(args['out'])):
		sys.exit("\nOutput directory does not exist: '%s'" % os.path.dirname(args['out']))

def pangenome_arguments():
	""" Get arguments for metagenomic pangenome profiling """
	parser = argparse.ArgumentParser(usage='phylo_cnv.py genes [options]')
	parser.add_argument('program', help=argparse.SUPPRESS)
	parser.add_argument('-v', '--verbose', action='store_true', default=False)
	parser.add_argument('--debug', action='store_true', default=False, help='Print out shell commands for debugging purposes')
	parser.add_argument('--tax_mask', action='store_true', default=False, help=argparse.SUPPRESS)
	parser.add_argument('--remove', choices=['bowtie2_db', 'bam'], nargs='*', help='Remove specified temporary files')
	
	io = parser.add_argument_group('Input/Output (required)')
	io.add_argument('-1', type=str, dest='m1', help='FASTA/FASTQ file containing 1st mate if paired or unpaired reads')
	io.add_argument('-2', type=str, dest='m2', help='FASTA/FASTQ file containing 2nd mate if paired')
	io.add_argument('-p', type=str, dest='profile', help='Path to species profile')
	io.add_argument('-o', type=str, dest='out', help='Path to output directory', required=True)

	pipe = parser.add_argument_group('Pipeline')
	pipe.add_argument('--all', action='store_true', dest='all',
		default=False, help='Run entire pipeline')
	pipe.add_argument('--build_db', action='store_true', dest='build_db',
		default=False, help='Build bowtie2 database of pangenomes')
	pipe.add_argument('--align', action='store_true', dest='align',
		default=False, help='Align reads to pangenome database')
	pipe.add_argument('--coverage', action='store_true', dest='cov',
		default=False, help='Compute coverage of genes in pangenome database')

	gc = parser.add_argument_group('Species to include in pangenome database')
	gc.add_argument('--gc_topn', type=int, dest='gc_topn', help='Top N most abundant (None)')
	gc.add_argument('--gc_cov', type=float, dest='gc_cov', help='Coverage threshold (None)')
	gc.add_argument('--gc_rbun', type=float, dest='gc_rbun', help='Relative abundance threshold (None)')
	gc.add_argument('--gc_id', type=str, dest='gc_id', help='Identifier of specific genome cluster or comma-separated list of ids (None)')
			
	speed = parser.add_argument_group('Alignment speed')
	speed.add_argument('-s', type=str, dest='speed', default='very-sensitive',
		choices=['very-fast', 'fast', 'sensitive', 'very-sensitive'],
		help='Alignment speed/sensitivity (very-sensitive)')
	speed.add_argument('-n', type=int, dest='reads', help='# reads to use from input file(s) (use all)')
	speed.add_argument('-t', dest='threads', default=1, help='Number of threads to use')
	
	map = parser.add_argument_group('Computing gene coverage')
	map.add_argument('--mapid', type=float, dest='mapid',
		default=93.0, help='Discard alignments with percent id < MAPID. Higher values indicate fewer mismatches allowed (93.0)')
	map.add_argument('--aln_cov', type=float, dest='aln_cov',
		default=0.70, help='Discard alignments where read coverage < ALN_COV. Higher values indicate that reads must be globally covered by alignment (0.70)')

	args = vars(parser.parse_args())
	if args['gc_id']: args['gc_id'] = args['gc_id'].split(',')
	
	return args

def snv_arguments():
	""" Get arguments for metagenomic pangenome profiling """
	parser = argparse.ArgumentParser(usage='phylo_cnv.py snvs [options]')
	parser.add_argument('program', help=argparse.SUPPRESS)
	parser.add_argument('-v', '--verbose', action='store_true', default=False)
	parser.add_argument('--debug', action='store_true', default=False, help='Print out shell commands for debugging purposes')
	parser.add_argument('--tax_mask', action='store_true', default=False, help=argparse.SUPPRESS)
	parser.add_argument('--remove', choices=['bowtie2_db', 'bam', 'vcf'], nargs='*', help='Remove specified temporary files')
	
	io = parser.add_argument_group('Input/Output (required)')
	io.add_argument('-1', type=str, dest='m1', help='FASTA/FASTQ file containing 1st mate if paired or unpaired reads')
	io.add_argument('-2', type=str, dest='m2', help='FASTA/FASTQ file containing 2nd mate if paired')
	io.add_argument('-p', type=str, dest='profile', help='Path to species profile')
	io.add_argument('-o', type=str, dest='out', help='Path to output directory', required=True)

	pipe = parser.add_argument_group('Pipeline')
	pipe.add_argument('--all', action='store_true', dest='all',
		default=False, help='Run entire pipeline')
	pipe.add_argument('--build_db', action='store_true', dest='build_db',
		default=False, help='Build bowtie2 database of pangenomes')
	pipe.add_argument('--align', action='store_true', dest='align',
		default=False, help='Align reads to pangenome database')
	pipe.add_argument('--pileup', action='store_true', dest='pileup',
		default=False, help='Run samtools mpileup')
	pipe.add_argument('--call', action='store_true', dest='call',
		default=False, help='Call SNPs and format output')
		
	gc = parser.add_argument_group('Species to include in representative genome database')
	gc.add_argument('--gc_topn', type=int, dest='gc_topn', help='Top N most abundant (None)')
	gc.add_argument('--gc_cov', type=float, dest='gc_cov', help='Coverage threshold (None)')
	gc.add_argument('--gc_rbun', type=float, dest='gc_rbun', help='Relative abundance threshold (None)')
	gc.add_argument('--gc_id', type=str, dest='gc_id', help='Identifier of specific genome cluster or comma-separated list of ids (None)')
			
	speed = parser.add_argument_group('Alignment speed')
	speed.add_argument('-s', type=str, dest='speed', default='very-sensitive',
		choices=['very-fast', 'fast', 'sensitive', 'very-sensitive'],
		help='Alignment speed/sensitivity (very-sensitive)')
	speed.add_argument('-n', type=int, dest='reads', help='# reads to use from input file(s) (use all)')
	speed.add_argument('-t', dest='threads', default=1, help='Number of threads to use')
	
	map = parser.add_argument_group('Read/base filters')
	map.add_argument('--mapid', type=float, dest='mapid',
		default=93.0, help='Discard alignments with percent id < MAPID. Higher values indicate fewer mismatches allowed (93.0)')
	map.add_argument('--mapq', type=str, dest='mapq',
		default=20, help='Minimum map quality (20)')
	map.add_argument('--baseq', type=str, dest='baseq',
		default=20, help='Minimum base quality (20)')

	args = vars(parser.parse_args())
	if args['gc_id']: args['gc_id'] = args['gc_id'].split(',')
	
	return args

def check_genes(args):
	""" Check validity of command line arguments """
	# pipeline options
	if not any([args['all'], args['build_db'], args['align'], args['cov']]):
		sys.exit("\nSpecify one or more pipeline option(s): --all, --build_db, --align, --cov")
	# turn on entire pipeline
	if args['all']:
		args['build_db'] = True
		args['align'] = True
		args['cov'] = True
	# no genome cluster selection options, but building db
	if (args['build_db']
		and not any([args['gc_id'], args['gc_topn'], args['gc_cov'], args['gc_rbun']])):
		error = "\nTo build a pangenome database, you must specify genome-clusters."
		error += "\nUse or or more of: --gc_id, --gc_topn, --gc_cov, and/or --gc_rbun"
		sys.exit(error)
	# genome cluster selection options, but not building db
	if (not args['build_db']
		and any([args['gc_id'], args['gc_topn'], args['gc_cov'], args['gc_rbun']])):
		error = "\nYou've specify genome-clusters, but are not building a database."
		error += "\nTry running with --build_db, or remove options: --gc_id, --gc_topn, --gc_cov, and --gc_rbun"
		sys.exit(error)
	# genome cluster selection options, but no no profile file
	if (args['gc_topn'] or args['gc_cov'] or args['gc_rbun']) and not args['profile']:
		sys.exit("\nTo specify genome-clusters with --gc_topn, --gc_cov, or --gc_rbun, you must supply a profile file with -p")
	# no database but --align specified
	if (args['align']
		and not args['build_db']
		and not os.path.isfile('%s/db/pangenomes.fa' % args['out'])):
		error = "\nYou've specified --align, but no database has been built"
		error += "\nTry running with --build_db"
		sys.exit(error)
	# no bamfile but --cov specified
	if (args['cov']
		and not args['align']
		and not os.path.isfile('%s/pangenome.bam' % args['out'])):
		error = "\nYou've specified --coverage, but no alignments were found"
		error += "\nTry running with --align"
		sys.exit(error)
	# no reads
	if args['align'] and not args['m1']:
		sys.exit("\nTo align reads, you must specify path to input FASTA/FASTQ")
	# check input file paths
	for arg in ['m1', 'm2', 'profile']:
		if args[arg] and not os.path.isfile(args[arg]):
			sys.exit("\nInput file does not exist: '%s'" % args[arg])
	# input options
	if args['m2'] and not args['m1']:
		sys.exit("\nMust specify -1 and -2 if aligning paired end reads")
	# sanity check input values
	if args['mapid'] < 1 or args['mapid'] > 100:
		sys.exit("\nMAPID must be between 1 and 100")
	if args['aln_cov'] < 0 or args['aln_cov'] > 1:
		sys.exit("\nALN_COV must be between 0 and 1")

def check_snvs(args):
	""" Check validity of command line arguments """
	# pipeline options
	if not any([args['all'], args['build_db'], args['align'], args['pileup'], args['call']]):
		sys.exit("\nSpecify one or more pipeline option(s): --all, --build_db, --align, --pileup, --call")
	# turn on entire pipeline
	if args['all']:
		args['build_db'] = True
		args['align'] = True
		args['pileup'] = True
		args['call'] = True
	# no genome cluster selection options, but building db
	if (args['build_db']
		and not any([args['gc_id'], args['gc_topn'], args['gc_cov'], args['gc_rbun']])):
		error = "\nTo build a genome database, you must specify genome-clusters."
		error += "\nUse or or more of: --gc_id, --gc_topn, --gc_cov, and/or --gc_rbun"
		sys.exit(error)
	# genome cluster selection options, but not building db
	if (not args['build_db']
		and any([args['gc_id'], args['gc_topn'], args['gc_cov'], args['gc_rbun']])):
		error = "\nYou've specify genome-clusters, but are not building a database."
		error += "\nTry running with --build_db, or remove options: --gc_id, --gc_topn, --gc_cov, and --gc_rbun"
		sys.exit(error)
	# genome cluster selection options, but no no profile file
	if (args['gc_topn'] or args['gc_cov'] or args['gc_rbun']) and not args['profile']:
		sys.exit("\nTo specify genome-clusters with --gc_topn, --gc_cov, or --gc_rbun, you must supply a profile file with -p")
	# no database but --align specified
	if (args['align']
		and not args['build_db']
		and not os.path.isfile('%s/db/genomes.fa' % args['out'])):
		error = "\nYou've specified --align, but no database has been built"
		error += "\nTry running with --build_db"
		sys.exit(error)
	# no bamfile but --pileup specified
	if (args['pileup']
		and not args['align']
		and not os.path.isfile('%s/genomes.bam' % args['out'])):
		error = "\nYou've specified --pileup, but no alignments were found"
		error += "\nTry running with --align"
		sys.exit(error)
	# no vcfile but --call specified
	if (args['call']
		and not args['pileup']
		and not os.path.isfile('%s/genomes.vcf' % args['out'])):
		error = "\nYou've specified --call, but no vcf file was found"
		error += "\nTry running with --pileup"
		sys.exit(error)
	# no reads
	if args['align'] and not args['m1']:
		sys.exit("\nTo align reads, you must specify path to input FASTA/FASTQ")
	# check input file paths
	for arg in ['m1', 'm2', 'profile']:
		if args[arg] and not os.path.isfile(args[arg]):
			sys.exit("\nInput file does not exist: '%s'" % args[arg])
	# input options
	if args['m2'] and not args['m1']:
		sys.exit("\nMust specify -1 and -2 if aligning paired end reads")
	# sanity check input values
	if args['mapid'] < 1 or args['mapid'] > 100:
		sys.exit("\nMAPQ must be between 1 and 100")
	if args['mapq'] < 0 or args['mapq'] > 100:
		sys.exit("\nMAPQ must be between 0 and 100")
	if args['baseq'] < 0 or args['baseq'] > 100:
		sys.exit("\nBASEQ must be between 0 and 100")

if __name__ == '__main__':

	program = get_program()
	args = get_arguments(program)
	check_arguments(program, args)
	run_program(program, args)
	




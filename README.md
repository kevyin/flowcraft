# assemblerflow

A [Nextflow](https://www.nextflow.io/) pipeline assembler for genomics data.
Pick your modules. Assemble them. Run the pipeline.

![Nextflow version](https://img.shields.io/badge/nextflow->0.26.0-brightgreen.svg)
![Python version](https://img.shields.io/badge/python-3.6-brightgreen.svg)
[![Build Status](https://travis-ci.org/ODiogoSilva/assemblerflow.svg?branch=master)](https://travis-ci.org/ODiogoSilva/assemblerflow)
[![codecov](https://codecov.io/gh/ODiogoSilva/assemblerflow/branch/master/graph/badge.svg)](https://codecov.io/gh/ODiogoSilva/assemblerflow)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/f518854f780b41a08ca2fb1c14e360f0)](https://www.codacy.com/app/o.diogosilva/assemblerflow?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=ODiogoSilva/assemblerflow&amp;utm_campaign=Badge_Grade)
[![Documentation Status](https://readthedocs.org/projects/assemblerflow/badge/?version=latest)](http://assemblerflow.readthedocs.io/en/latest/?badge=latest)
[![PyPI](https://img.shields.io/pypi/v/assemblerflow.svg)](https://pypi.python.org/pypi/assemblerflow/1.0.0rc3)

## The premisse

#### Build

What if building your own genomics pipeline would be as simple as:

```
assemblerflow.py build -t "trimmomatic fastqc skesa pilon" -o my_pipeline.nf
```

Seems pretty simple right? What if we could run this pipeline on any linux machine or cluster by leveraging
the awesomeness of [nextflow](https://www.nextflow.io/) and [docker](https://www.docker.com/)/[singularity](http://singularity.lbl.gov/)
containers without having to install any of the pipeline dependencies in a single command?

#### Run

```
nextflow run my_pipeline.nf --fastq path/to/fastq

N E X T F L O W  ~  version 0.28.0
Launching `my_pipeline` [prickly_mcnulty] - revision: 041b7b793f

============================================================
                M Y   P I P E L I N E
============================================================
Built using assemblerflow v1.0.2

 Input FastQ                 : 2
 Input samples               : 1
 Reports are found in        : ./reports
 Results are found in        : ./results
 Profile                     : standard

Starting pipeline at Sun Apr 08 18:22:24 WEST 2018

[warm up] executor > local
[7c/eb5f2f] Submitted process > integrity_coverage_1_1 (02AR0553)
(...)
[31/7d90a1] Submitted process > compile_pilon_report_1_6

Completed at: Sun Apr 08 18:43:41 WEST 2018
Duration    : 21m 17s
Success     : true
Exit status : 0
```

Congratulations! You just built and executed your own pipeline with
only two commands! :tada:

## Installation

## User guide

## Developer guide

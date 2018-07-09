#!/usr/bin/env python3

"""
Purpose
-------

This module is intended execute trimmomatic on paired-end FastQ files.

Expected input
--------------

The following variables are expected whether using NextFlow or the
:py:func:`main` executor.

- ``sample_id`` : Pair of FastQ file paths.
    - e.g.: ``'SampleA'``
- ``fastq_pair`` : Pair of FastQ file paths.
    - e.g.: ``'SampleA_1.fastq.gz SampleA_2.fastq.gz'``
- ``trim_range`` : Crop range detected using FastQC.
    - e.g.: ``'15 151'``
- ``opts`` : List of options for trimmomatic
    - e.g.: ``'["5:20", "3", "3", "55"]'``
    - e.g.: ``'[trim_sliding_window, trim_leading, trim_trailing, trim_min_length]'``
- ``phred`` : List of guessed phred values for each sample
    - e.g.: ``'[SampleA: 33, SampleB: 33]'``
- ``clear`` : If 'true', remove the input fastq files at the end of the
    component run, IF THE FILES ARE IN THE WORK DIRECTORY

Generated output
----------------

The generated output are output files that contain an object, usually a string.
(Values within ``${}`` are substituted by the corresponding variable.)

- ``${sample_id}_*P*``: Pair of paired FastQ files generated by Trimmomatic
    - e.g.: ``'SampleA_1_P.fastq.gz SampleA_2_P.fastq.gz'``
- ``trimmomatic_status``: Stores the status of the trimmomatic run. If it was\
    successfully executed, it stores 'pass'. Otherwise, it stores the \
    ``STDERR`` message.
    - e.g.: ``'pass'``

Code documentation
------------------

"""

# TODO: More control over read trimming
# TODO: Add option to remove adapters
# TODO: What to do when there is encoding failure

__version__ = "1.0.3"
__build__ = "29062018"
__template__ = "trimmomatic-nf"

import os
import re
import json
import fileinput
import subprocess

from subprocess import PIPE
from collections import OrderedDict

from flowcraft_utils.flowcraft_base import get_logger, MainWrapper

logger = get_logger(__file__)


def __get_version_trimmomatic():

    try:

        cli = ["java", "-jar", TRIM_PATH, "-version"]
        p = subprocess.Popen(cli, stdout=PIPE, stderr=PIPE)
        stdout, _ = p.communicate()

        version = stdout.strip().decode("utf8")

    except Exception as e:
        logger.debug(e)
        version = "undefined"

    return {
        "program": "Trimmomatic",
        "version": version,
    }


if __file__.endswith(".command.sh"):
    SAMPLE_ID = '$sample_id'
    FASTQ_PAIR = '$fastq_pair'.split()
    TRIM_RANGE = '$trim_range'.split()
    TRIM_OPTS = [x.strip() for x in '$opts'.strip("[]").split(",")]
    PHRED = '$phred'
    ADAPTERS_FILE = '$ad'
    CLEAR = '$clear'

    logger.debug("Running {} with parameters:".format(
        os.path.basename(__file__)))
    logger.debug("SAMPLE_ID: {}".format(SAMPLE_ID))
    logger.debug("FASTQ_PAIR: {}".format(FASTQ_PAIR))
    logger.debug("TRIM_RANGE: {}".format(TRIM_RANGE))
    logger.debug("TRIM_OPTS: {}".format(TRIM_OPTS))
    logger.debug("PHRED: {}".format(PHRED))
    logger.debug("ADAPTERS_FILE: {}".format(ADAPTERS_FILE))
    logger.debug("CLEAR: {}".format(CLEAR))

TRIM_PATH = "/NGStools/Trimmomatic-0.36/trimmomatic.jar"
ADAPTERS_PATH = "/NGStools/Trimmomatic-0.36/adapters"


def parse_log(log_file):
    """Retrieves some statistics from a single Trimmomatic log file.

    This function parses Trimmomatic's log file and stores some trimming
    statistics in an :py:class:`OrderedDict` object. This object contains
    the following keys:

        - ``clean_len``: Total length after trimming.
        - ``total_trim``: Total trimmed base pairs.
        - ``total_trim_perc``: Total trimmed base pairs in percentage.
        - ``5trim``: Total base pairs trimmed at 5' end.
        - ``3trim``: Total base pairs trimmed at 3' end.

    Parameters
    ----------
    log_file : str
        Path to trimmomatic log file.

    Returns
    -------
    x : :py:class:`OrderedDict`
        Object storing the trimming statistics.

    """

    template = OrderedDict([
        # Total length after trimming
        ("clean_len", 0),
        # Total trimmed base pairs
        ("total_trim", 0),
        # Total trimmed base pairs in percentage
        ("total_trim_perc", 0),
        # Total trimmed at 5' end
        ("5trim", 0),
        # Total trimmed at 3' end
        ("3trim", 0),
        # Bad reads (completely trimmed)
        ("bad_reads", 0)
    ])

    with open(log_file) as fh:

        for line in fh:
            # This will split the log fields into:
            # 0. read length after trimming
            # 1. amount trimmed from the start
            # 2. last surviving base
            # 3. amount trimmed from the end
            fields = [int(x) for x in line.strip().split()[-4:]]

            if not fields[0]:
                template["bad_reads"] += 1

            template["5trim"] += fields[1]
            template["3trim"] += fields[3]
            template["total_trim"] += fields[1] + fields[3]
            template["clean_len"] += fields[0]

        total_len = template["clean_len"] + template["total_trim"]

        if total_len:
            template["total_trim_perc"] = round(
                (template["total_trim"] / total_len) * 100, 2)
        else:
            template["total_trim_perc"] = 0

    return template


def write_report(storage_dic, output_file, sample_id):
    """ Writes a report from multiple samples.

    Parameters
    ----------
    storage_dic : dict or :py:class:`OrderedDict`
        Storage containing the trimming statistics. See :py:func:`parse_log`
        for its generation.
    output_file : str
        Path where the output file will be generated.
    """

    with open(output_file, "w") as fh, open(".report.json", "w") as json_rep:

        # Write header
        fh.write("Sample,Total length,Total trimmed,%,5end Trim,3end Trim,"
                 "bad_reads\\n")

        # Write contents
        for sample, vals in storage_dic.items():
            fh.write("{},{}\\n".format(
                sample, ",".join([str(x) for x in vals.values()])))

            json_dic = {
                "tableRow": [{
                    "sample": sample_id,
                    "data": [
                        {"header": "trimmed",
                         "value": vals["total_trim_perc"],
                         "table": "qc",
                         "columnBar": True},
                    ]
                }],
                "plotData": [{
                    "sample": sample_id,
                    "data": {
                        "sparkline": vals["clean_len"]
                    }
                }],
                "badReads": vals["bad_reads"]
            }
            json_rep.write(json.dumps(json_dic, separators=(",", ":")))


def trimmomatic_log(log_file, sample_id):

    log_storage = OrderedDict()

    log_id = log_file.rstrip("_trimlog.txt")

    log_storage[log_id] = parse_log(log_file)

    os.remove(log_file)

    write_report(log_storage, "trimmomatic_report.csv", sample_id)


def clean_up(fastq_pairs, clear):
    """Cleans the working directory of unwanted temporary files"""

    # Find unpaired fastq files
    unpaired_fastq = [f for f in os.listdir(".")
                      if f.endswith("_U.fastq.gz")]

    # Remove unpaired fastq files, if any
    for fpath in unpaired_fastq:
        os.remove(fpath)

    # Expected output to assess whether it is safe to remove temporary input
    expected_out = [f for f in os.listdir(".") if f.endswith("_trim.fastq.gz")]

    if clear == "true" and len(expected_out) == 2:
        for fq in fastq_pairs:
            # Get real path of fastq files, following symlinks
            rp = os.path.realpath(fq)
            logger.debug("Removing temporary fastq file path: {}".format(rp))
            if re.match(".*/work/.{2}/.{30}/.*", rp):
                os.remove(rp)


def merge_default_adapters():
    """Merges the default adapters file in the trimmomatic adapters directory

    Returns
    -------
    str
        Path with the merged adapters file.
    """

    default_adapters = [os.path.join(ADAPTERS_PATH, x) for x in
                        os.listdir(ADAPTERS_PATH)]
    filepath = os.path.join(os.getcwd(), "default_adapters.fasta")

    with open(filepath, "w") as fh, \
            fileinput.input(default_adapters) as in_fh:
        for line in in_fh:
            fh.write(line)

    return filepath


@MainWrapper
def main(sample_id, fastq_pair, trim_range, trim_opts, phred, adapters_file,
         clear):
    """ Main executor of the trimmomatic template.

    Parameters
    ----------
    sample_id : str
        Sample Identification string.
    fastq_pair : list
        Two element list containing the paired FastQ files.
    trim_range : list
        Two element list containing the trimming range.
    trim_opts : list
        Four element list containing several trimmomatic options:
        [*SLIDINGWINDOW*; *LEADING*; *TRAILING*; *MINLEN*]
    phred : int
        Guessed phred score for the sample. The phred score is a generated
        output from :py:class:`templates.integrity_coverage`.
    adapters_file : str
        Path to adapters file. If not provided, or the path is not available,
        it will use the default adapters from Trimmomatic will be used
    clear : str
        Can be either 'true' or 'false'. If 'true', the input fastq files will
        be removed at the end of the run, IF they are in the working directory
    """

    logger.info("Starting trimmomatic")

    # Create base CLI
    cli = [
        "java",
        "-Xmx{}".format("$task.memory"[:-1].lower().replace(" ", "")),
        "-jar",
        TRIM_PATH.strip(),
        "PE",
        "-threads",
        "$task.cpus"
    ]

    # If the phred encoding was detected, provide it
    try:
        # Check if the provided PHRED can be converted to int
        phred = int(phred)
        phred_flag = "-phred{}".format(str(phred))
        cli += [phred_flag]
    # Could not detect phred encoding. Do not add explicit encoding to
    # trimmomatic and let it guess
    except ValueError:
        pass

    # Add input samples to CLI
    cli += fastq_pair

    # Add output file names
    output_names = []
    for i in range(len(fastq_pair)):
        output_names.append("{}_{}_trim.fastq.gz".format(
            SAMPLE_ID, str(i + 1)))
        output_names.append("{}_{}_U.fastq.gz".format(
            SAMPLE_ID, str(i + 1)))
    cli += output_names

    if trim_range != ["None"]:
        cli += [
            "CROP:{}".format(trim_range[1]),
            "HEADCROP:{}".format(trim_range[0]),
        ]

    if os.path.exists(adapters_file):
        logger.debug("Using the provided adapters file '{}'".format(
            adapters_file))
    else:
        logger.debug("Adapters file '{}' not provided or does not exist. Using"
                     " default adapters".format(adapters_file))
        adapters_file = merge_default_adapters()

    cli += [
        "ILLUMINACLIP:{}:3:30:10:6:true".format(adapters_file)
    ]

    # Add trimmomatic options
    cli += [
        "SLIDINGWINDOW:{}".format(trim_opts[0]),
        "LEADING:{}".format(trim_opts[1]),
        "TRAILING:{}".format(trim_opts[2]),
        "MINLEN:{}".format(trim_opts[3]),
        "TOPHRED33",
        "-trimlog",
        "{}_trimlog.txt".format(sample_id)
    ]

    logger.debug("Running trimmomatic subprocess with command: {}".format(cli))

    p = subprocess.Popen(cli, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()

    # Attempt to decode STDERR output from bytes. If unsuccessful, coerce to
    # string
    try:
        stderr = stderr.decode("utf8")
    except (UnicodeDecodeError, AttributeError):
        stderr = str(stderr)

    logger.info("Finished trimmomatic subprocess with STDOUT:\\n"
                "======================================\\n{}".format(stdout))
    logger.info("Finished trimmomatic subprocesswith STDERR:\\n"
                "======================================\\n{}".format(stderr))
    logger.info("Finished trimmomatic with return code: {}".format(
        p.returncode))

    trimmomatic_log("{}_trimlog.txt".format(sample_id), sample_id)

    clean_up(fastq_pair, clear)

    # Check if trimmomatic ran successfully. If not, write the error message
    # to the status channel and exit.
    with open(".status", "w") as status_fh:
        if p.returncode != 0:
            status_fh.write("fail")
            return
        else:
            status_fh.write("pass")


if __name__ == '__main__':

    main(SAMPLE_ID, FASTQ_PAIR, TRIM_RANGE, TRIM_OPTS, PHRED, ADAPTERS_FILE,
         CLEAR)

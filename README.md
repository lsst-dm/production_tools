
Rubin Production Tools
====

This is an interface to error reports and pipeline logs during production pipeline runs. 

The daily error report is generated from JSON files stored in a Google cloud storage bucket, and are
the output of a logging filter which selects only messages with error serverity. The messages are
then grouped by run, and then similar error messages are combined so that they are displayed only
once with a list of all matching dataIds following.

The log interface displays logs from a Butler repository, after selecting by collection name and
data id fields.

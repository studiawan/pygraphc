#/bin/bash

# example search via Splunk API
python search.py --username=admin "search source=dec-1.log host=box sourcetype=linux_secure | cluster labelfield=cluster_id labelonly=t | table cluster_id _raw | sort _time | reverse" --output_mode=csv > ~/dec-1-perline.csv
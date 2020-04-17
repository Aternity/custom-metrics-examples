# !/bin/bash

# Hello World example of calling the Custom Metrics REST API using curl.

# Note: the following example assumes the curl commands are being run locally 
# on a system with a v11.4+ Aternity APM agent installed. If not, replace 
# localhost with the agent's host:port and ensure the agent is accessible to 
# remote clients.

# First, you'll need to define a metric. This is done by hitting the "/metric" 
# endpoint. The following example command defines a metric with the id 
# "hello-world-curl". It also provides a display name, description and unit for
# the metric.
curl -k -X POST -H 'Content-type:application/json' -d '{"metric-definitions": [{"metric-id": "hello-world-curl", "display-name": "Hello World Curl", "description": "Metric from Hello World Curl Example", "units": "count", "version": 1}]}' https://localhost:7074/Aternity/CustomMetrics/1.0.0/metric

# Next, you'll want to publish metric values (samples) by hitting the 
# "/samples" endpoint. The following example command publishes a single metric 
# sample to the "hello-world-curl" metric previously defined. The value is a
# random number, $RANDOM, and the timestamp is the current timestamp in 
# seconds: $(date +%s). It also sets a single dimension: "myDimension:test-1".
curl -k -X PUT -H 'Content-type:application/json' -d '{"metric-samples": [{"metric-id": "hello-world-curl", "dimensions": {"myDimension": "test-1"}, "tags": {}, "timestamp": ['$(date +%s)'], "value": ['$RANDOM'], "source": "curl"}]}' https://localhost:7074/Aternity/CustomMetrics/1.0.0/samples

# Finally, login to the Aternity APM UI. Your data will be available on the 
# 'Custom Metrics' tab.
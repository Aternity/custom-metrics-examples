# Hello World example of calling the Custom Metrics REST API using Python

import time
import random
import requests

# Host of port where Aternity APM agent is install. This example assumes the
# agent is local. If not, replace localhost with the agent's hostname and 
# ensure the agent is accessible to remote clients.
HOST = "localhost"  # Hostname of where 
PORT = 7074
BASE_URL = 'https://%s:%s/Aternity/CustomMetrics/1.0.0' % (HOST, PORT)


def helloWorldPython():
    """
    Add a random number every minute for five minutes
    """

    # First, you'll need to define a metric. This is done by hitting the 
    # "/metric" endpoint. The following example defines a metric with the id 
    # "hello-world-python". It also provides a display name, description and
    # unit for the metric.
    metric_definition = {
        "version": 1,
        "metric-id": "hello-world-python",
        "display-name": "Hello World Python",
        "description": "Metric from Hello World Python Example",
        "units": "count"
    }

    # POST the metric definition to the Aternity APM agent
    requests.post(BASE_URL + "/metric", json={"metric-definitions": [metric_definition]}, verify=False)

    for i in range(5):

        timestamp = int(time.time())
        value = random.randint(1,10)

        # Next, you'll want to publish metric values (samples) by hitting the 
        # "/samples" endpoint. The following example publishes a single metric
        # sample to the "hello-world-python" metric previously defined. The 
        # value is a random number and the timestamp is the current timestamp 
        # in seconds. It also sets a single dimension: "myDimension:test-1".
        sample = {
            "metric-id": "hello-world-python",
            "source": "python",
            "timestamp": [timestamp],
            "value": [value],
            "dimensions":{
                "myDimension": "test-1"
            },
            "tags":{}
        }

        # PUT the metric sample to the Aternity APM agent
        requests.put(BASE_URL + "/samples", json={"metric-samples": [sample]}, verify=False)

        print("  - Metric sample published. Sleeping 60s...")
        
        # Sleep for 60 seconds
        time.sleep(60)

    return

if __name__ == "__main__":
    print("Starting Custom Metrics Hello World Python Example...")
    helloWorldPython()

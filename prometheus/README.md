# Code adapted from
https://github.com/prometheus/prometheus/tree/master/documentation/examples/remote_storage/remote_storage_adapter

# Remote storage adapter

This is a write adapter that receives samples via Prometheus's remote write
protocol and stores them in Graphite, InfluxDB, or OpenTSDB. It is meant as a
replacement for the built-in specific remote storage implementations that have
been removed from Prometheus.

For InfluxDB, this binary is also a read adapter that supports reading back
data through Prometheus via Prometheus's remote read protocol.

## Prereqsuisite
1. You have an existing Prometheus instance
2. You have your own container image repository
3. You have an Aternity APM Agent(11.4.3+) running and connected to your Aternity APM Analysis Server

## This is experimental
Running this in production environment `at your own risk`!!

## Build

for plain binary
```bash
go build -o remote-storage-adapter main.go
```

for docker image
```bash
docker build . -t YOUR_IMAGE_REPO/atny-remote-storage-adapter:0.1.0
```

## Running locally

`variables in [] are optional`

Running the binary on a host
```bash
# CMX_AGENT_HOSTNAME is an ip/DNS record to your Aternity APM CMX agent
# CMX_AGENT_PORT is usually 7074
[REGION=YOUR_REGION] [ENV=YOUR_ENV_NAME] ./remote_storage_adapter --atny-url=https://ATERNITY_APM_AGENT_HOST:APM_AGENT_PORT/
```

Running as docker container
```bash
# CMX_AGENT_HOSTNAME is an ip/DNS record to your Aternity APM CMX agent
# CMX_AGENT_PORT is usually 7074
docker run [-e REGION=us-east-1] [-e ENV=latest] YOUR_IMAGE_REPO/atny-remote-storage-adapter:0.1.0 --atny-url=https://ATERNITY_APM_AGENT_HOST:APM_AGENT_PORT/ [--atny-cmx-dimensions="extraDim0,Dim0Val,extraDim1,Dim1Val"]
```

Running in Kubernetes
```bash
# assuming the environment you run this command has proper set up in ~/.kube/config,
# using the yaml template we provide
kubectl apply -f ./remote_storage_adapter.yaml
```

## Configuring Prometheus

To configure Prometheus to send samples to this binary, add the following to your `prometheus.yml`:

`Make sure you only use one of the following url:`
```yaml
remote_write:
    # if you run remote storage adapter on an arbitrary host outside your k8s, make sure your prometheus server is able to reach it
    - url: http://HOSTNAME:9201/write

    # if you run remote storage adapter on k8s cluster:
    # SERVICE_NAME is the name of the remote storage adapter service
    # NAMESPACE is the name of the NAMESPACE where you run this remote storage adapter
    - url: http://SERVICE_NAME.NAMESPACE/write

    # if you deploy using the remote-storage-adapter.yaml we provide and didn't change the K8s Service manifest, you can use:
    - url: http://prometheus-remote-storage-adapter.monitoring/write
```

## Viewing the K8s dashboard in Aternity APM WebUI

We have a starting K8s dashboard for you to play around with.

1. Make sure you are have permission to modify CMX dashboard

2. Click "Create New Dashboard"

3. In the new CMX dashboard, click the gear button and "Edit JSON"

4. Copy and paste the content of `dashboard.json` in this repo to the dialog.

5. Save the dashboard


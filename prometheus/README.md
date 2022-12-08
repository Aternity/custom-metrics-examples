# Prometheus remote storage adapter for Alluvio Aternity APM

This is an experimental write adapter that receives samples via Prometheus's remote write protocol and stores them in [Alluvio Aternity APM](https://www.riverbed.com/products/application-performance-monitoring). 

The code is based on [Prometheus remote_storage_adapter example](https://github.com/prometheus/prometheus/tree/master/documentation/examples/remote_storage/remote_storage_adapter). *remote_storage_adapter* is meant as a replacement for the built-in specific remote storage implementations that have been removed from Prometheus.

## Prerequisite

1. Docker host or Kubernetes cluster with a container image repository
2. a running Prometheus instance
3. an Aternity APM account (SaaS) - see [Trials for Alluvio Aternity](https://www.riverbed.com/trial-download/alluvio-aternity)
3. a running Aternity APM Agent exposing CMX (default port 7074)

## Build

for plain binary
```bash
go build -o remote-storage-adapter main.go
```

for docker image
```bash
docker build . -t YOUR_IMAGE_REPO/atny-remote-storage-adapter:0.1.0
```

## Running

Configure args and variables:

* YOUR_ATERNITY_AGENT_HOST is an ip/DNS record to your Aternity APM CMX agent
* YOUR_CMX_PORT is the CMX port, usually 7074
* YOUR_ENV_NAME and YOUR_REGION are optional for tagging metrics with ENV and REGION

Running the binary on a host

```bash
[REGION=YOUR_REGION] [ENV=YOUR_ENV_NAME] ./remote_storage_adapter --atny-url=https://YOUR_ATERNITY_AGENT_HOST:YOUR_CMX_PORT/ [--atny-cmx-dimensions="extraDim0,Dim0Val,extraDim1,Dim1Val"]
```

> **Note**
> [...] parts are optional

For example

```bash
REGION=francecentral ENV=prod ./remote_storage_adapter --atny-url=https://aternity_agent_cmx:7074/
```

### Running as docker container

```bash
docker run [-e REGION=YOUR_REGION] [-e ENV=YOUR_ENV_NAME] YOUR_IMAGE_REPO/atny-remote-storage-adapter:0.1.0 --atny-url=https://YOUR_ATERNITY_AGENT_HOST:YOUR_CMX_PORT/ [--atny-cmx-dimensions="extraDim0,Dim0Val,extraDim1,Dim1Val"]
```

> **Note**
> [...] parts are optional

### Running in Kubernetes

Configure the [yaml template](remote-storage-adapter.yaml)

```bash
kubectl apply -f ./remote_storage_adapter.yaml
```

## Configuring Prometheus

To configure Prometheus to send samples to this binary, add the following to your `prometheus.yml`:

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

> **Warning**
> Make sure you only use one url

## Viewing in Aternity APM WebUI in a custom dashboard

We have a starting custom dashboard, "K8s dashboard", for you to play around with.

1. Make sure you are have permission to modify Custom Dashboards

2. Click "Create New Dashboard"

3. In the new CMX dashboard, click the gear button and "Edit JSON"

4. Copy and paste the content of [dashboard.json](dashboard.json) to the dialog.

5. Save the dashboard


### License

Copyright (c) 2022 Riverbed Technology, Inc.

The contents provided here are licensed under the terms and conditions of the MIT License accompanying the software ("License"). The scripts are distributed "AS IS" as set forth in the License. The script also include certain third party code. All such third party code is also distributed "AS IS" and is licensed by the respective copyright holders under the applicable terms and conditions (including, without limitation, warranty and liability disclaimers) identified in the license notices accompanying the software.
# Riverbed APM - Custom Metrics Examples

The Custom Metrics REST API and Java SDK allow users to extend the support of custom metrics beyond the out-of-the-box plugins that ship with [Alluvio Aternity APM](https://www.riverbed.com/products/application-performance-monitoring). This repo provides various examples of how to publish custom metrics.

For a quick start, have a look to the examples:

- [hello-world](hello-world)
- [Prometheus](prometheus)
- [cmx-q](cmx-q)
- [availability-monitor](availability-monitor)
- [dashboards](dashboards)

## REST API

Each Aternity APM agent (v11.4+) locally exposes a REST API for collecting Custom Metrics. The API specification is available in this repo as `swagger.yaml`. 

To publish metrics, first define the metric and then start pushing samples (values). See `hello-world/rest-api/` for a simple example.

## Java SDK

Custom Metrics also provides a Java SDK to make it easy to publish metrics from your Java applications. Like the REST API, when using the Java SDK you'll first define a metric and then start pushing samples (values). See `hello-world/java-sdk/` for a simple example.

> **Note**
> Using the Java SDK requires `cmxsdk.jar` and `AwUtil.jar` which are provided with the Aternity APM agent. 


## Custom Metrics Data Model

Metrics are stored as a time-ordered set of data points (a time series).  Basically a metric is a variable you would like to monitor over time which can provide insights into application behavior or the user experience. CPU usage, a count of messages in a queue, or the number of widgets produced are examples of metrics to monitor.

Each metric is uniquely identified by an *id* and a set of *dimensions*. The metric id is a string that identifies a particular type of metric (e.g. server-cpu-usage). Dimensions are a set of string key-value pairs that describe the source publishing values to the metric (e.g. server-cpu-usage for server=app1 vs server=app2).  Changing the set of dimensions or the value of a dimension is equivalent to creating a new metric.  Dimensions also determine how Aternity APM will aggregate data. Aggregations are performed across dimensions for metrics having the same id.

Consider the example of metric id `widgets-produced` with the dimensions `worker` and `product`.

```
id = widgets-produced,  dimensions = [worker : james, product: foo],  timestamps = [1, 2, ...], values = [10, 20, ...]
id = widgets-produced,  dimensions = [worker : sally, product: foo],  timestamps = [1, 2, ...], values = [15,  0, ...]
id = widgets-produced,  dimensions = [worker : sally, product: bar],  timestamps = [1, 2, ...], values = [ 0, 20, ...]
```

Aternity APM will collect and process the values for these three distinct metrics.  We could then query to see the values published for a specific metric, like the number of widgets produced by the `worker` *sally* for the `product` *bar*.  Since Aternity APM performs aggregations across dimensions for metrics having the same id we could also query for things like the number of widgets produced across all `workers` for all `products`, or by all of the `workers` for just `product` *foo*.

Dimensions with many unique values, like session ids or raw URLs, are often poor choices as they result in the creation of a large number of metrics and computations. Consider only adding dimensions with a smaller number of unique values like regions, servers or URL paths instead of raw URLs.  

### License

Copyright (c) 2022 Riverbed Technology, Inc.

The contents provided here are licensed under the terms and conditions of the MIT License accompanying the software ("License"). The scripts are distributed "AS IS" as set forth in the License. The script also include certain third party code. All such third party code is also distributed "AS IS" and is licensed by the respective copyright holders under the applicable terms and conditions (including, without limitation, warranty and liability disclaimers) identified in the license notices accompanying the software.

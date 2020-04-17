# To configure:
There are three values yaml files provided. There is one for each endpoint scraper helm deployment.  
  
valuesksm.yaml = kube-state-metrics scraper  
valuescadvisor.yaml = cAdvisor scraper  
valueskubelet.yaml = kubelet scaper  

```
Edit valuesksm.yaml, valuescadvisor.yaml and valueskubelet.yaml file with values appropriate for your environment. The following environmental values may need to be modified to fit your environment, however defaults are included that work with most environments:
```

Example environmental values for kube-state-metrics from the valuesksm.yaml file:  
```  
env:  
    pesync:  
        RVBD_DSAPORT: 7074  
        METRIC_URL: "http://kube-state-metrics.default.svc.cluster.local:8080/metrics"  
        AUTH_TOKEN: ""  
        AUTH_TOKEN_PATH: "/var/run/secrets/kubernetes.io/serviceaccount/token"  
        API_NAME: "KSM"  
        IS_DAEMONSET: false  
        LABEL_MAPPINGS: "{}"  
        DIMENSIONED_LABELS: "['*']"  
```		
RVBD_DSAPORT is the port idenfier for the AppInternals agent running on the node. This should not need to be changed.  
METRIC_URL is the endpoint URL of the service that provides the metric information.  
AUTH_TOKEN is the bearer authentication token that should be used when accessing the service. Typically this should be empty as the credentials will be read from the AUTH_TOKEN_PATH variable. If needed, paste the bearer token to be used here. 
AUTH_TOKEN_PATH is the path to the file that contains the authentication token that should be used when accessing the service.  
API_NAME is the name of the metrics API endpoint. Metrics are pushed to AppInternals in the format pe/<API_NAME>/<metric_name>.  
IS_DAEMONSET controls if the deployment is done via a daemonset. This should not need to be changed.  
LABEL_MAPPINGS can be used to map one metric label to another label name.    
For example:  
```
LABEL_MAPPINGS: "{'container_label_io_kubernetes_pod_name': 'pod_name'}"  
```  
will map the container_label_io_kubernetes_pod_name to the label pod_name.  
  
DIMENSIONED_LABELS allow you to control what labels are used as dimensions. '*' means all labels are dimensioned.  
For example: 
```
DIMENSION_LABELS: "['container','pod','node']  
```
will cause only the container, pod and node labels to be used as dimensions in the AppInternals metrics.  

# To install:
Once the configuration is complete the scrapers can be installed:  
  
## To install kube-state-metrics scraper:
```
helm install pesync --generate-name -f valuesksm.yaml
```
## To install cAdvisor scraper: 
```
helm install pesync --generate-name -f valuescadvisor.yaml
```
## To install kubelet scraper:  
```
helm install pesync --generate-name -f valueskubelet.yaml
```

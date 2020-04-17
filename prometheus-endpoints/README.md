### Prometheus endpoint scraper for AppInternals Custom Metrics
  
The purpose of this project is to scrape endpoints that publish their metrics information in Prometheus metrics format as defined here: https://prometheus.io/docs/concepts/data_model and push them into AppInternals Analysis Server.  
Example endpoints that can be scraped are cAdvsor, kube-state-metrics and kubelet endpoints.
  
See the kubernetes/helm directory for directions on how to install the scraper containers using helm.  
See the dashboards directory for directions on how to install the various available dashboards into the AppInternals Analysis Server.

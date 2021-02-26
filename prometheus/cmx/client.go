// Copyright 2013 The Prometheus Authors
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

package cmx

import (
	"bytes"
	"context"
	"crypto/tls"
	"encoding/json"
	"io"
	"io/ioutil"
	"math"
	"net/http"
	"net/url"
	"sync"
	"time"

	"github.com/go-kit/kit/log"
	"github.com/go-kit/kit/log/level"
	"github.com/pkg/errors"
	"github.com/prometheus/common/model"
)

const (
	putEndpoint     = "/Riverbed-Technology/CustomMetrics/1.0.0"
	contentTypeJSON = "application/json"
)

// Client allows sending batches of Prometheus samples to CMX.
type Client struct {
	logger log.Logger

	url        string
	timeout    time.Duration
	dimensions map[string]TagValue
}

var metricDefinitions map[string]bool = make(map[string]bool)
var metricDefinitionMutex sync.RWMutex

// NewClient creates a new Client.
func NewClient(logger log.Logger, url string, timeout time.Duration, dimensions map[string]TagValue) *Client {
	http.DefaultTransport.(*http.Transport).TLSClientConfig = &tls.Config{InsecureSkipVerify: true}
	return &Client{
		logger:     logger,
		url:        url,
		timeout:    timeout,
		dimensions: dimensions,
	}
}

type metricDefinition struct {
	Version     int    `json:"version"`
	MetricID    string `json:"metric-id"`
	DisplayName string `json:"display-name"`
	Description string `json:"description"`
	Units       string `json:"units"`
}

// StoreMetricDefinitionsRequest is used for building a JSON request for storing samples
// via the CMX.
type StoreMetricDefinitionsRequest struct {
	MetricDefinitions []metricDefinition `json:"metric-definitions"`
}

type metricSample struct {
	MetricID   string              `json:"metric-id"`
	Source     string              `json:"source"`
	Timestamp  []int64             `json:"timestamp"`
	Value      []float64           `json:"value"`
	Dimensions map[string]TagValue `json:"dimensions"`
	Tags       map[string]TagValue `json:"tags"`
}

// StoreSamplesRequest is used for building a JSON request for storing samples
// via the CMX.
type StoreSamplesRequest struct {
	MetricSamples []metricSample `json:"metric-samples"`
}

// tagsFromMetric translates Prometheus metric into CMX tags.
func tagsFromMetric(m model.Metric) map[string]TagValue {
	tags := make(map[string]TagValue, len(m)-1)
	for l, v := range m {
		if l == model.MetricNameLabel {
			continue
		}
		tags[string(l)] = TagValue(v)
	}
	return tags
}

func (c *Client) putMetricDef(mdreq StoreMetricDefinitionsRequest, u *url.URL) error {
	// post metric definitions
	buf, err := json.Marshal(mdreq)
	if err != nil {
		return err
	}

	ctx, cancel := context.WithTimeout(context.Background(), c.timeout)
	defer cancel()
	level.Info(c.logger).Log("msg", "pushing new metric definitions to", "url", u.String()+"/metric", "len", len(mdreq.MetricDefinitions))
	req, err := http.NewRequest("POST", u.String()+"/metric", bytes.NewBuffer(buf))
	if err != nil {
		level.Info(c.logger).Log("msg", "error post new metric definitions", "err", err)
		return err
	}
	req.Header.Set("Content-Type", contentTypeJSON)
	resp, err := http.DefaultClient.Do(req.WithContext(ctx))
	if err != nil {
		level.Info(c.logger).Log("msg", "error do new metric definitions", "err", err)
		return err
	}
	defer func() {
		io.Copy(ioutil.Discard, resp.Body)
		resp.Body.Close()
	}()

	// API returns status code 200 for successful writes.
	if resp.StatusCode == http.StatusOK {
		level.Info(c.logger).Log("msg", "success pushing new metric definitions")
	} else {
		level.Info(c.logger).Log("msg", "error pushing new metric definitions")
	}

	// API returns status code 400 on error, encoding error details in the
	// response content in JSON.
	buf, err = ioutil.ReadAll(resp.Body)
	if err != nil {
		return err
	}
	//var r map[string]int
	//if err := json.Unmarshal(buf, &r); err != nil {
	//	return err
	//}
	return nil
}

func (c *Client) putMetricSamples(reqs StoreSamplesRequest, u *url.URL) (*http.Response, error) {
	level.Info(c.logger).Log("msg", "pushing new metric samples", "url", u.String()+"/samples", "len", len(reqs.MetricSamples))
	buf, err := json.Marshal(reqs)
	if err != nil {
		level.Info(c.logger).Log("msg", "error marshal new metric samples", err)
		return nil, err
	}

	ctx, cancel2 := context.WithTimeout(context.Background(), c.timeout)
	defer cancel2()

	req, err := http.NewRequest("PUT", u.String()+"/samples", bytes.NewBuffer(buf))
	if err != nil {
		level.Info(c.logger).Log("msg", "error creating put new metric samples request", err)
		return nil, err
	}
	req.Header.Set("Content-Type", contentTypeJSON)
	resp, err := http.DefaultClient.Do(req.WithContext(ctx))
	if err != nil {
		level.Info(c.logger).Log("msg", "error do new metric samples", err)
		return nil, err
	}
	defer func() {
		io.Copy(ioutil.Discard, resp.Body)
		resp.Body.Close()
	}()

	return resp, nil
}

// Write sends a batch of samples to CMX via its HTTP API.
func (c *Client) Write(samples model.Samples) error {
	//level.Info(c.logger).Log("msg", "write called")
	metricDefinitionMutex.Lock()
	defer metricDefinitionMutex.Unlock()
	reqs := StoreSamplesRequest{}
	mdreq := StoreMetricDefinitionsRequest{}
	for _, s := range samples {
		v := float64(s.Value)
		if math.IsNaN(v) || math.IsInf(v, 0) {
			level.Debug(c.logger).Log("msg", "Cannot send value to CMX, skipping sample", "value", v, "sample", s)
			continue
		}
		metric := s.Metric[model.MetricNameLabel]
		dimensions := tagsFromMetric(s.Metric)
		for k, kv := range c.dimensions {
			dimensions[k] = kv
		}
		sample := metricSample{
			MetricID:   string(metric),
			Source:     string("prometheus"),
			Timestamp:  []int64{s.Timestamp.Unix()},
			Value:      []float64{v},
			Tags:       tagsFromMetric(s.Metric),
			Dimensions: dimensions,
		}
		reqs.MetricSamples = append(reqs.MetricSamples, sample)

		if metricDefinitions[string(metric)] == false {
			md := metricDefinition{
				Version:     1,
				MetricID:    string(metric),
				DisplayName: string(metric),
				Description: string("prometheus"),
				Units:       "count"}

			mdreq.MetricDefinitions = append(mdreq.MetricDefinitions, md)
			level.Info(c.logger).Log("msg", "Adding new metric definition", "id", string(metric))
			metricDefinitions[string(metric)] = true
		}
	}

	u, err := url.Parse(c.url)
	if err != nil {
		return err
	}

	u.Path = putEndpoint

	if len(mdreq.MetricDefinitions) > 0 {
		err = c.putMetricDef(mdreq, u)
		if err != nil {
			return err
		}
	}

	// post samples
	if len(reqs.MetricSamples) > 0 {
		resp2, err2 := c.putMetricSamples(reqs, u)

		if err2 != nil {
			return err2
		}

		// API returns status code 200 for successful writes.
		if resp2.StatusCode == http.StatusOK {
			level.Info(c.logger).Log("msg", "success pushing new metric samples")
			return nil
		}

		// PUT /samples returns 404 when metricDef doesn't exist - happens when cmx server restart while using the global session
		if resp2.StatusCode == http.StatusNotFound {
			level.Info(c.logger).Log("msg", "metric definition doesn't exist, recreating..")

			for _, s := range samples {
				metric := s.Metric[model.MetricNameLabel]
				md := metricDefinition{
					Version:     1,
					MetricID:    string(metric),
					DisplayName: string(metric),
					Description: string("prometheus"),
					Units:       "count"}

				mdreq.MetricDefinitions = append(mdreq.MetricDefinitions, md)
			}
			err = c.putMetricDef(mdreq, u)
			if err != nil {
				level.Error(c.logger).Log("msg", "fail to recreate metric definition.", "err", err)
				return err
			}

			// retry sending samples
			resp2, err2 = c.putMetricSamples(reqs, u)
			if err2 != nil {
				return err2
			}
		}

		level.Info(c.logger).Log("msg", "error pushing new metric samples", "code", resp2.StatusCode)

		// API returns status code 400 on error, encoding error details in the
		// response content in JSON.
		buf, err_read := ioutil.ReadAll(resp2.Body)
		level.Info(c.logger).Log("msg", "resp pushing new metric samples", "buf", buf)
		if err_read != nil {
			return err_read
		}

		var r2 map[string]int
		//if err2 := json.Unmarshal(buf2, &r2); err2 != nil {
		//	return err2
		//	}

		return errors.Errorf("failed to write %d samples to CMX, %d succeeded", r2["failed"], r2["success"])
	}
	return nil
}

// Name identifies the client as a CMX client.
func (c Client) Name() string {
	return "cmx"
}

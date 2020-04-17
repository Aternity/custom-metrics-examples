
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import os
import re
import json
import time
import datetime
import dateutil.tz
import dateutil.parser
import pytz
import requests
import logging
import parser
import base64
from collections import defaultdict

try:
    import StringIO
except ImportError:
    # Python 3
    import io as StringIO

CMX_SERVER_BASE_URL = 'https://%s/Riverbed-Technology/CustomMetrics/1.0.0'
CMX_SERVER_PORT = 443
USE_SESSION = False

logger = None
CURRENTTIME = int(time.time())

mappings = {}
all_metric_definitions = {}
prev_samples = {}
dimensioned_labels = {}

if not os.path.exists('pe_sync.state'):
    with open('pe_sync.state', 'w') as f:
        json.dump({}, f)

def setup_logging(log_level):

    global logger
    
    if logger:
        return

    FORMAT = "%(asctime)s : %(levelname)7s : %(message)s"

    consoleLogHandler = logging.StreamHandler()
    consoleLogHandler.setLevel(log_level)
    consoleLogHandler.setFormatter(logging.Formatter(FORMAT))

    fileLogHandler = logging.FileHandler('./pe_sync.log')
    fileLogHandler.setLevel(log_level)
    fileLogHandler.setFormatter(logging.Formatter(FORMAT))

    logger = logging.getLogger("pe-sync")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(consoleLogHandler)
    logger.addHandler(fileLogHandler)

    return

def pe_get_units_for_metric(metric):

    fields = metric.split("_")
    lfpos = len(fields)-1
    lf = fields[lfpos]
    if lf == "seconds":
        return 'seconds'
    elif lf == "bytes":
        return 'bytes'
    elif lf == "count":
        return 'count'
    elif "_bytes_" in metric:
        return 'bytes'
    elif "_seconds_" in metric:
        return 'seconds'

    return '#'

def synthesize_metrics(pe_host, source, cmx_server, metric, sample, samples, synth_samples):
    global prev_samples
    metric_name = metric.name
    #print metric_name

    if metric_name == "container_cpu_usage_seconds" or metric_name == "container_spec_cpu_quota" or metric_name == "container_spec_cpu_period":
        synth_metric_name = "pe/SYNTH/container_cpu_usage_pct"
        if sample.labels.get("id", None) == None:
            return
        k = createkey(pe_host, metric_name, source, sample.labels["id"])
        synth_samples[k] = sample
        k = createkey(pe_host, "container_cpu_usage_seconds", source, sample.labels["id"])
        ccuss = synth_samples.get(k, None)
        k = createkey(pe_host, "container_spec_cpu_quota", source, sample.labels["id"])
        cscqs = synth_samples.get(k, None)
        k = createkey(pe_host, "container_spec_cpu_period", source, sample.labels["id"])
        cscps = synth_samples.get(k, None)

        if ccuss != None and cscqs != None and cscps != None:
            ccus = float(ccuss.value)
            cscq = float(cscqs.value)
            cscp = float(cscps.value)

            if ccus == ccus and cscq == cscq and cscp == cscp and cscq > 0 and cscp > 0:
                #logger.debug("CREATING SYNTH CPU")
                k = createkey(pe_host, "container_cpu_usage_seconds", source, ccuss.labels)
                prevs = prev_samples.get(k, None)
                if prevs != None:
                    prev_ccuss = prevs.value
                    #logger.debug(ccus)
                    #logger.debug(prev_ccuss)
                    if ccus < prev_ccuss:
                        logger.error("WHEN CALCULATING CPU %s < %s", ccuss, prev_samples)
                        return
                    #logger.debug(ccus)
                    #logger.debug(cscq)
                    #logger.debug(cscp)
                
                    #v = 100.0 * (ccus/(cscq/cscp))
 
                    v = 100.0 * ((ccus - prev_ccuss)/cscq)
                    md = build_metric_definition(synth_metric_name, synth_metric_name, "Container CPU Usage Percentage", units="%")
                    all_metric_definitions[synth_metric_name] = md
                    samples.append(build_sample(synth_metric_name, source, [ccuss.timestamp], [v], ccuss.labels))
                    #logger.debug("CPU PCT=%s", str(v))
    if metric_name == "container_memory_rss" or metric_name == "container_spec_memory_limit_bytes":
        synth_metric_name = "pe/SYNTH/container_rss_usage_pct"
        if sample.labels.get("id", None) == None:
            return
        k = createkey(pe_host, metric_name, source, sample.labels)
        synth_samples[k] = sample
        #print sample
        k = createkey(pe_host, "container_memory_rss", source, sample.labels)
        cmrs = synth_samples.get(k, None)
        k = createkey(pe_host, "container_spec_memory_limit_bytes", source, sample.labels)
        csmlbs = synth_samples.get(k, None)

        if cmrs != None and csmlbs != None:

            cmr = float(cmrs.value)
            csmlb = float(csmlbs.value)      

            if cmr == cmr and csmlb == csmlb and csmlb > 0:
                v = 100.0 * (cmr/csmlb)
                md = build_metric_definition(synth_metric_name, synth_metric_name, "Container Memory RSS Usage Percentage", units="%")
                all_metric_definitions[synth_metric_name] = md
                samples.append(build_sample(synth_metric_name, source, [cmrs.timestamp], [v], cmrs.labels))
                #logger.debug("RSS PCT=%s", str(v))
    if metric_name == "container_memory_rss" or metric_name == "container_spec_memory_reservation_limit_bytes":
        synth_metric_name = "pe/SYNTH/container_rss_reservation_usage_pct"
        if sample.labels.get("id", None) == None:
            return
        k = createkey(pe_host, metric_name, source, sample.labels["id"])
        synth_samples[k] = sample
        k = createkey(pe_host, "container_memory_rss", source, sample.labels["id"])
        cmrs = synth_samples.get(k, None)
        k = createkey(pe_host, "container_spec_memory_reservation_limit_bytes", source, sample.labels["id"])
        csmlbs = synth_samples.get(k, None)

        if cmrs != None and csmlbs != None:
            cmr = float(cmrs.value)
            csmlb = float(csmlbs.value)    
            if cmr == cmr and csmlb == csmlb and csmlb > 0:
                v = 100.0 * (cmr/csmlb)
                md = build_metric_definition(synth_metric_name, synth_metric_name, "Container Memory RSS Reservation Usage Percentage", units="%")
                all_metric_definitions[synth_metric_name] = md
                samples.append(build_sample(synth_metric_name, source, [cmrs.timestamp], [v], cmrs.labels))
                #logger.debug("REQ RSS PCT=%s", str(v))
    if metric_name == "container_fs_usage_bytes" or metric_name == "container_fs_limit_bytes":
        synth_metric_name = "pe/SYNTH/container_fs_usage_pct"
        if sample.labels.get("id", None) == None:
            return
        if sample.labels.get("device", None) == None:
            return

        k = createkey(pe_host, metric_name, source, sample.labels)
        synth_samples[k] = sample
        k = createkey(pe_host, "container_fs_usage_bytes", source, sample.labels)
        cmrs = synth_samples.get(k, None)
        k = createkey(pe_host, "container_fs_limit_bytes", source, sample.labels)
        csmlbs = synth_samples.get(k, None)

        if cmrs != None and csmlbs != None:
            cmr = float(cmrs.value)
            csmlb = float(csmlbs.value)      

            if cmr == cmr and csmlb == csmlb and csmlb > 0:
                v = 100.0 * (cmr/csmlb)
                md = build_metric_definition(synth_metric_name, synth_metric_name, "Container File System Usage Percentage", units="%")
                all_metric_definitions[synth_metric_name] = md
                samples.append(build_sample(synth_metric_name, source, [cmrs.timestamp], [v], cmrs.labels))
                #logger.debug("FS PCT=%s", str(v))

def appinternals_get_units_for_metric(metric):

    if 'count' in metric:
        return 'count'

    elif 'duration' in metric:
        return 'milliseconds'

    elif 'period' in metric:
        return 'milliseconds'

    elif 'cpu_quota' in metric:
        return 'milliseconds'       
    return 'count'
 
def pretty_print_POST(req):
    print('{}\n{}\n{}\n\n{}'.format(
        '-----------BEGIN REQUEST-----------',
        req.method + ' ' + req.url,
        '\n'.join('{}: {}'.format(k, v) for k, v in req.headers.items()),
        req.body,
    ))

def do_debug_request(session, method, url, payload=None):
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    #r = requests.post(url, data=json.dumps(payload), headers=headers)
    bare = requests.Request(method, url, data=json.dumps(payload), headers=headers)
    prepared = bare.prepare()
    pretty_print_POST(prepared)
 
    r = session.send(prepared, verify=False, timeout=5)
    if not r:
        logger.debug("Unable to add samples to %s. Giving up", url)
        logger.debug("Request payload = %s", payload)
        raise Exception("Unable to add samples. Giving up")
    return r.status_code

def do_request(session, method, url, payload=None):
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    #r = requests.post(url, data=json.dumps(payload), headers=headers)
    bare = requests.Request(method, url, data=json.dumps(payload), headers=headers)
    prepared = bare.prepare()

    num_tries = 0
    r = None
    while num_tries < 3:
        num_tries += 1
        try:
            r = session.send(prepared, verify=False, timeout=5)
        except Exception as e:
            logger.debug("Exception encountered in posting! [e=%s]", e)
            time.sleep(1)
        else:
            break

    if not r:
        logger.debug("Unable to add samples to %s. Giving up", url)
        logger.debug("Request payload = %s", payload)
        raise Exception("Unable to add samples. Giving up")
        
    if r.status_code != 200:
        logger.debug("Request failed with code '%d'. [URL=%s] with payload: %s", r.status_code, url, payload)

    return r.status_code

def start_session(cmx_server, source, containerID, sessionID=None):
    
    session = requests.session()

    base_url = CMX_SERVER_BASE_URL % cmx_server

    if sessionID is None:
        r = session.post(base_url+"/session", json={'source': source, 'containerId': containerID}, verify=False)
    else:
        # restart old session
        r = session.put(base_url+"/session/%s" % sessionID, json={"source": source, "containerId": containerID}, verify=False)
    if r.status_code != 200:
        logger.debug("Request failed with code '%d'", r.status_code)    
    return session

def add_metric(cmx_server, session, metric_definitions):
    t = time.time()
    starttime = t
    base_url = CMX_SERVER_BASE_URL % cmx_server

    # {"metric-definitions":[{"version":1,"metric-id":"m1","display-name":"MDef 1","description":"","units":"count"}]}
    ret = do_request(session, "POST", base_url+"/metric", metric_definitions)
    t = time.time()
    endtime = t
    logger.debug("ADDING METRICS TOOK %d SECONDS", endtime-starttime)
    return ret

def add_samples(cmx_server, session, metric_samples):
    t = time.time()
    starttime = t
    base_url = CMX_SERVER_BASE_URL % cmx_server

    ret = do_request(session, "PUT", base_url+"/samples", metric_samples)
    t = time.time()
    endtime = t
    logger.debug("ADDING SAMPLES TOOK %d SECONDS", endtime-starttime)
    return ret

def build_metric_definition(name, mID, description='', units='count'):

    # {"version":1,"metric-id":"m1","display-name":"MDef 1","description":"","units":"count"}
    return {
        "version": 1,
        "metric-id": mID,
        "display-name": name,
        "description": description,
        "units": units
        }

def build_sample(metric_id, source, timestamps=None, values=None, dimensions=None, tags=None):

    global CURRENTTIME
    ptimestamps=[]
    # {"metric-samples":[{"metric-id":"m1","source":"arout","timestamp":[1568213885],"value":[123.456],"dimensions":{},"tags":{}}]
    if timestamps is None:
        timestamps = [CURRENTTIME]
    for ts in timestamps:
        if ts == None:
            ts = CURRENTTIME
        ptimestamps.append(int(ts))

    if values is None:
        values = [] 

    mappeddimensions = {}
    if dimensions:
        for key, v in dimensions.items():
            if "*" in dimensioned_labels or key in dimensioned_labels:
                mappedkey = mappings.get(key, None)
                if mappedkey != None:
                    #logger.debug("ADDING NEW MAPPED %s %s", str(mappedkey), str(v))
                    mappeddimensions[mappedkey] = v
                mappeddimensions[key] = v

    return {
        "metric-id": metric_id,
        "source":source,
        "timestamp":ptimestamps,
        "value":values,
        "dimensions":{} if not mappeddimensions else mappeddimensions,
        "tags":{} if not tags else tags
    }

def fetch_data_from_pe(pe_host, auth_token, api_name):
    url = "%s" % pe_host
    
    try:
        logger.debug("GETTING DATA FROM URL %s", url)
        r = requests.get("%s" % (url), headers={"Authorization": auth_token}, verify=False, timeout=50)
    except Exception as e:
        logger.warning("Request to pe failed. [e=%s]", e)
        return None

    try:
        response = r.text
    except Exception as e:
        logger.error("Exception fetching data from pe! [e=%s]. status_code=%d. Response text=%s", e, r.status_code, r.text)
        return None

    return response
    
def num(s):
    return float(s)

def createkey(pe_host, metric_name, source, labels):
    k = pe_host + metric_name + source + str(labels)
    k = hash(k)

    return k

def pull_and_push_pe_data(session, cmx_server, pe_host, pe_auth_token, pe_auth_token_file, api_name): #cmx_server, api_name, metrics, attributes, order_by=None, start_str=None, end_str=None):

    global CURRENTTIME
    global prev_samples

    logger.debug("Fetching data for %s at %d", api_name, CURRENTTIME)

    if pe_auth_token_file and pe_auth_token_file != "":
        #logger.debug("OPENING AUTH TOKEN FILE %s", pe_auth_token_file)
        fo = open(pe_auth_token_file, "r")
        pe_auth_token = "BEARER " + fo.readline()
        fo.close()

    pe_data = fetch_data_from_pe(pe_host, pe_auth_token, api_name)
    if not pe_data:
        logger.debug("No data to process")
        return False
    
    source = "pe"
    
    # create all of the metrics every time.
    # it's harmless to create the metric definition again, so always do it
    samples = []
    synth_samples = {}
    next_prev_samples = {}
    
    pe_data = StringIO.StringIO(pe_data.encode().decode('ascii'))
    try:
        pmetrics = parser.text_fd_to_metric_families(pe_data)
    except Exception as e:
        logger.error("Exception parsing %s [%s]", str(e), str(pe_data.getvalue()))
        return False
        
    for metric in pmetrics:
        metric_name = "pe/%s/%s" % (api_name, metric.name)
        md = all_metric_definitions.get(metric_name, None)
        if md == None:
            #logger.debug("metric %s not found. adding", metric_name)
            md = build_metric_definition(metric_name, metric_name, metric.documentation, units=pe_get_units_for_metric(metric.name))
            all_metric_definitions[metric_name] = md
        for sample in metric.samples:
            try:
                synthesize_metrics(pe_host, source, cmx_server, metric, sample, samples, synth_samples)
                v=num(sample.value)
                if v == v:
                    s = build_sample(metric_name, source, [sample.timestamp], [v], sample.labels)

                    samples.append(s)
                    if metric.typ == "counter":
                        # make a delta metric
                        k = createkey(pe_host, metric.name, source, sample.labels)
                        prevs = prev_samples.get(k, None)
                        next_prev_samples[k] = sample
                        
                        if prevs != None:
                            prevv = prevs.value
                            if v < prevv:
                                logger.error("BAD COUNT VALUE FOR METRIC " + metric_name + str(v) + "<" + str(prevv))
                                logger.error("CUR=" + str(sample))
                                logger.error("PRV=" + str(prevs))
                                continue
                            delta_metric_name = metric_name + "_delta"
                            md = all_metric_definitions.get(delta_metric_name, None)
                            if md == None:
                                md = build_metric_definition(delta_metric_name, delta_metric_name, metric.documentation, units=pe_get_units_for_metric(metric.name))
                                all_metric_definitions[delta_metric_name] = md

                            s = build_sample(delta_metric_name, source, [sample.timestamp], [v-prevv], sample.labels)
                            samples.append(s)

            except Exception as e:
                logger.error("Could not convert value [%s] %s %s %s", sample.value, e, metric_name, sample)


    prev_samples.update(next_prev_samples)  
    logger.debug("There are %d counter samples", len(prev_samples.keys())) 
    logger.debug("Adding %d metric definitions to cmx server %s at %d...", len(all_metric_definitions), cmx_server, CURRENTTIME)

    if len(all_metric_definitions) > 0:
        add_metric(cmx_server, session, {"metric-definitions": list(all_metric_definitions.values())})

    logger.debug("Adding %d samples to cmx server %s at %d...", len(samples), cmx_server, CURRENTTIME)
   
    if len(samples) > 0:
        add_samples(cmx_server, session, {"metric-samples": samples})

    return True

def process_pe_realm(session, cmx_server, pe_realm):

    logger.debug("Fetching pe data from URL %s...", pe_realm['METRIC_URL'])
    api = pe_realm['API_NAME']
    logger.debug("Fetching pe data from api %s...", api)

    pull_and_push_pe_data(
        session,
        cmx_server, 
        pe_realm['METRIC_URL'], 
        pe_realm.get('AUTH_TOKEN'), 
        pe_realm.get('AUTH_TOKEN_PATH'), 
        api
    )

    return True

def expand_env(env):

    fullenv = env
    while fullenv:
        spos = env.find("{env")

        if spos == -1:
            break

        epos = env.find("}", spos)
        if epos == -1:
            break

        newenv = env[spos+5:epos]
        print(newenv)
        newenv = os.environ.get(newenv, None)
        if newenv:
            print(newenv)
            fullenv = env[0:spos] + str(newenv) + env[epos+1:]
            env = fullenv
        else:
            break

    print(fullenv)
    return fullenv


def parse_config():
    config = {}
    config['RVBD_DSAHOST'] = expand_env(os.environ['RVBD_DSAHOST'])
    print(config)
    config['RVBD_DSAPORT'] = expand_env(os.environ['RVBD_DSAPORT'])
    config['METRIC_URL'] = expand_env(os.environ['METRIC_URL'])
    config['AUTH_TOKEN'] = expand_env(os.environ.get('AUTH_TOKEN', None))
    config['AUTH_TOKEN_PATH'] = expand_env(os.environ.get('AUTH_TOKEN_PATH', None))
    config['API_NAME'] = expand_env(os.environ['API_NAME'])

    pe_realms = []
    pe_realm = {}
    pe_realm['METRIC_URL'] = config['METRIC_URL']
    pe_realm['AUTH_TOKEN'] = config['AUTH_TOKEN']
    pe_realm['AUTH_TOKEN_PATH'] = config['AUTH_TOKEN_PATH']
    pe_realm['API_NAME'] = config['API_NAME']
    pe_realms.append(pe_realm)
    config['PE_REALMS'] = pe_realms
    return config

def parse_mappings():
    global mappings
    mappings = os.environ.get('LABEL_MAPPINGS', None)

    if mappings == None:
        mappings = {}
    else:
        mappings = eval(mappings)

    logger.debug(mappings)

def parse_dimensioned_labels():
    global dimensioned_labels
    dimensioned_labels = os.environ.get('DIMENSIONED_LABELS', None)

    if dimensioned_labels == None:
        dimensioned_labels = {}
    else:
        dimensioned_labels = set(eval(dimensioned_labels))

    logger.debug(dimensioned_labels)

def main():

    global CURRENTTIME
    setup_logging(logging.DEBUG)
    parse_mappings()
    parse_dimensioned_labels()
    config = parse_config()
    cmx_server = "%s:%s" % (config['RVBD_DSAHOST'], config['RVBD_DSAPORT'])
    container_id = str(time.time())
    session_created = False

    while True:
        while session_created == False:
            try:
                session = start_session(cmx_server, "pe", container_id)
                session_created = True
            except:
                logger.error("ERROR CREATING CMX SESSION")
                time.sleep(10)
        now = time.localtime().tm_sec
        sleepsecs = 65-now
        logger.debug("WATING %d SECS...", sleepsecs)
        time.sleep(sleepsecs)
        t = time.time()
        starttime = t
        for pe_realm in config['PE_REALMS']:
            try:
                process_pe_realm(session, cmx_server, pe_realm)
            except Exception as e:
                logger.error("ERROR PROCESSING " + str(e))
                pass
        t = time.time()
        endtime = t
        logger.debug("PROCESSING TIME TOOK %d SECONDS", endtime-starttime)

        CURRENTTIME = int(time.time())
        CURRENTTIME = int(CURRENTTIME//60 * 60)


    return True


if __name__ == "__main__":
    
    main()

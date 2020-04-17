package com.aternity.samples;

import java.io.File;
import java.io.FileInputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.HashMap;
import java.util.Map;
import java.util.Properties;

import com.riverbed.agent.cmxsdk.api.CmxClientEnvironment;
import com.riverbed.agent.cmxsdk.api.CmxMetricDefinition;
import com.riverbed.agent.cmxsdk.api.CmxSdkClient;
import com.riverbed.agent.cmxsdk.api.ICmxClientEnvironment;
import com.riverbed.agent.cmxsdk.api.ICmxClientEnvironmentBuilder;
import com.riverbed.agent.cmxsdk.api.ICmxMetric;
import com.riverbed.agent.cmxsdk.api.ICmxMetricDefinition;

/**
 * Availability Monitor that check hosts and URLs and publishes result to the 
 * Custom Metrics Java SDK.
 * 
 * Note: the following example assumes the Java application is being run
 * locally on a system with the Aternity APM Agent installed.
 */
public class CmxAvailabilityMonitor {

    public static String CMX_NAME;
    public static String CMX_HOST = null;
    public static int CMX_PORT = 0;
    public static String[] HOSTS;
    public static String[] URLS;
    public static int CMX_INTERVAL_SEC = 5;

    private static CmxSdkClient cmxClient;
    private static ICmxMetric[] metricHosts;
    private static ICmxMetric[] metricUrls;    

    public static void main(String[] args) {

        System.out.println("Starting Custom Metrics Availability Monitor...");
        try {
            loadProperties();
            connect();			// Connect to CMX Server, establish a session
            initMetrics();		// Setup Dimension and Metric definitions that will be used for this session

            //noinspection InfiniteLoopStatement
            while (true) {
                postMetrics();
                Thread.sleep(CMX_INTERVAL_SEC * 1_000 );
            }
        }
        catch (Exception e) {
            e.printStackTrace();
        }
        finally {
            if (cmxClient != null) {
                try { cmxClient.close(); }
                catch (Exception ee) {
                    // ignore problems on a close
                }
            }
        }        
    }


    public static void connect() {
        try {
            ICmxClientEnvironmentBuilder builder =
                    CmxClientEnvironment.CmxClientEnvironmentBuilder
                    .defaultBuilder(CMX_NAME);
            if (CMX_HOST!=null) {builder = builder.host(CMX_HOST);}
            if (CMX_PORT!=0) {builder = builder.port(CMX_PORT);}
            ICmxClientEnvironment cmxEnv = builder.build();
            cmxClient = new CmxSdkClient(cmxEnv);
            cmxClient.open();
        }
        catch (Exception e) {
            e.printStackTrace();
            System.exit(3);
        }
    }

    public static void postMetrics() {
        try {
            int i;
            long currTime = System.currentTimeMillis() / 1000;
            for (i=0; i < HOSTS.length; i++) {
                metricHosts[i].addSample(currTime, isHostReachable(HOSTS[i]) ? 1 : 0);
            }
            currTime = System.currentTimeMillis() / 1000;
            for (i=0; i < URLS.length; i++) {
                metricUrls[i].addSample(currTime, isURLReachable(URLS[i]) ? 1 : 0);
            }
            System.out.println(" - Metrics posted");
        }
        catch (Exception e) {
            e.printStackTrace();
            System.exit(2);
        }
    }


    public static void initMetrics() {
        int i;
        try {
            // Dimension & Metrics for Hosts
            ICmxMetricDefinition hostMetricDef = new CmxMetricDefinition.CmxMetricDefinitionBuilder("host-available")
                    .version(1)
                    .description("Host Availability description goes here...")
                    .displayName("Host Availability")
                    .units("count")
                    .build();
            metricHosts = new ICmxMetric[HOSTS.length];
            for (i=0; i < HOSTS.length; i++) {
                Map<String, String> dimsHost = new HashMap<>();
                dimsHost.put( "host", HOSTS[i]); // dimensions have a name and a value
                metricHosts[i] = cmxClient.createMetric( hostMetricDef, dimsHost );
            }
            // Dimension & Metrics for URLS
            ICmxMetricDefinition urlMetricDef = new CmxMetricDefinition.CmxMetricDefinitionBuilder("url-available")
                    .version(1)
                    .description("URL Availability description goes here...")
                    .displayName("URL Availability")
                    .units("count")
                    .build();
            metricUrls = new ICmxMetric[URLS.length];
            for (i=0; i < URLS.length; i++) {
                Map<String, String> dimsUrl = new HashMap<>();
                dimsUrl.put( "url", URLS[i]);
                metricUrls[i] = cmxClient.createMetric( urlMetricDef, dimsUrl );
            }
            System.out.println(" - Metric Definitions created");
        }
        catch (Exception e) {
            e.printStackTrace();
            System.exit(1);
        }
    }
    

    public static boolean isURLReachable(String _url) {
        boolean b = true;
        try {
            URL url = new URL(_url);
            HttpURLConnection urlConn = (HttpURLConnection) url.openConnection();
            urlConn.setConnectTimeout(5_000);
            urlConn.connect();
            urlConn.disconnect();
        }
        catch (Exception ex) {
            b = false;
        }
        return b;
    }


    public static boolean isHostReachable(String _ipAddress) {
        boolean b;
        try {
            Process p1;
            if (File.separatorChar == '/' ) { // Linux
                p1 = java.lang.Runtime.getRuntime().exec("ping -c 1 " + _ipAddress.trim());
            } else { // Windows
                p1 = java.lang.Runtime.getRuntime().exec("ping -n 1 " + _ipAddress.trim());
            }
            int returnVal = p1.waitFor();
            b = (returnVal == 0);
        }
        catch (Exception e) {
            b = false;
        }
        return b;
    }

    
    // File: cmx.properties
    //  cmx.name=
    //  #cmx.host= (optional)
    //  #cmx.port= (optional)
    //  #cmx.interval.sec=(optional)
    //  hosts=www.google.com,d.e.a.d.z.o.n.e.com  # comma separated
    //  urls=https://www.google.com,http://d.e.a.d.z.o.n.e.com  # comma separated
    static private void loadProperties() {
        Properties properties = new Properties();
        try (InputStream input = new FileInputStream("cmx.properties")) {
            properties.load(input);
            CMX_NAME = properties.getProperty("cmx.name").trim();
            final String host = properties.getProperty("cmx.host");
            if (host != null) {
                CMX_HOST = host.trim();
            }
            final String portString = properties.getProperty("cmx.port");
            if (portString != null) {
                CMX_PORT = Integer.parseInt(portString.trim());
            }
            HOSTS = properties.getProperty("hosts").split(",");
            URLS = properties.getProperty("urls").split(",");
            final String intervalsString = properties.getProperty("cmx.interval.sec");
            if (intervalsString != null) {
                CMX_INTERVAL_SEC = Integer.parseInt(intervalsString.trim());
            }

            System.out.println(" - Properties loaded");
        } catch (Exception ex) {
            ex.printStackTrace();
            System.exit(4);
        }
        // Don't care about close errors
    }

}
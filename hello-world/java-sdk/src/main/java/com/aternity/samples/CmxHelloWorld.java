package com.aternity.samples;

import java.util.HashMap;
import java.util.Map;
import java.util.Random;

import com.riverbed.agent.cmxsdk.api.CmxClientEnvironment.CmxClientEnvironmentBuilder;
import com.riverbed.agent.cmxsdk.api.CmxMetricDefinition.CmxMetricDefinitionBuilder;
import com.riverbed.agent.cmxsdk.api.CmxSdkClient;
import com.riverbed.agent.cmxsdk.api.CmxSdkException;
import com.riverbed.agent.cmxsdk.api.ICmxClientEnvironment;
import com.riverbed.agent.cmxsdk.api.ICmxMetric;
import com.riverbed.agent.cmxsdk.api.ICmxMetricDefinition;

/**
 * Hello World example of calling the Custom Metrics Java SDK API.
 * 
 * Note: the following example assumes the Java application is being run
 * locally on a system with the Aternity APM Agent installed.
 */
public class CmxHelloWorld {

    static final Random random = new Random();

    public static void main(String[] args) {

        System.out.println("Starting Custom Metrics Hello World Java Example...");
        CmxSdkClient client = null;
        
        try {
            // Open a connection to the Aternity APM Agent (cmx server component)        
        	ICmxClientEnvironment env = CmxClientEnvironmentBuilder.defaultBuilder("hello-world-java").build();		
			client = new CmxSdkClient(env);
			client.open();
			
			 // Define a set of dimensions. The following example sets a single dimension: "myDimension:test-1".
            Map<String, String> dimensions = new HashMap<String, String>();
            dimensions.put("myDimension", "test-1");
                       
            // Define a metric. The following example defines a metric with the id "hello-world-java". 
            // It also provides a display name, description and unit for the metric.
            ICmxMetricDefinition helloWorldJavaMetricDef = new CmxMetricDefinitionBuilder("hello-world-java")
                    .version(1)
                    .description("Metric from Hello World Java Example")
                    .displayName("Hello World Java")
                    .units("count")
                    .build();

            ICmxMetric helloWorldJavaMetric = client.createMetric(helloWorldJavaMetricDef, dimensions);
            
            for (int ctr=0; ctr < 5; ctr++) {
                // Next, publish metric values (samples). The following example publishes a single metric sample to the 
                // "hello-world-java" metric defined previously. The value is a random number between 0 and 100 and the
                // timestamp is the current timestamp in seconds.
                long currTime = System.currentTimeMillis() / 1000;
                helloWorldJavaMetric.addSample(currTime, random.nextInt(100));

                // Sleep 5s before publishing another metric sample
                System.out.println("  - Metric sample published. Sleeping 5s...");
                Thread.sleep(5000);
            }
          
        } catch (Exception e) {
            e.printStackTrace();

        } finally {
            // Close the connection to the Aternity APM Agent (cmx server component)
            if (client != null) {
                try {
                    client.close();
                } catch (CmxSdkException e) {
                    e.printStackTrace();
                }
            }
        }
    }
}
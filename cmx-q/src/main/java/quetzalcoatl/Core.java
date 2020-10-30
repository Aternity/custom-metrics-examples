package quetzalcoatl;

import java.io.OutputStream;
import java.io.PrintStream;
import java.net.InetAddress;
import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;
import java.util.stream.Collectors;

import com.riverbed.agent.cmxsdk.api.CmxClientEnvironment.CmxClientEnvironmentBuilder;
import com.riverbed.agent.cmxsdk.api.CmxMetricDefinition;
import com.riverbed.agent.cmxsdk.api.CmxSdkClient;
import com.riverbed.agent.cmxsdk.api.ICmxClientEnvironment;
import com.riverbed.agent.cmxsdk.api.ICmxMetric;
import com.riverbed.agent.cmxsdk.api.ICmxMetricDefinition;

import org.apache.commons.cli.CommandLine;
import org.apache.commons.cli.CommandLineParser;
import org.apache.commons.cli.DefaultParser;
import org.apache.commons.cli.HelpFormatter;
import org.apache.commons.cli.MissingOptionException;
import org.apache.commons.cli.Options;

public class Core {

   
    static final boolean RVBD_CMX_AGENT_SECURE = true;
    
    
	public static void main(String[] args) {
		
		String metricName="";
		String metricDesc="";
		String metricUnit="count";
		long timeStamp=System.currentTimeMillis();
		double sample=0;
		String  RVBD_CMX_AGENT_HOST = "localhost";
		int     RVBD_CMX_AGENT_PORT = 7074;
		Map<String, String> dimensionsMap = new HashMap<String, String>();
        Map<String, String> tagsMap = new HashMap<String, String>();
        
		//input params
		Options options = new Options();
	      options
	      	.addRequiredOption("m", "metric", true, "Metric name as string.")
	        .addRequiredOption("s", "sample", true, "Sample of the metric as number")
	        .addOption("v", "unit",true, "(Optional) Description the metric as string. Defaults to metricname.")
	        .addOption("u", "unit",true, "(Optional) Unit of the metric as string. Defaults to count.")
	        .addOption("c", "clock",true, "(Optional) Clock timestamp. Defaults to now.")
	        .addOption("y", "(Optional) Show debug. Defaults to off.")
	        .addOption("d", "dimension",true, "(Optional) Key:value pairs. Example: dim1:abc,dim2:xyz. Defaults to none.")
	        .addOption("t", "tag",true, "(Optional) Key:value pairs. Example: tag1:abc,tag22:xyz. Defaults to none.")
	        .addOption("a","agentHost" , true, "(Optional) IP/Host Address of the agent. Defaults to localhost.")
	      	.addOption("p", "port", true, "(Optional) Port of the agent.Unit of the metric as string. Defaults to 7074.")
	      	;
	      HelpFormatter formatter = new HelpFormatter();
	      CommandLineParser parser = new DefaultParser();
	      
		try {
			
			////parse the options passed as command line arguments
		    CommandLine cmd = parser.parse( options, args);
		    
		    if (cmd.hasOption("m")) {
		    	metricName=cmd.getOptionValue("m");
		    }
			
		    if (cmd.hasOption("s") && cmd.hasOption("s")) {
		    	try {
					sample=Double.parseDouble(cmd.getOptionValue("s"));
				} catch (Exception e) {
					throw new NumberFormatException(options.getOption("s").getLongOpt()+" "+cmd.getOptionValue("s")+" is not a number");
				}
		    }
		    
		    if (cmd.hasOption("v")) {
		    	metricDesc=cmd.getOptionValue("v");
		    }else {
		    	metricDesc=metricName;
		    }
		    
		    if (cmd.hasOption("u")) {
		    	metricUnit=cmd.getOptionValue("u");
		    }
		    
		    if (cmd.hasOption("a")) {
		    	RVBD_CMX_AGENT_HOST=cmd.getOptionValue("a");
		    }
		    
		    if (cmd.hasOption("p") && cmd.hasOption("p")) {
		    	try {
		    		RVBD_CMX_AGENT_PORT=Integer.parseInt(cmd.getOptionValue("p"));
				} catch (Exception e) {
					throw new NumberFormatException(options.getOption("p").getLongOpt()+" "+cmd.getOptionValue("p")+" is not a number");
				}
		    }
		    
		    if (cmd.hasOption("c") && cmd.hasOption("c")) {
		    	try {
		    		timeStamp=Long.parseLong(cmd.getOptionValue("c"));
				} catch (Exception e) {
					throw new NumberFormatException(options.getOption("c").getLongOpt()+" "+cmd.getOptionValue("p")+" is not a number");
				}
		    }
		    
		    if (!cmd.hasOption("y")) {
		    	//TODO: Stop SDK std out, hack because SDK is logging too verbosely and cant set the log level
	            disableOut();
		    }
		    
		    if (cmd.hasOption("d")) {
		    	dimensionsMap = Arrays.stream(cmd.getOptionValue("d").split(","))
		    		    .map(s -> s.split(":"))
		    		    .collect(Collectors.toMap(
		    		        a -> a[0],  //key
		    		        a -> a[1]   //value
		    		    ));	
		    }
		    
		    if (cmd.hasOption("t")) {
		    	tagsMap= Arrays.stream(cmd.getOptionValue("t").split(","))
		    		    .map(s -> s.split(":"))
		    		    .collect(Collectors.toMap(
		    		        a -> a[0],  //key
		    		        a -> a[1]   //value
		    		    ));
		    }
		   
			//Utility reports with client hostname by default
			String source=InetAddress.getLocalHost().getHostName();
			
			//Configure CMX client
			ICmxClientEnvironment env = CmxClientEnvironmentBuilder
				      .defaultBuilder(source)
				      .host(RVBD_CMX_AGENT_HOST)
				      .port(RVBD_CMX_AGENT_PORT)
				      .secure(RVBD_CMX_AGENT_SECURE)
				      .build();
			
			
			CmxSdkClient client = new CmxSdkClient(env);
			client.open();
			
            //Create and send sample
            ICmxMetricDefinition mDef = (new CmxMetricDefinition.CmxMetricDefinitionBuilder(metricName)
                   .version(1)
                   .description(metricDesc)
                   .displayName(metricName)
                   .units(metricUnit)
                   .build());
            	
            ICmxMetric cmxMetric = client.createMetric(mDef, dimensionsMap, tagsMap);
            cmxMetric.addSample(timeStamp, sample);
          	
            client.close();
			
           
		} catch (NumberFormatException e){
			System.out.println(e.getMessage());
			formatter.printHelp(" ",options);
		}  catch (MissingOptionException e){
			System.out.println(e.getMessage());
			formatter.printHelp(" ",options);
		} catch (Exception e) {
			System.out.println(e.getMessage());
			e.printStackTrace();
		}
		
	}
	
	private static void disableOut() {
		System.setOut(new PrintStream(new OutputStream() {
        public void write(int b) {
            //DO NOTHING
        }
		}));
	}

}

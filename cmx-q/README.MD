# Q

Q utility allows sending custom metric samples over a simple CLI. Requires java 1.8

## Installation

1. Copy the cmxsdk.jar from the APM agent to a local path
2. Add the jar to your local maven repo. Use the following group,artifact,version to match what is in the pom
```
<dependency>
	<groupId>com.riverbed.agent.cmxsdk.api</groupId>
  	<artifactId>cmxsdk</artifactId>
	<version>2.0</version>
</dependency>
```
3. Use maven to compile and package the Q.jar

```
mvn clean compile package
```

## Usage

```
java -jar Q-0.1.jar 
usage:
 -a,--agentHost <arg>   (Optional) IP/Host Address of the agent. Defaults to localhost.
 -c,--clock <arg>       (Optional) Clock timestamp. Defaults to now.
 -d,--dimension <arg>   (Optional) Key:value pairs. Example: dim1:abc,dim2:xyz. Defaults to none.
 -m,--metric <arg>      Metric name as string.
 -p,--port <arg>        (Optional) Port of the agent.Unit of the metric as string. Defaults to 7074.
 -s,--sample <arg>      Sample of the metric as number
 -t,--tag <arg>         (Optional) Key:value pairs. Example: tag1:abc,tag22:xyz. Defaults to none.
 -u,--unit <arg>        (Optional) Unit of the metric as string. Defaults to count.
 -v,--unit <arg>        (Optional) Description the metric as string. Defaults to metricname.
 -y                     (Optional) Show debug. Defaults to off.
```

## Examples
Sending a simple metric and sample
```
java -jar Q-0.1.jar -m testmetric001 -s 15.3
```

Sending a metric sample with tags and dimensions
```
java -jar Q-0.1.jar -m testmetric001 -s 205 -a 100.25.190.108 -d application:demo,server:xyz -t env:dev,cloud:aws
```


## License
[MIT](https://choosealicense.com/licenses/mit/)
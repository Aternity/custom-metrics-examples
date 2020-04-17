# Availability Monitor Java SDK Example

This basic example shows how to check hosts and URLs to see if a set of machines and/or web sites are up and running. The metrics report a 1 for each if it's up, and a zero if it's down.  To run the Availability Monitor Java SDK example follow the steps below. 

The steps assume that both a Java JDK (v8+) and Aternity APM agent (v11.4+) is installed locally.

* Install Maven dependencies.  The following command assumes default agent installation paths; adjust as necessary.

Linux: 

`mvn deploy:deploy-file -Dfile=/opt/Panorama/hedzup/mn/lib/cmxsdk.jar -DgroupId=com.riverbed.agent -DartifactId=cmxsdk -Dversion=1.0 -Dpackaging=jar -Durl=file:./lib/ -DrepositoryId=lib -DupdateReleaseInfo=true`

Windows: 

`mvn deploy:deploy-file -Dfile=C:\Panorama\hedzup\mn\lib\cmxsdk.jar -DgroupId=com.riverbed.agent -DartifactId=cmxsdk -Dversion=1.0 -Dpackaging=jar -Durl=file:./lib/ -DrepositoryId=lib -DupdateReleaseInfo=true`


* Compile the application

`mvn clean compile assembly:single`

* Run the application

`java -jar ./target/cmx-availability-monitor-1.0-jar-with-dependencies.jar`


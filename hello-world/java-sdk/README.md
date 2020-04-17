# Hello World Java SDK Example

To run the Java SDK example follow the steps below. 

The steps assume that both a Java JDK (v8+) and Aternity APM agent (v11.4+) is installed locally.

* Install Maven dependencies.  The following command assumes default agent installation paths; adjust as necessary.

Linux: 

`mvn deploy:deploy-file -Dfile=/opt/Panorama/hedzup/mn/lib/cmxsdk.jar -DgroupId=com.riverbed.agent -DartifactId=cmxsdk -Dversion=1.0 -Dpackaging=jar -Durl=file:./lib/ -DrepositoryId=lib -DupdateReleaseInfo=true`

Windows: 

`mvn deploy:deploy-file -Dfile=C:\Panorama\hedzup\mn\lib\cmxsdk.jar -DgroupId=com.riverbed.agent -DartifactId=cmxsdk -Dversion=1.0 -Dpackaging=jar -Durl=file:./lib/ -DrepositoryId=lib -DupdateReleaseInfo=true`


* Compile the CMX Hello World test application

`mvn clean compile assembly:single`

* Run the CMX Hello World test application

`java -jar ./target/java-sdk-samples-1.0-jar-with-dependencies.jar`


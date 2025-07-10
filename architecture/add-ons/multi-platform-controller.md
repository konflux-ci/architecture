# Multi Platform Controller


## Overview

The Multi Platform Controller is a Kubernetes Controller that can provision virtual machines for Tekton `TaskRun` instances. This allows these TaskRuns to SSH into the provided virtual machines to build images in platforms other than amd64.

## The TaskRun Contract

The Multi Platform Controller has no understanding of the build pipeline logic. It only understands how to provision hosts and allocate SSH keys. For the Multi Platform Controller to act on a `TaskRun` it must meet the following conditions:

- It must mount a secret with the name `multi-platform-ssh-$(context.taskRun.name)`
- It must have a parameter called `PLATFORM` which specifies the required platform

If these conditions are met the controller will reconcile on the task and attempt to provision a virtual machine for the task. If it is successful it will create  secret (`multi-platform-ssh-$(context.taskRun.name)`) with the following entries:

- `otp` a one-time-password that can be used to obtain the VM's SSH key from the OTP server.
- `otp-ca` a certificate-authority certificate used to validate the HTTPS connection to the OTP server.
- `otp-server` the url of the OTP server.
- `host` the host name or IP to connect to, including the username in the form `user@host`
- `user-dir` the working directory to perform the build in

Note that these SSH credentials are only valid while the `TaskRun` is executing.

If the operator is unsuccessful then it will still create the secret, however it will only have a single item called `error` with the error message. The task is expected to echo this to the logs and then fail if this error is present.

The reason why this works is that the `TaskRun` will create a pod that references a non-existent secret (e.g. if the `TaskRun` was called `devfile-sample-t7rd7-build-container-arm64` then the resulting pod will reference a secret called `multi-platform-ssh-devfile-sample-t7rd7-build-container-arm64`). As this secret does not exist yet, the pod will not start but instead Kubernetes will wait until the secret is ready before running the pod. This gives the controller time to provision a SSH based host, and then create the secret with the required details. The secret is created even on failure to prevent the task hanging until timeout and to allow any error messages to be propagated to the user.

## The Controller

The controller is responsible for allocating SSH credentials to TaskRuns that meet the contract specified above. It currently supports fixed pools and fully dynamic host provisioning.

### Configuration

At present the controller requires no CRDs. Configuration is provided through a `ConfigMap` that defines the available hosts. This `ConfigMap` is called `host-config` and lives in the `multi-platform-controller` namespace. This `ConfigMap` must have the `build.appstudio.redhat.com/multi-platform-config` label.

An example is shown below:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  labels:
    build.appstudio.redhat.com/multi-platform-config: hosts
  name: host-config
  namespace: multi-platform-controller
data:
  local-platforms: linux/amd64
  dynamic-platforms: linux/arm64
  dynamic-pool-platforms: linux-m4xlarge/amd64
  instance-tag: unique-identifier

  dynamic.linux-arm64.type: aws
  dynamic.linux-arm64.region: us-east-1
  dynamic.linux-arm64.ami: ami-03d6a5256a46c9feb
  dynamic.linux-arm64.instance-type: t4g.medium
  dynamic.linux-arm64.key-name: sdouglas-arm-test
  dynamic.linux-arm64.aws-secret: awsiam
  dynamic.linux-arm64.ssh-secret: awskeys
  dynamic.linux-arm64.security-group: "launch-wizard-1"
  dynamic.linux-arm64.max-instances: "10"

  dynamic.linux-m4xlarge-amd64.type: aws
  dynamic.linux-m4xlarge-amd64.region: us-east-1
  dynamic.linux-m4xlarge-amd64.ami: ami-026ebd4cfe2c043b2
  dynamic.linux-m4xlarge-amd64.instance-type: m6a.4xlarge
  dynamic.linux-m4xlarge-amd64.key-name: konflux-stage-ext-mab01
  dynamic.linux-m4xlarge-amd64.aws-secret: aws-account
  dynamic.linux-m4xlarge-amd64.ssh-secret: aws-ssh-key
  dynamic.linux-m4xlarge-amd64.security-group-id: sg-05bc8dd0b52158567
  dynamic.linux-m4xlarge-amd64.max-instances: "4"
  dynamic.linux-m4xlarge-amd64.max-concurrency: "4"
  dynamic.linux-m4xlarge-amd64.subnet-id: subnet-030738beb81d3863a
  dynamic.linux-m4xlarge-amd64.instance-tag: "some-pool-identifier"

  host.ppc1.address: "150.240.147.198"
  host.ppc1.platform: "linux/ppc64le"
  host.ppc1.user: "root"
  host.ppc1.secret: "awskeys"
  host.ppc1.concurrency: "4"

  host.ibmz1.address: "169.59.165.178"
  host.ibmz1.platform: "linux/s390x"
  host.ibmz1.user: "root"
  host.ibmz1.secret: "awskeys"
  host.ibmz1.concurrency: "4"
```

The `local-platforms` entry tells the system which platforms actually run locally in the cluster rather then on remote VMs. The `dynamic-platforms` entry tells the system which platforms are using dynamic provisioning. The `dynamic-pool-platforms` entry tells the system which platforms are using dynamically provisioned pools of hosts. The `instance-tag` is a unique value that is used by the system to determine which virtual machines it owns in the remote environment.

Dynamic configuration properties depend on the provider. At the moment `aws`, `ibmz` and `ibmp` are supported.

For static host pools each host has a unique name, and provides different parameters that can be configured:

- `address` The address or host name
- `secret` The name of a secret in the `multi-platform-controller` namespace that contains the SSH keys for this host. These keys are never copied into the user namespace.
- `concurrency` The number of builds that can be running on the host at any one time. Note that this is tracked by the controller rather than the host, so for example if you had a host referenced by both staging and production each environment is not aware of the other environments builds.
- `user` The username to use to connect to the host
- `platform` The hosts platform

Dynamic pool entries use a combination of dynamic and static host settings.


### Allocation Process

When a `TaskRun` is identified that meets the contract above the controller will attempt to allocate a virtual machine for them.

The host selection process depends on if the platform is configured to use local, dynamic provisioning, a static pool or a dynamic pool:

*"Local" provisioning*

For platform that are configured as "local", no provisioning is done. Instead the secret required by the user task is generated so that it only contains a `host` value which is set to `localhost`. Tasks need to detect this configuration and switch to a code path that would perform the task's function locally within the running POD, as opposed to shelling out to a remote VM.

The purpose behind this configuration is to allow for hiding the fact with a task is executing locally or remotely from the pipeline users and instead have a single task that does both. 

*Host Pool*

The controller looks at the current configuration, and also looks for all running tasks with a host assigned. Using this information it picks one of the hosts at random that has the most amount of free slots. This algorithm is very simple, but works fine when all hosts are the same size. If we are mixing hosts of different sizes then we may need a better algorithm.

*Dynamic*

The controller checks that the maximum number of virtual machines has not been exceeded, and if not asks the cloud provider to spin up a new virtual machine. It then schedules regular requeue requests to check when the machine is ready (so the controller loop is not blocked waiting for the VM).

Once the host is selected the controller runs a 'provisioning' task to prepare the host. This task currently does the following:

- Create a new user specifically for this build
- Generate a new pair of SSH keys for this user and install them
- Send the private key for this user to the OTP service
- Create the required secret and use it to store OTP returned from the service,
  as well as other details as listed above.

Once the secret has been created then the original `TaskRun` will start, and can use the new user on the remote host to perform the build. This approach means that every build is run under a different user.

Which hosts are allocated with which tasks are tracked by adding additional labels onto the `TaskRun` object.

If the provisioning task fails then a label is added to the `TaskRun` indicating that it has failed and allocation is re-tried, excluding all hosts in the failed list. If all of them fail then the error secret is created.

Note that this failed list is per `TaskRun`, there is no global tracking of the health of the hosts. This means that if a host is down it will potentially be retried many times, however when it comes back up it will be in service immediately.

*Dynamic Pool*

The controller uses a pool of VMs in a similar way to how a static Host Pool is allocated. When it runs out of execution slots within the pool it allocates new VMs up to the given `max-instances` limit.

VMs are kept in the pool up to the amount of minutes defined by the `max-age` configuration option. Beyond that no new tasks are scheduled to those VMs, and when they become idle, they are de-allocated.

The controller does not maintain any state about the VM pool, instead it reconstructs it in-memory as needed. The controller tells different pools apart within the cloud provider's API by using the `instance-tag` option, therefore its important to define a different value for each dynamic pool.

### One Time Passwords

Putting an SSH key directly into a secret opens up a potential security issue, where a user could steal this key, connect to a virtual machine, and compromise a build. Our existing tamper protections cannot detect this case.

To avoid this the Multi Platform Controller is leveraging a One Time Password approach to managing SSH keys. Instead of the multi platform controller creating a secret with an SSH key, it creates a one time password and adds this to the secret. This secret can then be exchanged exactly once for an SSH key.

If an attacker reads the secret and gains access the VM the task will immediately fail as it will not be able to access the VM.

### Clean Up

When the `TaskRun` is completed then the user is removed from the remote host via a cleanup task.

## One Time Password Service

The one time password service is a HTTP based service that provides two endpoints, one to accept a private key and return a OTP, and another to serve the private key when provided with the OTP.

There is a single OTP service per cluster, which is be secured via HTTPS.

## Host Requirements

In order to work with the multi platform controller remote hosts need to meet the following requirements:

- Provide a user that can successfully use `sudo` to add and delete users, and copy generated SSH keys into their home directories
- They *should* be running RHEL, however this is not strictly speaking a technical requirement

### Additional Requirements

There are still unanswered questions about these hosts and additional requirements that may be placed on them.

- How do we handle logs from these machines? Where will they be stored?
- Should the 'main' user be locked down so that it can only add and remove the build users? At present the main user used by the controller has root access (not the users used by the build, but the user that creates these users).
- Do we need any kind of intrusion detection or additional monitoring software on these VMs?

## IBM Cloud Configuration

This section explains what is needed to configure an IBM Cloud Account. Power PC and System Z are both very different and have different configuration, so these are divided into different sections.

### Pool based config

Pool based configuration is handled by simply starting virtual machines using the boot images selected. You must also select/create appropriate SSH Keys for the instances (i.e. don't use a personal key). Once these are up and running they can be added to the `host-config` ConfigMap as per the example above. The SSH keys much be added to the vault and deployed to the namespace using external secrets.

### Dynamic Config

This section lists the config options required for dynamic config. To figure out what these values should be for both Power and System Z you can go to the page to create virtual machines, configuring a machine with the settings you want (including the boot image created above), and then instead of hitting 'create', hit the 'sample API call' button. The sample API call will contain the configuration values you need.

To use dynamic configuration you need to configure a secret with an IBM account access key. This secret requires a single entry with the name `api-key` that contains the IBM API key.

This API key should not be a personal key, but should be a service based key.

#### Power PC

Power PC requires the following config options:

```yaml
  dynamic.linux-ppc64le.type: ibmp
  dynamic.linux-ppc64le.ssh-secret: <1>
  dynamic.linux-ppc64le.secret: <2>
  dynamic.linux-ppc64le.key: <3>
  dynamic.linux-ppc64le.image: <4>
  dynamic.linux-ppc64le.crn: "crn:v1:bluemix:public:power-iaas:dal10:a/934e118c399b4a28a70afdf2210d708f:8c9ef568-16a5-4aa2-bfd5-946349c9aeac::" <5>
  dynamic.linux-ppc64le.url: "https://us-south.power-iaas.cloud.ibm.com" <6>
  dynamic.linux-ppc64le.network: "dff71085-73da-49f5-9bf2-5ea60c66c99b" <7>
  dynamic.linux-ppc64le.system: "e980" <8>
  dynamic.linux-ppc64le.cores: "0.25" <9>
  dynamic.linux-ppc64le.memory: "2" <10>
  dynamic.linux-ppc64le.max-instances: "2" <11>
```
1. Name of the secret with the SSH Private Key
2. Name of the secret with the IAM Access Key
3. Name of the SSH Key from the IBM Cloud Console
4. The name of the boot image you created above
5. The CRN of the workspace
6. The API endpoint to use, which changes by region
7. The network ID to use
8. The type of system to start
9. The number of cores to allocate
10. Memory in GB
11. The maximum number of instances to create at a given time


#### System Z

System Z requires the following config options:

```yaml
  dynamic.linux-s390x.type: ibmz
  dynamic.linux-s390x.ssh-secret:  <1>
  dynamic.linux-s390x.secret:  <2>
  dynamic.linux-s390x.key:  <3>
  dynamic.linux-s390x.image: "sdouglas-rhel-snapshot" <4>
  dynamic.linux-s390x.vpc: "us-east-default-vpc" <5>
  dynamic.linux-s390x.subnet: "us-east-2-default-subnet" <6>
  dynamic.linux-s390x.region: "us-east-2" <7>
  dynamic.linux-s390x.url: "https://us-east.iaas.cloud.ibm.com/v1" <8>
  dynamic.linux-s390x.profile: "bz2-1x4" <9>
  dynamic.linux-s390x.max-instances: "2" <10>
```
1. Name of the secret with the SSH Private Key
2. Name of the secret with the IAM Access Key
3. Name of the SSH Key from the IBM Cloud Console
4. The name of the boot image you created above
5. The VPC name
6. The subnet name
7. The region to use
8. The region API URI
9. The type of machine to allocate
10. The maximum number of instances to create at a given time

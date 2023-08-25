# Multi Platform Controller


## Overview

The Multi Platform Controller is a Kubernetes Controller that can provision virtual machines for Tekton `TaskRun` instances. This allows these TaskRuns to SSH into the provided virtual machines to build images in platforms other than amd64.

## The TaskRun Contract

The Multi Platform Controller has no understanding of the build pipeline logic. It only understands how to provision hosts and allocate SSH keys. For the Multi Platform Controller to act on a `TaskRun` it must meet the following conditions:

- It must have the `build.appstudio.redhat.com/multi-platform-required` label
- It must mount a secret with the name `multi-platform-ssh-$(context.taskRun.name)`
- It must have a parameter called `ARCH` which specifies the required platformitecture

If these conditions are met the controller will reconcile on the task and attempt to provision a virtual machine for the task. If it is successful it will create  secret (`multi-platform-ssh-$(context.taskRun.name)`) with the following entries:

- `id_rsa` the SSH key to use to connect to the host (NOTE: this will be replaced by one-time-password)
- `host` the host name or IP to connect to, including the username in the form `user@host`
- `build-dir` the working directory to perform the build in
- `one-time-password` a one time password that can be exchanged for an SSH Key.

Note that these SSH credentials are only valid while the `TaskRun` is executing.

Note that the first implementation of this will put the `id_rsa` key directly into the secret, at some point in the near future this will change to a one time password instead.

If the operator is unsuccessful then it will still create the secret, however it will only have a single item called `error` with the error message. The task is expected to echo this to the logs and then fail if this error is present.

The reason why this works is that the `TaskRun` will create a pod that references a non-existent secret (e.g. if the `TaskRun` was called `devfile-sample-t7rd7-build-container-arm64` then the resulting pod will reference a secret called `multi-platform-ssh-devfile-sample-t7rd7-build-container-arm64`). As this secret does not exist yet, the pod will not start but instead Kubernetes will wait until the secret is ready before running the pod. This gives the controller time to provision a SSH based host, and then create the secret with the required details. The secret is created even on failure to prevent the task hanging until timeout and to allow any error messages to be propagated to the user.

## The Controller

The controller is responsible for allocating SSH credentials to TaskRuns that meet the contract specified above.  It currently supports fixed pools and fully dynamic host provisioning.

### Configuration

At present the controller requires no CRDs (although this might change for dynamic pooling). Configuration is provided through a `ConfigMap` that defines the available hosts. This `ConfigMap` is called `host-config` and lives in the `multi-platform-controller` namespace. This `ConfigMap` must have the `build.appstudio.redhat.com/multi-platform-config` label.

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
  dynamic-platforms: linux/arm64
  instance-tag: unique-identifier

  dynamic.linux-arm64.type: aws
  dynamic.linux-arm64.region: us-east-1
  dynamic.linux-arm64.ami: ami-03d6a5256a46c9feb
  dynamic.linux-arm64.instance-type: t4g.medium
  dynamic.linux-arm64.key-name: sdouglas-arm-test
  dynamic.linux-arm64.aws-secret: awsiam
  dynamic.linux-arm64.ssh-secret: awskeys
  dynamic.linux-arm64.security-group: "launch-wizard-1"
  dynamic.linux-arm64.max-instances: "2"


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

The `dynamic-platforms` entry tells the system which platforms are using dynamic provisioning. The `instance-tag` is a unique value that is used by the system to determine which virtual machines it owns in the remote environment.

Dynamic configuration properties depend on the provider. At the moment `aws`, `ibmz` and `ibmp` are supported.

For static host pools each host has a unique name, and provides different parameters that can be configured:

- `address` The address or host name
- `secret` The name of a secret in the `multi-platform-controller` namespace that contains the SSH keys for this host. These keys are never copied into the user namespace.
- `concurrency` The number of builds that can be running on the host at any one time. Note that this is tracked by the controller rather than the host, so for example if you had a host referenced by both staging and production each environment is not aware of the other environments builds.
- `user` The username to use to connect to the host
- `platform` The hosts platform


### Allocation Process

When a `TaskRun` is identified that meets the contract above the controller will attempt to allocate a virtual machine for them.

The host selection process depends on if the platform is configured to use dynamic provisioning or a pool:

*Host Pool*

The controller looks at the current configuration, and also looks for all running tasks with a host assigned. Using this information it picks one of the hosts at random that has the most amount of free slots. This algorithm is very simple, but works fine when all hosts are the same size. If we are mixing hosts of different sizes then we may need a better algorithm.

*Dynamic*

The controller checks that the maximum number of virtual machines has not been exceeded, and if not asks the cloud provider to spin up a new virtual machine. It then schedules regular requeues to check when the machine is ready (so the controller loop is not blocked waiting for the VM).

Once the host is selected the controller runs a 'provisioning' task to prepare the host. This task currently does the following:

- Create a new user specifically for this build
- Generate a new pair of SSH keys for this user and install them
- Copy the private key for this user back to the cluster and create the required secret with this information

Once the secret has been created then the original `TaskRun` will start, and can use the new user on the remote host to perform the build. This approach means that every build is run under a different user, and only low privilege ephemeral SSH keys end up in the user's namespace.

Which hosts are allocated with which tasks are tracked by adding additional labels onto the `TaskRun` object.

If the provisioning task fails then a label is added to the `TaskRun` indicating that it has failed and allocation is re-tried, excluding all hosts in the failed list. If all of them fail then the error secret is created.

Note that this failed list is per `TaskRun`, there is no global tracking of the health of the hosts. This means that if a host is down it will potentially be retried many times, however when it comes back up it will be in service immediately.

### One Time Passwords

Putting an SSH key directly into a secret opens up a potential security issue, where a user could steal this key, connect to a virtual machine, and compromise a build. Our existing tamper protections cannot detect this case.

For our existing builds currently it would be possible for an admin to push a bad image, or run a bad task, however this would fail the enterprise contract.

To avoid this the Multi Platform Controller is going to move to a One Time Password approach to managing SSH keys. Instead of the multi platform controller creating a secret with an SSH key, instead it will create a one time password and add this to the secret. This secret can then be exchanged exactly once for an SSH key.

If an attacker reads the secret and gains access the VM the task will immediately fail as it will not be able to access the VM.

#### One Time Password Service

The one time password service will be a HTTP based service that provides two endpoints, one to accept a password + OTP pair combo, and another to serve the keypair when provided with the password.

There will be a single OTP service per cluster, which will be secured via HTTPS.

### Clean Up

When the `TaskRun` is completed then the user is removed from the remote host via a cleanup task.

## Host Requirements

In order to work with the multi platform controller remote hosts need to meet the following requirements:

- Provide a user that can successfully use `sudo` to add and delete users, and copy generated SSH keys into their home directories
- They *should* be running RHEL, however this is not strictly speaking a technical requirement

### Additional Requirements

There are still unanswered questions about these hosts and additional requirements that may be placed on them.

- How do we handle logs from these machines? Where will they be stored?
- Should the 'main' user be locked down so that it can only add and remove the build users? At present the main user used by the controller has root access (not the users used by the build, but the user that creates these users).
- Do we need any kind of intrusion detection or additional monitoring software on these VMs?





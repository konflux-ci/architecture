# Security Guild recommended tools

This document lists the available tools that we researched for performing linting, Static Code Analysis, and vulnerability scanning on different platforms and languages. The goal is to introduce one of more of these tools into Konflux for customers to use.

From our discussions in the Secure Engineering Guild, our current position is that we would encourage teams to use the tools highlighted in this list for consistency. But if a team finds a different tool that's a better fit-for-purpose, that is also fine. The ProdSec org also supports some tools, and some tools will be integrated into our product over time (taking the responsibility of implementation off of our teams). Where we have a recommendation, it makes sense to follow it if it fits your team/product's needs.
Per our discussions with ProdSec, we should not use tools that could potentially "phone home," or any that could otherwise expose information about embargoed vulnerabilities, unless they have previously approved our particular use of the tool.

### Linting Tools

#### Golang
**golangci-lint** - https://github.com/golangci/golangci-lint

```
Usage:
$ cd my/golang/project
$ golangci-lint run
```

#### Docker
**hadolint** - https://github.com/hadolint/hadolint
_Note: In order to lint Bash code inside a Dockerfile, it uses Shellcheck internally._

```
Usage:
$ hadolint Dockerfile
(or)
$ docker run --rm -i ghcr.io/hadolint/hadolint < Dockerfile
```

### Vulnerability Scanners

**clair** - https://github.com/quay/clair
- quay.io uses Clair internally and the project is officially under them.
- Check these [docs](https://quay.github.io/clair/howto/deployment.html) to understand the deployment models Clair currently uses.
- For teams using quay.io as their container image registry, we enjoy the benefit of these scans via their website. You can check the results under the vulnerabilites tab of an image.

_Note: [clair-in-ci](https://quay.io/repository/redhat-appstudio/clair-in-ci) is a feature which includes security scanning via clair. It is enabled by default for any Pipelines created in Konflux. A Tekton Task is available that can be used to run clair in your own Pipelines [here](https://github.com/redhat-appstudio/build-definitions/tree/main/task/clair-scan/)._

### SAST Tools

**_gosec_** - https://github.com/securego/gosec

**find-sec-bugs** - https://github.com/find-sec-bugs/find-sec-bugs

**synk** - https://github.com/snyk/cli

_Note: Konflux uses synk to perform static analysis. A Tekton Task is available that can be used to run synk in your own Pipelines [here](https://github.com/redhat-appstudio/build-definitions/blob/main/task/sast-snyk-check)._

**checkov** - https://github.com/bridgecrewio/checkov
- Checkov uses a common command line interface to manage and analyze infrastructure as code (IaC) scan results across platforms such as Terraform, CloudFormation, Kubernetes, Helm, ARM Templates and Serverless framework. ([source](https://www.checkov.io/))
- As mentioned above, checkov covers most cloud platforms / tools including Kubernetes / OpenShift. It enforces a bunch of best practices to be followed for every platform.
- It also integrates well with [kustomize](https://www.checkov.io/7.Scan%20Examples/Kustomize.html) - we could simply scan a kustomize directory, and it would check everything within that.


[kube-score](https://github.com/zegl/kube-score), [kubesec](https://github.com/controlplaneio/kubesec), [kubeconform](https://github.com/yannh/kubeconform), [kubelinter](https://github.com/stackrox/kube-linter) were some other tools that were explored. Teams are welcome to experiment with these or other tools if none of the above mentioned tools in the doc meet your requirements. But as mentioned earlier, beware of any security implications of using a tool. Checking with the ProdSec team on the approval status is a good first step when considering a new tool.

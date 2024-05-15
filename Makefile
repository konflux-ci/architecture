CRD_REF_DOCS:=go run -modfile tools/go.mod github.com/elastic/crd-ref-docs

service-provider-repository:=https://github.com/redhat-appstudio/service-provider-integration-operator.git
service-provider-path:=api/v1beta1

application-environment-api-repository:=https://github.com/redhat-appstudio/application-api.git
application-environment-api-path:=api/v1alpha1

gitops-repository:=https://github.com/redhat-appstudio/managed-gitops.git
gitops-path:=backend-shared/apis/managed-gitops/v1alpha1

build-service-repository:=https://github.com/redhat-appstudio/build-service.git
build-service-path:=api/v1alpha1/

integration-service-repository:=https://github.com/redhat-appstudio/integration-service.git
integration-service-path:=api/v1alpha1

release-service-repository:=https://github.com/redhat-appstudio/release-service.git
release-service-path:=api/v1alpha1

jvm-build-service-repository:=https://github.com/redhat-appstudio/jvm-build-service.git
jvm-build-service-path:=pkg/apis/jvmbuildservice/v1alpha1

enterprise-contract-repository:=https://github.com/enterprise-contract/enterprise-contract-controller.git
enterprise-contract-path:=api/v1alpha1

devsandbox-repository:=https://github.com/codeready-toolchain/api.git
devsandbox-path:=api/v1alpha1

internal-services-repository:=https://github.com/redhat-appstudio/internal-services.git
internal-services-path:=api/v1alpha1

.PHONY: content/ref/%.md
content/ref/%.md: doc=$(basename $(notdir $@))
content/ref/%.md:
	mkdir -p "crd-temp/$(doc)" && cd "crd-temp/$(doc)" && git clone "$($(doc)-repository)" . || git pull --autostash
	mkdir -p content/ref && $(CRD_REF_DOCS) --log-level=ERROR --output-path=content/ref/$(doc).md --renderer=markdown --source-path=crd-temp/$(doc)/$($(doc)-path)

.PHONY: api-docs
api-docs: content/ref/service-provider.md content/ref/application-environment-api.md content/ref/gitops.md content/ref/build-service.md content/ref/integration-service.md content/ref/release-service.md content/ref/jvm-build-service.md content/ref/enterprise-contract.md content/ref/devsandbox.md content/ref/internal-services.md

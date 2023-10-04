# Component Detection Query (CDQ) Controller Logic

## CDQ Detection Logic

When the repository is imported, CDQ looks for devfile and dockerfile under context directory. If neither devfile or dockerfile exist, HAS will run [Alizer](https://github.com/devfile/alizer) against the repository to detect components. If there is a component being detected under context, or devfile or dockerfile exists, CDQ will consider the repository is a single component project. Otherwise, it is a multi-component project.

**CDQ Detection Logic for a component:**

* If devfile and dockerfile exist under context, use the devfile and dockerfile.

    Devfile locations, with priority, we look for: `<context>/devfile.yaml` -> `<context>/.devfile.yaml` -> `<context>/.devfile/devfile.yaml` -> `<context>/.devfile/.devfile.yaml`.

    Dockerfile location we look for: `<context>/Dockerfile` -> `<context>/docker/Dockerfile` -> `<context>/.docker/Dockerfile` -> `<context>/build/Dockerfile`
    _Containerfile is an alternative for Dockerfile._

* If only devfile exist under context,  look for Dockerfile definition under devfile image component.
* If only dockerfile exist, use the dockerfile. a proper devfile content will be generated with a matched runtime upon component creation
* If neither file exist, run Alizer to analyze the component and match a devfile and a dockerfile from registry

![](../../diagrams/hybrid-application-service/cdq-detection.jpg)


## CDQ Validation Logic

CDQ validates the devfile to ensure the provided devfile is valid, and with proper outerloop definition. The validation logic is:

* The devfile needs to be valid, which follows the [validation rules](https://devfile.io/docs/2.2.0/devfile-validation-rules)
* The Kubernetes component URI and Kubernetes definition content need to be valid
* If the devfile contains no devfile kubernetes/image components, this means the devfile contains no outerloop definition and CDQ ignores the devfile from provided repository. The CDQ detection logic will fall back to the behavior that with no devfile exists in the repository.
* When the devfile contains no deploy command/apply command, if devfile contains more than one Kubernetes components but with no deploy command being defined, or contains more than one image components but with no apply command being defined. CDQ will error out.

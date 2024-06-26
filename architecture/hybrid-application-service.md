# Hybrid Application Service (HAS)

Hybrid Application Service (HAS) is a component within Konflux that provides Kubernetes webhooks for Application and Component resources

## Webhooks
- Validation webhook for Application CRs that prevents resources from being created with invalid names or display names.
- Validation webhook for Component CRs that ensures valid application name, component name, and source are specified
- Defaulting webhook for Component CRs that configures the OwnerReference for the Component to be that of its parent Application. 
- Webhook to manage the BuildNudgesRef relationship between nudging components: setting and removing nudging components from the status of nudged components


## Links

- Repository: https://github.com/redhat-appstudio/application-service
- Webhook definitions: https://github.com/redhat-appstudio/application-service/tree/main/webhooks


# X. KITE Architecture and Components

Date: 2025-09-08

## Status

Proposed

## Context

The [KITE](https://github.com/Issues-Dashboard/kite) is a proof-of-concept designed to detect, create, and track issues that block application releases in Konflux.

It prevents duplicate issue records, automates issue creation and resolution, and powers the **Issues Dashboard** where teams can view and manage disruptions.

## Concrete Uses Cases and User Workflows
## Why Konflux Issues Dashboard vs External Issue Trackers

The Konflux Issues Dashboard serves a fundamentally different purpose from traditional issue tracking systems like Jira. Rather than replacing external issue management, it acts as an **operational monitoring dashboard**, similar to a car dashboard that alerts you to immediate mechanical problems that need attention *now*, not planning or project management issues.

## Primary Use Cases
**1. Developer Morning Check-in Workflow**

**Scenario**: A developer is managing 8 components across 3 different applications.

**Current Problem**:
- That developer must manually check each component's build and test pipelinerun statuses across multiple views.
- Each view only displays information related to a specific application or component. This leads to more time spent gathering data.


**With Issues Dashboard**:
- The developer opens the Konflux Issues Dashboard
- They have a summary of all existing issues related to their applications, components, etc
- Rather than having to dig through each issue individually across multiple views and then decide what to work on first, issues can be filtered by severity.
  - This allows them to work on critical issues first, potentially unblocking them from moving forward.

**Value**:
- Time saved (e.g. 5-30 minutes daily)
- Immediate awareness of all blocking issues


**2. Cross-Component Failure Correlation**

**Scenario**: A developer notices that his application is failing but doesn't realize it's related to a shared library issue affecting multiple teams.

**Current Problem**: Multiple teams independently debug the same root cause, wasting collective hours.

**With Issues Dashboard**:
- Single issue: "Shared library v2.1 causing build failures"
- **Scope**: Components affected by the same issue can fall under the same [scope](https://github.com/Issues-Dashboard/kite/blob/main/packages/backend/docs/Webhooks.md#issue-grouping-with-scope-objects).
- **Grouping**: By grouping the issues, multiple teams are alerted of the same error, preventing separate debugging efforts.
**Auto-resolution**: When the library is fixed, all related issues can be [resolved automatically](https://github.com/Issues-Dashboard/kite/blob/main/packages/backend/docs/Webhooks.md#automatic-issue-resolution-via-custom-webhooks) because of the shared scope.

**3. User Support Rotation**

**Scenario**: I am an associate on a Konflux Support rotation. A user complains that their application won't build and they don't know why

**Current Problem**:
- Depending on the supporting associates skill set, they may or may not have the knowledge of how to investigate such issues.
  - Querying a Konflux cluster and checking the logs for a failing pipelinerun can require multiple skills that are out of reach for a supporting associate.
- The user might have to navigate through multiple views in order to get a clear picture of what could be the cause.
- A power user capable of investigating logs for a CR on a Konflux cluster still needs to figure out where to check.

**With Issues Dashboard**:
- A non-technical associate can point to the Issues Dashboard and point them towards three issues related to failed builds.
  - Each issue has logs to those builds, allowing for deeper investigation.
- A power-user associate can use the [KITE CLI tool](https://github.com/Issues-Dashboard/kite/tree/main/packages/cli) to quickly check if any existing issue records exist in the namespace(s) the user has access to.
  - The CLI tool reports three build failures in namespace `team-gamma`, with logs for each failure.

**Value**:
- Non-technical support associates can leverage the issues dashboard to quickly show them what is happening where and why.
- Power-user support associates can quickly find the information they need using the CLI tool, getting them closer to where deeper analysis is needed.
- Regular users also have access to these tools, potentially reducing the amount of support tickets filed.

**4. Security Vulnerability Response**

**Scenario**: A critical CVE is discovered in a widely-used dependency (e.g. a container base image, Python package, or RPM package) that affects multiple components across different teams.

**Current Problem**:
- Teams are unaware that MintMaker's automated security updates are failing.
- MintMaker runs Renovate to automatically create PRs/MRs with `[SECURITY]` tags for CVE fixes, but when these fail due to authentication issues, dependency conflicts, or breaking changes, there's no centralized visibility.
- Teams only discover the security exposure during manual audits, security scans, or after incidents occur.

**With Issues Dashboard**:
```
- Issue: "[SECURITY] Critical CVE-2024-1234 in base image - MintMaker updates failing"
- Severity: Critical
- Affected Scope: 15 components across 6 namespaces
- Failure Details:
  • 4 components: GitLab Renovate token expired in namespace secrets
  • 7 components: Container registry authentication failed
  • 3 components: Dependency version conflicts preventing clean updates
  • 1 component: Repository lacks required GitHub App installation
- Direct Links:
  • Failed Renovate execution logs for each component
  • CVE vulnerability details and severity assessment
  • Registry credential setup instructions
  • Dependency conflict resolution guide
```

**Resolution Workflow**:
1. **Immediate Alert**: All affected teams see the security issue in their dashboard when MintMaker detects failures
2. **Targeted Remediation**: Teams can address specific failure causes (refresh tokens, fix registry auth, resolve conflicts)
3. **Progress Tracking**: As MintMaker successfully creates security PRs for each component and those PRs get merged, the issue scope automatically shrinks
4. **Auto-Resolution**: Issue resolves completely when all components have successful security updates merged

**Key Value**:
- Instead of X teams independently discovering a critical security vulnerability days or weeks later through security scanners, all teams are immediately aware with specific remediation steps.
- Security teams can also track organization-wide CVE remediation progress in real-time, meeting compliance requirements more effectively.

## Why This Can't Be Replaced by Jira
1. **Real-time Pipeline Integration**: Records of issues related to failed pipelineruns are created/resolved automatically based on pipeline state changes.
2. **(Potentially) Zero Manual Overhead**: Once teams are integrated, no humans are needed to create, categorize or close issues.
3. **Temporal Context**: Issues exist only while problems exist, no stale issue cleanup should be needed.
4. **Operational Focus**: The Issues Dashboard shows "what is broken right now" not "what work needs to be done"
5. **Cross-team Correlation**: The Issues Dashboard has the ability to group related failures across components and applications, informing multiple teams (if applicable).

## Common Concerns
**Why not use existing issue trackers?**
- External trackers excel at project management and planning
- They're poor at real-time operational alerting and resolution
- Manual overhead of creating/closing issues
- Cross-namespace issue correlation requires K8s-native understanding

**Isn't this just another monitoring tool?**
- The Issues Dashboard complements monitoring by focusing on actionable development items
- The context provided by the dashboard aims to be developer-friendly (failed builds, test failures, dependency problems)

This dashboard fills the gaps between low-level monitoring alerts and high-level project management. It gives developers a single pane view for "what needs my immediate attention to keep shipping software".


## Architecture Overview

The following diagram illustrates the key components and data flow of the KITE system:

```mermaid
graph TB
    subgraph "Konflux Cluster"
        K8S[Kubernetes Resources:<br/> PipelineRuns, Deployments, etc.]
        BO[KITE Bridge Operator]
        CTRL1[PipelineRun Controller]
        CTRL2[Custom Controller A]
        CTRL3[Custom Controller B]
    end

    subgraph "KITE Backend"
        API[KITE Backend API]
        WH[Webhook Endpoints]
        SVC[Issue Service]
        REPO[Issue Repository]
    end

    subgraph "Data Layer"
        PG[(PostgreSQL Database:<br/> Issues Records)]
    end

    subgraph "User Interfaces"
        DASH[Issues Dashboard]
        CLI[KITE CLI Tool]
        EXT[External Tools:<br/> Monitoring, Alerts]
    end

    %% Operator Flow
    BO -->|watches| K8S
    BO -->|watches specific resource| CTRL1
    BO -->|watches specific resource| CTRL2
    BO -->|watches specific resource| CTRL3
    CTRL1 -->|HTTP POST| API
    CTRL2 -->|HTTP POST| API
    CTRL3 -->|HTTP POST| API

    %% Backend Flow
    API -->|handle issue creation or update| SVC
    WH -->|handle issue creation or update| SVC
    SVC -->|Duplicate Prevention| REPO
    REPO -->|ACID Transactions| PG

    %% User Interface Flow
    DASH -->|Query Issues| API
    CLI -->|Query Issues| API
    EXT -->|REST API| API
```

## Decision

We will implement KITE as a distributed system with the following key architectural decisions:

### Bridge Operator Architecture

The **[KITE Bridge Operator](https://github.com/Issues-Dashboard/kite/tree/main/packages/operator)** implements the "bridge operator" pattern, which connects a Kubernetes environment with external systems not natively managed by Kubernetes.

The operator:

- **Monitors Kubernetes Resources**: Watches for events on various cluster resources (currently focusing on Tekton `PipelineRun` objects)
- **Detects State Changes**: Identifies successes or failures in monitored resources
- **Reports to Backend**: Sends failure information to the KITE backend service for persistence
- **Extensible Design**: Can be extended with additional controllers for monitoring other resource types

The operator runs as a standard Kubernetes controller with cluster-wide permissions to monitor resources across namespaces.

### KITE Backend Service

The **[KITE Backend](https://github.com/Issues-Dashboard/kite/tree/main/packages/backend)** is a Go-based REST API service that:

- **Provides API Endpoints**: Offers [REST API](https://github.com/Issues-Dashboard/kite/blob/main/packages/backend/docs/API.md) for creating, updating, and querying issues
- **Webhook Support**: Includes [specialized webhook endpoints](https://github.com/Issues-Dashboard/kite/blob/main/packages/backend/docs/Webhooks.md) for simplified issue creation/resolution
- **Issue Management**: Handles the complete lifecycle of issues (creation, updates, resolution)
- **Database Integration**: Manages all database operations and data persistence
- **Namespace isolation**: Issue access is namespace-restricted for isolation and security. (WIP)

The backend is built using the [Gin](https://github.com/gin-gonic/gin) HTTP web framework and follows standard HTTP API patterns.

### Team Integration Strategy

KITE provides two primary integration paths for teams to onboard their services and start tracking issues:

#### Recommended Integration Path

**1. Build Custom Controllers**
Teams [develop custom controllers](https://github.com/Issues-Dashboard/kite/blob/main/packages/operator/docs/ControllerDevelopmentGuide.md) for the KITE Bridge Operator that:
- **Watch Specific Resources**: Monitor the Kubernetes resources relevant to their services (e.g., Deployments, Jobs, Custom Resources)
- **Detect State Changes**: Identify success and failure conditions based on their service requirements
- **Report to Backend**: Send issue creation/resolution events to the KITE backend via API calls

**2. Implement Custom Webhook Endpoints**
Teams can [develop custom webhook endpoints](https://github.com/Issues-Dashboard/kite/blob/main/packages/backend/docs/Webhooks.md) tailored to their specific events, giving them:
- **Simplified Integration**: Webhooks handle the complexity of issue creation and duplicate checking automatically
- **Custom Payloads**: Design request payloads that match the team's existing monitoring and alerting systems
- **Automatic Resolution**: Webhook endpoints can automatically resolve issues when success events are received

##### Recommended Integration Path Benefits

- **Standardized Integration**: Teams follow the controller + webhook pattern, providing a consistent integration approach
- **Customized Logic**: Teams have full control over their controllers and webhook logic, enabling flexibility for specific use cases
- **Reduced Development Overhead**: Leverage existing KITE infrastructure rather than building custom issue tracking solutions

#### Alternative Integration Approach

For teams that cannot integrate directly with KITE controllers or webhooks, [external service integration](https://github.com/Issues-Dashboard/kite/blob/main/packages/backend/docs/ExternalServiceIntegration.md) is available through:
- **Direct API Usage**: Teams can use the standard REST API to create and manage issues programmatically

### External PostgreSQL Database

We have chosen to use an **external PostgreSQL database** instead of storing issues as Kubernetes Custom Resources in etcd for the following critical reasons:

#### Protecting etcd from Overload

- **High Volume Data**: Issue tracking generates large amounts of data from continuous monitoring of pipeline runs, builds, and other cluster events
- **etcd Limitations**: etcd is optimized for cluster state management, not high-volume application data storage
- **Cluster Stability**: Overloading etcd with issue records could impact overall cluster performance and stability
- **Resource Separation**: Keeping application data separate from Kubernetes cluster state prevents interference

#### Volume and Performance Considerations

- **Issue Frequency**: In a busy Konflux environment, hundreds or thousands of issues could be created daily
- **Data Growth**: Issue records include metadata, logs, relationships, and historical data that grow over time
- **Query Patterns**: Issue tracking requires complex searches, filtering, and reporting that would strain etcd
- **Retention Policies**: Long-term storage of historical issues for trend analysis is better suited to a database

### Duplicate Issue Prevention

The KITE backend implements several mechanisms to prevent duplicate issues from being created:

#### Database-Level Protection

- **Atomic Transactions**: Uses PostgreSQL transactions with row-level locking (`FOR UPDATE`)
- **Concurrent Safety**: Multiple requests for the same issue cannot create duplicates

#### Application-Level Logic

- **Upsert Pattern**: The system always checks for existing issues before creating new ones
- **Duplicate Detection**: Matches issues based on:
  - [Resource scope](https://github.com/Issues-Dashboard/kite/blob/main/packages/backend/docs/Webhooks.md#benefits-of-scope-based-grouping) (type, name, namespace)
  - Issue state (Active/Resolved)

### Automatic Issue Lifecycle Management

KITE implements automatic issue creation, updating and resolution using the combination of a custom controller + webhook. This minimizes manual intervention and prevents duplicate issue records.

#### High-Level Issue Automation Overview

This diagram shows a simplified flow of how KITE automatically detects and manages issues:

```mermaid
flowchart LR
    subgraph "Kubernetes Cluster"
        RESOURCE[Kubernetes Resource:<br/> PipelineRun, Deployment, etc.]
        CONTROLLER[KITE Bridge Operator:<br/> Controllers Watch & Evaluate Kubernetes Resource]
    end

    subgraph "KITE Backend"
        API[KITE API]
        LOGIC[Issue Management: <br> Create/Update/Resolve]
        DB[(PostgreSQL: <br/>Issue Storage)]
    end

    subgraph "User Interface"
        DASHBOARD[Issues Dashboard]
    end

    %% Main Flow
    RESOURCE -->|State Changes| CONTROLLER
    CONTROLLER --> DECISION{Success or Failure?}

    DECISION -->|Failure| FAIL_REQ[POST endpoint to upsert issue]
    DECISION -->|Success| SUCCESS_REQ[POST endpoint to resolve active issues]

    FAIL_REQ -->|Send event| API
    SUCCESS_REQ -->|Send event| API

    API --> LOGIC
    LOGIC <--> DB
    DB --> DASHBOARD
```

### Additional Architectural Decisions

#### Modular Design

- **Separate Packages**: Backend, CLI, and Operator are independent packages
- **Clear Interfaces**: Well-defined APIs between components
- **Independent Deployment**: Components can be deployed and scaled independently

#### Configuration Management

- **Environment Variables**: Extensive use of environment-based configuration
- **Feature Flags**: Ability to enable/disable features like namespace checking and webhooks

#### Development & Operations

- **Container-First**: All components designed for containerized deployment
- **Health Checks**: Built-in health endpoints for monitoring
- **Logging**: Structured logging with configurable levels and formats
- **Metrics**: Support for metrics collection (when enabled)

## Requirements Alignment
This section demonstrates how KITE's architecture addresses the [specified project requirements](https://docs.google.com/document/d/1HbNCqbrpfOi1MR7oYoaUTINIu5rAQ_bVy1NJCnDqYzM/edit?tab=t.0#heading=h.nk0gqur98cd3).

### Dashboard with issues

**Requirement**: Dashboard with issues, an issue groups one or multiple events that have the same cause or are otherwise connected.

- **Implementation**: Issues Dashboard provides centralized view (UI TODO)
- **Grouping Logic**: Issues are grouped by scope objects (namespace, resource type, resource name) preventing duplicates
- **Real-time Updates**: Dashboard reflects current issue states as they're created, updated, and resolved

### Scope Support
**Requirement**:

- Scope:
  - Workspace/Namespace
  - Application
  - Component
  - PipelineRun

**Implementation**:

- Database schema includes flexible scope objects with `resourceType`, `resourceName`, `resourceNamespace`
- Controllers can monitor any Kubernetes resource type
- Extensible scope model supports future scope types

### Filtering and Search Capabilities
**Requirement**:

- User can filter out issues based on their:
  - Issue type (failed releases, failed builds, MintMaker fails)
  - Severity (warning, error/fail, information)
  - Scope (which components or applications we care about)
  - Issue being connected to development pipelines or releasable/production content.

**Implementation**:

- REST API supports comprehensive filtering parameters
- Search functionality across issue titles and descriptions
- Scope-based filtering enables component/application-specific views


### Debugging and Links Support

**Requirement**: Users can get through the links in the issue to the logs or other information needed to debug and resolve the problem

**Implementation**:

- Issue model includes `links` array for pipeline logs, dashboards, etc.
- Controllers and webhooks can add relevant debugging URLs
- Structured link storage with titles and descriptions for context


### Extensibility

**Requirement**: Dashboard must be easily extendable, especially when it comes to adding new issue types.

**Implementation**:

- **Controller Framework**: Bridge Operator pattern allows easy addition of new resource monitors
- **Webhook System**: Custom webhook endpoints can be added without code changes
- **API Design**: RESTful API structure supports extension without breaking changes
- **Database Schema**: Flexible issue and scope models support new issue types

### Issue Types and Automatic Resolution

**Requirements**:

- I want issues to be automatically resolved if the underlying problem is solved.
- I want to see issues for:
  - Failed integration tests
  - Failed builds (PR and Push)
  - Special filtering for MintMaker PRs
  - Show due dates when they exist
  - Show migration information when it exists
  - Failed releases (both tenant and managed)
  - Failed pipeline runs (even catastrophic failures when the pipeline does not run at all)
  - MintMaker / Dependency management issues

**Implementation**:

- **Build Failures**: Custom/PipelineRun controller detects failed builds, resolves on successful runs
- **Integration Test Failures**: Custom controller(s) can be added for integration test monitoring
- **Release Failures**: Custom controllers can be added to monitor release failures
- **MintMaker Issues**: Webhook endpoints and/or custom controllers can be configured for dependency management failures
- **Tekton Task Updates**: Controllers can monitor task definitions and create issue records on pending updates

### Deployment and integration

**Requirements**:

- The project is developed as a Kubernetes native project independent of the Konflux community.
- The dashboard is optional for a Konflux deployment (a Konflux add-on).

**Implementation**:

- **Kubernetes Native**: All components deployed as standard K8s resources
- **Add-on Architecture**: This is designed to be standalone and extend Konflux

### API Access for External Tools

**Requirement**: Provide an API so external CI tools (for example RHEL on GitLab) can query issues related to a particular pipeline run.

**Implementation**:

- RESTful API with comprehensive filtering by resource type, name, namespace
- Query endpoints support pipeline run identification
- JSON responses suitable for programmatic consumption


### Error Handling and Debugging

**Requirement**: UI should reflect backend API errors where they are happening for easier debugging

**Implementation**:

- Structured error responses from backend API
- HTTP status codes and error messages can be propagated to dashboard (UI TODO)
- Logging framework captures detailed error information
- Health check endpoints for monitoring KITE component statuses

## Consequences

### Positive

- **Scalability**: External database can handle large volumes of issue data while not overloading etcd
- **Performance**: Database optimizations enable fast queries and reporting
- **Extensibility**: Bridge operator pattern allows easy addition of new resource monitors
- **Data Integrity**: Strong consistency guarantees prevent duplicate issues

### Negative

- **Complexity**: Additional infrastructure component (PostgreSQL, Stand-alone API, additional controllers) to manage
- **Dependencies**: System requires external database availability
- **Cost**: Additional resources needed for database hosting and management
- **Network**: Additional network hops between operator and backend

### Future Considerations

- **Multi-Cluster Support**: Architecture supports scaling across multiple Konflux clusters
- **Controller Expansion**: The architecture supports adding monitors for additional resource types
- **Controller Config**: A configuration file where users can select which controllers they want to use, rather than all
- **Integration Points**: API design supports integration with external tools and dashboards
- **MCP Server Integration**: The REST API architecture enables KITE to serve as an MCP (Model Context Protocol) server:
  - **Real-time Issue Context**: AI assistants could query current cluster issues and their status
  - **Interactive Troubleshooting**: Enable AI-powered tools (maybe via the [KITE CLI](https://github.com/Issues-Dashboard/kite/tree/main/packages/cli) tool) to help users understand and resolve issues

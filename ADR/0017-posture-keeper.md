# 17. Posture Keeper

Date: 2023-02-18

## Status

Accepted

## Context
Posture keeper is a REST-based web service that allows clients to store and retrieve SAST analysis data for a specific git repository and commit SHA. The service is designed to be scalable, reliable, and secure, and uses MongoDB as its underlying data store. The service is implemented using Quarkus. By utilizing this service StoneSoup is going to be able to provides experiences that reflects the current state of security and/or quality posture of the applications.

## Design Goals

The following are the key design goals of the service:

* Support storing and retrieving SAST analysis data for a specific git repository and commit SHA
* Accept and produce JSON-formatted data
* Use MongoDB as the underlying data store for efficient data retrieval and storage
* Support secure authentication and authorization to ensure only authorized clients can upload and retrieve data
* Implement rate limiting for the POST endpoint to prevent abuse and ensure optimal performance
* Implement pagination for the GET endpoint to efficiently retrieve large volumes of data

## Architecture

The Posture Keeper is implemented as a microservice using Quarkus. The architecture consists of the following components:

### Client

The client is responsible for making requests to the service endpoints using HTTP. Clients can be web applications, mobile applications, or any other type of application that can communicate over HTTP.

### REST API

The REST API is implemented using Quarkus. The API provides endpoints for storing and retrieving SAST analysis data for a specific git repository and commit SHA. It also provides an endpoint for comparing two analysis results and returning the new defects.

The REST API is designed to accept and produce JSON-formatted data. It uses the Quarkus framework to handle HTTP requests and responses, and uses the MongoDB driver to interact with the MongoDB database.

### MongoDB

MongoDB is used as the underlying data store for the service. It stores the uploaded SARIF files as plain JSON data, along with metadata such as the repository URL, commit SHA, and tool name.

The MongoDB database is designed to be scalable, reliable, and efficient. It uses sharding and replication to ensure data availability and reliability. It also uses indexes to ensure efficient data retrieval.

### Authentication and Authorization

The service uses a secure authentication and authorization mechanism to ensure that only authorized clients can upload and retrieve SAST analysis data.

### Rate Limiting

The service implements rate limiting for the POST endpoint to prevent abuse and ensure optimal performance. The rate limiting can be implemented using Quarkus' built-in support for rate limiting.

### Pagination

The service implements pagination for the GET endpoint to efficiently retrieve large volumes of data. The pagination can be implemented using the MongoDB driver.

## Consequences

* With the introduction of the service the pipelines that do SAST analysis should upload thier results to the service
* The experience around displaying the security and quality posture of applications should enhance with the usage of the data provided by the service.


# Hydrocron Architecture

This document renders the Structurizr C4 model defined in [`docs/architecture.dsl`](docs/architecture.dsl) as
Mermaid diagrams so it's viewable directly on GitHub. That DSL file is the source of truth &mdash; if the
architecture changes, update it first and regenerate these diagrams to match.

## System Context

Hydrocron repackages SWOT hydrology granules into timeseries-friendly CSV, JSON, and GeoJSON, served over a
REST API.

```mermaid
graph LR
    dataUser(["Data User"])
    maintainer(["Hydrocron Maintainer"])
    cmr[["NASA CMR"]]
    earthdata[["NASA Earthdata Cloud"]]
    cumulus[["PO.DAAC Cumulus\nIngest Pipeline"]]
    hydrocron[["Hydrocron"]]

    dataUser -->|"GET /timeseries\nHTTPS, API key"| hydrocron
    hydrocron -->|"CSV / JSON / GeoJSON"| dataUser
    maintainer -->|"Manual backfill trigger"| hydrocron
    hydrocron -->|"Query granule metadata\nHTTPS/REST"| cmr
    hydrocron -->|"Read shapefile granules\nS3"| earthdata
    cumulus -->|"Publishes CNM-R notification\nSNS"| hydrocron

    classDef person fill:#08427b,color:#fff,stroke:#052e56;
    classDef external fill:#999999,color:#fff,stroke:#6b6b6b;
    classDef system fill:#1168bd,color:#fff,stroke:#0b4884;
    class dataUser,maintainer person;
    class cmr,earthdata,cumulus external;
    class hydrocron system;
```

## Containers

```mermaid
graph LR
    dataUser(["Data User"])
    maintainer(["Hydrocron Maintainer"])
    cmr[["NASA CMR"]]
    earthdata[["NASA Earthdata Cloud"]]
    cumulus[["PO.DAAC Cumulus\nIngest Pipeline"]]

    subgraph hydrocron["Hydrocron"]
        subgraph api["API"]
            apiGateway["API Gateway"]
            authorizerLambda["Authorizer Lambda"]
            timeseriesLambda["Timeseries API Lambda"]
        end

        subgraph ingest["Ingest Pipeline"]
            scheduler["EventBridge Scheduler"]
            trackIngestLambda["Track Ingest Lambda"]
            loadDataLambda["Load Data Lambda"]
            loadGranuleLambda["Load Granule Lambda"]
            cnmLambda["CNM Response Lambda"]
            snsTopic["CNM Response Topic"]
        end

        subgraph data["Data Stores"]
            ssmParams[("SSM Parameter Store")]
            reachTable[("Reach Table(s)")]
            nodeTable[("Node Table(s)")]
            priorLakeTable[("Prior Lake Table(s)")]
            trackIngestTable[("Ingest Status Table(s)")]
        end
    end

    dataUser -->|"GET /timeseries"| apiGateway
    apiGateway -->|"Authorize request"| authorizerLambda
    authorizerLambda -->|"Read stored API keys"| ssmParams
    apiGateway -->|"Route authorized request"| timeseriesLambda
    timeseriesLambda -->|"Query"| reachTable
    timeseriesLambda -->|"Query"| nodeTable
    timeseriesLambda -->|"Query"| priorLakeTable
    timeseriesLambda -->|"CSV / JSON / GeoJSON"| dataUser

    maintainer -->|"Manual backfill invoke"| loadDataLambda

    scheduler -->|"Weekly trigger"| trackIngestLambda
    trackIngestLambda -->|"Query new/revised granules"| cmr
    trackIngestLambda -->|"Read/write ingest status"| trackIngestTable
    trackIngestLambda -->|"Read/write last-run timestamp"| ssmParams
    trackIngestLambda -->|"Dispatch granule load"| loadGranuleLambda

    loadDataLambda -->|"Search granules"| cmr
    loadDataLambda -->|"Dispatch granule load"| loadGranuleLambda

    loadGranuleLambda -->|"Read shapefile granule"| earthdata
    loadGranuleLambda -->|"Write parsed features"| reachTable
    loadGranuleLambda -->|"Write parsed features"| nodeTable
    loadGranuleLambda -->|"Write parsed features"| priorLakeTable
    loadGranuleLambda -->|"Record status"| trackIngestTable

    cumulus -->|"Publish CNM-R"| snsTopic
    snsTopic -->|"Trigger subscription"| cnmLambda
    cnmLambda -->|"Dispatch granule load"| loadGranuleLambda

    classDef person fill:#08427b,color:#fff,stroke:#052e56;
    classDef external fill:#999999,color:#fff,stroke:#6b6b6b;
    classDef lambda fill:#f58536,color:#fff,stroke:#b85f1d;
    classDef gateway fill:#d86613,color:#fff,stroke:#a34e0e;
    classDef queue fill:#a166ab,color:#fff,stroke:#7a4a80;
    classDef store fill:#7d8998,color:#fff,stroke:#5b636e;
    classDef database fill:#3b48cc,color:#fff,stroke:#28329c;
    class dataUser,maintainer person;
    class cmr,earthdata,cumulus external;
    class apiGateway gateway;
    class authorizerLambda,timeseriesLambda,trackIngestLambda,loadDataLambda,loadGranuleLambda,cnmLambda lambda;
    class scheduler store;
    class snsTopic queue;
    class ssmParams store;
    class reachTable,nodeTable,priorLakeTable,trackIngestTable database;
```

## API Query Flow

How a data user retrieves a timeseries.

```mermaid
sequenceDiagram
    actor User as Data User
    participant GW as API Gateway
    participant Auth as Authorizer Lambda
    participant SSM as SSM Parameter Store
    participant TS as Timeseries API Lambda
    participant Reach as Reach Table(s)

    User->>GW: GET /timeseries?feature=Reach&reach_id=...&start_time=...&end_time=...
    GW->>Auth: Authorize request
    Auth->>SSM: Look up API key
    GW->>TS: Forward authorized request
    TS->>Reach: Query by reach_id and time range
    TS-->>User: CSV / JSON / GeoJSON response
```

## Scheduled Ingest Flow

How new SWOT granules are discovered and loaded on a weekly schedule.

```mermaid
sequenceDiagram
    participant Sched as EventBridge Scheduler
    participant Track as Track Ingest Lambda
    participant CMR as NASA CMR
    participant Status as Ingest Status Table(s)
    participant LoadG as Load Granule Lambda
    participant S3 as NASA Earthdata Cloud
    participant Reach as Reach Table(s)

    Sched->>Track: Weekly trigger for a feature type
    Track->>CMR: Query for new/revised granules
    Track->>Status: Record status: to_ingest
    Track->>LoadG: Dispatch granule for loading
    LoadG->>S3: Read shapefile granule
    LoadG->>Reach: Write parsed features
    LoadG->>Status: Update status: ingested
```

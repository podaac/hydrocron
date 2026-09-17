workspace "Hydrocron" "C4 model of the Hydrocron SWOT hydrology timeseries API and its data ingest pipeline." {

    model {
        dataUser = person "Data User" "A scientist, researcher, or application that queries Hydrocron for SWOT river, lake, and node timeseries data. Authenticates with a default or trusted-partner API key." "Person"
        maintainer = person "Hydrocron Maintainer" "PO.DAAC/TVA team member who deploys Hydrocron via Terraform and manually triggers historical/backfill data loads." "Person"

        cmr = softwareSystem "NASA CMR" "Common Metadata Repository. Catalogs SWOT granule metadata (collections, revision dates, checksums, S3 locations) queried via python-cmr and earthaccess." "External System"
        earthdataCloud = softwareSystem "NASA Earthdata Cloud" "PO.DAAC's cloud archive (S3) holding published SWOT L2_HR_RiverSP and L2_HR_LakeSP shapefile granules." "External System"
        cumulus = softwareSystem "PO.DAAC Cumulus Ingest Pipeline" "NASA Cumulus instance that ingests new SWOT granules and publishes Cumulus Notification Messages (CNM-R) when data becomes available." "External System"

        hydrocron = softwareSystem "Hydrocron" "Repackages SWOT hydrology granules into timeseries-friendly CSV, JSON, and GeoJSON, served over a REST API." "HydrocronSystem" {

            apiGateway = container "API Gateway" "Private REST API exposing the /timeseries endpoint; enforces per-key usage plans and quotas." "Amazon API Gateway" "APIGateway"
            authorizerLambda = container "Authorizer Lambda" "Custom Lambda authorizer that validates the x-hydrocron-key header against stored API keys and assigns the caller's usage plan." "AWS Lambda (Python)" "Lambda"
            timeseriesLambda = container "Timeseries API Lambda" "Parses query parameters, queries feature tables by ID and time range, and formats the response as CSV, JSON, or GeoJSON." "AWS Lambda (Python)" "Lambda"

            scheduler = container "EventBridge Scheduler" "Weekly scheduled triggers, one each for reach, node, and prior lake collections." "Amazon EventBridge Scheduler" "Scheduler"
            trackIngestLambda = container "Track Ingest Lambda" "Queries CMR for new or revised granules since the last run, records their ingest status, and dispatches loads for anything missing or updated." "AWS Lambda (Python)" "Lambda"
            loadDataLambda = container "Load Data Lambda" "Searches CMR for granules in a given collection/date range and dispatches each for loading. Used for manual/backfill loads." "AWS Lambda (Python)" "Lambda"
            loadGranuleLambda = container "Load Granule Lambda" "Reads a single SWOT shapefile granule from S3, parses reach/node/prior-lake features, and writes them to DynamoDB." "AWS Lambda (Python)" "Lambda"
            cnmLambda = container "CNM Response Lambda" "Unpacks incoming CNM-R notifications from SNS and dispatches the referenced granule for loading." "AWS Lambda (Python)" "Lambda"
            snsTopic = container "CNM Response Topic" "Receives Cumulus Notification Messages (CNM-R) for newly published SWOT granules." "Amazon SNS" "Queue"

            ssmParams = container "SSM Parameter Store" "Holds API keys, Earthdata Login credentials, and per-collection last-run timestamps." "AWS Systems Manager Parameter Store" "Store"
            reachTable = container "Reach Table(s)" "Reach-level timeseries, keyed by reach_id and range_start_time, with a GranuleUR GSI. One table pair per collection version." "Amazon DynamoDB" "Database"
            nodeTable = container "Node Table(s)" "Node-level timeseries, keyed by node_id and range_start_time, with a GranuleUR GSI. One table pair per collection version." "Amazon DynamoDB" "Database"
            priorLakeTable = container "Prior Lake Table(s)" "Prior-lake-level timeseries, keyed by lake_id and range_start_time, with a GranuleUR GSI. One table pair per collection version." "Amazon DynamoDB" "Database"
            trackIngestTable = container "Ingest Status Table(s)" "Tracks per-granule ingest status (to_ingest/ingested/failed) and feature counts, keyed by granuleUR and revision_date." "Amazon DynamoDB" "Database"
        }

        # API query path
        dataUser -> apiGateway "Requests SWOT timeseries (GET /timeseries) with API key" "HTTPS"
        apiGateway -> authorizerLambda "Invokes to authorize request and resolve usage plan" "AWS Lambda invoke"
        authorizerLambda -> ssmParams "Reads stored default/trusted API keys" "AWS SDK"
        apiGateway -> timeseriesLambda "Routes authorized request to" "AWS Lambda invoke"
        timeseriesLambda -> reachTable "Queries reach timeseries by feature ID and time range" "AWS SDK (boto3)"
        timeseriesLambda -> nodeTable "Queries node timeseries by feature ID and time range" "AWS SDK (boto3)"
        timeseriesLambda -> priorLakeTable "Queries prior lake timeseries by feature ID and time range" "AWS SDK (boto3)"
        timeseriesLambda -> dataUser "Returns timeseries as CSV, JSON, or GeoJSON"

        # Manual / backfill path
        maintainer -> loadDataLambda "Manually invokes for historical or backfill data loads" "AWS Lambda invoke"

        # Scheduled tracking / ingest path
        scheduler -> trackIngestLambda "Triggers weekly ingest run per feature type (reach/node/prior lake)" "Amazon EventBridge"
        trackIngestLambda -> cmr "Queries for new and revised granules by revision date" "HTTPS/REST (python-cmr)"
        trackIngestLambda -> trackIngestTable "Reads/writes per-granule ingest status" "AWS SDK (boto3)"
        trackIngestLambda -> ssmParams "Reads/writes last-run timestamp; reads Earthdata credentials" "AWS SDK (boto3)"
        trackIngestLambda -> loadGranuleLambda "Invokes asynchronously to load a missing or updated granule" "AWS Lambda invoke"

        loadDataLambda -> cmr "Searches for granules in a collection/date range" "HTTPS/REST (earthaccess)"
        loadDataLambda -> loadGranuleLambda "Invokes asynchronously for each discovered granule" "AWS Lambda invoke"

        loadGranuleLambda -> earthdataCloud "Downloads and reads a SWOT shapefile granule" "Direct S3 access (earthaccess)"
        loadGranuleLambda -> reachTable "Writes parsed reach features" "AWS SDK (boto3)"
        loadGranuleLambda -> nodeTable "Writes parsed node features" "AWS SDK (boto3)"
        loadGranuleLambda -> priorLakeTable "Writes parsed prior lake features" "AWS SDK (boto3)"
        loadGranuleLambda -> trackIngestTable "Records ingest status and feature counts" "AWS SDK (boto3)"

        # CNM notification path
        cumulus -> snsTopic "Publishes CNM-R notification on new/updated granule availability" "Amazon SNS"
        snsTopic -> cnmLambda "Triggers subscription with CNM-R message" "Amazon SNS"
        cnmLambda -> loadGranuleLambda "Invokes asynchronously with granule path parsed from the CNM-R message" "AWS Lambda invoke"
    }

    views {
        systemContext hydrocron "SystemContext" "High-level view of Hydrocron and the external actors and systems it interacts with." {
            include *
            autoLayout lr
        }

        container hydrocron "Containers" "Container-level view of Hydrocron's API and data ingest pipeline." {
            include *
            autoLayout lr
        }

        dynamic hydrocron "APIQueryFlow" "How a data user retrieves a timeseries." {
            dataUser -> apiGateway "GET /timeseries?feature=Reach&reach_id=...&start_time=...&end_time=..."
            apiGateway -> authorizerLambda "Authorize request"
            authorizerLambda -> ssmParams "Look up API key"
            apiGateway -> timeseriesLambda "Forward authorized request"
            timeseriesLambda -> reachTable "Query by reach_id and time range"
            timeseriesLambda -> dataUser "CSV / JSON / GeoJSON response"
            autoLayout lr
        }

        dynamic hydrocron "ScheduledIngestFlow" "How new SWOT granules are discovered and loaded on a weekly schedule." {
            scheduler -> trackIngestLambda "Weekly trigger for a feature type"
            trackIngestLambda -> cmr "Query for new/revised granules"
            trackIngestLambda -> trackIngestTable "Record status: to_ingest"
            trackIngestLambda -> loadGranuleLambda "Dispatch granule for loading"
            loadGranuleLambda -> earthdataCloud "Read shapefile granule"
            loadGranuleLambda -> reachTable "Write parsed features"
            loadGranuleLambda -> trackIngestTable "Update status: ingested"
            autoLayout lr
        }

        styles {
            element "Person" {
                shape person
                background #08427b
                color #ffffff
            }
            element "External System" {
                shape roundedbox
                background #999999
                color #ffffff
            }
            element "HydrocronSystem" {
                background #1168bd
                color #ffffff
            }
            element "Container" {
                background #438dd5
                color #ffffff
            }
            element "Lambda" {
                shape hexagon
                background #f58536
                color #ffffff
            }
            element "APIGateway" {
                shape hexagon
                background #d86613
                color #ffffff
            }
            element "Scheduler" {
                shape hexagon
                background #7d8998
                color #ffffff
            }
            element "Queue" {
                shape pipe
                background #a166ab
                color #ffffff
            }
            element "Store" {
                shape cylinder
                background #7d8998
                color #ffffff
            }
            element "Database" {
                shape cylinder
                background #3b48cc
                color #ffffff
            }
        }
    }
}

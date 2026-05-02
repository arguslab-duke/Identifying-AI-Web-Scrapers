# Identifying AI Web Scrapers Using Canary Tokens
## ACM CCS 2026 Artifact Submission

All data has been anonymized to avoid revealing specific information about our deployed websites, as the sites are being used in ongoing research.

This repository contains:
- An example of one of our websites (one used during our pilot study, not used for data collection) and its backend
- All of the filtered data used in our paper

### ./data
Data is provided for each stage of queries (1-3). Within each stage folder there is data from condition 1 (fully online), condition 2 (offline), condition 3 (blocked). Folders saying "prev cond 2" or "prev cond 3" have returned to condition 1 (fully online) after being in condition 2 or condition 3 respectively. For a better understanding, Figure 3 in the paper outlines this visually.

Data files contain a list of [User-Agent, ASN] pairs matched from the raw LLM responses. There is one data file per chat session where canary tokens were successfully matched and filtered, numbered 21-40 to represent which of our websites said query was about. Each individual canary token is shown once per data file, making a maximum of ten canary token matches from each website per unique visitor (User-Agent + ASN).

### ./website - Getting started
Our website backend relies on a Google Cloud Run and Google Cloud SQL infastructure that [must first be setup in order to run](https://developers.google.com/workspace/guides/create-project).

#### Setting up Google Cloud:

- For the project name, use ```scraper1-proj```. For the region, use ```us-central1```.

- You will need to [initiate a Google Cloud SQL database using PostgreSQL](https://docs.cloud.google.com/sql/docs/introduction). Name the instance ```template-db```. Note the password you set for authentication for use in the environment variables below.


#### Running locally:
- Install all requirements from ```./data/requirements.txt```.

- Download and install the [Google Cloud SQL Auth Proxy](https://docs.cloud.google.com/sql/docs/mysql/sql-proxy).

- Initiate the proxy:
```
./cloud-sql-proxy scraper1-proj:us-central1:template-db
```


- Now, in a second terminal, set the following environment variables:
```
export PROJECT_ID="scraper1-proj"
export SCRAPER_VERSION="1"
export SERVICE_NAME="scraper$SCRAPER_VERSION-serv"
export DB_NAME="scraper$SCRAPER_VERSION-db"
export DB_USER="postgres"
export DB_PASS=[password you set earlier]
export REGION="us-central1"
```

- And finally, simply run the server:
``` python server.py```
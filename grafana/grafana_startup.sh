#!/bin/bash

# Ensure required directories exist
mkdir -p /etc/grafana/provisioning/datasources
mkdir -p /etc/grafana/provisioning/dashboards

# Generate datasource configuration using environment variables
cat <<EOF > /etc/grafana/provisioning/datasources/datasource.yml
apiVersion: 1

datasources:
  - name: InfluxDB
    type: influxdb
    url: http://${INFLUXDB_HOST:-influxdb}:${INFLUXDB_PORT:-8086}
    access: proxy
    isDefault: true
    jsonData:
      organization: ${DOCKER_INFLUXDB_INIT_ORG}
      defaultBucket: ${DOCKER_INFLUXDB_INIT_BUCKET}
      version: Flux
    secureJsonData:
      token: ${DOCKER_INFLUXDB_INIT_GRAFANA_TOKEN}
EOF

# Generate dashboard provisioning configuration
cat <<EOF > /etc/grafana/provisioning/dashboards/dashboard-provisioning.yml
apiVersion: 1

providers:
  - name: 'ITE_Dashboards'
    orgId: 1
    folder: ''
    type: 'file'
    disableDeletion: false
    updateIntervalSeconds: 10
    options:
      path: /etc/grafana/provisioning/dashboards/ite.json
EOF

# Start Grafana
exec /run.sh



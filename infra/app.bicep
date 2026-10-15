param location string = 'westus2'
param image string
param registryServer string
param identityId string
param environmentId string
param publicHost string
param appName string = 'matchlens-dev'
param storageUrl string = ''
param clientId string = ''
// Keep MCP discovery available without a scale-from-zero startup delay.
param minReplicas int = 1
resource app 'Microsoft.App/containerApps@2025-01-01' = {
  name: appName
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: { '${identityId}': {} }
  }
  properties: {
    managedEnvironmentId: environmentId
    workloadProfileName: 'Consumption'
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
        allowInsecure: false
      }
      registries: [{ server: registryServer, identity: identityId }]
    }
    template: {
      containers: [{
        name: 'matchlens'
        image: image
        env: [
          { name: 'MATCHLENS_PUBLIC_HOST', value: publicHost }
          { name: 'MATCHLENS_STORAGE_URL', value: storageUrl }
          { name: 'AZURE_CLIENT_ID', value: clientId }
        ]
        resources: { cpu: json('0.25'), memory: '0.5Gi' }
        probes: [
          { type: 'Liveness', httpGet: { path: '/health', port: 8000 }, periodSeconds: 30 }
          { type: 'Readiness', httpGet: { path: '/health', port: 8000 }, periodSeconds: 10 }
        ]
      }]
      scale: {
        minReplicas: minReplicas
        maxReplicas: 1
        rules: [{ name: 'http', http: { metadata: { concurrentRequests: '20' } } }]
      }
    }
  }
}
output url string = 'https://${app.properties.configuration.ingress.fqdn}'
output mcpUrl string = 'https://${app.properties.configuration.ingress.fqdn}/mcp'

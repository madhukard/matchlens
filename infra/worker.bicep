param location string = 'westus2'
param image string
param registryServer string
param identityId string
param clientId string
param environmentId string
param storageUrl string
param aiEndpoint string = 'https://matchlens-dev-ai-1f5dc8.openai.azure.com'
resource job 'Microsoft.App/jobs@2025-01-01' = {
  name: 'matchlens-live-worker'
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: { '${identityId}': {} }
  }
  properties: {
    environmentId: environmentId
    workloadProfileName: 'Consumption'
    configuration: {
      triggerType: 'Manual'
      replicaTimeout: 1200
      replicaRetryLimit: 0
      manualTriggerConfig: { parallelism: 1, replicaCompletionCount: 1 }
      registries: [{ server: registryServer, identity: identityId }]
    }
    template: {
      containers: [{
        name: 'worker'
        image: image
        command: ['python', '-m', 'matchlens.worker']
        args: ['--interval', '2']
        env: [
          { name: 'AZURE_CLIENT_ID', value: clientId }
          { name: 'AZURE_OPENAI_ENDPOINT', value: aiEndpoint }
          { name: 'MATCHLENS_MODEL', value: 'gpt-6-sol' }
          { name: 'MATCHLENS_STORAGE_URL', value: storageUrl }
        ]
        resources: { cpu: json('0.25'), memory: '0.5Gi' }
      }]
    }
  }
}

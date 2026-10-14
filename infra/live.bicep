param location string = 'westus2'
param storageName string = 'matchlenslive1f5dc8'
param registryName string = 'matchlensdev1f5dc8'
param aiName string = 'matchlens-dev-ai-1f5dc8'

resource runtime 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' existing = {
  name: 'matchlens-dev-runtime'
}
resource worker 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'matchlens-dev-worker'
  location: location
}
resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageName
  location: location
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
  properties: {
    supportsHttpsTrafficOnly: true
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false
  }
}
resource blob 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: storage
  name: 'default'
  properties: { deleteRetentionPolicy: { enabled: true, days: 7 } }
}
resource runs 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: blob
  name: 'runs'
  properties: { publicAccess: 'None' }
}
resource read 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(runs.id, runtime.id, 'reader')
  scope: runs
  properties: {
    principalId: runtime.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1')
  }
}
resource write 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(runs.id, worker.id, 'writer')
  scope: runs
  properties: {
    principalId: worker.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
  }
}
resource ai 'Microsoft.CognitiveServices/accounts@2024-10-01' existing = { name: aiName }
resource inference 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(ai.id, worker.id, 'inference')
  scope: ai
  properties: {
    principalId: worker.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd')
  }
}
resource registry 'Microsoft.ContainerRegistry/registries@2023-07-01' existing = { name: registryName }
resource pull 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(registry.id, worker.id, 'acrpull')
  scope: registry
  properties: {
    principalId: worker.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d')
  }
}
output storageUrl string = storage.properties.primaryEndpoints.blob
output workerId string = worker.id
output workerClientId string = worker.properties.clientId
output runtimeClientId string = runtime.properties.clientId

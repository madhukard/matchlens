param location string = resourceGroup().location
param registryName string
param environmentName string = 'matchlens-dev-env-west'
param environmentLocation string = 'westus2'
resource registry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: registryName
  location: location
  sku: { name: 'Basic' }
  properties: { adminUserEnabled: false }
}
resource identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'matchlens-dev-runtime'
  location: location
}
resource pull 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(registry.id, identity.id, 'acrpull')
  scope: registry
  properties: {
    principalId: identity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d')
  }
}
resource environment 'Microsoft.App/managedEnvironments@2025-01-01' = {
  name: environmentName
  location: environmentLocation
  properties: {
    workloadProfiles: [{ name: 'Consumption', workloadProfileType: 'Consumption' }]
  }
}
output registryServer string = registry.properties.loginServer
output identityId string = identity.id
output environmentId string = environment.id
output defaultDomain string = environment.properties.defaultDomain

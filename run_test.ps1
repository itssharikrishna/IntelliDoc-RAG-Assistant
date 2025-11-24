# If ExecutionPolicy blocks, run this first in the same PowerShell:
# Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# run_test.ps1
$ErrorActionPreference = "Stop"

# 1) Create HttpClient
$handler = New-Object System.Net.Http.HttpClientHandler
$handler.AllowAutoRedirect = $true
$client = New-Object System.Net.Http.HttpClient($handler)
$client.Timeout = [System.TimeSpan]::FromMinutes(10)

# Base URL
$base = "http://127.0.0.1:8000"

Write-Host "Logging in..."
# 2) Login (form-url-encoded)
$loginList = New-Object 'System.Collections.Generic.List[System.Collections.Generic.KeyValuePair[String,String]]'
$loginList.Add((New-Object System.Collections.Generic.KeyValuePair[string,string]("username","admin")))
$loginList.Add((New-Object System.Collections.Generic.KeyValuePair[string,string]("password","adminpass")))
$formContent = New-Object System.Net.Http.FormUrlEncodedContent($loginList)

$loginResp = $client.PostAsync("$base/admin/login", $formContent).Result
$loginBody = $loginResp.Content.ReadAsStringAsync().Result
if (-not $loginResp.IsSuccessStatusCode) {
    Write-Error "Login failed: $($loginResp.StatusCode) `n$loginBody"
    exit 1
}
$token = (ConvertFrom-Json $loginBody).access_token
Write-Host "Got token (truncated):" $token.Substring(0,40) "..."

# 3) Upload file (multipart/form-data)
$samplePath = Join-Path (Get-Location) "sample.pdf"
if (-not (Test-Path $samplePath)) {
    Write-Error "sample.pdf not found at $samplePath. Place sample.pdf in project root and re-run."
    exit 1
}

Write-Host "Uploading sample.pdf..."
$multipart = New-Object System.Net.Http.MultipartFormDataContent

# file content
$fileStream = [System.IO.File]::OpenRead($samplePath)
$fileContent = New-Object System.Net.Http.StreamContent($fileStream)
$fileContent.Headers.ContentDisposition = New-Object System.Net.Http.Headers.ContentDispositionHeaderValue("form-data")
$fileContent.Headers.ContentDisposition.Name = '"file"'
$fileContent.Headers.ContentDisposition.FileName = '"' + [System.IO.Path]::GetFileName($samplePath) + '"'
$fileContent.Headers.ContentType = [System.Net.Http.Headers.MediaTypeHeaderValue]::Parse("application/pdf")
$multipart.Add($fileContent, "file", [System.IO.Path]::GetFileName($samplePath))

# token part
$tokenContent = New-Object System.Net.Http.StringContent($token)
$tokenContent.Headers.ContentDisposition = New-Object System.Net.Http.Headers.ContentDispositionHeaderValue("form-data")
$tokenContent.Headers.ContentDisposition.Name = '"token"'
$multipart.Add($tokenContent, "token")

$uploadResp = $client.PostAsync("$base/admin/upload", $multipart).Result
$uploadBody = $uploadResp.Content.ReadAsStringAsync().Result
if (-not $uploadResp.IsSuccessStatusCode) {
    Write-Error "Upload failed: $($uploadResp.StatusCode) `n$uploadBody"
    $fileStream.Dispose()
    exit 1
}
Write-Host "Upload response:" $uploadBody
$fileStream.Dispose()

# 4) Query the server
Write-Host "Querying for a short summary..."
$jsonBody = '{"q":"write short summary"}'
$reqContent = New-Object System.Net.Http.StringContent($jsonBody, [System.Text.Encoding]::UTF8, "application/json")
$queryResp = $client.PostAsync("$base/query", $reqContent).Result
$queryBody = $queryResp.Content.ReadAsStringAsync().Result
if (-not $queryResp.IsSuccessStatusCode) {
    Write-Error "Query failed: $($queryResp.StatusCode) `n$queryBody"
    exit 1
}
Write-Host "Query response:`n" $queryBody

# Dispose client
$client.Dispose()

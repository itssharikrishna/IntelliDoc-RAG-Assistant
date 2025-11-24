# run_demo.ps1

$base = "http://localhost:8000"
$samplePdf = Join-Path $PSScriptRoot "web\sample.pdf"

if (-Not (Test-Path $samplePdf)) {
    Write-Host "Sample PDF not found at $samplePdf. Put a sample.pdf there or update the path." -ForegroundColor Yellow
    exit 1
}

Write-Host "1) Logging in..."
try {
    $loginResp = Invoke-RestMethod -Uri "$base/admin/login" -Method Post -Form @{ username="admin"; password="adminpass" }
} catch {
    Write-Error "Login failed: $($_.Exception.Message)"
    exit 1
}

$token = $loginResp.access_token
Write-Host "Received token length:" ($token.Length)

Write-Host "`n2) Uploading sample PDF..."
try {
    $form = @{
        file = Get-Item $samplePdf
        token = $token
    }
    $uploadResp = Invoke-RestMethod -Uri "$base/admin/upload" -Method Post -Form $form
    Write-Host "Upload response:" ($uploadResp | ConvertTo-Json -Depth 5)
} catch {
    Write-Error "Upload failed: $($_.Exception.Message)"
    exit 1
}

Start-Sleep -Seconds 2

Write-Host "`n3) Querying (strict verbatim + citation)..."

# -------------------------------
# PROMPT: strict verbatim + citation
# This prompt asks the model to return the exact sentence(s) from the document
# that define or describe the process of conduction of electric current
# through solutions, and to include supporting source chunk ids.
# If no exact sentence exists, the model must respond with the fallback text.
# -------------------------------

$queryPrompt = @"
From the retrieved contexts provided below, find and return the sentence(s) that define or describe the process of conduction of electric current through solutions. Copy the sentence(s) exactly as they appear in the retrieved contexts (preserve punctuation and spacing). After the sentence(s), list the top 1-2 supporting source chunk ids and their source filenames/pages if available in this format:

Sources:
- <source> id: <chunk-id> (page X)
- <source> id: <chunk-id> (page Y)

If no matching sentence is present within the retrieved contexts, reply exactly: "No exact definition found in the retrieved contexts."
"@

$payload = @{ q = $queryPrompt } | ConvertTo-Json
try {
    $queryResp = Invoke-RestMethod -Uri "$base/query" -Method Post -Body $payload -ContentType 'application/json'
    Write-Host "`n--- QUERY RESPONSE ---"
    Write-Host "Answer:`n" $queryResp.answer
    Write-Host "`nContexts (top results):"
    $i = 1
    foreach ($c in $queryResp.contexts) {
        Write-Host "[$i] source: $($c.source) id: $($c.id) chunk: $($c.chunk)"
        $snippet = $c.text
        if ($snippet.Length -gt 300) { $snippet = $snippet.Substring(0,300) + "..." }
        Write-Host $snippet
        $i++
        Write-Host "-----"
    }
} catch {
    Write-Error "Query failed: $($_.Exception.Message)"
    exit 1
}

Write-Host "`nDemo complete."

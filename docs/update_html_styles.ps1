# Script to update HTML styles in docs/help_docs directory
$htmlFiles = Get-ChildItem -Path "D:\Python\transformer_test_simulator_v1\docs\help_docs" -Filter "*.html"

foreach ($file in $htmlFiles) {
    $filePath = $file.FullName
    $content = Get-Content -Path $filePath -Raw
    
    # Update root CSS variables to add sidebar-bg-color
    $content = $content -replace '(:root\s*\{[^}]*--card-bg-color:\s*#495057;)([^}]*\})', '$1
            --sidebar-bg-color: #2c2c2c; /* Darker background for sidebar */$2'
    
    # Update sidebar CSS to use the new variable
    $content = $content -replace '(\.sidebar\s*\{[^}]*background-color:\s*)var\(--card-bg-color\)(;[^}]*\})', '$1var(--sidebar-bg-color)$2'
    
    # Save the updated content back to the file
    Set-Content -Path $filePath -Value $content
    
    Write-Host "Updated $($file.Name)"
}

Write-Host "All HTML files have been updated."

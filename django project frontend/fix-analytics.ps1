$file = "src\app\services\analytics.service.ts"
$content = Get-Content $file -Raw

# Remove all duplicate dislikeMovie methods
$content = $content -replace '(?s)\n\n  /\*\*\s*\n   \* Dislike.*?\n  \}\n\}', "`n}"

# Find where to insert (before the last closing brace)
$lastBrace = $content.LastIndexOf("`n}")
if ($lastBrace -gt 0) {
    $before = $content.Substring(0, $lastBrace)
    
    # New method
    $newMethod = @'

  dislikeMovie(data: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/dislikes/`, data);
  }
'@
    
    $newContent = $before + $newMethod + "`n}"
    Set-Content $file $newContent -NoNewline
    Write-Output "Method added successfully"
} else {
    Write-Output "Could not find insertion point"
}

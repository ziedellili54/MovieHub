$file = "src\app\components\dashboard\dashboard.ts"
$content = Get-Content $file -Raw

# Remove all duplicate dislikeMovie methods
$content = $content -replace '(?s)\n\n  /\*\*\s*\n   \* Dislike.*?\n  \}\n\}', "`n}"

# Find where to insert (after selectGenreFromDropdown)
$insertPoint = $content.LastIndexOf("`n  selectGenreFromDropdown")
if ($insertPoint -gt 0) {
    $endOfMethod = $content.IndexOf("`n  }", $insertPoint) + 4
    $before = $content.Substring(0, $endOfMethod)
    $after = $content.Substring($endOfMethod)
    
    # New method
    $newMethod = @'

  dislikeMovie(movie: any, event: Event): void {
    event.stopPropagation();
    const movieId = movie.id || movie.movie_id;
    const isFromRecommendations = this.recommendedMovies.some((m: any) => (m.id || m.movie_id) === movieId);
    let position = null;
    if (isFromRecommendations) {
      position = this.recommendedMovies.findIndex((m: any) => (m.id || m.movie_id) === movieId) + 1;
    }
    const dislikeData = {
      username: this.username,
      movie_id: movieId,
      dislike_reason: 'not_interested',
      was_ai_recommendation: isFromRecommendations,
      recommendation_position: position
    };
    this.analyticsService.dislikeMovie(dislikeData).subscribe(
      (response: any) => {
        console.log('Movie disliked:', response);
        this.successMessage = movie.title + ' ne sera plus affiché';
        this.recommendedMovies = this.recommendedMovies.filter((m: any) => (m.id || m.movie_id) !== movieId);
        this.trendingMovies = this.trendingMovies.filter((m: any) => (m.id || m.movie_id) !== movieId);
        this.continueWatchingMovies = this.continueWatchingMovies.filter((m: any) => (m.movie_id || m.id) !== movieId);
        this.filteredMovies = this.filteredMovies.filter((m: any) => m.id !== movieId);
        this.selectedMovieForDetail = null;
        setTimeout(() => this.successMessage = '', 3000);
      },
      (error: any) => {
        console.error('Error disliking movie:', error);
        this.errorMessage = 'Erreur lors du dislike';
        setTimeout(() => this.errorMessage = '', 3000);
      }
    );
  }
'@
    
    $newContent = $before + $newMethod + $after
    Set-Content $file $newContent -NoNewline
    Write-Output "Method added successfully"
} else {
    Write-Output "Could not find insertion point"
}

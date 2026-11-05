import { Component, OnInit, inject, ChangeDetectorRef } from '@angular/core';
import { Router } from '@angular/router';
import { MovieService } from '../../services/movie.service';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-api-browser',
  imports: [FormsModule, CommonModule],
  templateUrl: './api-browser.html',
  styleUrl: './api-browser.css'
})
export class ApiBrowserComponent implements OnInit {
  private movieService = inject(MovieService);
  private router = inject(Router);
  private cdr = inject(ChangeDetectorRef);

  apiUrl = '';
  loading = false;
  items: any[] = [];
  filteredItems: any[] = [];
  successMessage = '';
  errorMessage = '';

  // Filters
  searchQuery = '';
  selectedYear = '';
  selectedType = '';
  showExistingOnly = false;
  showNewOnly = false;

  // Years list
  yearsList: number[] = Array.from({ length: 2026 - 1950 + 1 }, (_, i) => 2026 - i);

  // Pagination
  currentPage = 1;
  itemsPerPage = 50;

  ngOnInit() {
    // Check if we have a saved API URL
    const savedUrl = localStorage.getItem('last_api_url');
    if (savedUrl) {
      this.apiUrl = savedUrl;
    }
  }

  onBrowseApi() {
    if (!this.apiUrl.trim()) {
      this.errorMessage = 'Please enter an API URL';
      return;
    }

    this.loading = true;
    this.errorMessage = '';
    this.successMessage = '⏳ Fetching all pages from API (this may take a moment)...';
    this.items = [];
    this.filteredItems = [];

    this.movieService.browseExternalApi(this.apiUrl.trim()).subscribe({
      next: (res) => {
        this.items = res.items || [];
        this.filteredItems = [...this.items];
        this.applyFilters();
        this.loading = false;
        this.successMessage = `✅ Loaded ${this.items.length} items from API`;
        localStorage.setItem('last_api_url', this.apiUrl.trim());
        this.cdr.detectChanges();
      },
      error: (err) => {
        this.errorMessage = err.error?.error || 'Failed to browse API';
        this.loading = false;
        this.items = [];
        this.filteredItems = [];
        this.cdr.detectChanges();
      }
    });
  }

  toggleItemSelection(item: any) {
    if (item.already_exists) return;
    item.selected = !item.selected;
    this.cdr.detectChanges();
  }

  selectAll() {
    const availableItems = this.getPaginatedItems().filter(item => !item.already_exists);
    const allSelected = availableItems.every(item => item.selected);
    
    availableItems.forEach(item => {
      item.selected = !allSelected;
    });
    this.cdr.detectChanges();
  }

  hasSelectedItems(): boolean {
    return this.items.some(item => item.selected && !item.already_exists);
  }

  getSelectedCount(): number {
    return this.items.filter(item => item.selected && !item.already_exists).length;
  }

  getExistingCount(): number {
    return this.items.filter(item => item.already_exists).length;
  }

  getNewCount(): number {
    return this.items.filter(item => !item.already_exists).length;
  }

  onSaveSelected() {
    const selected = this.items.filter(item => item.selected && !item.already_exists);
    
    if (selected.length === 0) {
      this.errorMessage = 'No items selected';
      return;
    }

    this.loading = true;
    this.movieService.saveSelectedOMDb(selected).subscribe({
      next: (res) => {
        let msg = res.message || `Successfully added ${selected.length} items`;
        
        if (res.errors && res.errors.length > 0) {
          msg += ` | ${res.errors.length} errors occurred`;
          console.error('Save errors:', res.errors);
        }
        
        this.successMessage = msg;
        
        // Mark items as already existing
        selected.forEach(item => {
          item.already_exists = true;
          item.selected = false;
        });
        
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        this.errorMessage = err.error?.error || err.message || 'Failed to save items';
        console.error('Save error:', err);
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }

  applyFilters() {
    let filtered = [...this.items];

    // Search filter
    if (this.searchQuery.trim()) {
      const query = this.searchQuery.toLowerCase();
      filtered = filtered.filter(item =>
        item.title?.toLowerCase().includes(query) ||
        item.director?.toLowerCase().includes(query) ||
        item.cast?.toLowerCase().includes(query)
      );
    }

    // Year filter
    if (this.selectedYear) {
      filtered = filtered.filter(item => item.release_year == this.selectedYear);
    }

    // Type filter
    if (this.selectedType) {
      filtered = filtered.filter(item => 
        item.type?.toLowerCase().includes(this.selectedType.toLowerCase())
      );
    }

    // Existing/New filter
    if (this.showExistingOnly) {
      filtered = filtered.filter(item => item.already_exists);
    } else if (this.showNewOnly) {
      filtered = filtered.filter(item => !item.already_exists);
    }

    this.filteredItems = filtered;
    this.currentPage = 1;
    this.cdr.detectChanges();
  }

  getPaginatedItems(): any[] {
    const start = (this.currentPage - 1) * this.itemsPerPage;
    const end = start + this.itemsPerPage;
    return this.filteredItems.slice(start, end);
  }

  getTotalPages(): number {
    return Math.ceil(this.filteredItems.length / this.itemsPerPage);
  }

  goToPage(page: number) {
    if (page >= 1 && page <= this.getTotalPages()) {
      this.currentPage = page;
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }

  getPages(): number[] {
    const total = this.getTotalPages();
    const pages: number[] = [];
    const maxVisible = 7;
    let start = Math.max(1, this.currentPage - Math.floor(maxVisible / 2));
    let end = Math.min(total, start + maxVisible - 1);
    
    if (end - start + 1 < maxVisible) {
      start = Math.max(1, end - maxVisible + 1);
    }
    
    for (let i = start; i <= end; i++) {
      pages.push(i);
    }
    return pages;
  }

  goBack() {
    // Navigate back to the appropriate dashboard based on user role
    const role = sessionStorage.getItem('role');
    if (role === 'admin') {
      this.router.navigate(['/admin/dashboard']);
    } else {
      this.router.navigate(['/dashboard']);
    }
  }

  onImageError(event: any) {
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="300" height="450" viewBox="0 0 300 450"><rect width="100%" height="100%" fill="#1a1a26"/><text x="50%" y="48%" fill="#ffae00" font-size="20" font-weight="bold" font-family="sans-serif" text-anchor="middle">MovieHub</text><text x="50%" y="54%" fill="#64748b" font-size="14" font-family="sans-serif" text-anchor="middle">No Image</text></svg>`;
    event.target.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg);
  }

  Math = Math;
}

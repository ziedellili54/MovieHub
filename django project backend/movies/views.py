import os
import requests as ext_requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.authentication import BasicAuthentication
from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Movie, TVShow, Pack


def test_simple_view(request):
    return HttpResponse("If you see this text, routing and views work fine.")

class FetchMoviesView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    def post(self, request):
        year = request.data.get("year", "2020")
        movie_type = request.data.get("type", "Movie")

        url = "https://netflix-movies-and-tv-shows1.p.rapidapi.com/list"

        payload = {
            "page": "1",
            "title": "",
            "type": movie_type,
            "director": "",
            "cast": "",
            "country": "",
            "release_year": str(year),
            "listed_in": ""
        }

        headers = {
            "x-rapidapi-key": os.getenv("RAPIDAPI_KEY"),
            "x-rapidapi-host": "netflix-movies-and-tv-shows1.p.rapidapi.com",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        response = ext_requests.post(url, data=payload, headers=headers)
        result = response.json()
        shows = result.get("result", {}).get("data", [])

        saved_count = 0
        for show in shows:
            raw_type = show.get("type", "Movie")
            listed_in = show.get("listed_in", "")
            
            # Auto-set primary_category to first genre
            primary_category = ""
            if listed_in:
                genres = [g.strip() for g in listed_in.split(',')]
                primary_category = genres[0] if genres else ""
            
            item_data = dict(
                show_id=show.get("show_id", ""),
                title=show.get("title", ""),
                type=raw_type,
                release_year=show.get("release_year"),
                director=show.get("director", ""),
                cast=show.get("cast", ""),
                country=show.get("country", ""),
                rating=show.get("rating", ""),
                duration=show.get("duration", ""),
                listed_in=listed_in,
                primary_category=primary_category,
                description=show.get("description", "")
            )
            if "tv" in str(raw_type).lower():
                TVShow(**item_data).save()
            else:
                Movie(**item_data).save()
            saved_count += 1

        return Response({
            "message": f"Fetched and saved {saved_count} items for {year}",
            "count": saved_count
        })


class ListMoviesView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    def get(self, request):
        limit = int(request.GET.get('limit', 24))
        page = int(request.GET.get('page', 1))
        offset = (page - 1) * limit

        search = request.GET.get('search', '').strip()
        filter_type = request.GET.get('type', '').strip()
        filter_genre = request.GET.get('genre', '').strip()
        sort_by = request.GET.get('sort', 'title-asc')

        # Build query filters
        query = {}
        if search:
            # Search in both title AND genre (listed_in field)
            # MongoDB $or query to search multiple fields - MongoEngine syntax
            from mongoengine import Q
            search_filter = Q(title__icontains=search) | Q(listed_in__icontains=search)
        else:
            search_filter = None
        
        genre_query = {}
        if filter_genre:
            genre_query['listed_in__icontains'] = filter_genre

        # Combine results from both 'movies' and 'tv_shows' collections
        items = []
        
        target = filter_type.lower()
        if not target or 'movie' in target:
            if filter_type and 'movie' in target:
                genre_query['type__icontains'] = filter_type
            # Apply search filter
            if search_filter:
                movie_items = Movie.objects.filter(search_filter, **genre_query)
            elif genre_query:
                movie_items = Movie.objects.filter(**genre_query)
            else:
                movie_items = Movie.objects.all()
            items.extend(list(movie_items))
            if 'type__icontains' in genre_query and not ('tv' in target or 'show' in target):
                if 'type__icontains' in genre_query:
                    del genre_query['type__icontains']
                
        if not target or 'tv' in target or 'show' in target:
            if search_filter:
                tv_items = TVShow.objects.filter(search_filter, **genre_query)
            elif genre_query:
                tv_items = TVShow.objects.filter(**genre_query)
            else:
                tv_items = TVShow.objects.all()
            items.extend(list(tv_items))

        # Sorting
        if sort_by == 'title-asc':
            items.sort(key=lambda x: (x.title or '').lower())
        elif sort_by == 'title-desc':
            items.sort(key=lambda x: (x.title or '').lower(), reverse=True)
        elif sort_by == 'year-desc':
            items.sort(key=lambda x: x.release_year or 0, reverse=True)
        elif sort_by == 'year-asc':
            items.sort(key=lambda x: x.release_year or 0)

        total = len(items)
        paged_items = items[offset:offset + limit]

        data = []
        for item in paged_items:
            # Auto-set primary_category if not set
            if not hasattr(item, 'primary_category') or not item.primary_category:
                genres_list = (getattr(item, 'listed_in', '') or '').split(',')
                primary = genres_list[0].strip() if genres_list and genres_list[0].strip() else ''
                if primary:
                    item.primary_category = primary
                    item.save()
            
            data.append({
                "id": str(item.id),
                "show_id": getattr(item, 'show_id', ''),
                "title": item.title,
                "type": getattr(item, 'type', 'Movie'),
                "release_year": item.release_year,
                "director": getattr(item, 'director', ''),
                "cast": getattr(item, 'cast', ''),
                "country": getattr(item, 'country', ''),
                "rating": getattr(item, 'rating', ''),
                "duration": getattr(item, 'duration', ''),
                "listed_in": getattr(item, 'listed_in', ''),
                "primary_category": getattr(item, 'primary_category', ''),
                "description": getattr(item, 'description', ''),
                "poster": getattr(item, 'poster', None)
            })

        return Response({"movies": data, "count": len(data), "total": total, "page": page, "limit": limit})


class GenresView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    def get(self, request):
        try:
            raw_genres = set(Movie.objects.distinct('listed_in')).union(set(TVShow.objects.distinct('listed_in')))
            genres_set = set()
            for item in raw_genres:
                if item:
                    for g in str(item).split(','):
                        clean = g.strip()
                        if clean:
                            genres_set.add(clean)
            return Response({"genres": sorted(list(genres_set))})
        except Exception as e:
            return Response({"genres": []})


class AddMovieView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    def post(self, request):
        data = request.data

        if "title" not in data:
            return Response({"error": "Title is required"}, status=400)

        listed_in = data.get("listed_in", "")
        
        # Auto-set primary_category to first genre
        primary_category = data.get("primary_category", "")
        if not primary_category and listed_in:
            genres = [g.strip() for g in listed_in.split(',')]
            primary_category = genres[0] if genres else ""

        movie = Movie(
            show_id=data.get("show_id", ""),
            title=data.get("title"),
            type=data.get("type", ""),
            release_year=data.get("release_year"),
            director=data.get("director", ""),
            cast=data.get("cast", ""),
            country=data.get("country", ""),
            rating=data.get("rating", ""),
            duration=data.get("duration", ""),
            listed_in=listed_in,
            primary_category=primary_category,
            description=data.get("description", "")
        )
        movie.save()

        return Response({
            "message": "Movie added successfully!",
            "id": str(movie.id)
        }, status=201)


def fetch_page(request):
    message = None
    year = ""

    if request.method == "POST":
        year = request.POST.get("year", "2023")
        movie_type = request.POST.get("type", "Movie")

        url = "https://netflix-movies-and-tv-shows1.p.rapidapi.com/list"
        payload = {
            "page": "1", "title": "", "type": movie_type,
            "director": "", "cast": "", "country": "",
            "release_year": str(year), "listed_in": ""
        }
        headers = {
            "x-rapidapi-key": os.getenv("RAPIDAPI_KEY"),
            "x-rapidapi-host": "netflix-movies-and-tv-shows1.p.rapidapi.com",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        response = ext_requests.post(url, data=payload, headers=headers)
        result = response.json()
        shows = result.get("result", {}).get("data", [])

        for show in shows:
            Movie(
                show_id=show.get("show_id", ""),
                title=show.get("title", ""),
                type=show.get("type", ""),
                release_year=show.get("release_year"),
                director=show.get("director", ""),
                cast=show.get("cast", ""),
                country=show.get("country", ""),
                rating=show.get("rating", ""),
                duration=show.get("duration", ""),
                listed_in=show.get("listed_in", ""),
                description=show.get("description", "")
            ).save()

        message = f"Fetched and saved {len(shows)} shows for {year}"

    return render(request, "movies/fetch_page.html", {"message": message, "fetched_year": year})


def movies_page(request):
    selected_year = request.GET.get("year", "")

    # Combine both Movie and TVShow collections
    items = []
    
    if selected_year:
        items.extend(list(Movie.objects.filter(release_year=int(selected_year))))
        items.extend(list(TVShow.objects.filter(release_year=int(selected_year))))
    else:
        items.extend(list(Movie.objects.all()))
        items.extend(list(TVShow.objects.all()))
    
    # Sort by title
    items.sort(key=lambda x: (x.title or "").lower())

    username = request.session.get("username")
    user_profile = None
    if username:
        try:
            from accounts.models import User
            user_profile = User.objects.get(username=username)
        except Exception:
            pass

    return render(request, "movies/movies_page.html", {
        "movies": items,  # Still called 'movies' for template compatibility
        "selected_year": selected_year,
        "user_profile": user_profile
    })


def fetch_all_years_page(request):
    message = None

    if request.method == "POST":
        import time
        start_year = 1950
        end_year = 2026
        total_saved = 0

        url = "https://netflix-movies-and-tv-shows1.p.rapidapi.com/list"
        headers = {
            "x-rapidapi-key": os.getenv("RAPIDAPI_KEY"),
            "x-rapidapi-host": "netflix-movies-and-tv-shows1.p.rapidapi.com",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        for year in range(start_year, end_year + 1):
            payload = {
                "page": "1", "title": "", "type": "Movie",
                "director": "", "cast": "", "country": "",
                "release_year": str(year), "listed_in": ""
            }
            try:
                response = ext_requests.post(url, data=payload, headers=headers)
                if response.status_code == 200:
                    result = response.json()
                    shows = result.get("result", {}).get("data", [])

                    for show in shows:
                        Movie(
                            show_id=show.get("show_id", ""),
                            title=show.get("title", ""),
                            type=show.get("type", ""),
                            release_year=show.get("release_year"),
                            director=show.get("director", ""),
                            cast=show.get("cast", ""),
                            country=show.get("country", ""),
                            rating=show.get("rating", ""),
                            duration=show.get("duration", ""),
                            listed_in=show.get("listed_in", ""),
                            description=show.get("description", "")
                        ).save()
                        total_saved += 1
                else:
                    print(f"Skipping year {year}: API returned status {response.status_code}")
            except Exception as e:
                print(f"Error fetching year {year}: {e}")

            # Sleep 1 second between requests to respect rate limits
            time.sleep(1)

        message = f"Fetched and saved {total_saved} shows across {start_year}-{end_year}"

    return render(request, "movies/fetch_all_page.html", {"message": message})


def search_movie_page(request):
    results = []
    message = None
    searched = False

    if request.method == "POST" and "search" in request.POST:
        title = request.POST.get("title", "")
        year = request.POST.get("year", "")
        searched = True

        query = {}
        if title:
            query["title__icontains"] = title  # case-insensitive partial match
        if year:
            query["release_year"] = int(year)

        results = Movie.objects.filter(**query)

        if not results:
            message = "No movies found in your database for that search."

    return render(request, "movies/search_movie_page.html", {
        "results": results,
        "message": message,
        "searched": searched
    })


def add_searched_movie(request):
    if request.method == "POST":
        title = request.POST.get("title", "")
        # Check for duplicate before saving
        if Movie.objects.filter(title__iexact=title).first():
            return redirect("movies_page")
        Movie(
            show_id=request.POST.get("show_id", ""),
            title=title,
            type=request.POST.get("type", ""),
            release_year=request.POST.get("release_year") or None,
            director=request.POST.get("director", ""),
            cast=request.POST.get("cast", ""),
            country=request.POST.get("country", ""),
            rating=request.POST.get("rating", ""),
            duration=request.POST.get("duration", ""),
            listed_in=request.POST.get("listed_in", ""),
            description=request.POST.get("description", "")
        ).save()

    return redirect("movies_page")

def add_movie_page(request):
    message = None
    error = None
    years = list(range(2026, 1949, -1))

    if request.method == "POST":
        title = request.POST.get("title", "").strip()

        # Duplicate check — case-insensitive
        if Movie.objects.filter(title__iexact=title).first():
            error = f"\u274c '{title}' is already in your database!"
        else:
            Movie(
                title=title,
                type=request.POST.get("type"),
                release_year=int(request.POST.get("release_year")),
                director=request.POST.get("director", ""),
                cast=request.POST.get("cast", ""),
                country=request.POST.get("country", ""),
                listed_in=request.POST.get("listed_in", "")
            ).save()
            message = f"\u2705 '{title}' added successfully!"

    return render(request, "movies/add_movie_page.html", {"years": years, "message": message, "error": error})


def api_search_and_save(request):
    """
    Searches the external Netflix API by title and returns the results.
    Also marks which movies already exist in MongoDB.
    On POST with selected show_ids, saves those movies (skipping duplicates).
    """
    api_results = []
    saved_titles = []
    skipped_titles = []
    search_query = ""
    searched = False
    message = None

    if request.method == "POST":
        action = request.POST.get("action", "search")
        search_query = request.POST.get("title", "").strip()

        if action == "search" and search_query:
            searched = True
            omdb_key = os.getenv("OMDB_KEY")
            if not omdb_key:
                message = "⚠️ OMDB_KEY is missing from your .env file. Get a free key at https://www.omdbapi.com/apikey.aspx"
            else:
                try:
                    # OMDb search: returns up to 10 results matching the title
                    response = ext_requests.get(
                        "https://www.omdbapi.com/",
                        params={"s": search_query, "apikey": omdb_key}
                    )
                    result = response.json()

                    if result.get("Response") == "True":
                        shows = result.get("Search", [])

                        for show in shows:
                            title = show.get("Title", "")
                            # Fetch full details for each result to get director/plot/etc.
                            detail_resp = ext_requests.get(
                                "https://www.omdbapi.com/",
                                params={"i": show.get("imdbID", ""), "apikey": omdb_key}
                            )
                            detail = detail_resp.json() if detail_resp.status_code == 200 else {}

                            already_saved = bool(Movie.objects.filter(title__iexact=title).first())

                            # Parse year safely
                            raw_year = show.get("Year", "")
                            try:
                                release_year = int(raw_year[:4]) if raw_year else None
                            except (ValueError, TypeError):
                                release_year = None

                            api_results.append({
                                "show_id": show.get("imdbID", ""),
                                "title": title,
                                "type": "Movie" if show.get("Type", "movie") == "movie" else "TV Show",
                                "release_year": release_year,
                                "director": detail.get("Director", "N/A"),
                                "cast": detail.get("Actors", ""),
                                "country": detail.get("Country", ""),
                                "rating": detail.get("Rated", ""),
                                "duration": detail.get("Runtime", ""),
                                "listed_in": detail.get("Genre", ""),
                                "description": detail.get("Plot", ""),
                                "poster": show.get("Poster", ""),
                                "already_saved": already_saved,
                            })

                        if not api_results:
                            message = "No movies found on OMDb for that search."
                    else:
                        message = f"OMDb: {result.get('Error', 'No results found.')}"
                except Exception as e:
                    message = f"API error: {e}"

class ApiSearchOMDbView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        search_query = request.GET.get("title", "").strip()
        if not search_query:
            return Response({"results": []})

        omdb_key = os.getenv("OMDB_KEY")
        if not omdb_key:
            return Response({"error": "OMDB_KEY is missing from .env"}, status=500)

        try:
            response = ext_requests.get(
                "https://www.omdbapi.com/",
                params={"s": search_query, "apikey": omdb_key}
            )
            result = response.json()

            if result.get("Response") == "True":
                shows = result.get("Search", [])
                api_results = []

                for show in shows:
                    title = show.get("Title", "")
                    raw_type = show.get("Type", "movie")
                    item_type = "Movie" if raw_type.lower() == "movie" else "TV Show"

                    detail_resp = ext_requests.get(
                        "https://www.omdbapi.com/",
                        params={"i": show.get("imdbID", ""), "apikey": omdb_key}
                    )
                    detail = detail_resp.json() if detail_resp.status_code == 200 else {}

                    if item_type == "TV Show":
                        already_saved = bool(TVShow.objects.filter(title__iexact=title).first())
                    else:
                        already_saved = bool(Movie.objects.filter(title__iexact=title).first())

                    raw_year = show.get("Year", "")
                    try:
                        release_year = int(raw_year[:4]) if raw_year else None
                    except (ValueError, TypeError):
                        release_year = None

                    api_results.append({
                        "show_id": show.get("imdbID", ""),
                        "title": title,
                        "type": item_type,
                        "release_year": release_year,
                        "director": detail.get("Director", "N/A"),
                        "cast": detail.get("Actors", "N/A"),
                        "country": detail.get("Country", "N/A"),
                        "rating": detail.get("Rated", "N/A"),
                        "duration": detail.get("Runtime", "N/A"),
                        "listed_in": detail.get("Genre", "N/A"),
                        "description": detail.get("Plot", "N/A"),
                        "poster": show.get("Poster") if show.get("Poster") != "N/A" else None,
                        "already_saved": already_saved
                    })

                return Response({"results": api_results})
            else:
                return Response({"error": result.get("Error", "No results found"), "results": []})
        except Exception as e:
            return Response({"error": str(e), "results": []})


class ApiSaveSelectedOMDbView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        items = request.data.get("items", [])
        if not items:
            return Response({"error": "No items provided"}, status=400)

        saved_titles = []
        skipped_titles = []
        error_titles = []

        for item in items:
            try:
                title = item.get("title", "").strip()
                if not title:
                    continue
                    
                item_type = item.get("type", "Movie")
                listed_in = item.get("listed_in") or ""
                
                # Auto-set primary_category to first genre
                primary_category = ""
                if listed_in:
                    genres = [g.strip() for g in listed_in.split(',')]
                    primary_category = genres[0] if genres else ""
                
                if "tv" in str(item_type).lower() or "show" in str(item_type).lower():
                    existing = TVShow.objects.filter(title__iexact=title).first()
                    if existing:
                        skipped_titles.append(title)
                    else:
                        TVShow(
                            show_id=str(item.get("show_id", "")),
                            title=title,
                            type="TV Show",
                            release_year=item.get("release_year") or None,
                            director=item.get("director") or "",
                            cast=item.get("cast") or "",
                            country=item.get("country") or "",
                            rating=str(item.get("rating") or ""),
                            duration=str(item.get("duration") or ""),
                            listed_in=listed_in,
                            primary_category=primary_category,
                            description=item.get("description") or "",
                            poster=item.get("poster") or ""
                        ).save()
                        saved_titles.append(title)
                else:
                    existing = Movie.objects.filter(title__iexact=title).first()
                    if existing:
                        skipped_titles.append(title)
                    else:
                        Movie(
                            show_id=str(item.get("show_id", "")),
                            title=title,
                            type="Movie",
                            release_year=item.get("release_year") or None,
                            director=item.get("director") or "",
                            cast=item.get("cast") or "",
                            country=item.get("country") or "",
                            rating=str(item.get("rating") or ""),
                            duration=str(item.get("duration") or ""),
                            listed_in=listed_in,
                            primary_category=primary_category,
                            description=item.get("description") or "",
                            poster=item.get("poster") or ""
                        ).save()
                        saved_titles.append(title)
            except Exception as e:
                error_titles.append(f"{title}: {str(e)}")
                continue

        response_data = {
            "message": f"Successfully saved {len(saved_titles)} title(s).",
            "saved": saved_titles,
            "skipped": skipped_titles
        }
        
        if error_titles:
            response_data["errors"] = error_titles
            
        return Response(response_data)


class ExternalApiBrowseView(APIView):
    """
    Browse external API - fetch all movies from a given API URL
    POST with {"api_url": "https://..."} to fetch all items
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        api_url = request.data.get("api_url", "").strip()
        
        if not api_url:
            return Response({"error": "API URL is required"}, status=400)
        
        try:
            all_items = []
            
            # Try to fetch multiple pages from ANY API
            # Attempt up to 50 pages to get as much content as possible
            for page_num in range(1, 51):
                try:
                    # Build paginated URL - try different pagination patterns
                    page_url = api_url
                    
                    # Pattern 1: ?page=X or &page=X
                    if '?' in api_url:
                        if 'page=' in api_url:
                            import re
                            page_url = re.sub(r'page=\d+', f'page={page_num}', api_url)
                        else:
                            page_url = f"{api_url}&page={page_num}"
                    else:
                        page_url = f"{api_url}?page={page_num}"
                    
                    # Fetch this page
                    response = ext_requests.get(page_url, timeout=10)
                    
                    if response.status_code != 200:
                        # If first page fails, break
                        if page_num == 1:
                            return Response({
                                "error": f"Failed to fetch from API. Status: {response.status_code}"
                            }, status=400)
                        # If subsequent page fails, just stop paginating
                        break
                    
                    data = response.json()
                    
                    # Extract items from this page
                    page_items = []
                    
                    if isinstance(data, list):
                        page_items = data
                    elif isinstance(data, dict):
                        # Try common keys
                        for key in ['results', 'data', 'items', 'movies', 'shows', 'list', 'Search']:
                            if key in data:
                                potential_items = data[key]
                                if isinstance(potential_items, list):
                                    page_items = potential_items
                                    break
                                elif isinstance(potential_items, dict) and 'data' in potential_items:
                                    page_items = potential_items['data']
                                    break
                    
                    # If no items found on this page, we've reached the end
                    if not page_items:
                        break
                    
                    # Add to total collection
                    all_items.extend(page_items)
                    
                    # Check pagination metadata to see if there are more pages
                    should_continue = False
                    if isinstance(data, dict):
                        total_pages = data.get('total_pages') or data.get('totalPages') or data.get('total_results', 0)
                        current_page = data.get('page', page_num)
                        
                        if total_pages and current_page < total_pages:
                            should_continue = True
                        elif len(page_items) > 0 and page_num < 50:
                            # If we got items but no pagination info, try next page
                            should_continue = True
                    elif isinstance(data, list) and len(data) > 0:
                        # For direct array responses, keep trying
                        should_continue = True
                    
                    if not should_continue:
                        break
                        
                    # Small delay to be nice to the API
                    import time
                    time.sleep(0.1)
                    
                except Exception as e:
                    print(f"Error fetching page {page_num}: {e}")
                    # If first page errors, raise it
                    if page_num == 1:
                        raise
                    # Otherwise, just stop pagination
                    break
            
            if not all_items:
                return Response({
                    "error": "Could not find items in API response. Please check the API structure.",
                    "sample": str(data)[:500] if 'data' in locals() else "No data"
                }, status=400)
            
            # Process items and check if they exist in database
            processed_items = []
            
            for item in all_items:  # Process ALL items
                # Extract common fields (flexible for different API structures)
                title = item.get("title") or item.get("name") or item.get("Title") or ""
                
                if not title:
                    continue
                
                item_type = "Movie"
                if item.get("type"):
                    item_type = item.get("type")
                elif item.get("media_type") == "tv":
                    item_type = "TV Show"
                elif "show" in str(item.get("type", "")).lower():
                    item_type = "TV Show"
                
                # Check if exists in database
                already_exists = False
                if "tv" in item_type.lower() or "show" in item_type.lower():
                    already_exists = bool(TVShow.objects.filter(title__iexact=title).first())
                else:
                    already_exists = bool(Movie.objects.filter(title__iexact=title).first())
                
                # Extract year
                release_year = None
                year_field = item.get("release_year") or item.get("year") or item.get("Year") or item.get("release_date") or item.get("first_air_date")
                if year_field:
                    try:
                        # Extract year from date string or number
                        year_str = str(year_field)[:4]
                        release_year = int(year_str) if year_str.isdigit() else None
                    except:
                        pass
                
                # Extract poster URL (handle TMDB poster_path format)
                poster = item.get("poster") or item.get("Poster", "")
                poster_path = item.get("poster_path")
                if poster_path and poster_path.startswith("/"):
                    poster = f"https://image.tmdb.org/t/p/w500{poster_path}"
                elif not poster and poster_path:
                    poster = poster_path
                
                # Extract genres (handle array format from TMDB)
                genres = ""
                if item.get("listed_in"):
                    genres = item.get("listed_in")
                elif item.get("genres"):
                    genre_data = item.get("genres")
                    if isinstance(genre_data, list):
                        # Handle array of genre objects [{id: 1, name: "Action"}]
                        if genre_data and isinstance(genre_data[0], dict):
                            genres = ", ".join([g.get("name", "") for g in genre_data if g.get("name")])
                        else:
                            genres = ", ".join(genre_data)
                    else:
                        genres = str(genre_data)
                elif item.get("genre"):
                    genres = item.get("genre")
                
                processed_items.append({
                    "title": title,
                    "type": item_type,
                    "release_year": release_year,
                    "director": item.get("director", ""),
                    "cast": item.get("cast", ""),
                    "country": item.get("country", ""),
                    "rating": item.get("rating") or item.get("vote_average", ""),
                    "duration": item.get("duration") or item.get("runtime", ""),
                    "listed_in": genres,
                    "description": item.get("description") or item.get("overview") or item.get("plot", ""),
                    "poster": poster,
                    "show_id": str(item.get("show_id") or item.get("id") or item.get("imdbID", "")),
                    "already_exists": already_exists
                })
            
            return Response({
                "items": processed_items,
                "total": len(processed_items),
                "api_url": api_url
            })
            
        except ext_requests.exceptions.Timeout:
            return Response({"error": "Request timeout. API took too long to respond."}, status=408)
        except ext_requests.exceptions.RequestException as e:
            return Response({"error": f"Failed to connect to API: {str(e)}"}, status=400)
        except Exception as e:
            return Response({"error": f"Error processing API data: {str(e)}"}, status=400)


class DeleteMovieView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    def delete(self, request, movie_id):
        try:
            movie = Movie.objects.get(id=movie_id)
            movie.delete()
            return Response({"message": "Movie deleted successfully"})
        except Movie.DoesNotExist:
            return Response({"error": "Movie not found"}, status=404)


class EditMovieView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    def put(self, request, movie_id):
        try:
            movie = Movie.objects.get(id=movie_id)
            data = request.data
            movie.title = data.get("title", movie.title).strip()
            movie.type = data.get("type", movie.type).strip()
            try:
                movie.release_year = int(data.get("release_year", movie.release_year))
            except (ValueError, TypeError):
                pass
            movie.director = data.get("director", movie.director).strip()
            movie.cast = data.get("cast", movie.cast).strip()
            movie.country = data.get("country", movie.country).strip()
            movie.listed_in = data.get("listed_in", movie.listed_in).strip()
            movie.description = data.get("description", movie.description).strip()
            movie.save()
            return Response({"message": "Movie updated successfully"})
        except Movie.DoesNotExist:
            return Response({"error": "Movie not found"}, status=404)


class PackPreviewView(APIView):
    """GET /api/packs/preview/?genres=Drama,Horror&years=2023,2024
    Returns movies+tvshows matching the genre/year criteria.
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        genres_param = request.GET.get("genres", "")
        years_param = request.GET.get("years", "")

        genres = [g.strip() for g in genres_param.split(",") if g.strip()]
        years = []
        for y in years_param.split(","):
            try:
                years.append(int(y.strip()))
            except (ValueError, TypeError):
                pass

        def item_matches(item):
            year_ok = not years or (item.release_year in years)
            if not year_ok:
                return False
            if not genres:
                return True
            listed = (item.listed_in or "").lower()
            return any(g.lower() in listed for g in genres)

        results = []
        for m in Movie.objects.all():
            if item_matches(m):
                results.append({
                    "id": str(m.id),
                    "title": m.title,
                    "type": m.type or "Movie",
                    "release_year": m.release_year,
                    "listed_in": m.listed_in,
                    "poster": m.poster,
                    "source": "movies"
                })
        for t in TVShow.objects.all():
            if item_matches(t):
                results.append({
                    "id": str(t.id),
                    "title": t.title,
                    "type": "TV Show",
                    "release_year": t.release_year,
                    "listed_in": t.listed_in,
                    "poster": t.poster,
                    "source": "tv_shows"
                })

        results.sort(key=lambda x: x["title"] or "")
        return Response({"results": results, "total": len(results)})


class PackListView(APIView):
    """GET /api/packs/  -> list all packs ordered by level
    POST /api/packs/ -> create a new pack
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    def _serialize(self, pack):
        return {
            "id": str(pack.id),
            "name": pack.name,
            "genres": pack.genres,
            "years": pack.years,
            "movie_ids": pack.movie_ids,
            "level": pack.level,
            "cover_image": pack.cover_image or "",
            "cover_height": getattr(pack, "cover_height", 250),
            "cover_position": getattr(pack, "cover_position", "center"),
            "cover_fit": getattr(pack, "cover_fit", "contain"),
        }

    def get(self, request):
        packs = Pack.objects.order_by("level")
        result = []
        for pack in packs:
            movies_data = []
            for mid in pack.movie_ids:
                m = Movie.objects(id=mid).first()
                if not m:
                    m = TVShow.objects(id=mid).first()
                if m:
                    movies_data.append({
                        "id": str(m.id),
                        "title": m.title,
                        "type": getattr(m, 'type', 'Movie'),
                        "release_year": m.release_year,
                        "listed_in": m.listed_in,
                        "poster": m.poster,
                    })
            p = self._serialize(pack)
            p["movies"] = movies_data
            result.append(p)
        return Response({"packs": result})

    def post(self, request):
        name = request.data.get("name", "").strip()
        if not name:
            return Response({"error": "Pack name is required"}, status=400)
        genres = request.data.get("genres", [])
        years = request.data.get("years", [])
        movie_ids = request.data.get("movie_ids", [])
        level = request.data.get("level", 1)
        try:
            level = int(level)
        except (ValueError, TypeError):
            level = 1
        cover_image = request.data.get("cover_image", "")
        cover_height = int(request.data.get("cover_height", 250))
        cover_position = request.data.get("cover_position", "center")
        cover_fit = request.data.get("cover_fit", "contain")
        pack = Pack(
            name=name, genres=genres, years=[int(y) for y in years],
            movie_ids=movie_ids, level=level, cover_image=cover_image,
            cover_height=cover_height, cover_position=cover_position,
            cover_fit=cover_fit
        )
        pack.save()
        return Response({"message": f'Pack "{name}" created successfully.', "id": str(pack.id)}, status=201)


class PackDetailView(APIView):
    """PUT  /api/packs/<pack_id>/ -> update pack
    DELETE /api/packs/<pack_id>/ -> delete pack
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    def put(self, request, pack_id):
        try:
            pack = Pack.objects.get(id=pack_id)
        except Exception:
            return Response({"error": "Pack not found"}, status=404)
        data = request.data
        if "name" in data:
            pack.name = data["name"].strip()
        if "genres" in data:
            pack.genres = data["genres"]
        if "years" in data:
            pack.years = [int(y) for y in data["years"]]
        if "movie_ids" in data:
            pack.movie_ids = data["movie_ids"]
        if "level" in data:
            try:
                pack.level = int(data["level"])
            except (ValueError, TypeError):
                pass
        if "cover_image" in data:
            pack.cover_image = data["cover_image"]
        if "cover_height" in data:
            try:
                pack.cover_height = int(data["cover_height"])
            except (ValueError, TypeError):
                pass
        if "cover_position" in data:
            pack.cover_position = data["cover_position"]
        if "cover_fit" in data:
            pack.cover_fit = data["cover_fit"]
        pack.save()
        return Response({"message": f'Pack "{pack.name}" updated successfully.'})

    def delete(self, request, pack_id):
        try:
            pack = Pack.objects.get(id=pack_id)
            name = pack.name
            pack.delete()
            return Response({"message": f'Pack "{name}" deleted.'})
        except Exception:
            return Response({"error": "Pack not found"}, status=404)

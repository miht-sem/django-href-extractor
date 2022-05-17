from django.shortcuts import render
from .models import UrlToParse, ParsedUrl
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import requests
from django.shortcuts import redirect
from django.core.paginator import Paginator
from concurrent.futures import as_completed
from requests_futures.sessions import FuturesSession

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/61.0.3163.100 Safari/537.36'}


def is_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def parser_best(web_url):
    found_urls = set()
    response = requests.get(web_url, headers)
    soup = BeautifulSoup(response.text, "lxml")

    for url in soup.find_all('a'):
        url_href = url.get('href')
        if url_href is None:
            continue
        if is_url(url_href):
            found_urls.add(url_href)
        else:
            found_urls.add(urljoin(web_url, url_href))

    return found_urls


def paginator(parsed_urls, request):
    p = Paginator(parsed_urls, 10)
    page = request.GET.get('page')
    return p.get_page(page)


def main(request):
    parsed_urls = UrlToParse.objects.get_queryset().order_by('url_id')
    if 'search' in request.GET:
        what_searched = request.GET['search']
        parsed_urls = UrlToParse.objects.get_queryset().order_by('url_id').filter(
            url_to_parse__contains=what_searched)
        return render(request, 'main.html',
                      {'urls': paginator(parsed_urls, request),
                       "searched": True, "what_searched": what_searched, "sorted": False})
    if 'sort' in request.GET:
        parsed_urls = sorted(parsed_urls)
        return render(request, 'main.html',
                      {'urls': paginator(parsed_urls, request),
                       "sorted": True, "searched": False})
    return render(request, 'main.html', {'urls': paginator(parsed_urls, request)})


def parsed(request, url_id):
    parsed_urls = UrlToParse.objects.get(
        url_id=url_id).entries.get_queryset().order_by('id')
    if 'search' in request.GET:
        what_searched = request.GET['search']
        parsed_urls = parsed_urls.filter(
            found_url__contains=what_searched)
        return render(request, 'parsed_url.html',
                      {'urls': paginator(parsed_urls, request),
                       "requested_url": UrlToParse.objects.get(url_id=url_id).url_to_parse,
                       "searched": True, "what_searched": what_searched, "sorted": False, "url_id": url_id})
    if 'sort' in request.GET:
        parsed_urls = sorted(parsed_urls)
        return render(request, 'parsed_url.html',
                      {'urls': paginator(parsed_urls, request),
                       "requested_url": UrlToParse.objects.get(url_id=url_id).url_to_parse,
                       "sorted": True, "searched": False, "url_id": url_id})

    return render(request, 'parsed_url.html',
                  {'urls': paginator(parsed_urls, request),
                   "requested_url": UrlToParse.objects.get(url_id=url_id).url_to_parse,
                   "searched": False, "sorted": False, "url_id": url_id})


def add_url(request):
    parsed_urls = UrlToParse.objects.get_queryset().order_by('url_id')

    if 'url' in request.GET:
        url = request.GET['url']

        if not is_url(url):
            parsed_urls = UrlToParse.objects.get_queryset().order_by('url_id')
            return redirect('/',
                            {'urls': paginator(parsed_urls, request), "searched": False, "sorted": False})

        urls = parser_best(url)
        url_model, created = UrlToParse.objects.get_or_create(url_to_parse=url)

        if created:
            urls = parser_best(url)
            url_model.save()
        if not created:
            parsed_urls = UrlToParse.objects.get(
                url_id=url_model.url_id).entries.get_queryset().order_by('id')
            return redirect(f'/show_url/{url_model.url_id}/',
                            {'urls': paginator(parsed_urls, request), "requested_url": url_model.url_to_parse,
                             "searched": False,
                             "sorted": False})
        try:
            with FuturesSession(max_workers=16) as session:
                futures = [session.get(f'https://api.domainsdb.info/v1/domains/search?domain={parsed_url}') for
                           parsed_url in urls]
                for future in as_completed(futures):
                    response = future.result()
                    url = response.request.url[52:]
                    print('Got response from', url)
                    data = response.json()
                    try:
                        arr = data['domains'][0]
                        url_data = ParsedUrl(
                            from_url=url_model,
                            found_url=url,
                            domain=arr['domain'],
                            create_date=arr['create_date'],
                            update_date=arr['update_date'],
                            country=arr['country'],
                            isDead=arr['isDead'],
                            A=str(arr['A']),
                            NS=str(arr['NS']),
                            CNAME=str(arr['CNAME']),
                            MX=str(arr['MX']),
                            TXT=str(arr['TXT'])
                        )
                        url_data.save()
                    except Exception as e:
                        print(f'Incorrect url: {e}')
        except Exception as e:
            session.close()
            print(f'Some problems with threads: {e}')
        parsed_urls = UrlToParse.objects.get(
            url_id=url_model.url_id).entries.get_queryset().order_by('id')
        return redirect(f'/show_url/{url_model.url_id}/',
                        {'urls': paginator(parsed_urls, request), "requested_url": url_model.url_to_parse,
                         "searched": False,
                         "sorted": False})

    return redirect('/', {'urls': paginator(parsed_urls, request), "searched": False, "sorted": False})


def delete_url(request, url_id):
    url_to_delete = UrlToParse.objects.get(url_id=url_id)
    url_to_delete.delete()
    parsed_urls = UrlToParse.objects.get_queryset().order_by('url_id')
    return redirect('/', {'urls': paginator(parsed_urls, request), "searched": False, "sorted": False})


def delete_all_urls(request):
    urls_to_delete = UrlToParse.objects.all()
    urls_to_delete.delete()
    return redirect('/', {'parsed_urls': {}, "searched": False, "sorted": False})

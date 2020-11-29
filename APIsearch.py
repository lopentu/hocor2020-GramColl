import json
import requests
import time



def search(pattern=None, cql_enable=True, board=None, year_from=None, year_to=None, author=None, number=20, wordsaroundhit=0):
    PTT_BLACKLAB_API = "http://140.112.147.132:8999/blacklab-server"
    
    filters = []
    filter_string = ""

    if pattern is None and isinstance(pattern, str): 
        raise ValueError("pattern must be given in type <string>!")

    if type(year_from) != type(year_to):
        raise ValueError("year_from and year_to must be in type <string>!")

    if not cql_enable:
        pattern = f"[word=\"{pattern}\"]"

    if board is not None:
        filters.append(f'board:("{board}")')

    if year_from is not None and year_to is not None:
        filters.append(f'year:[{year_from} TO {year_to}]')

    if len(filters) != 0:
        filter_string = " AND ".join(filters) + "&"
    
    # Pagination
    num_per_page = 100
    num_of_pages = int(number // num_per_page + 0.01) + 1
    params = {
            'outputformat': 'json',
            'filter': filter_string,
            'waitfortotal': 'yes',
            'wordsaroundhit': wordsaroundhit,
            'patt': pattern,
            'first': 0,
            'number': num_per_page
        }

    requested_urls = []
    hits = []
    for i in range(num_of_pages):
        # Last page
        if i == num_of_pages - 1:
            params['number'] = number % num_per_page
        
        response = requests.get(f'{PTT_BLACKLAB_API}/indexes/hits/', params=params)
        #print(response.url)
        requested_urls.append(response.url)
        text = json.loads(response.text)
        if i == 0:
            num_of_results_found = text.get("summary").get("numberOfHits")
            print(f'Found {num_of_results_found} results')
        if num_of_results_found <= len(hits): break
        if text.get("hits") is None: break
        hits += text.get("hits")
        params['first'] += num_per_page

        #time.sleep(0.035)

    return hits, requested_urls



def quote_params(params: dict):
    return '&'.join(f"{requests.utils.quote(k)}={requests.utils.quote(str(v))}" for k, v in params.items())


def get_capture_groups(hit, pos_tags=False):
    s_idx = hit['start']
    
    fullcntx_words = hit['left']['word'] + hit['match']['word'] + hit['right']['word']
    fullcntx_tags = hit['left']['pos'] + hit['match']['pos'] + hit['right']['pos']
    
    groups = {}
    for g in hit['captureGroups']:
        start, end = g['start'] - s_idx, g['end'] - s_idx
        
        tokens = fullcntx_words[start:end]
        if pos_tags:
            tags = fullcntx_tags[start:end]
            tokens = [(tokens[i], tags[i]) for i in range(len(tokens))]
        
        groups[g['name']] = tokens
    
    return groups


def top_n(freq_table: dict, n=25):
    return sorted(freq_table.items(), key=lambda x: x[1], reverse=True)[:n]

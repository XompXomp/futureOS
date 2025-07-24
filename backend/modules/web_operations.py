from config.settings import settings

class WebOperations:
    @staticmethod
    def search_web(state: dict) -> dict:
        query = state.get('query', '')
        from googleapiclient.discovery import build
        api_key = settings.GOOGLE_PSE_API_KEY
        cx = settings.GOOGLE_PSE_CX
        if not api_key or not cx:
            state['results'] = 'Google PSE API key or CX not set.'
            return state
        service = build("customsearch", "v1", developerKey=api_key)
        try:
            search_results = service.cse().list(q=query, cx=cx, num=5).execute()
            results = []
            for item in search_results.get('items', []):
                results.append({
                    'title': item.get('title', ''),
                    'link': item.get('link', ''),
                    'snippet': item.get('snippet', ''),
                    'displayLink': item.get('displayLink', '')
                })
            state['results'] = results if results else 'No results found.'
            return state
        except Exception as e:
            state['results'] = str(e)
            return state 

            
from .search_request import SearchRequest
import requests
from bs4 import BeautifulSoup
import asyncio

MIRROR_SOURCES = ["GET", "Cloudflare", "IPFS.io", "Infura"]

class LibgenSearch:
    def __init__(self, search_category="fiction", search_language="english"):
        self.search_category = search_category.lower()
        self.search_language = search_language.lower()

    async def search_title(self, query):
        """
        Asynchronously search by title only
        """
        try:
            search_request = SearchRequest(query, search_category=self.search_category, search_language=self.search_language)
            return await search_request.aggregate_request_data()
        except Exception as e:
            raise Exception(f"Error finding title: {str(e)}")

    async def search_filtered(self, query, filters, exact_match=True) -> List[str]:
        """
        Asynchronously search filtered results

        Args: 
            query, filters, exact_match (boolean)
        
        Returns:
            List[str]: A string array of filtered results

        Raises:

        """

        try:
            search_request = SearchRequest(query, search_category=self.search_category, search_language=self.search_language)
            if !search_request:
                raise Exception("No results found")
            
            results = await search_request.aggregate_request_data()

            filtered_results = await filter_results(
                results = results, filters = filters, exact_match=exact_match
            )
            return filtered_results

        except Exception as e:
            raise Exception(f"Error searching: {str(e)}")


    async def resolve_download_links(self, item: dict) -> Dict[str, str]:
        """
        Asynchronously resolves download links from a mirror URL.
        
        Args:
            item (dict): Dictionary containing mirror URLs under the "Mirrors" key
            
        Returns:
            Dict[str, str]: Dictionary mapping mirror source names to their download URLs
            
        Raises:
            KeyError: If "Mirrors" key is missing or empty
            aiohttp.ClientError: If there's an error fetching the page
        """
        try:
            mirrors: List[str] = item["Mirrors"]
            if not mirrors:
                raise KeyError("No mirrors found in item")
                
            mirror_url: str = mirrors[0]
            
            async with aiohttp.ClientSession() as session:
                async with session.get(mirror_url) as response:
                    response.raise_for_status()
                    page_content = await response.text()
                    
            soup = BeautifulSoup(page_content, "html.parser")
            links = soup.find_all("a", string=MIRROR_SOURCES)
            
            download_links = {
                link.string: link["href"] 
                for link in links 
                if link.get("href")
            }
            
            return download_links
            
        except KeyError as e:
            raise KeyError(f"Invalid item structure: {str(e)}")
        except aiohttp.ClientError as e:
            raise aiohttp.ClientError(f"Failed to fetch mirror page: {str(e)}")
        except Exception as e:
            raise Exception(f"Error resolving download links: {str(e)}")


    async def filter_results(results, filters, exact_match):
        """
        Returns a list of results that match the given filter criteria.
        When exact_match = true, we only include results that exactly match
        the filters (ie. the filters are an exact subset of the result).

        When exact-match = false,
        we run a case-insensitive check between each filter field and each result.

        exact_match defaults to TRUE -
        this is to maintain consistency with older versions of this library.
        """

        filtered_list = []
        if exact_match:
            for result in results:
                # check whether a candidate result matches the given filters
                if filters.items() <= result.items():
                    filtered_list.append(result)

        else:
            filter_matches_result = False
            for result in results:
                for field, query in filters.items():
                    if query.casefold() in result[field].casefold():
                        filter_matches_result = True
                    else:
                        filter_matches_result = False
                        break
                if filter_matches_result:
                    filtered_list.append(result)
        print(filtered_list)
        return filtered_list

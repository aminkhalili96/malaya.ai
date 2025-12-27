"""
Price Comparison Service
Searches Shopee and Lazada for product prices.
"""
import os
import re
from typing import List, Dict, Optional
import httpx
from bs4 import BeautifulSoup

class PriceComparisonService:
    """
    Compares product prices across Shopee and Lazada Malaysia.
    Uses web scraping for real-time prices.
    """
    
    PLATFORMS = {
        "shopee": {
            "search_url": "https://shopee.com.my/search?keyword={query}",
            "base_url": "https://shopee.com.my"
        },
        "lazada": {
            "search_url": "https://www.lazada.com.my/catalog/?q={query}",
            "base_url": "https://www.lazada.com.my"
        }
    }
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    async def search_shopee(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        Search Shopee Malaysia for products.
        Note: Shopee uses heavy JS rendering, so this returns API-based results.
        """
        # Shopee API endpoint (simplified)
        api_url = f"https://shopee.com.my/api/v4/search/search_items?keyword={query}&limit={max_results}"
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(api_url, headers=self.HEADERS)
                
                if response.status_code != 200:
                    return []
                
                data = response.json()
                items = data.get("items", [])
                
                results = []
                for item in items[:max_results]:
                    item_data = item.get("item_basic", {})
                    results.append({
                        "platform": "Shopee",
                        "name": item_data.get("name", ""),
                        "price": item_data.get("price", 0) / 100000,  # Convert from cents
                        "original_price": item_data.get("price_before_discount", 0) / 100000,
                        "rating": item_data.get("item_rating", {}).get("rating_star", 0),
                        "sold": item_data.get("sold", 0),
                        "url": f"https://shopee.com.my/product/{item_data.get('shopid')}/{item_data.get('itemid')}",
                        "image": f"https://cf.shopee.com.my/file/{item_data.get('image')}"
                    })
                
                return results
        except Exception as e:
            return [{"error": str(e), "platform": "Shopee"}]
    
    async def search_lazada(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        Search Lazada Malaysia for products.
        """
        search_url = f"https://www.lazada.com.my/catalog/?q={query.replace(' ', '+')}"
        
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(search_url, headers=self.HEADERS)
                
                if response.status_code != 200:
                    return []
                
                soup = BeautifulSoup(response.text, "html.parser")
                
                # Extract product cards (Lazada structure)
                results = []
                product_cards = soup.select("[data-tracking='product-card']")[:max_results]
                
                for card in product_cards:
                    name_elem = card.select_one(".RfADt")
                    price_elem = card.select_one(".ooOxS")
                    link_elem = card.select_one("a")
                    
                    if name_elem and price_elem:
                        price_text = price_elem.get_text()
                        price = float(re.sub(r'[^\d.]', '', price_text) or 0)
                        
                        results.append({
                            "platform": "Lazada",
                            "name": name_elem.get_text().strip(),
                            "price": price,
                            "url": f"https://www.lazada.com.my{link_elem['href']}" if link_elem else "",
                        })
                
                return results
        except Exception as e:
            return [{"error": str(e), "platform": "Lazada"}]
    
    async def compare_prices(
        self, 
        query: str, 
        max_budget: Optional[float] = None,
        max_results: int = 5
    ) -> Dict:
        """
        Compare prices across platforms.
        
        Args:
            query: Product search query
            max_budget: Optional max price filter (in MYR)
            max_results: Max results per platform
            
        Returns:
            dict with platform results, best deals, and summary
        """
        # Search both platforms concurrently
        import asyncio
        shopee_task = self.search_shopee(query, max_results)
        lazada_task = self.search_lazada(query, max_results)
        
        shopee_results, lazada_results = await asyncio.gather(
            shopee_task, lazada_task
        )
        
        all_results = shopee_results + lazada_results
        
        # Filter by budget if specified
        if max_budget:
            all_results = [
                r for r in all_results 
                if r.get("price", float("inf")) <= max_budget
            ]
        
        # Sort by price
        valid_results = [r for r in all_results if "error" not in r and r.get("price", 0) > 0]
        valid_results.sort(key=lambda x: x.get("price", float("inf")))
        
        # Find best deal
        best_deal = valid_results[0] if valid_results else None
        
        return {
            "query": query,
            "shopee": [r for r in shopee_results if "error" not in r],
            "lazada": [r for r in lazada_results if "error" not in r],
            "all_results": valid_results,
            "best_deal": best_deal,
            "price_range": {
                "min": valid_results[0]["price"] if valid_results else None,
                "max": valid_results[-1]["price"] if valid_results else None,
            },
            "total_found": len(valid_results)
        }


# Global instance
price_service = PriceComparisonService()

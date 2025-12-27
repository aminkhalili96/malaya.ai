"""
Currency Converter Service
Real-time currency conversion with MYR as base.
"""
import os
from typing import Dict, Optional
import httpx
from datetime import datetime, timedelta

class CurrencyService:
    """
    Currency conversion service with caching.
    Uses free API for real-time rates.
    """
    
    # Fallback rates (as of Dec 2024)
    FALLBACK_RATES = {
        "USD": 4.47,
        "SGD": 3.31,
        "EUR": 4.67,
        "GBP": 5.62,
        "JPY": 0.029,
        "CNY": 0.61,
        "THB": 0.13,
        "IDR": 0.00028,
        "AUD": 2.85,
        "INR": 0.053,
    }
    
    def __init__(self):
        self.rates_cache: Dict[str, float] = {}
        self.cache_time: Optional[datetime] = None
        self.cache_ttl = timedelta(hours=1)
    
    async def fetch_rates(self) -> Dict[str, float]:
        """
        Fetch latest exchange rates from API.
        Returns rates with MYR as base.
        """
        # Check cache
        if self.cache_time and datetime.now() - self.cache_time < self.cache_ttl:
            return self.rates_cache
        
        try:
            # Using exchangerate.host API (free)
            api_url = "https://api.exchangerate.host/latest?base=MYR"
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(api_url)
                
                if response.status_code == 200:
                    data = response.json()
                    self.rates_cache = data.get("rates", self.FALLBACK_RATES)
                    self.cache_time = datetime.now()
                    return self.rates_cache
        except Exception:
            pass
        
        # Return fallback rates
        return self.FALLBACK_RATES
    
    async def convert(
        self, 
        amount: float, 
        from_currency: str, 
        to_currency: str
    ) -> Dict:
        """
        Convert amount from one currency to another.
        
        Args:
            amount: Amount to convert
            from_currency: Source currency code (e.g., "USD")
            to_currency: Target currency code (e.g., "MYR")
            
        Returns:
            dict with converted amount, rate, and metadata
        """
        rates = await self.fetch_rates()
        from_code = from_currency.upper()
        to_code = to_currency.upper()
        
        # Get rates relative to MYR
        if from_code == "MYR":
            from_rate = 1.0
        else:
            from_rate = 1 / rates.get(from_code, 1.0)
        
        if to_code == "MYR":
            to_rate = 1.0
        else:
            to_rate = rates.get(to_code, 1.0)
        
        # Calculate conversion
        myr_amount = amount * from_rate
        converted_amount = myr_amount * to_rate
        
        # Calculate direct rate
        direct_rate = converted_amount / amount if amount > 0 else 0
        
        return {
            "from": {
                "currency": from_code,
                "amount": amount
            },
            "to": {
                "currency": to_code,
                "amount": round(converted_amount, 2)
            },
            "rate": round(direct_rate, 6),
            "inverse_rate": round(1 / direct_rate, 6) if direct_rate > 0 else 0,
            "timestamp": datetime.now().isoformat(),
            "source": "exchangerate.host"
        }
    
    async def get_myr_rates(self) -> Dict:
        """
        Get common currencies against MYR.
        """
        rates = await self.fetch_rates()
        
        common_currencies = ["USD", "SGD", "EUR", "GBP", "JPY", "CNY", "THB", "IDR"]
        
        return {
            "base": "MYR",
            "rates": {
                code: round(1 / rates.get(code, 1.0), 4)
                for code in common_currencies
                if code in rates
            },
            "updated": datetime.now().isoformat()
        }
    
    def format_amount(self, amount: float, currency: str) -> str:
        """
        Format amount with currency symbol.
        """
        symbols = {
            "MYR": "RM",
            "USD": "$",
            "SGD": "S$",
            "EUR": "€",
            "GBP": "£",
            "JPY": "¥",
            "CNY": "¥",
            "THB": "฿",
            "IDR": "Rp",
        }
        
        symbol = symbols.get(currency.upper(), currency.upper())
        return f"{symbol}{amount:,.2f}"


# Global instance
currency_service = CurrencyService()

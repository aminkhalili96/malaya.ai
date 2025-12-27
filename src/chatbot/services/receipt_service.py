"""
Receipt Scanner Service
OCR receipts and categorize expenses.
"""
import os
from typing import Dict, List, Optional
from openai import AsyncOpenAI
import json

class ReceiptScannerService:
    """
    Scans receipts using GPT-4o Vision and extracts:
    - Store name
    - Date
    - Items with prices
    - Total
    - Categorized expenses
    """
    
    EXPENSE_CATEGORIES = [
        "food & dining",
        "groceries",
        "transportation",
        "utilities",
        "entertainment",
        "shopping",
        "health",
        "education",
        "other"
    ]
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    async def scan_receipt(self, image_base64: str) -> Dict:
        """
        Scan a receipt image and extract structured data.
        
        Args:
            image_base64: Base64 encoded receipt image
            
        Returns:
            dict with store, date, items, total, and category
        """
        # Handle data URL prefix
        if image_base64.startswith("data:"):
            image_base64 = image_base64.split(",")[1]
        
        system_prompt = """You are a receipt scanner. Extract information from the receipt image.

Return JSON in this exact format:
{
    "store_name": "Store name",
    "date": "YYYY-MM-DD or null if not visible",
    "items": [
        {"name": "Item name", "quantity": 1, "price": 10.50}
    ],
    "subtotal": 0.00,
    "tax": 0.00,
    "total": 0.00,
    "payment_method": "cash/card/ewallet or null",
    "currency": "MYR",
    "category": "food & dining/groceries/etc"
}

If something is unclear, make your best guess. All prices should be numbers, not strings."""

        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Extract data from this receipt:"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Add expense tracking metadata
        result["expense_id"] = f"exp_{hash(image_base64[:100])}"
        result["scanned_at"] = self._get_timestamp()
        
        return result
    
    async def categorize_expense(self, description: str, amount: float) -> str:
        """
        Categorize an expense based on description.
        """
        prompt = f"""Categorize this expense into exactly one category:

Expense: {description}
Amount: RM{amount}

Categories: {', '.join(self.EXPENSE_CATEGORIES)}

Return only the category name, nothing else."""

        response = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=20
        )
        
        category = response.choices[0].message.content.strip().lower()
        
        # Validate category
        if category not in self.EXPENSE_CATEGORIES:
            category = "other"
        
        return category
    
    async def generate_expense_report(
        self, 
        receipts: List[Dict]
    ) -> Dict:
        """
        Generate expense report from multiple receipts.
        """
        total_spent = sum(r.get("total", 0) for r in receipts)
        
        # Group by category
        by_category = {}
        for receipt in receipts:
            cat = receipt.get("category", "other")
            if cat not in by_category:
                by_category[cat] = {"count": 0, "total": 0, "items": []}
            by_category[cat]["count"] += 1
            by_category[cat]["total"] += receipt.get("total", 0)
            by_category[cat]["items"].append(receipt.get("store_name", "Unknown"))
        
        # Group by store
        by_store = {}
        for receipt in receipts:
            store = receipt.get("store_name", "Unknown")
            if store not in by_store:
                by_store[store] = {"visits": 0, "total": 0}
            by_store[store]["visits"] += 1
            by_store[store]["total"] += receipt.get("total", 0)
        
        return {
            "total_receipts": len(receipts),
            "total_spent": round(total_spent, 2),
            "by_category": by_category,
            "by_store": by_store,
            "top_category": max(by_category.items(), key=lambda x: x[1]["total"])[0] if by_category else None,
            "average_transaction": round(total_spent / len(receipts), 2) if receipts else 0
        }
    
    def _get_timestamp(self) -> str:
        from datetime import datetime
        return datetime.now().isoformat()


# Global instance
receipt_scanner = ReceiptScannerService()

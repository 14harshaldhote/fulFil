#!/usr/bin/env python3
"""
Test Data Generator for Product Importer

This script generates various CSV files to test all scenarios mentioned in the assignment:
- Small datasets (10 products)
- Medium datasets (1,000 products)
- Large datasets (100,000 and 500,000 products)
- Duplicate SKUs with case variations
- Invalid/edge case data
- Unicode and special characters

Usage:
    python generate_test_data.py

Output files will be saved in the same 'data' folder.
"""

import csv
import random
import string
import os
from datetime import datetime

# Output directory (same folder as this script)
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

# Product categories and sample data for realistic generation
CATEGORIES = [
    ("Electronics", ["Smartphone", "Laptop", "Tablet", "Headphones", "Smart Watch", "Camera", "Speaker", "Monitor", "Keyboard", "Mouse"]),
    ("Clothing", ["T-Shirt", "Jeans", "Jacket", "Dress", "Sneakers", "Hat", "Sweater", "Shorts", "Socks", "Hoodie"]),
    ("Home & Garden", ["Chair", "Table", "Lamp", "Rug", "Plant Pot", "Bed Frame", "Bookshelf", "Mirror", "Curtains", "Cushion"]),
    ("Sports", ["Running Shoes", "Yoga Mat", "Dumbbell", "Bicycle", "Tennis Racket", "Football", "Swim Goggles", "Fitness Band", "Jump Rope", "Helmet"]),
    ("Books", ["Novel", "Cookbook", "Biography", "Science Book", "History Book", "Art Book", "Travel Guide", "Self-Help Book", "Dictionary", "Comic Book"]),
]

BRANDS = ["Apple", "Samsung", "Sony", "Nike", "Adidas", "IKEA", "Amazon", "Microsoft", "Google", "LG", "HP", "Dell", "Lenovo", "Asus", "Bose"]

ADJECTIVES = ["Premium", "Professional", "Ultimate", "Compact", "Wireless", "Portable", "Smart", "Classic", "Modern", "Ergonomic", "Eco-Friendly", "Luxury"]


def generate_sku(index: int, case_variation: bool = False) -> str:
    """Generate a SKU with optional case variation for testing case-insensitivity."""
    base_sku = f"SKU-{index:06d}"
    
    if case_variation:
        # Randomly vary the case
        variations = [
            base_sku.upper(),           # SKU-000001
            base_sku.lower(),           # sku-000001
            base_sku.capitalize(),      # Sku-000001
            f"sKu-{index:06d}",         # sKu-000001
            f"Sku-{index:06d}",         # Sku-000001
        ]
        return random.choice(variations)
    
    return base_sku


def generate_product_name() -> str:
    """Generate a realistic product name."""
    category, products = random.choice(CATEGORIES)
    product = random.choice(products)
    brand = random.choice(BRANDS)
    adjective = random.choice(ADJECTIVES)
    
    # Various name formats
    formats = [
        f"{brand} {product}",
        f"{brand} {adjective} {product}",
        f"{adjective} {product} by {brand}",
        f"{product} - {brand}",
        f"{brand} {product} {random.randint(1, 20)}",
    ]
    
    return random.choice(formats)


def generate_description() -> str:
    """Generate a realistic product description."""
    features = [
        "High quality materials",
        "Fast shipping available",
        "1-year warranty included",
        "Best seller in category",
        "Customer favorite",
        "Limited edition",
        "Free returns",
        "Eco-friendly packaging",
        "Award-winning design",
        "Made with premium components",
    ]
    
    desc_parts = random.sample(features, random.randint(2, 4))
    return ". ".join(desc_parts) + "."


def generate_price() -> float:
    """Generate a realistic price."""
    return round(random.uniform(9.99, 2999.99), 2)


def write_csv(filename: str, rows: list, include_header: bool = True):
    """Write rows to a CSV file."""
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        if include_header:
            writer.writerow(['sku', 'name', 'description', 'price'])
        
        for row in rows:
            writer.writerow(row)
    
    print(f"✅ Generated: {filename} ({len(rows)} rows)")
    return filepath


def generate_small_dataset():
    """
    Test Case 1: Small CSV Upload (10 products)
    - Basic import test
    - All valid data
    """
    rows = []
    for i in range(1, 11):
        rows.append([
            generate_sku(i),
            generate_product_name(),
            generate_description(),
            generate_price()
        ])
    
    write_csv("test_small_10_products.csv", rows)


def generate_medium_dataset():
    """
    Test Case: Medium CSV Upload (1,000 products)
    - Performance baseline
    - Mix of data
    """
    rows = []
    for i in range(1, 1001):
        rows.append([
            generate_sku(i),
            generate_product_name(),
            generate_description(),
            generate_price()
        ])
    
    write_csv("test_medium_1000_products.csv", rows)


def generate_large_dataset(count: int, filename: str):
    """
    Test Case 2: Large CSV (Performance Test)
    - 100K or 500K rows
    - Tests async processing and batch inserts
    """
    rows = []
    
    print(f"⏳ Generating {count:,} products (this may take a moment)...")
    
    for i in range(1, count + 1):
        rows.append([
            generate_sku(i),
            generate_product_name(),
            generate_description(),
            generate_price()
        ])
        
        if i % 50000 == 0:
            print(f"   Generated {i:,} / {count:,}...")
    
    write_csv(filename, rows)


def generate_duplicate_sku_test():
    """
    Test Case 3: Duplicate SKU (Overwrite Test)
    - Same SKU with different cases
    - Should result in ONE product with last data
    """
    rows = [
        # First occurrence
        ["SKU-001", "Old Product Name", "Original description", 100.00],
        # Duplicate with different case - should OVERWRITE
        ["sku-001", "New Product Name", "Updated description", 120.00],
        # Another product
        ["SKU-002", "Another Product", "Some description", 50.00],
        # Duplicate of SKU-002 with mixed case
        ["Sku-002", "Updated Another Product", "New description", 55.00],
        # Triple duplicate with SKU-003
        ["SKU-003", "First Version", "V1 desc", 10.00],
        ["sku-003", "Second Version", "V2 desc", 20.00],
        ["sKu-003", "Third Version (Final)", "V3 desc - should be this one", 30.00],
        # Normal unique products
        ["SKU-004", "Unique Product 1", "Desc 1", 40.00],
        ["SKU-005", "Unique Product 2", "Desc 2", 50.00],
    ]
    
    write_csv("test_duplicate_sku_overwrite.csv", rows)


def generate_invalid_rows_test():
    """
    Test Case 4: Invalid Rows
    - Missing required fields
    - Invalid data types
    - Edge cases
    """
    rows = [
        # Valid rows
        ["SKU-VALID-001", "Valid Product 1", "Good description", 99.99],
        ["SKU-VALID-002", "Valid Product 2", "Another good description", 149.99],
        
        # Invalid: Missing SKU (empty)
        ["", "Product Without SKU", "Should be skipped", 50.00],
        
        # Invalid: SKU is just whitespace
        ["   ", "Product With Whitespace SKU", "Should be skipped", 60.00],
        
        # Valid: Missing name (should use SKU as name)
        ["SKU-NO-NAME", "", "Description only", 70.00],
        
        # Valid: Missing description (optional field)
        ["SKU-NO-DESC", "Product Without Description", "", 80.00],
        
        # Edge case: Price not numeric (should handle gracefully)
        ["SKU-BAD-PRICE", "Product with Bad Price", "Description", "abc"],
        
        # Valid: Very long description
        ["SKU-LONG-DESC", "Long Description Product", "A" * 500, 100.00],
        
        # Valid: Unicode in name and description
        ["SKU-UNICODE", "日本語製品 Product", "Description with émojis 🎉 and spëcial çharacters", 200.00],
        
        # Edge case: Price is zero
        ["SKU-ZERO-PRICE", "Free Product", "Price is zero", 0.00],
        
        # Edge case: Negative price
        ["SKU-NEG-PRICE", "Negative Price Product", "Should handle this", -50.00],
        
        # Valid rows at the end
        ["SKU-VALID-003", "Final Valid Product", "Last good one", 299.99],
    ]
    
    write_csv("test_invalid_rows.csv", rows)


def generate_edge_cases_test():
    """
    Test Case: Edge Cases
    - Extra columns (should be ignored)
    - Whitespace trimming
    - Unicode and special characters
    """
    # Note: This CSV has an extra column that should be ignored
    rows = [
        ["SKU-EDGE-001", "  Whitespace Trimmed Name  ", "  Description with spaces  ", 99.99],
        ["SKU-EDGE-002", "Unicode: 中文 العربية हिन्दी", "Multi-language support test", 149.99],
        ["SKU-EDGE-003", "Special: @#$%^&*()", "Symbols in name", 199.99],
        ["SKU-EDGE-004", "Quotes: \"Double\" and 'Single'", "Quote handling", 249.99],
        ["SKU-EDGE-005", "Commas, In, Name", "Comma escaping test", 299.99],
        ["SKU-EDGE-006", "Newline\nIn\nName", "Newline handling", 349.99],
        ["  SKU-EDGE-007  ", "SKU with whitespace", "Should trim SKU", 399.99],
        ["sku-edge-008", "Lowercase SKU", "Case handling", 449.99],
        ["SKU-EDGE-009", "Tab\tIn\tName", "Tab character test", 499.99],
        ["SKU-EDGE-010", "Very Long Name " * 20, "Long name test", 549.99],
    ]
    
    write_csv("test_edge_cases.csv", rows)


def generate_realistic_mixed_test():
    """
    Test Case: Realistic Mixed Data (500 products)
    - Combination of valid, duplicate, and edge cases
    - Good for demo purposes
    """
    rows = []
    
    # 400 normal valid products
    for i in range(1, 401):
        rows.append([
            generate_sku(i),
            generate_product_name(),
            generate_description(),
            generate_price()
        ])
    
    # 50 products with case-varied SKUs (some will be duplicates of above)
    for i in range(1, 51):  # These duplicate SKUs 1-50
        rows.append([
            generate_sku(i, case_variation=True),
            f"Updated: {generate_product_name()}",
            f"Updated: {generate_description()}",
            generate_price()
        ])
    
    # 30 products with edge cases
    edge_cases = [
        ["SKU-SPECIAL-001", "Unicode: 日本語 Product", "Japanese description", 999.99],
        ["SKU-SPECIAL-002", "Emoji: 🎉 Party Product", "Fun product with emoji", 49.99],
        ["SKU-SPECIAL-003", "", "No name product", 19.99],  # Empty name
        ["SKU-SPECIAL-004", "Long " * 50, "Very long name", 29.99],
        ["SKU-SPECIAL-005", "Quotes \"Test\"", "Quote handling", 39.99],
    ]
    rows.extend(edge_cases)
    
    # 20 more normal products
    for i in range(501, 521):
        rows.append([
            generate_sku(i),
            generate_product_name(),
            generate_description(),
            generate_price()
        ])
    
    # Shuffle to make it more realistic
    random.shuffle(rows)
    
    write_csv("test_realistic_mixed_500.csv", rows)


def generate_all():
    """Generate all test CSV files."""
    print("\n" + "="*60)
    print("🔧 Product Importer - Test Data Generator")
    print("="*60 + "\n")
    
    # 1. Small dataset (10 products)
    generate_small_dataset()
    
    # 2. Medium dataset (1,000 products)
    generate_medium_dataset()
    
    # 3. Duplicate SKU test
    generate_duplicate_sku_test()
    
    # 4. Invalid rows test
    generate_invalid_rows_test()
    
    # 5. Edge cases test
    generate_edge_cases_test()
    
    # 6. Realistic mixed test (500 products)
    generate_realistic_mixed_test()
    
    # 7. Large datasets (optional - uncomment to generate)
    print("\n" + "-"*60)
    print("📦 Large Dataset Generation (may take time)")
    print("-"*60)
    
    generate_large_dataset(100000, "test_large_100k_products.csv")
    
    # Uncomment below for 500K dataset (takes longer, ~100MB file)
    # generate_large_dataset(500000, "test_large_500k_products.csv")
    
    print("\n" + "="*60)
    print("✅ All test files generated successfully!")
    print("="*60)
    print(f"\n📁 Output directory: {OUTPUT_DIR}")
    print("\n📋 Generated files:")
    print("   - test_small_10_products.csv         (Basic import test)")
    print("   - test_medium_1000_products.csv      (Medium scale test)")
    print("   - test_duplicate_sku_overwrite.csv   (SKU case-insensitivity test)")
    print("   - test_invalid_rows.csv              (Error handling test)")
    print("   - test_edge_cases.csv                (Unicode/special chars test)")
    print("   - test_realistic_mixed_500.csv       (Combined scenarios test)")
    print("   - test_large_100k_products.csv       (Performance test)")
    print("\n💡 Tip: Start with small files, then test large files for performance.\n")


if __name__ == "__main__":
    generate_all()

# Catalog ingest notes

Source: `ManikaSaini/zomato-restaurant-recommendation`

This Hugging Face dump is **Bangalore** Zomato listings (neighborhoods such as Banashankari,
not a multi-city India dump). Prefer UI examples that exist in the tables below — e.g.
`Bangalore` (city), `Banashankari` / `Indiranagar` / `Koramangala` (location),
`Italian` / `Chinese` / `North Indian` (cuisine).

## Last ingest

- Rows: **51696**
- Budget cutoffs (cost for two): low <= 300.00; medium <= 600.00; above that is high
- Cost min / median / max: 40.0 / 400.0 / 6000.0
- Rows with rating: 41665
- Rows with cost: 51371

### Top cities

- Bangalore: 49712
- Delhi: 2

### Top locations

- BTM: 5124
- HSR: 2523
- Koramangala 5th Block: 2504
- JP Nagar: 2235
- Whitefield: 2144
- Indiranagar: 2083
- Jayanagar: 1926
- Marathahalli: 1846
- Bannerghatta Road: 1630
- Bellandur: 1286
- Electronic City: 1258
- Koramangala 1st Block: 1238
- Brigade Road: 1218
- Koramangala 7th Block: 1181
- Koramangala 6th Block: 1156

### Top cuisines

- North Indian: 21085
- Chinese: 15547
- South Indian: 8644
- Fast Food: 8096
- Biryani: 6492
- Continental: 5765
- Desserts: 5633
- Cafe: 5303
- Beverages: 4747
- Italian: 3389
- Bakery: 2840
- Street Food: 2595
- Pizza: 2073
- Burger: 2009
- Seafood: 1810

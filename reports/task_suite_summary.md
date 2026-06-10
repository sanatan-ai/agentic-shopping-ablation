# Task Suite Summary

- **Total tasks:** 50
- **Catalogue source:** `data\processed\catalogue.parquet`
- **Random seed:** 42

## Distribution

**By bucket:**

- Cameras: 10
- Headphones: 10
- LaptopAccessories: 10
- PhoneAccessories: 10
- Watches: 10

**By difficulty:**

- Easy: 15
- Medium: 20
- Hard: 15

**By preference:**

- cheapest: 24
- highest_rated: 26

**Crosstab (bucket × difficulty):**

| Bucket | Easy | Medium | Hard | Total |
|---|---|---|---|---|
| Cameras | 3 | 2 | 5 | 10 |
| Headphones | 3 | 7 | 0 | 10 |
| LaptopAccessories | 3 | 2 | 5 | 10 |
| PhoneAccessories | 3 | 2 | 5 | 10 |
| Watches | 3 | 7 | 0 | 10 |

## Valid-set statistics

- Min valid-set size: 2
- Max valid-set size: 30
- Median valid-set size: 12
- Tasks with multiple optima (ties): 12

## Sample tasks (one per difficulty)

### Easy (T005, PhoneAccessories)

**Prompt:** *I need a phone accessory priced below $8.00. Pick the highest-rated one.*

- Constraints: bucket=PhoneAccessories, max_price=$8.0, min_stars=None, brand=None
- Preference: highest_rated
- Valid-set size: 21; optimal: ['B0C9TXDGBC']

### Medium (T002, Headphones)

**Prompt:** *Looking for the best-rated pair of headphones under $17.00 with 4.5+ stars.*

- Constraints: bucket=Headphones, max_price=$17.0, min_stars=4.5, brand=None
- Preference: highest_rated
- Valid-set size: 9; optimal: ['7313205112', 'B0B652YMTF', 'B0CC6DSJQG', 'B0CGHZ9W2J', 'B0BXDBVYYM']

### Hard (T001, PhoneAccessories)

**Prompt:** *I need a phone accessory by Samsung, priced below $10.00, rated at least 4.5 stars. Pick the cheapest one.*

- Constraints: bucket=PhoneAccessories, max_price=$10.0, min_stars=4.5, brand=Samsung
- Preference: cheapest
- Valid-set size: 5; optimal: ['B09Q8Q2DK2']
